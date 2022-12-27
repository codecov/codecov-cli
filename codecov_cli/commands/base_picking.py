import logging
import typing
import uuid

import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.encoder import slug_is_invalid
from codecov_cli.helpers.request import send_put_request

logger = logging.getLogger("codecovcli")


@click.command()
@click.option(
    "--base-sha",
    help="Base commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    required=True,
)
@click.option(
    "--pr",
    help="Pull Request id to associate commit with",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.pull_request_number,
)
@click.option(
    "--slug",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.slug,
    help="owner/repo slug",
    envvar="CODECOV_SLUG",
)
@click.option(
    "-t",
    "--token",
    help="Codecov upload token",
    type=click.UUID,
    envvar="CODECOV_TOKEN",
)
@click.option(
    "--service",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.service,
    help="Specify the service provider of the repo e.g. github",
)
@click.pass_context
def pr_base_picking(
    ctx,
    base_sha: str,
    pr: typing.Optional[int],
    slug: typing.Optional[str],
    token: typing.Optional[uuid.UUID],
    service: typing.Optional[str],
):
    logger.debug(
        "Starting base picking process",
        extra=dict(
            extra_log_attributes=dict(
                pr=pr,
                slug=slug,
                token=token,
                service=service,
            )
        ),
    )

    if slug_is_invalid(slug):
        logger.error(
            "Slug is invalid. Slug should be in the form of owner_username/repo_name"
        )
        return

    data = {
        "user_provided_base_sha": base_sha,
    }
    headers = {"Authorization": f"token {token.hex}"}
    url = f"https://api.codecov.io/api/v1/{service}/{slug}/pulls/{pr}"
    sending_result = send_put_request(url=url, data=data, headers=headers)

    if sending_result.warnings:
        number_warnings = len(sending_result.warnings)
        pluralization = "s" if number_warnings > 1 else ""
        logger.info(
            f"Base picking process had {number_warnings} warning{pluralization}",
        )
        for ind, w in enumerate(sending_result.warnings):
            logger.warning(f"Warning {ind + 1}: {w}")
    if sending_result.error is not None:
        logger.error(f"Base picking failed: {sending_result.error.description}")
        return

    logger.info("Base picking finished successfully")
    logger.info(sending_result.text)
