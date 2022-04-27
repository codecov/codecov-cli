import typing
import uuid
from dataclasses import dataclass
from pathlib import Path

import click
import requests

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.helpers.coverage_file_finder import select_coverage_file_finder
from codecov_cli.helpers.network_finder import select_network_finder
from codecov_cli.helpers.versioning_systems import VersioningSystemInterface
from codecov_cli.plugins import select_preparation_plugins
from codecov_cli.types import UploadCollectionResult
from codecov_cli.upload_collector import UploadCollector


@dataclass
class UploadSendingResultWarning(object):
    __slots__ = ("message",)
    message: str


@dataclass
class UploadSendingError(object):
    __slots__ = ("code", "params", "description")
    code: str
    params: typing.Dict
    description: str


@dataclass
class UploadSendingResult(object):
    __slots__ = ("error", "warnings")
    error: typing.Optional[UploadSendingError]
    warnings: typing.List[UploadSendingResultWarning]


class UploadSender(object):
    def send_upload_data(
        self, upload_data: UploadCollectionResult, commit_sha: str, token: uuid.UUID
    ) -> UploadSendingResult:
        
        params = {
            "package": f"codecov-cli/{codecov_cli_version}",
            "commit": commit_sha,
        }
        headers = {"X-Upload-Token": token.hex}

        resp = requests.post(
            "https://codecov.io/upload/v4", headers=headers, params=params
        )

        if resp.status_code >= 400:
            return UploadSendingResult(
                error=UploadSendingError(
                    code=f"HTTP Error {resp.status_code}",
                    description=resp.text,
                    params={},
                ),
                warnings=[UploadSendingResultWarning("This did not go perfectly")],
            )

        result_url, put_url = resp.text.split("\n")
        return UploadSendingResult(error=None, warnings=[])


def do_upload_logic(
    versioning_system: VersioningSystemInterface,
    *,
    commit_sha: str,
    report_code: str,
    build_code: typing.Optional[str],
    build_url: typing.Optional[str],
    job_code: typing.Optional[str],
    env_vars: typing.Dict[str, str],
    flags: typing.List[str],
    name: typing.Optional[str],
    network_root_folder: Path,
    coverage_files_search_folder: Path,
    plugin_names: typing.List[str],
    token: uuid.UUID,
):
    preparation_plugins = select_preparation_plugins(plugin_names)
    coverage_file_selector = select_coverage_file_finder()
    network_finder = select_network_finder(versioning_system)
    collector = UploadCollector(
        preparation_plugins, network_finder, coverage_file_selector
    )
    upload_data = collector.generate_upload_data()
    sender = UploadSender()
    sending_result = sender.send_upload_data(upload_data, commit_sha, token)
    if sending_result.warnings:
        number_warnings = len(sending_result.warnings)
        pluralization = "warnings" if number_warnings > 1 else "warning"
        click.echo(
            click.style(
                f"Upload process had {number_warnings} {pluralization}",
                fg="yellow",
            )
        )
        for ind, w in enumerate(sending_result.warnings):
            click.echo(click.style(f"Warning {ind + 1}: {w.message}", fg="yellow"))
    if sending_result.error is not None:
        click.echo(click.style(f"Upload failed: {sending_result.error}", fg="red"))
    return sending_result
