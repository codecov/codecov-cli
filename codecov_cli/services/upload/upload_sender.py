import base64
import json
import logging
import typing
import uuid
import zlib
from dataclasses import dataclass

import requests

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.request import send_post_request, send_put_request
from codecov_cli.types import (
    RequestResult,
    UploadCollectionResult,
    UploadCollectionResultFile,
)


class UploadSender(object):
    def send_upload_data(
        self,
        upload_data: UploadCollectionResult,
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
        service: typing.Optional[str] = None,
    ) -> RequestResult:

        data = {
            "ci_url": build_url,
            "flags": flags,
            "env": env_vars,
            "name": name,
        }

        headers = {"Authorization": f"token {token.hex}"}
        encoded_slug = encode_slug(slug)
        url = f"https://api.codecov.io/upload/github/{encoded_slug}/commits/{commit_sha}/reports/{report_code}/uploads"
        resp = send_post_request(url=url, data=data, headers=headers)

        if resp.status_code >= 400:
            return resp

        resp_json_obj = json.loads(resp.text)
        put_url = resp_json_obj["raw_upload_location"]
        reports_payload = self._generate_payload(upload_data, env_vars)
        resp = send_put_request(put_url, data=reports_payload)
        return resp

    def _generate_payload(
        self, upload_data: UploadCollectionResult, env_vars: typing.Dict[str, str]
    ) -> bytes:
        network_files = upload_data.network
        payload = {
            "path_fixes": {
                "format": "legacy",
                "value": self._get_file_fixers(upload_data),
            },
            "network_files": network_files if network_files is not None else [],
            "coverage_files": self._get_coverage_files(upload_data),
            "metadata": {},
        }
        json_data = json.dumps(payload)
        return json_data.encode()

    def _get_file_fixers(self, upload_data: UploadCollectionResult):
        return [str(file_fixer.path) for file_fixer in upload_data.file_fixes]

    def _get_coverage_files(self, upload_data: UploadCollectionResult):
        return [self._format_coverage_file(file) for file in upload_data.coverage_files]

    def _format_coverage_file(self, file: UploadCollectionResultFile):
        format, formatted_content = self._get_format_info(file)
        return {
            "filename": file.get_filename().decode(),
            "format": format,
            "data": formatted_content,
            "labels": "",
        }

    def _get_format_info(self, file: UploadCollectionResultFile):
        format = "base64+compressed"
        formatted_content = (
            base64.b64encode(zlib.compress((file.get_content())))
        ).decode()
        return format, formatted_content
