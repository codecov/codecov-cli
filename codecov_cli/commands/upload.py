import os
import pathlib
import typing
import uuid

import click

from codecov_cli.entrypoints import do_upload_logic
from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum


def _turn_env_vars_into_dict(ctx, params, value):
    return dict((v, os.getenv(v, None)) for v in value)


@click.command()
@click.option(
    "--commit-sha",
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
    "--coverage-files-search-folder",
    help="Folder where to search for coverage files",
    type=click.Path(path_type=pathlib.Path),
    default=pathlib.Path.cwd,
    show_default="Current Working Directory",
)
@click.option(
    "--build-code",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.build_code,
)
@click.option(
    "--build-url",
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
    show_default="The value of CODECOV_TOKEN environment variable",
)
@click.option(
    "-n",
    "--name",
    help="Custom defined name of the upload. Visible in Codecov UI",
)
@click.option(
    "-B",
    "--branch",
    help="Specify the branch manually. Used to override pre-existing CI environment variables",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.branch,
)
@click.option(
    "-T",
    "--tag",
    help="Specify the tag manually",
)
@click.option(
    "-r",
    "--slug",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.slug,
    help="owner/repo slug used instead of the private repo token in Self-hosted",
    envvar="CODECOV_SLUG",
    show_default="The value of CODECOV_SLUG environment variable",
)
@click.option(
    "-P",
    "--pull-request-number",
    help="Specify the pull request number mannually. Used to override pre-existing CI environment variables",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.pull_request_number,
)
@click.option("--env-var", "env_vars", multiple=True, callback=_turn_env_vars_into_dict)
@click.option("--flag", "flags", multiple=True, default=[])
@click.option("--plugin", "plugin_names", multiple=True, default=[])
@click.pass_context
def do_upload(
    ctx: click.Context,
    commit_sha: str,
    report_code: str,
    build_code: typing.Optional[str],
    build_url: typing.Optional[str],
    job_code: typing.Optional[str],
    env_vars: typing.Dict[str, str],
    flags: typing.List[str],
    name: typing.Optional[str],
    network_root_folder: pathlib.Path,
    coverage_files_search_folder: pathlib.Path,
    token: typing.Optional[uuid.UUID],
    plugin_names: typing.List[str],
    branch: typing.Optional[str],
    tag: typing.Optional[str],
    slug: typing.Optional[str],
    pull_request_number: typing.Optional[str],
):
    versioning_system = ctx.obj["versioning_system"]
    codecov_yaml = ctx.obj["codecov_yaml"] or {}
    cli_config = codecov_yaml.get("cli", {})
    ci_adapter = ctx.obj.get("ci_adapter")
    print(
        dict(
            commit_sha=commit_sha,
            report_code=report_code,
            build_code=build_code,
            build_url=build_url,
            job_code=job_code,
            env_vars=env_vars,
            flags=flags,
            name=name,
            network_root_folder=network_root_folder,
            coverage_files_search_folder=coverage_files_search_folder,
            plugin_names=plugin_names,
            token=token,
            branch=branch,
            tag=tag,
            slug=slug,
            pull_request_number=pull_request_number,
        )
    )
    do_upload_logic(
        cli_config,
        versioning_system,
        ci_adapter,
        commit_sha=commit_sha,
        report_code=report_code,
        build_code=build_code,
        build_url=build_url,
        job_code=job_code,
        env_vars=env_vars,
        flags=flags,
        name=name,
        network_root_folder=network_root_folder,
        coverage_files_search_folder=coverage_files_search_folder,
        plugin_names=plugin_names,
        token=token,
        branch=branch,
        tag=tag,
        slug=slug,
        pull_request_number=pull_request_number,
    )
