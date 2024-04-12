import logging
import pathlib
import typing

import click

from codecov_cli.commands.commit import create_commit
from codecov_cli.commands.report import create_report
from codecov_cli.commands.upload import do_upload, global_upload_options
from codecov_cli.helpers.options import global_options

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
def upload_process(
    ctx,
    commit_sha: str,
    report_code: str,
    build_code: typing.Optional[str],
    build_url: typing.Optional[str],
    job_code: typing.Optional[str],
    env_vars: typing.Dict[str, str],
    flags: typing.List[str],
    name: typing.Optional[str],
    network_filter: typing.Optional[str],
    network_prefix: typing.Optional[str],
    network_root_folder: pathlib.Path,
    files_search_root_folder: pathlib.Path,
    files_search_exclude_folders: typing.List[pathlib.Path],
    files_search_explicitly_listed_files: typing.List[pathlib.Path],
    disable_search: bool,
    disable_file_fixes: bool,
    token: typing.Optional[str],
    plugin_names: typing.List[str],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    pull_request_number: typing.Optional[str],
    use_legacy_uploader: bool,
    fail_on_error: bool,
    dry_run: bool,
    git_service: typing.Optional[str],
    parent_sha: typing.Optional[str],
    handle_no_reports_found: bool,
    report_type: str,
):
    logger.debug(
        "Starting upload process",
        extra=dict(
            extra_log_attributes=dict(
                commit_sha=commit_sha,
                report_code=report_code,
                build_code=build_code,
                build_url=build_url,
                job_code=job_code,
                env_vars=env_vars,
                flags=flags,
                name=name,
                network_filter=network_filter,
                network_prefix=network_prefix,
                network_root_folder=network_root_folder,
                files_search_root_folder=files_search_root_folder,
                files_search_exclude_folders=files_search_exclude_folders,
                files_search_explicitly_listed_files=files_search_explicitly_listed_files,
                plugin_names=plugin_names,
                token=token,
                branch=branch,
                slug=slug,
                pull_request_number=pull_request_number,
                git_service=git_service,
                disable_search=disable_search,
                disable_file_fixes=disable_file_fixes,
                fail_on_error=fail_on_error,
                handle_no_reports_found=handle_no_reports_found,
            )
        ),
    )

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
    if report_type == "coverage":
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
        commit_sha=commit_sha,
        report_code=report_code,
        build_code=build_code,
        build_url=build_url,
        job_code=job_code,
        env_vars=env_vars,
        flags=flags,
        name=name,
        network_filter=network_filter,
        network_prefix=network_prefix,
        network_root_folder=network_root_folder,
        files_search_root_folder=files_search_root_folder,
        files_search_exclude_folders=files_search_exclude_folders,
        files_search_explicitly_listed_files=files_search_explicitly_listed_files,
        disable_search=disable_search,
        token=token,
        plugin_names=plugin_names,
        branch=branch,
        slug=slug,
        pull_request_number=pull_request_number,
        use_legacy_uploader=use_legacy_uploader,
        fail_on_error=fail_on_error,
        dry_run=dry_run,
        git_service=git_service,
        handle_no_reports_found=handle_no_reports_found,
        disable_file_fixes=disable_file_fixes,
        report_type=report_type,
    )
