import logging
import pathlib
import re
import typing
import uuid
from collections import namedtuple
from fnmatch import fnmatch

import click

from codecov_cli.services.upload.file_finder import FileFinder
from codecov_cli.services.upload.network_finder import NetworkFinder
from codecov_cli.types import (
    PreparationPluginInterface,
    UploadCollectionResult,
    UploadCollectionResultFileFixer,
)

logger = logging.getLogger("codecovcli")

fix_patterns_to_apply = namedtuple(
    "fix_patterns_to_apply", ["without_reason", "with_reason", "eof"]
)


class UploadCollector(object):
    def __init__(
        self,
        preparation_plugins: typing.List[PreparationPluginInterface],
        network_finder: NetworkFinder,
        file_finder: FileFinder,
        disable_file_fixes: bool = False,
    ):
        self.preparation_plugins = preparation_plugins
        self.network_finder = network_finder
        self.file_finder = file_finder
        self.disable_file_fixes = disable_file_fixes

    def _produce_file_fixes(
        self, files: typing.List[str]
    ) -> typing.List[UploadCollectionResultFileFixer]:
        if not files or self.disable_file_fixes:
            return []
        # patterns that we don't need to specify a reason for
        empty_line_regex = re.compile(r"^\s*$")
        comment_regex = re.compile(r"^\s*\/\/.*$")
        bracket_regex = re.compile(r"^\s*[\{\}]\s*(\/\/.*)?$")
        list_regex = re.compile(r"^\s*[\]\[]\s*(\/\/.*)?$")
        parenthesis_regex = re.compile(r"^\s*[\(\)]\s*(\/\/.*)?$")
        go_function_regex = re.compile(r"^\s*func\s*[\{]\s*(\/\/.*)?$")
        php_end_bracket_regex = re.compile(r"^\s*\);\s*(\/\/.*)?$")

        # patterns to specify a reason for
        comment_block_regex = re.compile(r"^\s*(\/\*|\*\/)\s*$")
        lcov_excel_regex = re.compile(r"\/\/ LCOV_EXCL")

        kt_patterns_to_apply = fix_patterns_to_apply(
            [bracket_regex, parenthesis_regex], [comment_block_regex], True
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
        for filename in files:
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
                # If lineno is unset that means that the
                # file is empty thus the eof should be 0
                # so lineno will be set to -1 here
                lineno = -1
                # overwrite lineno in this for loop
                # if f is empty, lineno stays at -1
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
        except IsADirectoryError as err:
            logger.info(f"Skipping {filename}, found a directory not a file")

        return UploadCollectionResultFileFixer(
            path, fixed_lines_without_reason, fixed_lines_with_reason, eof
        )

    def generate_upload_data(self, report_type="coverage") -> UploadCollectionResult:
        for prep in self.preparation_plugins:
            logger.debug(f"Running preparation plugin: {type(prep)}")
            prep.run_preparation(self)
        logger.debug("Collecting relevant files")
        network = self.network_finder.find_files()
        report_files = self.file_finder.find_files()
        logger.info(f"Found {len(report_files)} {report_type} files to report")
        if not report_files:
            if report_type == "test_results":
                error_message = "No JUnit XML reports found. Please review our documentation (https://docs.codecov.com/docs/test-result-ingestion-beta) to generate and upload the file."
            else:
                error_message = "No coverage reports found. Please make sure you're generating reports successfully."
            raise click.ClickException(
                click.style(
                    error_message,
                    fg="red",
                )
            )
        for file in report_files:
            logger.info(f"> {file}")
        return UploadCollectionResult(
            network=network,
            files=report_files,
            file_fixes=(
                self._produce_file_fixes(self.network_finder.find_files(True))
                if report_type == "coverage"
                else []
            ),
        )
