import logging
import typing

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.git import GitService
from codecov_cli.helpers.options import global_options
from codecov_cli.services.empty_upload import empty_upload_logic
from codecov_cli.types import CommandContext

logger = logging.getLogger("codecovcli")


@click.command()
@click.option("--force", is_flag=True, default=False)
@global_options
@click.pass_context
def empty_upload(
    ctx: CommandContext,
    commit_sha: str,
    force: bool,
    slug: typing.Optional[str],
    token: typing.Optional[str],
    git_service: typing.Optional[str],
    fail_on_error: typing.Optional[bool],
):
    enterprise_url = ctx.obj.get("enterprise_url")
    args = get_cli_args(ctx)
    logger.debug(
        "Starting empty upload process",
        extra=dict(
            extra_log_attributes=args,
        ),
    )
    return empty_upload_logic(
        commit_sha, slug, token, git_service, enterprise_url, fail_on_error, force, args
    )
