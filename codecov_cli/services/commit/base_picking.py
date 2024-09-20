import logging

from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
    send_put_request,
)

logger = logging.getLogger("codecovcli")


def base_picking_logic(base_sha, pr, slug, token, service, enterprise_url, args):
    data = {
        "cli_args": args,
        "user_provided_base_sha": base_sha,
    }
    headers = get_token_header_or_fail(token)
    upload_url = enterprise_url or CODECOV_API_URL
    url = f"{upload_url}/api/v1/{service}/{slug}/pulls/{pr}"
    sending_result = send_put_request(url=url, data=data, headers=headers)

    log_warnings_and_errors_if_any(sending_result, "Base picking")
    return sending_result
