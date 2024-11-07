import pathlib
import typing

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.versioning_systems import VersioningSystemInterface
from codecov_cli.services.upload import do_upload_logic


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
    return do_upload_logic(
        cli_config=cli_config,
        versioning_system=versioning_system,
        ci_adapter=ci_adapter,
        combined_upload=True,
        args=args,
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
        report_code=report_code,
        slug=slug,
        swift_project=swift_project,
        token=token,
        use_legacy_uploader=use_legacy_uploader,
        upload_file_type=upload_file_type,
    )
