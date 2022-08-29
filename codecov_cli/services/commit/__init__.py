import logging
import typing

from codecov_cli.helpers.encoder import encode_slug

from .commit_sender import CommitSender

logger = logging.getLogger("codecovcli")


def create_commit_logic(
    commit_sha: str,
    parent_sha: typing.Optional[str],
    pr: typing.Optional[str],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
):
    encoded_slug = encode_slug(slug)
    sender = CommitSender()
    sending_result = sender.send_commit_data(
        commit_sha=commit_sha,
        parent_sha=parent_sha,
        pr=pr,
        branch=branch,
        slug=encoded_slug,
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
