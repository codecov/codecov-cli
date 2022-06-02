import typing
import uuid
from pathlib import Path

import click

from codecov_cli.helpers.coverage_file_finder import select_coverage_file_finder
from codecov_cli.helpers.network_finder import select_network_finder
from codecov_cli.helpers.upload_sender import UploadSender
from codecov_cli.helpers.versioning_systems import VersioningSystemInterface
from codecov_cli.plugins import select_preparation_plugins
from codecov_cli.upload_collector import UploadCollector


def do_upload_logic(
    cli_config: typing.Dict,
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
    preparation_plugins = select_preparation_plugins(cli_config, plugin_names)
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
        click.secho(
            f"Upload process had {number_warnings} {pluralization}",
            fg="yellow",
        )
        for ind, w in enumerate(sending_result.warnings):
            click.echo(click.style(f"Warning {ind + 1}: {w.message}", fg="yellow"))
    if sending_result.error is not None:
        click.echo(click.style(f"Upload failed: {sending_result.error}", fg="red"))
    return sending_result
