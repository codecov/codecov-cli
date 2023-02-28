import logging
import typing
import uuid
from pathlib import Path

import click

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.request import log_warnings_and_errors_if_any
from codecov_cli.helpers.versioning_systems import VersioningSystemInterface
from codecov_cli.plugins import select_preparation_plugins
from codecov_cli.services.upload.coverage_file_finder import select_coverage_file_finder
from codecov_cli.services.upload.legacy_upload_sender import LegacyUploadSender
from codecov_cli.services.upload.network_finder import select_network_finder
from codecov_cli.services.upload.upload_collector import UploadCollector
from codecov_cli.services.upload.upload_sender import UploadSender
from codecov_cli.types import RequestResult

logger = logging.getLogger("codecovcli")


def do_upload_logic(
    cli_config: typing.Dict,
    versioning_system: VersioningSystemInterface,
    ci_adapter: CIAdapterBase,
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
    coverage_files_search_root_folder: Path,
    coverage_files_search_exclude_folders: typing.List[Path],
    coverage_files_search_explicitly_listed_files: typing.List[Path],
    plugin_names: typing.List[str],
    token: uuid.UUID,
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    pull_request_number: typing.Optional[str],
    use_legacy_uploader: bool = False,
    fail_on_error: bool = False,
    dry_run: bool = False,
    git_service: typing.Optional[str],
):
    preparation_plugins = select_preparation_plugins(cli_config, plugin_names)
    coverage_file_selector = select_coverage_file_finder(
        coverage_files_search_root_folder,
        coverage_files_search_exclude_folders,
        coverage_files_search_explicitly_listed_files,
    )
    network_finder = select_network_finder(versioning_system)
    collector = UploadCollector(
        preparation_plugins, network_finder, coverage_file_selector
    )
    upload_data = collector.generate_upload_data()
    if use_legacy_uploader:
        sender = LegacyUploadSender()
    else:
        sender = UploadSender()
    logger.debug(f"Selected uploader to use: {type(sender)}")
    ci_service = (
        ci_adapter.get_fallback_value(FallbackFieldEnum.service)
        if ci_adapter is not None
        else None
    )

    if not dry_run:
        sending_result = sender.send_upload_data(
            upload_data,
            commit_sha,
            token,
            env_vars,
            report_code,
            name,
            branch,
            slug,
            pull_request_number,
            build_code,
            build_url,
            job_code,
            flags,
            ci_service,
            git_service,
        )
    else:
        logger.info("dry-run option activated. NOT sending data to Codecov.")
        sending_result = RequestResult(
            error=None,
            warnings=None,
            status_code=200,
            text="Data NOT sent to Codecov because of dry-run option",
        )
    log_warnings_and_errors_if_any(sending_result, "Upload", fail_on_error)
    return sending_result
