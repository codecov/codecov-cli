import json
import logging

from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
    send_post_request,
)

logger = logging.getLogger("codecovcli")


def empty_upload_logic(
    commit_sha, slug, token, git_service, enterprise_url, fail_on_error, should_force
):
    encoded_slug = encode_slug(slug)
    headers = get_token_header_or_fail(token)
    upload_url = enterprise_url or CODECOV_API_URL
    url = f"{upload_url}/upload/{git_service}/{encoded_slug}/commits/{commit_sha}/empty-upload"
    sending_result = send_post_request(
        url=url, headers=headers, data={"should_force": should_force}
    )
    log_warnings_and_errors_if_any(sending_result, "Empty Upload", fail_on_error)
    if sending_result.status_code == 200:
        response_json = json.loads(sending_result.text)
        logger.info(response_json.get("result"))
        logger.info(f"Non ignored files {response_json.get('non_ignored_files')}")
    return sending_result
