import logging
import uuid

from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import send_post_request

logger = logging.getLogger("codecovcli")


def get_report_results_logic(
    commit_sha: str, code: str, slug: str, service: str, token: uuid.UUID
):
    encoded_slug = encode_slug(slug)
    sending_result = send_reports_result_request(
        commit_sha=commit_sha,
        report_code=code,
        encoded_slug=encoded_slug,
        service=service,
        token=token,
    )

    if sending_result.warnings:
        number_warnings = len(sending_result.warnings)
        pluralization = "s" if number_warnings > 1 else ""
        logger.info(
            f"Report results creating process had {number_warnings} warning{pluralization}",
        )
        for ind, w in enumerate(sending_result.warnings):
            logger.warning(f"Warning {ind + 1}: {w.message}")
    if sending_result.error is not None:
        logger.error(
            f"Report results creating failed: {sending_result.error.description}"
        )
    return sending_result


def send_reports_result_request(commit_sha, report_code, encoded_slug, service, token):
    headers = {"Authorization": f"token {token.hex}"}
    url = f"https://codecov.io/upload/{service}/{encoded_slug}/commits/{commit_sha}/reports/{report_code}/results"
    return send_post_request(url=url, headers=headers)
