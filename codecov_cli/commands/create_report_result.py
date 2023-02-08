import logging
import uuid

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService
from codecov_cli.services.report import create_report_results_logic

logger = logging.getLogger("codecovcli")


@click.command()
@click.option(
    "--commit-sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    required=True,
)
@click.option(
    "--code", help="The code of the report. If unsure, leave default", default="default"
)
@click.option(
    "--slug",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.slug,
    help="owner/repo slug used instead of the private repo token in Self-hosted",
    envvar="CODECOV_SLUG",
    required=True,
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
def create_report_results(
    ctx,
    commit_sha: str,
    code: str,
    slug: str,
    git_service: str,
    token: uuid.UUID,
):
    logger.debug(
        "Creating report results",
        extra=dict(
            extra_log_attributes=dict(
                commit_sha=commit_sha, code=code, slug=slug, service=git_service
            )
        ),
    )
    create_report_results_logic(commit_sha, code, slug, git_service, token)
