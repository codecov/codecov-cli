import logging
import typing
from pathlib import Path

import click

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.request import log_warnings_and_errors_if_any
from codecov_cli.helpers.versioning_systems import VersioningSystemInterface
from codecov_cli.plugins import select_preparation_plugins
from codecov_cli.services.upload.file_finder import select_file_finder
from codecov_cli.services.upload.legacy_upload_sender import LegacyUploadSender
from codecov_cli.services.upload.network_finder import select_network_finder
from codecov_cli.services.upload.upload_collector import UploadCollector
from codecov_cli.services.upload.upload_sender import UploadSender
from codecov_cli.services.upload_completion import upload_completion_logic
from codecov_cli.types import RequestResult

logger = logging.getLogger("codecovcli")


def do_upload_logic(
    cli_config: typing.Dict,
    versioning_system: VersioningSystemInterface,
    ci_adapter: CIAdapterBase,
    *,
    branch: typing.Optional[str],
    build_code: typing.Optional[str],
    build_url: typing.Optional[str],
    commit_sha: str,
    disable_file_fixes: bool = False,
    disable_search: bool = False,
    dry_run: bool = False,
    enterprise_url: typing.Optional[str],
    env_vars: typing.Dict[str, str],
    fail_on_error: bool = False,
    files_search_exclude_folders: typing.List[Path],
    files_search_explicitly_listed_files: typing.List[Path],
    files_search_root_folder: Path,
    flags: typing.List[str],
    git_service: typing.Optional[str],
    handle_no_reports_found: bool = False,
    job_code: typing.Optional[str],
    name: typing.Optional[str],
    network_filter: typing.Optional[str],
    network_prefix: typing.Optional[str],
    network_root_folder: Path,
    plugin_names: typing.List[str],
    pull_request_number: typing.Optional[str],
    report_code: str,
    slug: typing.Optional[str],
    token: str,
    upload_file_type: str = "coverage",
    use_legacy_uploader: bool = False,
):
    if upload_file_type == "coverage":
        preparation_plugins = select_preparation_plugins(cli_config, plugin_names)
    elif upload_file_type == "test_results":
        preparation_plugins = []
    file_selector = select_file_finder(
        files_search_root_folder,
        files_search_exclude_folders,
        files_search_explicitly_listed_files,
        disable_search,
        upload_file_type,
    )
    network_finder = select_network_finder(
        versioning_system,
        network_filter=network_filter,
        network_prefix=network_prefix,
        network_root_folder=network_root_folder,
    )
    collector = UploadCollector(
        preparation_plugins, network_finder, file_selector, disable_file_fixes
    )
    try:
        upload_data = collector.generate_upload_data(upload_file_type)
    except click.ClickException as exp:
        if handle_no_reports_found:
            logger.info(
                "No coverage reports found. Triggering notificaions without uploading."
            )
            upload_completion_logic(
                commit_sha=commit_sha,
                slug=slug,
                token=token,
                git_service=git_service,
                enterprise_url=enterprise_url,
                fail_on_error=fail_on_error,
            )
            return RequestResult(
                error=None,
                warnings=None,
                status_code=200,
                text="No coverage reports found. Triggering notificaions without uploading.",
            )
        else:
            raise exp
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
            upload_file_type,
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
            enterprise_url,
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
