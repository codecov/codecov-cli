import logging
import typing

import click
import sentry_sdk

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.options import global_options
from codecov_cli.services.commit import create_commit_logic
from codecov_cli.services.empty_upload import empty_upload_logic
from codecov_cli.types import CommandContext

logger = logging.getLogger("codecovcli")

_EXPLICIT_SOURCES = (
    click.core.ParameterSource.COMMANDLINE,
    click.core.ParameterSource.ENVIRONMENT,
)


def _should_create_commit(ctx: click.Context, **values: typing.Any) -> bool:
    """Only create a commit when the user explicitly provided commit values.

    Values populated through CI/versioning-system fallbacks (e.g. the current
    git branch) do not count as explicitly provided.
    """
    for name, value in values.items():
        if value is None:
            continue
        if ctx.get_parameter_source(name) in _EXPLICIT_SOURCES:
            return True
    return False


@click.command()
@click.option("--force", is_flag=True, default=False)
@click.option(
    "--parent-sha",
    help="SHA (with 40 chars) of what should be the parent of this commit",
)
@click.option(
    "-P",
    "--pr",
    "--pull-request-number",
    "pull_request_number",
    help="Specify the pull request number manually. Used to override pre-existing CI environment variables",
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
    parent_sha: typing.Optional[str],
    pull_request_number: typing.Optional[int],
    branch: typing.Optional[str],
):
    with sentry_sdk.start_transaction(op="task", name="Empty Upload"):
        with sentry_sdk.start_span(name="empty_upload"):
            enterprise_url = ctx.obj.get("enterprise_url")
            args = get_cli_args(ctx)

            if _should_create_commit(
                ctx,
                parent_sha=parent_sha,
                pull_request_number=pull_request_number,
                branch=branch,
            ):
                logger.debug(
                    "Attempting to Create Commit before doing an empty upload."
                )
                create_commit_logic(
                    commit_sha,
                    parent_sha,
                    pull_request_number,
                    branch,
                    slug,
                    token,
                    git_service,
                    enterprise_url,
                    fail_on_error,
                    args,
                )
            else:
                logger.debug(
                    "No parent SHA, pull request number or branch provided. Skipping commit creation."
                )

            logger.debug(
                "Starting empty upload process",
                extra=dict(
                    extra_log_attributes=args,
                ),
            )
            return empty_upload_logic(
                commit_sha, slug, token, git_service, enterprise_url, fail_on_error, force, args
            )
