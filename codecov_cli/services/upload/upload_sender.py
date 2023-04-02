import base64
import json
import typing
import uuid
import zlib
from typing import Any, Dict

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
        ci_service: typing.Optional[str] = None,
        git_service: typing.Optional[str] = None,
    ) -> RequestResult:

        data = {
            "ci_url": build_url,
            "flags": flags,
            "env": env_vars,
            "name": name,
            "job_code": job_code,
        }

        headers = get_token_header_or_fail(token)
        encoded_slug = encode_slug(slug)
        url = f"https://api.codecov.io/upload/{git_service}/{encoded_slug}/commits/{commit_sha}/reports/{report_code}/uploads"
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

    def _get_file_fixers(
        self, upload_data: UploadCollectionResult
    ) -> Dict[str, Dict[str, Any]]:
        """
        Returns file/path fixes in the following format:

        {
            {path}: {
                "eof": int(eof_line),
                "lines": {set_of_lines},
            },
        }
        """
        file_fixers = {}
        for file_fixer in upload_data.file_fixes:
            fixed_lines_with_reason = set(
                [fixer[0] for fixer in file_fixer.fixed_lines_with_reason]
            )
            total_fixed_lines = list(
                file_fixer.fixed_lines_without_reason.union(fixed_lines_with_reason)
            )
            file_fixers[str(file_fixer.path)] = {
                "eof": file_fixer.eof,
                "lines": total_fixed_lines,
            }

        return file_fixers

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
