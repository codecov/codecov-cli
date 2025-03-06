import logging
import os
import typing

from codecov_cli.helpers.config import CODECOV_INGEST_URL
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import (
    get_token_header,
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
    token: typing.Optional[str],
    service: typing.Optional[str],
    enterprise_url: typing.Optional[str] = None,
    fail_on_error: bool = False,
    args: dict = None,
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
        args=args,
    )

    log_warnings_and_errors_if_any(sending_result, "Commit creating", fail_on_error)
    return sending_result


def send_commit_data(
    commit_sha,
    parent_sha,
    pr,
    branch,
    slug,
    token,
    service,
    enterprise_url,
    args,
):
    # Old versions of the GHA use this env var instead of the regular branch
    # argument to provide an unprotected branch name
    if tokenless := os.environ.get("TOKENLESS"):
        branch = tokenless

    if branch and ":" in branch:
        logger.info(f"Creating a commit for an unprotected branch: {branch}")
    elif token is None:
        logger.warning(
            f"Branch `{branch}` is protected but no token was provided\nFor information on Codecov upload tokens, see https://docs.codecov.com/docs/codecov-tokens"
        )
    else:
        logger.info(f"Using token to create a commit for protected branch `{branch}`")

    headers = get_token_header(token)

    data = {
        "branch": branch,
        "cli_args": args,
        "commitid": commit_sha,
        "parent_commit_id": parent_sha,
        "pullid": pr,
    }

    upload_url = enterprise_url or CODECOV_INGEST_URL
    url = f"{upload_url}/upload/{service}/{slug}/commits"
    return send_post_request(
        url=url,
        data=data,
        headers=headers,
    )
