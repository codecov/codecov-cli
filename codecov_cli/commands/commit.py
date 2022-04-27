import typing

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum


@click.command()
@click.option(
    "--commit-sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
)
@click.option(
    "--parent-sha",
    help="SHA (with 40 chars) of what should be the parent of this commit",
)
@click.option(
    "--pr",
    help="Pull Request to associate commit with",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.pull_request_number,
)
@click.pass_context
def create_commit(
    ctx, commit_sha: str, parent_sha: typing.Optional[str], pr: typing.Optional[int]
):
    for x in range(10):
        click.echo(f"Hello {commit_sha}!")
