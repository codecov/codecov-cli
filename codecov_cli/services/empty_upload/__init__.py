import logging

from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
    send_post_request,
)

logger = logging.getLogger("codecovcli")


def empty_upload_logic(commit_sha, slug, token, git_service):
    encoded_slug = encode_slug(slug)
    headers = get_token_header_or_fail(token)
    url = f"https://api.codecov.io/upload/{git_service}/{encoded_slug}/commits/{commit_sha}/empty-upload"
    sending_result = send_post_request(url=url, headers=headers)
    log_warnings_and_errors_if_any(sending_result, "Empty Upload")
    return sending_result
