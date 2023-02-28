import logging
import pathlib
import re
import typing
import uuid
from collections import namedtuple
from fnmatch import fnmatch

from codecov_cli.services.upload.coverage_file_finder import CoverageFileFinder
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
        coverage_file_finder: CoverageFileFinder,
    ):
        self.preparation_plugins = preparation_plugins
        self.network_finder = network_finder
        self.coverage_file_finder = coverage_file_finder

    def _produce_file_fixes_for_network(
        self, network: typing.List[str]
    ) -> typing.List[UploadCollectionResultFileFixer]:
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

        return UploadCollectionResultFileFixer(
            path, fixed_lines_without_reason, fixed_lines_with_reason, eof
        )

    def generate_upload_data(self) -> UploadCollectionResult:
        for prep in self.preparation_plugins:
            logger.debug(f"Running preparation plugin: {type(prep)}")
            prep.run_preparation(self)
        logger.debug("Collecting relevant files")
        network = self.network_finder.find_files()
        coverage_files = self.coverage_file_finder.find_coverage_files()
        logger.debug(f"Found {len(coverage_files)} coverage files to upload")
        for file in coverage_files:
            logger.debug(f"> {file}")
        return UploadCollectionResult(
            network=network,
            coverage_files=coverage_files,
            file_fixes=self._produce_file_fixes_for_network(network),
        )
