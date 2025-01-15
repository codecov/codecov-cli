import logging
import typing

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.git import GitService
from codecov_cli.helpers.options import global_options
from codecov_cli.services.upload_completion import upload_completion_logic
from codecov_cli.types import CommandContext

logger = logging.getLogger("codecovcli")


@click.command()
@global_options
@click.pass_context
def send_notifications(
    ctx: CommandContext,
    commit_sha: str,
    slug: typing.Optional[str],
    token: typing.Optional[str],
    git_service: typing.Optional[str],
    fail_on_error: bool,
):
    enterprise_url = ctx.obj.get("enterprise_url")
    args = get_cli_args(ctx)
    logger.debug(
        "Sending notifications process has started",
        extra=dict(
            extra_log_attributes=args,
        ),
    )
    return upload_completion_logic(
        commit_sha,
        slug,
        token,
        git_service,
        enterprise_url,
        fail_on_error,
        args,
    )
