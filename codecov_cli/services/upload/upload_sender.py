import base64
import json
import logging
import typing
import zlib
from typing import Any, Dict

import sentry_sdk

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.helpers.config import CODECOV_INGEST_URL
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.helpers.upload_type import ReportType
from codecov_cli.helpers.request import (
    get_token_header,
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
        token: typing.Optional[str],
        env_vars: typing.Dict[str, str],
        report_code: str,
        report_type: ReportType = ReportType.COVERAGE,
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
        parent_sha: typing.Optional[str] = None,
        upload_coverage: bool = False,
        args: dict = None,
    ) -> RequestResult:
        current_transaction = sentry_sdk.get_current_scope().transaction
        if current_transaction:
            current_transaction.set_data("commit_sha", commit_sha)
            current_transaction.set_data("slug", slug)

        with sentry_sdk.start_span(name="upload_sender"):
            with sentry_sdk.start_span(name="upload_sender_preparation"):
                file_not_found = False
                if report_type == ReportType.TEST_RESULTS and not upload_data.files:
                    file_not_found = True

                data = {
                    "ci_service": ci_service,
                    "ci_url": build_url,
                    "cli_args": args,
                    "env": env_vars,
                    "flags": flags,
                    "job_code": job_code,
                    "name": name,
                    "version": codecov_cli_version,
                    "file_not_found": file_not_found,
                }

                if upload_coverage:
                    data["branch"] = branch
                    data["code"] = report_code
                    data["commitid"] = commit_sha
                    data["parent_commit_id"] = parent_sha
                    data["pullid"] = pull_request_number
                headers = get_token_header(token)
                encoded_slug = encode_slug(slug)
                upload_url = enterprise_url or CODECOV_INGEST_URL
                url, data = self.get_url_and_possibly_update_data(
                    data,
                    report_type,
                    upload_url,
                    git_service,
                    branch,
                    encoded_slug,
                    commit_sha,
                    report_code,
                    upload_coverage,
                )
                # Data that goes to storage
                reports_payload = self._generate_payload(
                    upload_data, env_vars, report_type
                )

            with sentry_sdk.start_span(name="upload_sender_storage_request"):
                logger.debug("Sending upload request to Codecov")
                resp_from_codecov = send_post_request(
                    url=url,
                    data=data,
                    headers=headers,
                )

                if file_not_found:
                    logger.info(
                        "No test results reports found. Triggering notifications without uploading."
                    )
                    return resp_from_codecov

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

            with sentry_sdk.start_span(name="upload_sender_storage"):
                logger.debug("Sending upload to storage")
                resp_from_storage = send_put_request(put_url, data=reports_payload)

            return resp_from_storage

    def _generate_payload(
        self,
        upload_data: UploadCollectionResult,
        env_vars: typing.Dict[str, str],
        report_type: ReportType = ReportType.COVERAGE,
    ) -> bytes:
        network_files = upload_data.network
        if report_type == ReportType.COVERAGE:
            payload = {
                "report_fixes": {
                    "format": "legacy",
                    "value": self._get_file_fixers(upload_data),
                },
                "network_files": network_files if network_files is not None else [],
                "coverage_files": self._get_files(upload_data),
                "metadata": {},
            }
        elif report_type == ReportType.TEST_RESULTS:
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
            file_fixers[file_fixer.path.as_posix()] = {
                "eof": file_fixer.eof,
                "lines": total_fixed_lines,
            }

        return file_fixers

    def _get_files(self, upload_data: UploadCollectionResult):
        return [self._format_file(file) for file in upload_data.files]

    def _format_file(self, file: UploadCollectionResultFile):
        format, formatted_content = self._get_format_info(file)
        return {
            "filename": file.get_filename(),
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
        report_type: ReportType,
        upload_url,
        git_service,
        branch,
        encoded_slug,
        commit_sha,
        report_code,
        upload_coverage=False,
        file_not_found=False,
    ):
        if report_type == ReportType.COVERAGE:
            base_url = f"{upload_url}/upload/{git_service}/{encoded_slug}"
            if upload_coverage:
                url = f"{base_url}/upload-coverage"
            else:
                url = f"{base_url}/commits/{commit_sha}/reports/{report_code}/uploads"
        elif report_type == ReportType.TEST_RESULTS:
            data["slug"] = encoded_slug
            data["branch"] = branch
            data["commit"] = commit_sha
            data["service"] = git_service
            data["file_not_found"] = file_not_found
            url = f"{upload_url}/upload/test_results/v1"

        return url, data
