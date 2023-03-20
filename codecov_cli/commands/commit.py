import logging
import typing
import uuid

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService
from codecov_cli.services.commit import create_commit_logic

logger = logging.getLogger("codecovcli")


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
    "--parent-sha",
    help="SHA (with 40 chars) of what should be the parent of this commit",
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
    "-t",
    "--token",
    help="Codecov upload token",
    type=click.UUID,
    envvar="CODECOV_TOKEN",
)
@click.option(
    "--git-service",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.git_service,
    type=click.Choice(service.value for service in GitService),
)
@click.pass_context
def create_commit(
    ctx,
    commit_sha: str,
    parent_sha: typing.Optional[str],
    pull_request_number: typing.Optional[int],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    token: typing.Optional[uuid.UUID],
    git_service: typing.Optional[str],
):
    logger.debug(
        "Starting create commit process",
        extra=dict(
            extra_log_attributes=dict(
                commit_sha=commit_sha,
                parent_sha=parent_sha,
                pr=pull_request_number,
                branch=branch,
                slug=slug,
                token=token,
                service=git_service,
            )
        ),
    )
    create_commit_logic(
        commit_sha, parent_sha, pull_request_number, branch, slug, token, git_service
    )
