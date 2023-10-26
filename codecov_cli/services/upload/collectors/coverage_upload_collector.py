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

logger = logging.getLogger("codecovcli")

fix_patterns_to_apply = namedtuple(
    "fix_patterns_to_apply", ["without_reason", "with_reason", "eof"]
)


class CoverageUploadCollector(object):
    def __init__(
        self,
        network_finder: NetworkFinder,
        coverage_file_finder: CoverageFileFinder,
        disable_file_fixes: bool = False,
        env_vars: typing.Dict[str, str] = None,
    ):
        self.network_finder = network_finder
        self.coverage_file_finder = coverage_file_finder
        self.disable_file_fixes = disable_file_fixes
        self.env_vars = env_vars

    def _produce_file_fixes_for_network(
        self, network: typing.List[str]
    ) -> typing.List[UploadCollectionResultFileFixer]:
        if not network or self.disable_file_fixes:
            return []
        # patterns that we don't need to specify a reason for
        empty_line_regex = re.compile(r"^\s*$")
        comment_regex = re.compile(r"^\s*\/\/.*$")
        bracket_regex = re.compile(r"^\s*[\{\}]\s*(\/\/.*)?$")
        list_regex = re.compile(r"^\s*[\]\[]\s*(\/\/.*)?$")
        go_function_regex = re.compile(r"^\s*func\s*[\{]\s*(\/\/.*)?$")
        php_end_bracket_regex = re.compile(r"^\s*\);\s*(\/\/.*)?$")

        # patterns to specify a reason for
        comment_block_regex = re.compile(r"^\s*(\/\*|\*\/)\s*$")
        lcov_excel_regex = re.compile(r"\/\/ LCOV_EXCL")

        kt_patterns_to_apply = fix_patterns_to_apply(
            [bracket_regex], [comment_block_regex], True
        )
        go_patterns_to_apply = fix_patterns_to_apply(
            [empty_line_regex, comment_regex, bracket_regex, go_function_regex],
            [comment_block_regex],
            False,
        )
        dart_patterns_to_apply = fix_patterns_to_apply(
            [bracket_regex],
            [],
            False,
        )
        php_patterns_to_apply = fix_patterns_to_apply(
            [bracket_regex, list_regex, php_end_bracket_regex],
            [],
            False,
        )

        cpp_swift_vala_patterns_to_apply = fix_patterns_to_apply(
            [empty_line_regex, bracket_regex],
            [lcov_excel_regex],
            False,
        )

        file_regex_patterns = {
            "*.kt": kt_patterns_to_apply,
            "*.go": go_patterns_to_apply,
            "*.dart": dart_patterns_to_apply,
            "*.php": php_patterns_to_apply,
            "*.c": cpp_swift_vala_patterns_to_apply,
            "*.cpp": cpp_swift_vala_patterns_to_apply,
            "*.cxx": cpp_swift_vala_patterns_to_apply,
            "*.h": cpp_swift_vala_patterns_to_apply,
            "*.hpp": cpp_swift_vala_patterns_to_apply,
            "*.m": cpp_swift_vala_patterns_to_apply,
            "*.swift": cpp_swift_vala_patterns_to_apply,
            "*.vala": cpp_swift_vala_patterns_to_apply,
        }

        result = []
        for filename in network:
            for glob, fix_patterns in file_regex_patterns.items():
                if fnmatch(filename, glob):
                    result.append(self._get_file_fixes(filename, fix_patterns))
                    break

        return result

    def _get_file_fixes(
        self, filename: str, fix_patterns_to_apply: fix_patterns_to_apply
    ) -> UploadCollectionResultFileFixer:
        path = pathlib.Path(filename)
        fixed_lines_without_reason = set()
        fixed_lines_with_reason = set()
        eof = None

        try:
            with open(filename, "r") as f:
                for lineno, line_content in enumerate(f):
                    if any(
                        pattern.match(line_content)
                        for pattern in fix_patterns_to_apply.with_reason
                    ):
                        fixed_lines_with_reason.add((lineno + 1, line_content))
                    elif any(
                        pattern.match(line_content)
                        for pattern in fix_patterns_to_apply.without_reason
                    ):
                        fixed_lines_without_reason.add(lineno + 1)

                if fix_patterns_to_apply.eof:
                    eof = lineno + 1
        except UnicodeDecodeError as err:
            logger.warning(
                f"There was an issue decoding: {filename}, file fixes were not applied to this file.",
                extra=dict(
                    encoding=err.encoding,
                    reason=err.reason,
                ),
            )

        return UploadCollectionResultFileFixer(
            path, fixed_lines_without_reason, fixed_lines_with_reason, eof
        )

    def generate_upload_data(self) -> bytes:
        logger.debug("Collecting relevant files")
        network = self.network_finder.find_files()
        coverage_files = self.coverage_file_finder.find_files()
        logger.info(f"Found {len(coverage_files)} coverage files to upload")
        if not coverage_files:
            raise click.ClickException(
                click.style(
                    "No coverage reports found. Please make sure you're generating reports successfully.",
                    fg="red",
                )
            )
        for file in coverage_files:
            logger.info(f"> {file}")
        collection_result = UploadCollectionResult(
            network=network,
            coverage_files=coverage_files,
            file_fixes=self._produce_file_fixes_for_network(network),
        )

        return self._generate_payload(collection_result, self.env_vars)

    def _generate_payload(
        self, upload_data: UploadCollectionResult, env_vars: typing.Dict[str, str]
    ) -> bytes:
        network_files = upload_data.network
        payload = {
            "report_fixes": {
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
