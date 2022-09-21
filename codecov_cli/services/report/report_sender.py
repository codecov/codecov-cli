import logging

import requests

from codecov_cli.types import RequestError, RequestResult

logger = logging.getLogger("codecovcli")


class ReportSender(object):
    def send_report_data(self, commit_sha: str, code: str, slug: str):
        data = {"code": code}
        headers = {}

        resp = requests.post(
            f"https://codecov.io/upload/{slug}/commits/{commit_sha}/reports",
            headers=headers,
            data=data,
        )

        if resp.status_code >= 400:
            logger.info(f"{resp}")
            return RequestResult(
                error=RequestError(
                    code=f"HTTP Error {resp.status_code}",
                    description=resp.text,
                    params={},
                ),
                warnings=[],
            )

        logger.debug(
            "Finished creating report process successfully",
            extra=dict(
                extra_log_attributes=dict(
                    commit_sha=commit_sha,
                    code=code,
                    slug=slug,
                )
            ),
        )
        return RequestResult(error=None, warnings=[])
