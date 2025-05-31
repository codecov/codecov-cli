import logging
import typing

import click
import sentry_sdk

from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.options import global_options
from codecov_cli.services.report import transplant_report_logic
from codecov_cli.types import CommandContext

logger = logging.getLogger("codecovcli")


@click.command(hidden=True)
@click.option(
    "--from-sha",
    help="SHA (with 40 chars) of the commit from which to forward coverage reports",
    required=True,
)
@global_options
@click.pass_context
def transplant_report(
    ctx: CommandContext,
    from_sha: str,
    commit_sha: str,
    slug: typing.Optional[str],
    token: typing.Optional[str],
    git_service: typing.Optional[str],
    fail_on_error: bool,
):
    with sentry_sdk.start_transaction(op="task", name="Transplant Report"):
        with sentry_sdk.start_span(name="transplant_report"):
            enterprise_url = ctx.obj.get("enterprise_url")
            args = get_cli_args(ctx)
            logger.debug(
                "Starting transplant report process",
                extra=dict(extra_log_attributes=args),
            )
            transplant_report_logic(
                from_sha,
                commit_sha,
                slug,
                token,
                git_service,
                enterprise_url,
                fail_on_error,
                args,
            )
