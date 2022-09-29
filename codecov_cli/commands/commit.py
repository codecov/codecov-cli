import logging
import typing
import uuid

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.services.commit import create_commit_logic

logger = logging.getLogger("codecovcli")


@click.command()
@click.option(
    "--commit-sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    required=True,
)
@click.option(
    "--parent-sha",
    help="SHA (with 40 chars) of what should be the parent of this commit",
)
@click.option(
    "--pr",
    help="Pull Request id to associate commit with",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.pull_request_number,
)
@click.option(
    "-B",
    "--branch",
    help="Branch to which this commit belongs to",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.branch,
)
@click.option(
    "--slug",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.slug,
    help="owner/repo slug used instead of the private repo token in Self-hosted",
    envvar="CODECOV_SLUG",
)
@click.option(
    "-t",
    "--token",
    help="Codecov upload token",
    type=click.UUID,
    envvar="CODECOV_TOKEN",
)
@click.pass_context
def create_commit(
    ctx,
    commit_sha: str,
    parent_sha: typing.Optional[str],
    pr: typing.Optional[int],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    token: typing.Optional[uuid.UUID],
):
    logger.debug(
        "Starting create commit process",
        extra=dict(
            extra_log_attributes=dict(
                commit_sha=commit_sha,
                parent_sha=parent_sha,
                pr=pr,
                branch=branch,
                slug=slug,
                token=token,
            )
        ),
    )
    create_commit_logic(commit_sha, parent_sha, pr, branch, slug, token)
