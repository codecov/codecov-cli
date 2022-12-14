import json
import logging
import time
import typing
import uuid

import requests

from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import (
    log_warnings_and_errors,
    request_result,
    send_post_request,
)

from .report_sender import ReportSender

logger = logging.getLogger("codecovcli")
MAX_TIME_FRAME = 60


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


def create_report_results_logic(
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


def send_reports_result_get_request(
    commit_sha, report_code, encoded_slug, service, token
):
    headers = {"Authorization": f"token {token.hex}"}
    url = f"https://codecov.io/upload/{service}/{encoded_slug}/commits/{commit_sha}/reports/{report_code}/results"
    time_elapsed = 0
    while time_elapsed < MAX_TIME_FRAME:
        resp = requests.get(url=url, headers=headers)
        response_obj = request_result(resp)
        response_content = json.loads(response_obj.text)

        # if response_status is 400 and higher
        if response_obj.error:
            log_warnings_and_errors(response_obj, "Getting report results")
            return response_obj

        state = response_content.get("state")
        if state == "error":
            logger.error(
                "An error occured while processing the report. Please try again later.",
                extra=dict(
                    response_status_code=response_obj.status_code,
                    text=response_obj.text,
                ),
            )
            return response_obj
        elif state == "pending":
            logger.info("Report with the given code is still being processed.")
        elif state == "completed":
            logger.info("Finished processing report results")
            logger.info(response_content.get("result")["state"])
            logger.info(response_content.get("result")["message"])
            return response_obj
        else:
            logger.info("Please try again later.")
            return response_obj
        time.sleep(5)
        time_elapsed += 5
    return response_obj
