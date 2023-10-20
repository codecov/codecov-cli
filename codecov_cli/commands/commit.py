import logging
import typing

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService
from codecov_cli.helpers.options import global_options
from codecov_cli.services.commit import create_commit_logic

logger = logging.getLogger("codecovcli")


@click.command()
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
@global_options
@click.pass_context
def create_commit(
    ctx,
    commit_sha: str,
    parent_sha: typing.Optional[str],
    pull_request_number: typing.Optional[int],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    token: typing.Optional[str],
    git_service: typing.Optional[str],
    fail_on_error: bool,
):
    enterprise_url = ctx.obj.get("enterprise_url")
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
                enterprise_url=enterprise_url,
            )
        ),
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
    )
