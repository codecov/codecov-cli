import logging
import uuid

import requests

from codecov_cli.types import RequestError, RequestResult

logger = logging.getLogger("codecovcli")


def send_post_request(
    url: str,
    data: dict = None,
    headers: dict = None,
):
    resp = requests.post(
        url=url,
        data=data,
        headers=headers,
    )
    return request_result(resp)


def get_token_header_or_fail(token: uuid.UUID) -> dict:
    if token is None:
        raise Exception("Codecov token not found.")
    if not isinstance(token, uuid.UUID):
        raise Exception(f"Token must be UUID. Received {type(token)}")
    return {"Authorization": f"token {token.hex}"}


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
    logger.debug(
        f"Process {process_desc} complete.",
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
