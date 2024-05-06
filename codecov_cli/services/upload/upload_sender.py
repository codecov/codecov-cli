import base64
import json
import logging
import typing
import zlib
from typing import Any, Dict

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.git import get_pull, is_fork_pr
from codecov_cli.helpers.request import (
    get_auth_header,
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
        upload_data: UploadCollectionResult,
        commit_sha: str,
        token: str,
        env_vars: typing.Dict[str, str],
        report_code: str,
        upload_file_type: str = "coverage",
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
            "ci_url": build_url,
            "flags": flags,
            "env": env_vars,
            "name": name,
            "job_code": job_code,
            "version": codecov_cli_version,
            "ci_service": ci_service,
        }

        headers = get_auth_header(token)
        encoded_slug = encode_slug(slug)
        upload_url = enterprise_url or CODECOV_API_URL
        url, data = self.get_url_and_possibly_update_data(
            data,
            upload_file_type,
            upload_url,
            git_service,
            encoded_slug,
            commit_sha,
            report_code,
        )
        # Data that goes to storage
        reports_payload = self._generate_payload(
            upload_data, env_vars, upload_file_type
        )

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
        resp_from_storage = send_put_request(put_url, data=reports_payload)
        return resp_from_storage

    def _generate_payload(
        self,
        upload_data: UploadCollectionResult,
        env_vars: typing.Dict[str, str],
        upload_file_type="coverage",
    ) -> bytes:
        network_files = upload_data.network
        if upload_file_type == "coverage":
            payload = {
                "report_fixes": {
                    "format": "legacy",
                    "value": self._get_file_fixers(upload_data),
                },
                "network_files": network_files if network_files is not None else [],
                "coverage_files": self._get_files(upload_data),
                "metadata": {},
            }
        elif upload_file_type == "test_results":
            payload = {
                "test_results_files": self._get_files(upload_data),
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

    def _get_files(self, upload_data: UploadCollectionResult):
        return [self._format_file(file) for file in upload_data.files]

    def _format_file(self, file: UploadCollectionResultFile):
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

    def get_url_and_possibly_update_data(
        self,
        data,
        report_type,
        upload_url,
        git_service,
        encoded_slug,
        commit_sha,
        report_code,
    ):
        if report_type == "coverage":
            url = f"{upload_url}/upload/{git_service}/{encoded_slug}/commits/{commit_sha}/reports/{report_code}/uploads"
        elif report_type == "test_results":
            data["slug"] = encoded_slug
            data["commit"] = commit_sha
            data["service"] = git_service
            url = f"{upload_url}/upload/test_results/v1"

        return url, data
