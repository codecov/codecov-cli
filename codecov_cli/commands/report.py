import logging
import uuid

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService
from codecov_cli.services.report import create_report_logic

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
    "--code", help="The code of the report. If unsure, leave default", default="default"
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
    "--git-service",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.git_service,
    type=click.Choice(service.value for service in GitService),
)
@click.option(
    "-t",
    "--token",
    help="Codecov upload token",
    type=click.UUID,
    envvar="CODECOV_TOKEN",
)
@click.pass_context
def create_report(
    ctx, commit_sha: str, code: str, slug: str, git_service: str, token: uuid.UUID
):
    logger.debug(
        "Starting create report process",
        extra=dict(
            extra_log_attributes=dict(
                commit_sha=commit_sha, code=code, slug=slug, service=git_service
            )
        ),
    )
    res = create_report_logic(commit_sha, code, slug, git_service, token)
    if not res.error:
        logger.info(
            "Finished creating report successfully",
            extra=dict(extra_log_attributes=dict(response=res.text)),
        )
