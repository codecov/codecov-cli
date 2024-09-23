import logging

import click

from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.options import global_options
from codecov_cli.services.report import create_report_results_logic
from codecov_cli.types import CommandContext

logger = logging.getLogger("codecovcli")


@click.command()
@click.option(
    "--code", help="The code of the report. If unsure, leave default", default="default"
)
@global_options
@click.pass_context
def create_report_results(
    ctx: CommandContext,
    commit_sha: str,
    code: str,
    slug: str,
    git_service: str,
    token: str,
    fail_on_error: bool,
):
    enterprise_url = ctx.obj.get("enterprise_url")
    args = get_cli_args(ctx)
    logger.debug(
        "Creating report results",
        extra=dict(
            extra_log_attributes=args,
        ),
    )
    create_report_results_logic(
        commit_sha, code, slug, git_service, token, enterprise_url, fail_on_error, args
    )
