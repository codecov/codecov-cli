import logging
import typing
import uuid

from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import send_post_request

logger = logging.getLogger("codecovcli")


def create_commit_logic(
    commit_sha: str,
    parent_sha: typing.Optional[str],
    pr: typing.Optional[str],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    token: uuid.UUID,
):
    encoded_slug = encode_slug(slug)
    sending_result = send_commit_data(
        commit_sha=commit_sha,
        parent_sha=parent_sha,
        pr=pr,
        branch=branch,
        slug=encoded_slug,
        token=token,
    )

    if sending_result.warnings:
        number_warnings = len(sending_result.warnings)
        pluralization = "s" if number_warnings > 1 else ""
        logger.info(
            f"Commit creating process had {number_warnings} warning{pluralization}",
        )
        for ind, w in enumerate(sending_result.warnings):
            logger.warning(f"Warning {ind + 1}: {w.message}")
    if sending_result.error is not None:
        logger.error(f"Commit creating failed: {sending_result.error.description}")
    return sending_result


def send_commit_data(commit_sha, parent_sha, pr, branch, slug, token):
    data = {
        "commitid": commit_sha,
        "parent_commit_id": parent_sha,
        "pullid": pr,
        "branch": branch,
    }
    headers = {"Authorization": f"token {token.hex}"}
    url = f"https://codecov.io/upload/{slug}/commits"
    return send_post_request(url=url, data=data, headers=headers)
