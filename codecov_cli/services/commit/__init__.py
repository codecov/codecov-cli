import logging
import os
import typing

from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.helpers.encoder import decode_slug, encode_slug
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
    token: str,
    service: typing.Optional[str],
    enterprise_url: typing.Optional[str] = None,
    fail_on_error: bool = False,
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
        enterprise_url=enterprise_url,
    )

    log_warnings_and_errors_if_any(sending_result, "Commit creating", fail_on_error)
    return sending_result


def send_commit_data(
    commit_sha, parent_sha, pr, branch, slug, token, service, enterprise_url
):
    # this is how the CLI receives the username of the user to whom the fork belongs
    # to and the branch name from the action
    tokenless = os.environ.get("TOKENLESS")
    if tokenless:
        headers = None  # type: ignore
        branch = tokenless  # type: ignore
        logger.info("The PR is happening in a forked repo. Using tokenless upload.")
    else:
        headers = get_token_header_or_fail(token)

    data = {
        "commitid": commit_sha,
        "parent_commit_id": parent_sha,
        "pullid": pr,
        "branch": branch,
    }

    upload_url = enterprise_url or CODECOV_API_URL
    url = f"{upload_url}/upload/{service}/{slug}/commits"
    return send_post_request(url=url, data=data, headers=headers)
