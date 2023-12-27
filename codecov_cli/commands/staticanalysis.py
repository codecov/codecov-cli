import asyncio
import logging
import pathlib
import typing

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.validators import validate_commit_sha
from codecov_cli.services.staticanalysis import run_analysis_entrypoint

logger = logging.getLogger("codecovcli")


_static_analysis_options = [
    click.option(
        "--foldertosearch",
        default=".",
        help="Folder to search",
        type=click.Path(path_type=pathlib.Path),
    ),
    click.option(
        "--numberprocesses",
        type=click.INT,
        default=None,
        help="number of processes to use",
    ),
    click.option("--pattern", default="*", help="file pattern to search for"),
    click.option("--force/--no-force", default=False),
    click.option(
        "--folders-to-exclude",
        help="Folders not to search",
        type=click.Path(path_type=pathlib.Path),
        multiple=True,
        default=[],
    ),
]


def static_analysis_options(func):
    for option in reversed(_static_analysis_options):
        func = option(func)
    return func


@click.command()
@static_analysis_options
# This is not part of the options list to avoid conflicts with label-analysis
# that uses --head-sha / --base-sha.
@click.option(
    "--commit-sha",
    "commit",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    callback=validate_commit_sha,
    required=True,
)
@click.option(
    "--token",
    required=True,
    envvar="CODECOV_STATIC_TOKEN",
    help="The static analysis token (NOT the same token as upload)",
)
@click.pass_context
def static_analysis(
    ctx: click.Context,
    foldertosearch: pathlib.Path,
    numberprocesses: typing.Optional[int],
    pattern: str,
    commit: str,
    token: str,
    force: bool,
    folders_to_exclude: typing.List[pathlib.Path],
):
    enterprise_url = ctx.obj.get("enterprise_url")
    logger.debug(
        "Starting Static Analysis processing",
        extra=dict(
            extra_log_attributes=dict(
                foldertosearch=foldertosearch,
                numberprocesses=numberprocesses,
                pattern=pattern,
                commit_sha=commit,
                token=token,
                force=force,
                folders_to_exclude=folders_to_exclude,
                enterprise_url=enterprise_url,
            )
        ),
    )
    return asyncio.run(
        run_analysis_entrypoint(
            ctx.obj["codecov_yaml"],
            foldertosearch,
            numberprocesses,
            pattern,
            commit,
            token,
            force,
            list(folders_to_exclude),
            enterprise_url,
        )
    )
