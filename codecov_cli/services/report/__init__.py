import logging
import typing

from codecov_cli.helpers.encoder import encode_slug

from .report_sender import ReportSender

logger = logging.getLogger("codecovcli")


def create_report_logic(
    commit_sha: str,
    code: str,
    slug: str,
):
    encoded_slug = encode_slug(slug)
    sender = ReportSender()
    sending_result = sender.send_report_data(
        commit_sha=commit_sha,
        code=code,
        slug=encoded_slug,
    )

    if sending_result.warnings:
        number_warnings = len(sending_result.warnings)
        pluralization = "s" if number_warnings > 1 else ""
        logger.info(
            f"Report creating process had {number_warnings} warning{pluralization}",
        )
        for ind, w in enumerate(sending_result.warnings):
            logger.warning(f"Warning {ind + 1}: {w.message}")
    if sending_result.error is not None:
        logger.error(f"Report creating failed: {sending_result.error.description}")
    return sending_result
