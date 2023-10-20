import logging
import typing

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService
from codecov_cli.helpers.options import global_options
from codecov_cli.services.upload_completion import upload_completion_logic

logger = logging.getLogger("codecovcli")


@click.command()
@global_options
@click.pass_context
def send_notifications(
    ctx,
    commit_sha: str,
    slug: typing.Optional[str],
    token: typing.Optional[str],
    git_service: typing.Optional[str],
    fail_on_error: bool,
):
    enterprise_url = ctx.obj.get("enterprise_url")
    logger.debug(
        "Sending notifications process has started",
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
    return upload_completion_logic(
        commit_sha,
        slug,
        token,
        git_service,
        enterprise_url,
        fail_on_error,
    )
