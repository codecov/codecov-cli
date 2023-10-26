import base64
import json
import logging
import pathlib
import re
import typing
import zlib
from collections import namedtuple
from fnmatch import fnmatch
from typing import Any, Dict

import click

from codecov_cli.services.upload.network_finder import NetworkFinder
from codecov_cli.services.upload.coverage_file_finder import CoverageFileFinder
from codecov_cli.types import (
    UploadCollectionResult,
    UploadCollectionResultFile,
    UploadCollectionResultFileFixer,
    PreparationPluginInterface,
)
from codecov_cli.services.upload.collectors.coverage_upload_collector import (
    CoverageUploadCollector,
)

logger = logging.getLogger("codecovcli")

fix_patterns_to_apply = namedtuple(
    "fix_patterns_to_apply", ["without_reason", "with_reason", "eof"]
)


class LegacyUploadCollector(CoverageUploadCollector):
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
