import os
import typing
import uuid
from dataclasses import dataclass
from pathlib import Path

import click
import requests

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.network import GitFileFinder
from codecov_cli.plugins import select_preparation_plugins
from codecov_cli.types import UploadCollectionResult
from codecov_cli.types import Feature
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
        self, upload_data: UploadCollectionResult
    ) -> UploadSendingResult:
        payload = {
            "network": upload_data.network,
        }
        params = {
            "package": f"codecov-cli/{codecov_cli_version}",
            "commit": upload_data.commit_sha,
        }
        headers = {"X-Upload-Token": upload_data.token.hex}

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

        reports_payload = self._generate_payload(upload_data)
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

    def _generate_payload(self, upload_data: UploadCollectionResult) -> bytes:
        env_vars_section = self._generate_env_vars_section(upload_data)
        return env_vars_section

    def _generate_env_vars_section(self, upload_data: UploadCollectionResult) -> bytes:
        env_vars = (
            upload_data.env_vars_clargs
            if upload_data.env_vars_clargs
            else self._get_env_vars()
        )

        filtered_env_vars = {
            key: value for key, value in env_vars.items() if value is not None
        }

        if not filtered_env_vars:
            return b""

        env_vars_section = "".join(
            f"{env_var}={value}\n" for env_var, value in filtered_env_vars.items()
        )
        return env_vars_section.encode() + b"<<<<<< ENV\n"

    def _get_env_vars(self) -> typing.Dict[str, typing.Optional[str]]:
        """Extracts and formats upload environment variables from CODECOV_ENV environment variable, or empty dictionary if CODECOV_ENV not found"""
        codecov_env = os.getenv("CODECOV_ENV", None)
        if not codecov_env:
            return {}

        return {var: os.getenv(var, None) for var in codecov_env.split(",")}


class CoverageFileFinder(object):
    def find_coverage_files(self):
        return []


def select_network_finder(root_network_folder):
    return GitFileFinder(root_network_folder)


def select_coverage_file_finder():
    return CoverageFileFinder()


def do_upload_logic(
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
    toggled_features: frozenset[str],
    network_prefix: typing.Optional[str],
    network_filter: typing.Optional[str],
):
    preparation_plugins = select_preparation_plugins(plugin_names)
    network_finder = select_network_finder(network_root_folder)
    coverage_file_selector = select_coverage_file_finder()
    collector = UploadCollector(
        preparation_plugins, network_finder, coverage_file_selector
    )
    upload_data = collector.generate_upload_data(
        commit_sha, token, env_vars, toggled_features, network_prefix, network_filter
    )
    print(upload_data)
    sender = UploadSender()
    sending_result = sender.send_upload_data(upload_data)
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
