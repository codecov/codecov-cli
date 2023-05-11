import logging
import typing
import uuid

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService
from codecov_cli.services.empty_upload import empty_upload_logic

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
def empty_upload(
    ctx,
    commit_sha: str,
    slug: typing.Optional[str],
    token: typing.Optional[uuid.UUID],
    git_service: typing.Optional[str],
):
    logger.debug(
        "Starting empty upload process",
        extra=dict(
            extra_log_attributes=dict(
                commit_sha=commit_sha,
                slug=slug,
                token=token,
                service=git_service,
            )
        ),
    )
    return empty_upload_logic(commit_sha, slug, token, git_service)
