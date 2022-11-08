import logging

import requests

from codecov_cli.helpers.request import send_post_request
from codecov_cli.types import RequestError, RequestResult

logger = logging.getLogger("codecovcli")


class ReportSender(object):
    def send_report_data(self, commit_sha: str, code: str, slug: str):
        data = {"code": code}
        headers = {}

        url = f"https://codecov.io/upload/{slug}/commits/{commit_sha}/reports"
        resp = send_post_request(url=url, headers=headers, data=data)
        return resp
