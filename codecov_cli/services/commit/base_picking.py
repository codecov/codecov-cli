import logging

from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
    send_put_request,
)

logger = logging.getLogger("codecovcli")


def base_picking_logic(base_sha, pr, slug, token, service):
    data = {
        "user_provided_base_sha": base_sha,
    }
    headers = get_token_header_or_fail(token)
    url = f"https://api.codecov.io/api/v1/{service}/{slug}/pulls/{pr}"
    sending_result = send_put_request(url=url, data=data, headers=headers)

    log_warnings_and_errors_if_any(sending_result, "Base picking")
    return sending_result
