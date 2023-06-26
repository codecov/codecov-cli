import logging
import pathlib
import typing
import uuid

import click

from codecov_cli.commands.commit import create_commit
from codecov_cli.commands.report import create_report
from codecov_cli.commands.upload import _turn_env_vars_into_dict, do_upload
from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService

logger = logging.getLogger("codecovcli")

# These options are the combined options of commit, report and upload commands
@click.command()
@click.option(
    "-C",
    "--sha",
    "--commit-sha",
    "commit_sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    required=True,
)
@click.option(
    "--report-code",
    help="The code of the report. If unsure, leave default",
    default="default",
)
@click.option(
    "--network-root-folder",
    help="Root folder from which to consider paths on the network section",
    type=click.Path(path_type=pathlib.Path),
    default=pathlib.Path.cwd,
    show_default="Current working directory",
)
@click.option(
    "-s",
    "--dir",
    "--coverage-files-search-root-folder",
    "coverage_files_search_root_folder",
    help="Folder where to search for coverage files",
    type=click.Path(path_type=pathlib.Path),
    default=pathlib.Path.cwd,
    show_default="Current Working Directory",
)
@click.option(
    "--exclude",
    "--coverage-files-search-exclude-folder",
    "coverage_files_search_exclude_folders",
    help="Folders to exclude from search",
    type=click.Path(path_type=pathlib.Path),
    multiple=True,
    default=[],
)
@click.option(
    "-f",
    "--file",
    "--coverage-files-search-direct-file",
    "coverage_files_search_explicitly_listed_files",
    help="Explicit files to upload. These will be added to the coverage files found for upload. If you wish to only upload the specified files, please consider using --disable-search to disable uploading other files.",
    type=click.Path(path_type=pathlib.Path),
    multiple=True,
    default=[],
)
@click.option(
    "--disable-search",
    help="Disable search for coverage files. This is helpful when specifying what files you want to uload with the --file option.",
    is_flag=True,
    default=False,
)
@click.option(
    "-b",
    "--build",
    "--build-code",
    "build_code",
    cls=CodecovOption,
    help="Specify the build number manually",
    fallback_field=FallbackFieldEnum.build_code,
)
@click.option(
    "--build-url",
    "build_url",
    cls=CodecovOption,
    help="The URL of the build where this is running",
    fallback_field=FallbackFieldEnum.build_url,
)
@click.option(
    "--job-code",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.job_code,
)
@click.option(
    "-t",
    "--token",
    help="Codecov upload token",
    type=click.UUID,
    envvar="CODECOV_TOKEN",
)
@click.option(
    "-n",
    "--name",
    help="Custom defined name of the upload. Visible in Codecov UI",
)
@click.option(
    "-B",
    "--branch",
    help="Branch to which this commit belongs to",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.branch,
)
@click.option(
    "-r",
    "--slug",
    "slug",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.slug,
    help="owner/repo slug used instead of the private repo token in Self-hosted",
    envvar="CODECOV_SLUG",
)
@click.option(
    "-P",
    "--pr",
    "--pull-request-number",
    "pull_request_number",
    help="Specify the pull request number mannually. Used to override pre-existing CI environment variables",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.pull_request_number,
)
@click.option(
    "-e",
    "--env",
    "--env-var",
    "env_vars",
    multiple=True,
    callback=_turn_env_vars_into_dict,
    help="Specify environment variables to be included with this build.",
)
@click.option(
    "-F",
    "--flag",
    "flags",
    multiple=True,
    default=[],
    help="Flag the upload to group coverage metrics. Multiple flags allowed.",
)
@click.option(
    "--plugin", "plugin_names", multiple=True, default=["xcode", "gcov", "pycoverage"]
)
@click.option(
    "-Z",
    "--fail-on-error",
    "fail_on_error",
    is_flag=True,
    help="Exit with non-zero code in case of error uploading.",
)
@click.option(
    "-d",
    "--dry-run",
    "dry_run",
    is_flag=True,
    help="Don't upload files to Codecov",
)
@click.option(
    "--legacy",
    "--use-legacy-uploader",
    "use_legacy_uploader",
    is_flag=True,
    help="Use the legacy upload endpoint",
)
@click.option(
    "--git-service",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.git_service,
    type=click.Choice(service.value for service in GitService),
)
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
    network_root_folder: pathlib.Path,
    coverage_files_search_root_folder: pathlib.Path,
    coverage_files_search_exclude_folders: typing.List[pathlib.Path],
    coverage_files_search_explicitly_listed_files: typing.List[pathlib.Path],
    disable_search: bool,
    token: typing.Optional[uuid.UUID],
    plugin_names: typing.List[str],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    pull_request_number: typing.Optional[str],
    use_legacy_uploader: bool,
    fail_on_error: bool,
    dry_run: bool,
    git_service: typing.Optional[str],
    parent_sha: typing.Optional[str],
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
                network_root_folder=network_root_folder,
                coverage_files_search_root_folder=coverage_files_search_root_folder,
                coverage_files_search_exclude_folders=coverage_files_search_exclude_folders,
                coverage_files_search_explicitly_listed_files=coverage_files_search_explicitly_listed_files,
                plugin_names=plugin_names,
                token="NOTOKEN" if not token else (str(token)[:1] + 18 * "*"),
                branch=branch,
                slug=slug,
                pull_request_number=pull_request_number,
                git_service=git_service,
                disable_search=disable_search,
                fail_on_error=fail_on_error,
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
        network_root_folder=network_root_folder,
        coverage_files_search_root_folder=coverage_files_search_root_folder,
        coverage_files_search_exclude_folders=coverage_files_search_exclude_folders,
        coverage_files_search_explicitly_listed_files=coverage_files_search_explicitly_listed_files,
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
    )
