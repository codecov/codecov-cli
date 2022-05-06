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
from codecov_cli.types import UploadCollectionResult, UploadCollectionResultFile
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
        self,
        upload_data: UploadCollectionResult,
        commit_sha: str,
        token: uuid.UUID,
        env_vars: typing.Dict[str, str],
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

        reports_payload = self._generate_payload(upload_data, env_vars)
        resp = requests.put(put_url, data=reports_payload)

        if resp.status_code >= 400:
            return UploadSendingResult(
                error=UploadSendingError(
                    code=f"HTTP Error {resp.status_code}",
                    description=resp.text,
                    params={},
                ),
                warnings=[UploadSendingResultWarning("This did not go perfectly")],
            )

        return UploadSendingResult(error=None, warnings=[])

    def _generate_payload(
        self, upload_data: UploadCollectionResult, env_vars: typing.Dict[str, str]
    ) -> bytes:
        env_vars_section = self._generate_env_vars_section(env_vars)
        network_section = self._generate_network_section(upload_data)
        coverage_files_section = self._generage_coverage_files_section(upload_data)

        return b"".join([env_vars_section, network_section, coverage_files_section])

    def _generate_env_vars_section(self, env_vars) -> bytes:
        filtered_env_vars = {
            key: value for key, value in env_vars.items() if value is not None
        }

        if not filtered_env_vars:
            return b""

        env_vars_section = "".join(
            f"{env_var}={value}\n" for env_var, value in filtered_env_vars.items()
        )
        return env_vars_section.encode() + b"<<<<<< ENV\n"

    def _generate_network_section(self, upload_data: UploadCollectionResult) -> bytes:
        network_files = upload_data.network

        if not network_files:
            return b""

        network_files_section = "".join(file + "\n" for file in network_files)
        return network_files_section.encode() + b"<<<<<< network\n"

    def _generage_coverage_files_section(self, upload_data: UploadCollectionResult):
        return b"".join(
            self._formate_coverage_file(file) for file in upload_data.coverage_files
        )

    def _formate_coverage_file(self, file: UploadCollectionResultFile) -> bytes:
        header = b"# path=" + file.get_filename() + b"\n"
        file_content = file.get_content() + b"\n"
        file_end = b"<<<<<< EOF\n"

        return header + file_content + file_end


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
    sending_result = sender.send_upload_data(upload_data, commit_sha, token, env_vars)
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
