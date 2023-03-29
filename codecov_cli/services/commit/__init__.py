import logging
import typing
import uuid

from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
    send_post_request,
)

logger = logging.getLogger("codecovcli")


def create_commit_logic(
    commit_sha: str,
    parent_sha: typing.Optional[str],
    pr: typing.Optional[str],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    token: uuid.UUID,
    service: typing.Optional[str],
):
    encoded_slug = encode_slug(slug)
    sending_result = send_commit_data(
        commit_sha=commit_sha,
        parent_sha=parent_sha,
        pr=pr,
        branch=branch,
        slug=encoded_slug,
        token=token,
        service=service,
    )

    log_warnings_and_errors_if_any(sending_result, "Commit creating")
    return sending_result


def send_commit_data(commit_sha, parent_sha, pr, branch, slug, token, service):
    data = {
        "commitid": commit_sha,
        "parent_commit_id": parent_sha,
        "pullid": pr,
        "branch": branch,
    }
    headers = get_token_header_or_fail(token)
    url = f"https://api.codecov.io/upload/{service}/{slug}/commits"
    return send_post_request(url=url, data=data, headers=headers)
