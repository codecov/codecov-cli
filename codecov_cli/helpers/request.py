import logging
import uuid
from time import sleep

import click
import requests

from codecov_cli.types import RequestError, RequestResult

logger = logging.getLogger("codecovcli")

MAX_RETRIES = 3


def backoff_time(curr_retry):
    return 2 ** (curr_retry - 1)


def retry_request(func):
    def wrapper(*args, **kwargs):
        retry = 0
        while retry < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as exp:
                logger.warning(
                    "Request failed. Retrying",
                    extra=dict(extra_log_attributes=dict(retry=retry)),
                )
                sleep(backoff_time(retry))
                retry += 1
        raise Exception("Request failed after too many retries")

    return wrapper


@retry_request
def send_post_request(
    url: str, data: dict = None, headers: dict = None, params: dict = None
):
    resp = requests.post(url=url, json=data, headers=headers, params=params)
    return request_result(resp)


def get_token_header_or_fail(token: uuid.UUID) -> dict:
    if token is None:
        raise click.ClickException(
            "Codecov token not found. Please provide Codecov token with -t flag."
        )
    if not isinstance(token, uuid.UUID):
        raise click.ClickException(f"Token must be UUID. Received {type(token)}")
    return {"Authorization": f"token {token.hex}"}


@retry_request
def send_put_request(
    url: str,
    data: dict = None,
    headers: dict = None,
):
    resp = requests.put(url=url, data=data, headers=headers)
    return request_result(resp)


def request_result(resp):
    if resp.status_code >= 400:
        return RequestResult(
            status_code=resp.status_code,
            error=RequestError(
                code=f"HTTP Error {resp.status_code}",
                description=resp.text,
                params={},
            ),
            warnings=[],
            text=resp.text,
        )

    return RequestResult(
        status_code=resp.status_code, error=None, warnings=[], text=resp.text
    )


def log_warnings_and_errors_if_any(
    sending_result: RequestResult, process_desc: str, fail_on_error: bool = False
):
    logger.info(
        f"Process {process_desc} complete",
    )
    logger.debug(
        f"{process_desc} result",
        extra=dict(extra_log_attributes=dict(result=sending_result)),
    )
    if sending_result.warnings:
        number_warnings = len(sending_result.warnings)
        pluralization = "s" if number_warnings > 1 else ""
        logger.info(
            f"{process_desc} process had {number_warnings} warning{pluralization}",
        )
        for ind, w in enumerate(sending_result.warnings):
            logger.warning(f"Warning {ind + 1}: {w.message}")
    if sending_result.error is not None:
        logger.error(f"{process_desc} failed: {sending_result.error.description}")
        if fail_on_error:
            exit(1)
