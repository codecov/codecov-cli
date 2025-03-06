import logging
import pathlib
import typing

import click
import sentry_sdk

from codecov_cli.commands.commit import create_commit
from codecov_cli.commands.report import create_report
from codecov_cli.commands.upload import do_upload, global_upload_options
from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.options import global_options
from codecov_cli.opentelemetry import close_telem
from codecov_cli.helpers.upload_type import report_type_from_str, ReportType
from codecov_cli.services.upload_coverage import upload_coverage_logic
from codecov_cli.types import CommandContext

logger = logging.getLogger("codecovcli")


# These options are the combined options of commit, report and upload commands
@click.command()
@global_options
@global_upload_options
@click.option(
    "--parent-sha",
    help="SHA (with 40 chars) of what should be the parent of this commit",
)
@click.pass_context
def upload_coverage(
    ctx: CommandContext,
    branch: typing.Optional[str],
    build_code: typing.Optional[str],
    build_url: typing.Optional[str],
    commit_sha: str,
    disable_file_fixes: bool,
    disable_search: bool,
    dry_run: bool,
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
    recurse_submodules: bool,
    report_code: str,
    report_type_str: str,
    slug: typing.Optional[str],
    swift_project: typing.Optional[str],
    token: typing.Optional[str],
    use_legacy_uploader: bool,
):
    with sentry_sdk.start_transaction(op="task", name="Upload Coverage"):
        with sentry_sdk.start_span(name="upload_coverage"):
            args = get_cli_args(ctx)
            logger.debug(
                "Starting upload coverage",
                extra=dict(
                    extra_log_attributes=args,
                ),
            )

            report_type = report_type_from_str(report_type_str)

            if not use_legacy_uploader and report_type == ReportType.COVERAGE:
                versioning_system = ctx.obj["versioning_system"]
                codecov_yaml = ctx.obj["codecov_yaml"] or {}
                cli_config = codecov_yaml.get("cli", {})
                ci_adapter = ctx.obj.get("ci_adapter")
                enterprise_url = ctx.obj.get("enterprise_url")
                args = get_cli_args(ctx)
                ctx.invoke(
                    upload_coverage_logic,
                    cli_config,
                    versioning_system,
                    ci_adapter,
                    branch=branch,
                    build_code=build_code,
                    build_url=build_url,
                    commit_sha=commit_sha,
                    disable_file_fixes=disable_file_fixes,
                    disable_search=disable_search,
                    dry_run=dry_run,
                    enterprise_url=enterprise_url,
                    env_vars=env_vars,
                    fail_on_error=fail_on_error,
                    files_search_exclude_folders=files_search_exclude_folders,
                    files_search_explicitly_listed_files=files_search_explicitly_listed_files,
                    files_search_root_folder=files_search_root_folder,
                    flags=flags,
                    gcov_args=gcov_args,
                    gcov_executable=gcov_executable,
                    gcov_ignore=gcov_ignore,
                    gcov_include=gcov_include,
                    git_service=git_service,
                    handle_no_reports_found=handle_no_reports_found,
                    job_code=job_code,
                    name=name,
                    network_filter=network_filter,
                    network_prefix=network_prefix,
                    network_root_folder=network_root_folder,
                    parent_sha=parent_sha,
                    plugin_names=plugin_names,
                    pull_request_number=pull_request_number,
                    recurse_submodules=recurse_submodules,
                    report_code=report_code,
                    slug=slug,
                    swift_project=swift_project,
                    token=token,
                    report_type=report_type,
                    use_legacy_uploader=use_legacy_uploader,
                    args=args,
                )
            else:
                ctx.invoke(
                    create_commit,
                    commit_sha=commit_sha,
                    parent_sha=parent_sha,
                    pull_request_number=pull_request_number,
                    branch=branch,
                    slug=slug,
                    token=token,
                    git_service=git_service,
                    fail_on_error=True,
                )
                if report_type == ReportType.COVERAGE:
                    ctx.invoke(
                        create_report,
                        token=token,
                        code=report_code,
                        fail_on_error=True,
                        commit_sha=commit_sha,
                        slug=slug,
                        git_service=git_service,
                    )
                ctx.invoke(
                    do_upload,
                    branch=branch,
                    build_code=build_code,
                    build_url=build_url,
                    commit_sha=commit_sha,
                    disable_file_fixes=disable_file_fixes,
                    disable_search=disable_search,
                    dry_run=dry_run,
                    env_vars=env_vars,
                    fail_on_error=fail_on_error,
                    files_search_exclude_folders=files_search_exclude_folders,
                    files_search_explicitly_listed_files=files_search_explicitly_listed_files,
                    files_search_root_folder=files_search_root_folder,
                    flags=flags,
                    gcov_args=gcov_args,
                    gcov_executable=gcov_executable,
                    gcov_ignore=gcov_ignore,
                    gcov_include=gcov_include,
                    git_service=git_service,
                    handle_no_reports_found=handle_no_reports_found,
                    job_code=job_code,
                    name=name,
                    network_filter=network_filter,
                    network_prefix=network_prefix,
                    network_root_folder=network_root_folder,
                    plugin_names=plugin_names,
                    pull_request_number=pull_request_number,
                    recurse_submodules=recurse_submodules,
                    report_code=report_code,
                    report_type_str=report_type_str,
                    slug=slug,
                    swift_project=swift_project,
                    token=token,
                    use_legacy_uploader=use_legacy_uploader,
                )
    close_telem()
