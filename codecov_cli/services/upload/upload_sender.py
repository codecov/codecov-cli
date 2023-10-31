import base64
import json
import logging
import typing
import uuid
import zlib
from typing import Any, Dict

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    send_post_request,
    send_put_request,
)
from codecov_cli.types import (
    RequestResult,
    UploadCollectionResult,
    UploadCollectionResultFile,
)

logger = logging.getLogger("codecovcli")


class UploadSender(object):
    def send_upload_data(
        self,
        upload_file_type: str,
        upload_data: bytes,
        commit_sha: str,
        token: uuid.UUID,
        env_vars: typing.Dict[str, str],
        report_code: str,
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
    ) -> RequestResult:
        data = {
            "upload_file_type": upload_file_type,
            "ci_url": build_url,
            "flags": flags,
            "env": env_vars,
            "name": name,
            "job_code": job_code,
            "version": codecov_cli_version,
        }

        # Data to upload to Codecov
        headers = get_token_header_or_fail(token)
        encoded_slug = encode_slug(slug)
        upload_url = enterprise_url or CODECOV_API_URL
        url = f"{upload_url}/upload/{git_service}/{encoded_slug}/commits/{commit_sha}/reports/{report_code}/uploads"

        logger.debug("Sending upload request to Codecov")
        resp_from_codecov = send_post_request(
            url=url,
            data=data,
            headers=headers,
        )
        if resp_from_codecov.status_code >= 400:
            return resp_from_codecov
        resp_json_obj = json.loads(resp_from_codecov.text)
        if resp_json_obj.get("url"):
            logger.info(
                f"Your upload is now processing. When finished, results will be available at: {resp_json_obj.get('url')}"
            )
        logger.debug(
            "Upload request to Codecov complete.",
            extra=dict(extra_log_attributes=dict(response=resp_json_obj)),
        )
        put_url = resp_json_obj["raw_upload_location"]
        logger.debug("Sending upload to storage")
        resp_from_storage = send_put_request(put_url, data=upload_data)
        return resp_from_storage
