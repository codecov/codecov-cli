import logging

import requests

from codecov_cli.types import RequestError, RequestResult

logger = logging.getLogger("codecovcli")


class CommitSender(object):
    def send_commit_data(
        self, commit_sha: str, parent_sha: str, pr: str, branch: str, slug: str
    ):
        data = {
            "commitid": commit_sha,
            "parent_commit_id": parent_sha,
            "pullid": pr,
            "branch": branch,
        }
        headers = {}

        resp = requests.post(
            f"https://codecov.io/upload/{slug}/commits", headers=headers, data=data
        )

        if resp.status_code >= 400:
            return RequestResult(
                error=RequestError(
                    code=f"HTTP Error {resp.status_code}",
                    description=resp.text,
                    params={},
                ),
                warnings=[],
            )

        return RequestResult(error=None, warnings=[])
