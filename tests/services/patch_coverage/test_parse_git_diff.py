from pathlib import Path
from typing import List

import pytest

from codecov_cli.services.patch_coverage.parse_git_diff import (
    get_file_path,
    get_files_in_diff,
    get_lines_added_and_removed,
    parse_diff_chunk_header,
    parse_diff_file,
)
from codecov_cli.services.patch_coverage.types import DiffFile, FileState


def DiffFileFactory(
    added_lines: List[int],
    removed_lines: List[int],
    state: FileState,
    path: Path,
) -> DiffFile:
    obj = DiffFile()
    obj.added_lines = added_lines
    obj.removed_lines = removed_lines
    obj.state = state
    obj.path = path
    return obj


class TestDiffParsing(object):

    example_diff = [
        "diff --git a/codecov_cli/fallbacks.py b/codecov_cli/fallbacks.py",
        "index d84c6eb..164be45 100644",
        "--- a/codecov_cli/fallbacks.py",
        "+++ b/codecov_cli/fallbacks.py",
        "@@ -11,6 +11,7 @@ class FallbackFieldEnum(Enum):",
        "      job_code = auto()",
        "      pull_request_number = auto()",
        "     slug = auto()",
        "+    # test change",
        "     branch = auto()",
        "     service = auto()",
        "     git_service = auto()",
        "@@ -39,3 +40,5 @@ class CodecovOption(click.Option):",
        "                 if res is not None:",
        "                     return res",
        "         return None",
        "+    ",
        "+    # test change",
        "diff --git a/codecov_cli/services/__init__.py b/codecov_cli/services/__init__.py",
        "deleted file mode 100644",
        "index e69de29..0000000",
        "diff --git a/tests/commands/test_invoke_labelanalysis.py b/tests/commands/test_invoke_labelanalysis.py",
        "index 4e1fa74..31fddd3 100644",
        "--- a/tests/commands/test_invoke_labelanalysis.py",
        "+++ b/tests/commands/test_invoke_labelanalysis.py",
        "@@ -50,7 +50,8 @@ def get_labelanalysis_deps(mocker):",
        '         "collected_labels": collected_labels,',
        "     }",
        " ",
        '-FAKE_BASE_SHA="0111111111111111111111111111111111111110"',
        "+",
        '+FAKE_BASE_SHA = "0111111111111111111111111111111111111110"',
        " ",
        " ",
        " class TestLabelAnalysisNotInvoke(object):",
        "@@ -207,7 +208,11 @@ class TestLabelAnalysisCommand(object):",
        "             cli_runner = CliRunner()",
        "             result = cli_runner.invoke(",
        "                 cli,",
        '-                ["label-analysis", "--token=STATIC_TOKEN", f"--base-sha={FAKE_BASE_SHA}"],',
        "+                [",
        '+                    "label-analysis",',
        '+                    "--token=STATIC_TOKEN",',
        '+                    f"--base-sha={FAKE_BASE_SHA}",',
        "+                ],",
        "                 obj={},",
        "             )",
        "             assert result.exit_code == 0",
        "@@ -308,7 +313,11 @@ class TestLabelAnalysisCommand(object):",
        "             cli_runner = CliRunner()",
        "             result = cli_runner.invoke(",
        "                 cli,",
        '-                ["label-analysis", "--token=STATIC_TOKEN", f"--base-sha={FAKE_BASE_SHA}"],',
        "+                [",
        '+                    "label-analysis",',
        '+                    "--token=STATIC_TOKEN",',
        '+                    f"--base-sha={FAKE_BASE_SHA}",',
        "+                ],",
        "                 obj={},",
        "             )",
        "             mock_get_runner.assert_called()",
    ]

    @pytest.mark.parametrize(
        "chunk,start_add,start_remove,expected",
        [
            (
                [
                    "      job_code = auto()",
                    "      pull_request_number = auto()",
                    "     slug = auto()",
                    "+    # test change",
                    "     branch = auto()",
                    "     service = auto()",
                    "     git_service = auto()",
                ],
                11,
                11,
                ([14], []),
            ),
            (
                [
                    "             cli_runner = CliRunner()",
                    "             result = cli_runner.invoke(",
                    "                 cli,",
                    '-                ["label-analysis", "--token=STATIC_TOKEN", f"--base-sha={FAKE_BASE_SHA}"],',
                    "+                [",
                    '+                    "label-analysis",',
                    '+                    "--token=STATIC_TOKEN",',
                    '+                    f"--base-sha={FAKE_BASE_SHA}",',
                    "+                ],",
                    "                 obj={},",
                    "             )",
                    "             assert result.exit_code == 0",
                ],
                208,
                207,
                ([211, 212, 213, 214, 215], [210]),
            ),
        ],
    )
    def test_get_lines_added_and_removed(
        self, chunk, start_add, start_remove, expected
    ):
        assert get_lines_added_and_removed(start_add, start_remove, chunk) == expected

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "diff --git a/codecov_cli/services/__init__.py b/codecov_cli/services/__init__.py",
                Path("codecov_cli/services/__init__.py"),
            ),
            (
                "diff --git a/codecov_cli/fallbacks.py b/codecov_cli/fallbacks.py",
                Path("codecov_cli/fallbacks.py"),
            ),
        ],
    )
    def test_get_file_path(self, line, expected):
        assert get_file_path(line) == expected

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "@@ -207,7 +208,11 @@ class TestLabelAnalysisCommand(object):",
                (208, 207, 11),
            ),
            (
                "@@ -308,7 +313,11 @@ class TestLabelAnalysisCommand(object):",
                (313, 308, 11),
            ),
            (
                "@@ -100,15 +115,4 @@ class TestLabelAnalysisCommand(object):",
                (115, 100, 15),
            ),
        ],
    )
    def test_parse_diff_chunk_header(self, line, expected):
        assert parse_diff_chunk_header(line) == expected

    def test_parse_diff_file_only_adds(self):
        raw_chunk_only_adds = self.example_diff[0:18]
        diff_file = parse_diff_file(raw_chunk_only_adds)
        assert isinstance(diff_file, DiffFile)
        assert diff_file.state == FileState.modified
        assert diff_file.path == Path("codecov_cli/fallbacks.py")
        assert diff_file.added_lines == [14, 43, 44]
        assert diff_file.removed_lines == []

    def test_parse_diff_file(self):
        raw_chunk = self.example_diff[21:61]
        diff_file = parse_diff_file(raw_chunk)
        print(raw_chunk)
        assert isinstance(diff_file, DiffFile)
        assert diff_file.state == FileState.modified
        assert diff_file.path == Path("tests/commands/test_invoke_labelanalysis.py")
        assert diff_file.added_lines == [
            53,
            54,
            211,
            212,
            213,
            214,
            215,
            316,
            317,
            318,
            319,
            320,
        ]
        assert diff_file.removed_lines == [53, 210, 311]

    def test_parse_diff_into_chunks(self):
        expected_result = [
            DiffFileFactory(
                path=Path("codecov_cli/fallbacks.py"),
                state=FileState.modified,
                added_lines=[14, 43, 44],
                removed_lines=[],
            ),
            DiffFileFactory(
                path=Path("codecov_cli/services/__init__.py"),
                state=FileState.deleted,
                added_lines=[],
                removed_lines=[],
            ),
            DiffFileFactory(
                path=Path("tests/commands/test_invoke_labelanalysis.py"),
                state=FileState.modified,
                added_lines=[
                    53,
                    54,
                    211,
                    212,
                    213,
                    214,
                    215,
                    316,
                    317,
                    318,
                    319,
                    320,
                ],
                removed_lines=[53, 210, 311],
            ),
        ]
        result = get_files_in_diff(self.example_diff)
        assert len(result) == len(expected_result)
        for received, expected in zip(result, expected_result):
            assert received.path == expected.path
            assert received.state == expected.state
            assert received.added_lines == expected.added_lines
            assert received.removed_lines == expected.removed_lines
