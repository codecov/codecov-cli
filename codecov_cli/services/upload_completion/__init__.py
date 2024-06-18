import json
import logging

from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import (
    get_token_header,
    log_warnings_and_errors_if_any,
    send_post_request,
)

logger = logging.getLogger("codecovcli")


def upload_completion_logic(
    commit_sha, slug, token, git_service, enterprise_url, fail_on_error=False
):
    encoded_slug = encode_slug(slug)
    headers = get_token_header(token)
    upload_url = enterprise_url or CODECOV_API_URL
    url = f"{upload_url}/upload/{git_service}/{encoded_slug}/commits/{commit_sha}/upload-complete"
    sending_result = send_post_request(url=url, headers=headers)
    log_warnings_and_errors_if_any(
        sending_result, "Upload Completion", fail_on_error=fail_on_error
    )
    if sending_result.status_code == 200:
        response_json = json.loads(sending_result.text)
        logger.info(response_json)
    return sending_result
