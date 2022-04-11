import os
import pathlib
import typing
import uuid

import click

from codecov_cli.entrypoints import do_upload_logic
from codecov_cli.fallbackers import CodecovOption, FallbackFieldEnum


def _turn_env_vars_into_dict(ctx, params, value):
    return dict((v, os.getenv(v, None)) for v in value)


def _validate_token_argument(ctx, params, value) -> uuid.UUID:
    try:
        return click.UUID(value)
    except click.exceptions.BadParameter:
        print("Couldn't parse input token as a UUID. trying to parse it as a file...")

    try:
        with open(value, "r") as tokenFile:
            return click.UUID(tokenFile.readline())
    except click.exceptions.BadParameter as err:
        print(f"The provided file content couldn't be parsed as a valid token: {err}")
    except OSError as err:
        print(f"File {value} coulnd't be opened for the following reason: {err}")

    raise click.exceptions.BadParameter("The provided parameter couldn't be parsed")


@click.command()
@click.option(
    "--commit-sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
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
    show_default=True,
)
@click.option(
    "--coverage-files-search-folder",
    help="Folder where to search for coverage files",
    type=click.Path(path_type=pathlib.Path),
    default=pathlib.Path.cwd,
    show_default=True,
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
    help="Codecov upload token represented as UUID or path to file containing the token",
    type=str,
    callback=_validate_token_argument,
    default=lambda: os.environ.get("CODECOV_TOKEN", None),
    show_default="Value of CODECOV_TOKEN environment variable",
)
@click.option("--env-var", "env_vars", multiple=True, callback=_turn_env_vars_into_dict)
@click.option("--flag", "flags", multiple=True, default=[])
@click.option("--plugin", "plugin_names", multiple=True, default=["gcov"])
@click.option("--name")
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
):

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
        )
    )
    do_upload_logic(
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
    )
