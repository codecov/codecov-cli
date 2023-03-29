import logging
import typing
import uuid
from dataclasses import dataclass

import requests

from codecov_cli import __version__ as codecov_cli_version
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
        upload_data: UploadCollectionResult,
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

        resp = requests.post(
            "https://codecov.io/upload/v4", headers=headers, params=params
        )

        if resp.status_code >= 400:
            return UploadSendingResult(
                error=UploadSendingError(
                    code=f"HTTP Error {resp.status_code}",
                    description=resp.text,
                    params={},
                ),
                warnings=[],
            )

        result_url, put_url = resp.text.split("\n")

        reports_payload = self._generate_payload(upload_data, env_vars)
        resp = requests.put(put_url, data=reports_payload)

        if resp.status_code >= 400:
            return UploadSendingResult(
                error=UploadSendingError(
                    code=f"HTTP Error {resp.status_code}",
                    description=resp.text,
                    params={},
                ),
                warnings=[],
            )

        return UploadSendingResult(error=None, warnings=[])

    def _generate_payload(
        self, upload_data: UploadCollectionResult, env_vars: typing.Dict[str, str]
    ) -> bytes:
        env_vars_section = self._generate_env_vars_section(env_vars)
        network_section = self._generate_network_section(upload_data)
        coverage_files_section = self._generate_coverage_files_section(upload_data)

        return b"".join([env_vars_section, network_section, coverage_files_section])

    def _generate_env_vars_section(self, env_vars) -> bytes:
        filtered_env_vars = {
            key: value for key, value in env_vars.items() if value is not None
        }

        if not filtered_env_vars:
            return b""

        env_vars_section = "".join(
            f"{env_var}={value}\n" for env_var, value in filtered_env_vars.items()
        )
        return env_vars_section.encode() + b"<<<<<< ENV\n"

    def _generate_network_section(self, upload_data: UploadCollectionResult) -> bytes:
        network_files = upload_data.network

        if not network_files:
            return b""

        network_files_section = "".join(file + "\n" for file in network_files)
        return network_files_section.encode() + b"<<<<<< network\n"

    def _generate_coverage_files_section(self, upload_data: UploadCollectionResult):
        return b"".join(
            self._format_coverage_file(file) for file in upload_data.coverage_files
        )

    def _format_coverage_file(self, file: UploadCollectionResultFile) -> bytes:
        header = b"# path=" + file.get_filename() + b"\n"
        file_content = file.get_content() + b"\n"
        file_end = b"<<<<<< EOF\n"

        return header + file_content + file_end
