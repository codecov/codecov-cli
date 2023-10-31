import logging
import typing
import uuid
from dataclasses import dataclass

import requests

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.helpers.config import LEGACY_CODECOV_API_URL
from codecov_cli.helpers.request import send_post_request, send_put_request
from codecov_cli.types import UploadCollectionResult, UploadCollectionResultFile

logger = logging.getLogger("codecovcli")


@dataclass
class UploadSendingResultWarning(object):
    __slots__ = ("message",)
    message: str


@dataclass
class UploadSendingError(object):
    __slots__ = ("code", "params", "description")
    code: str
    params: typing.Dict
    description: str


@dataclass
class UploadSendingResult(object):
    __slots__ = ("error", "warnings")
    error: typing.Optional[UploadSendingError]
    warnings: typing.List[UploadSendingResultWarning]


class LegacyUploadSender(object):
    def send_upload_data(
        self,
        upload_file_type: str,
        upload_data: bytes,
        commit_sha: str,
        token: uuid.UUID,
        env_vars: typing.Dict[str, str],
        report_code: str = None,
        name: typing.Optional[str] = None,
        branch: typing.Optional[str] = None,
        slug: typing.Optional[str] = None,
        pull_request_number: typing.Optional[str] = None,
        build_code: typing.Optional[str] = None,
        build_url: typing.Optional[str] = None,
        job_code: typing.Optional[str] = None,
        flags: typing.List[str] = None,
        ci_service: typing.Optional[str] = None,
        git_service: typing.Optional[str] = None,
        enterprise_url: typing.Optional[str] = None,
    ) -> UploadSendingResult:
        params = {
            "package": f"codecov-cli/{codecov_cli_version}",
            "commit": commit_sha,
            "build": build_code,
            "build_url": build_url,
            "branch": branch,
            "name": name,
            "slug": slug,
            "service": ci_service,
            "flags": flags,
            "pr": pull_request_number,
            "job": job_code,
        }

        if token:
            headers = {"X-Upload-Token": token.hex}
        else:
            logger.warning("Token is empty.")
            headers = {"X-Upload-Token": ""}

        upload_url = enterprise_url or LEGACY_CODECOV_API_URL
        resp = send_post_request(
            f"{upload_url}/upload/v4", headers=headers, params=params
        )
        if resp.status_code >= 400:
            return resp
        result_url, put_url = resp.text.split("\n")

        resp = send_put_request(put_url, data=upload_data)
        return resp
