import logging
import typing
import uuid

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService
from codecov_cli.helpers.options import global_options
from codecov_cli.services.empty_upload import empty_upload_logic

logger = logging.getLogger("codecovcli")


@click.command()
@global_options
@click.pass_context
def empty_upload(
    ctx,
    commit_sha: str,
    slug: typing.Optional[str],
    token: typing.Optional[uuid.UUID],
    git_service: typing.Optional[str],
):
    enterprise_url = ctx.obj.get("enterprise_url")
    logger.debug(
        "Starting empty upload process",
        extra=dict(
            extra_log_attributes=dict(
                commit_sha=commit_sha,
                slug=slug,
                token=token,
                service=git_service,
                enterprise_url=enterprise_url,
            )
        ),
    )
    return empty_upload_logic(commit_sha, slug, token, git_service, enterprise_url)
