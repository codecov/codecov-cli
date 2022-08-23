import asyncio
import pathlib

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.services.staticanalysis import run_analysis_entrypoint


@click.command()
@click.option(
    "--foldertosearch",
    default=".",
    help="Folder to search",
    type=click.Path(path_type=pathlib.Path),
)
@click.option("--numberprocesses", default=3, help="number of processes to use")
@click.option("--pattern", default="*", help="file pattern to search for")
@click.option("--force/--no-force", default=False)
@click.option(
    "--commit-sha",
    "commit",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    required=True,
)
@click.option("--token")
def static_analysis(foldertosearch, numberprocesses, pattern, commit, token, force):
    return asyncio.run(
        run_analysis_entrypoint(
            foldertosearch, numberprocesses, pattern, commit, token, force
        )
    )
