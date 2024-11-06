import logging
import os
import pathlib
import typing

import click

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.config import CODECOV_INGEST_URL
from codecov_cli.helpers.encoder import decode_slug, encode_slug
from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
)
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
MAX_NUMBER_TRIES = 3


def combined_upload_logic(
    cli_config: typing.Dict,
    versioning_system: VersioningSystemInterface,
    ci_adapter: CIAdapterBase,
    *,
    branch: typing.Optional[str],
    build_code: typing.Optional[str],
    build_url: typing.Optional[str],
    commit_sha: str,
    disable_file_fixes: bool,
    disable_search: bool,
    dry_run: bool,
    enterprise_url: typing.Optional[str],
    env_vars: typing.Dict[str, str],
    fail_on_error: bool,
    files_search_exclude_folders: typing.List[pathlib.Path],
    files_search_explicitly_listed_files: typing.List[pathlib.Path],
    files_search_root_folder: pathlib.Path,
    flags: typing.List[str],
    gcov_args: typing.Optional[str],
    gcov_executable: typing.Optional[str],
    gcov_ignore: typing.Optional[str],
    gcov_include: typing.Optional[str],
    git_service: typing.Optional[str],
    handle_no_reports_found: bool,
    job_code: typing.Optional[str],
    name: typing.Optional[str],
    network_filter: typing.Optional[str],
    network_prefix: typing.Optional[str],
    network_root_folder: pathlib.Path,
    parent_sha: typing.Optional[str],
    plugin_names: typing.List[str],
    pull_request_number: typing.Optional[str],
    report_code: str,
    slug: typing.Optional[str],
    swift_project: typing.Optional[str],
    token: typing.Optional[str],
    use_legacy_uploader: bool,
    upload_file_type: str = "coverage",
    args: dict = None,
):
    plugin_config = {
        "folders_to_ignore": files_search_exclude_folders,
        "gcov_args": gcov_args,
        "gcov_executable": gcov_executable,
        "gcov_ignore": gcov_ignore,
        "gcov_include": gcov_include,
        "project_root": files_search_root_folder,
        "swift_project": swift_project,
    }
    if upload_file_type == "coverage":
        preparation_plugins = select_preparation_plugins(
            cli_config, plugin_names, plugin_config
        )
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
        preparation_plugins,
        network_finder,
        file_selector,
        disable_file_fixes,
        plugin_config,
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
        # sender = LegacyUploadSender()
        raise NotImplementedError("Legacy uploader is not implemented")
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
            branch=branch,
            build_code=build_code,
            build_url=build_url,
            ci_service=ci_service,
            commit_sha=commit_sha,
            enterprise_url=enterprise_url,
            env_vars=env_vars,
            flags=flags,
            git_service=git_service,
            job_code=job_code,
            name=name,
            parent_sha=parent_sha,
            pull_request_number=pull_request_number,
            report_code=report_code,
            slug=slug,
            token=token,
            upload_file_type=upload_file_type,
            combined_upload=True,
            args=args,
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
