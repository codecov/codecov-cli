from datetime import datetime
from os import stat_result
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import call, patch

from codecov_cli.services.patch_coverage import PatchCoverageService, click
from codecov_cli.services.patch_coverage.types import DiffFile, FileState, FileStats
from tests.services.patch_coverage.factory import DiffFileFactory


class TestPatchCoverageService(object):
    @patch("codecov_cli.services.patch_coverage.subprocess")
    def test_execute_git(self, mock_subprocess):
        expected_result = CompletedProcess(
            args=["git"], returncode=0, stdout=b"process successful"
        )
        mock_subprocess.run.return_value = expected_result
        patch_coverage_service = PatchCoverageService()
        result = patch_coverage_service._execute_git(["diff"])
        assert result == "process successful"
        mock_subprocess.run.assert_called_with(["git", "diff"], capture_output=True)
        result = patch_coverage_service._execute_git(
            ["ls-files", "-o", "--exclude-standard"]
        )
        assert result == "process successful"
        mock_subprocess.run.assert_called_with(
            ["git", "ls-files", "-o", "--exclude-standard"], capture_output=True
        )

    @patch("codecov_cli.services.patch_coverage.get_files_in_diff")
    @patch("codecov_cli.services.patch_coverage.subprocess")
    def test_get_files_in_diff(self, mock_subprocess, mock_get_files_in_diff):
        mock_subprocess.run.return_value = CompletedProcess(
            args=["git"], returncode=0, stdout=b"diff line 1\ndiff line 2\ndiff line 3"
        )
        mock_get_files_in_diff.return_value = ["DiffFile_1", "DiffFIle_2"]
        patch_coverage_service = PatchCoverageService()
        files_in_diff = patch_coverage_service.get_files_in_diff(staged=False)
        assert files_in_diff == ["DiffFile_1", "DiffFIle_2"]
        mock_subprocess.run.assert_called_with(["git", "diff"], capture_output=True)
        mock_get_files_in_diff.assert_called_with(
            ["diff line 1", "diff line 2", "diff line 3"]
        )

    @patch("codecov_cli.services.patch_coverage.get_files_in_diff")
    @patch("codecov_cli.services.patch_coverage.subprocess")
    def test_get_files_in_diff_staged(self, mock_subprocess, mock_get_files_in_diff):
        mock_subprocess.run.return_value = CompletedProcess(
            args=["git"], returncode=0, stdout=b"diff line 1\ndiff line 2\ndiff line 3"
        )
        mock_get_files_in_diff.return_value = ["DiffFile_1", "DiffFIle_2"]
        patch_coverage_service = PatchCoverageService()
        files_in_diff = patch_coverage_service.get_files_in_diff(staged=True)
        assert files_in_diff == ["DiffFile_1", "DiffFIle_2"]
        mock_subprocess.run.assert_called_with(
            ["git", "diff", "--staged"], capture_output=True
        )
        mock_get_files_in_diff.assert_called_with(
            ["diff line 1", "diff line 2", "diff line 3"]
        )

    @patch("codecov_cli.services.patch_coverage.get_files_in_diff")
    @patch("codecov_cli.services.patch_coverage.subprocess")
    def test_get_files_in_diff_staged_some_base(
        self, mock_subprocess, mock_get_files_in_diff
    ):
        mock_subprocess.run.return_value = CompletedProcess(
            args=["git"], returncode=0, stdout=b"diff line 1\ndiff line 2\ndiff line 3"
        )
        mock_get_files_in_diff.return_value = ["DiffFile_1", "DiffFIle_2"]
        patch_coverage_service = PatchCoverageService()
        files_in_diff = patch_coverage_service.get_files_in_diff(
            staged=True, diff_base="main"
        )
        assert files_in_diff == ["DiffFile_1", "DiffFIle_2"]
        mock_subprocess.run.assert_called_with(
            ["git", "diff", "--staged", "main"], capture_output=True
        )
        mock_get_files_in_diff.assert_called_with(
            ["diff line 1", "diff line 2", "diff line 3"]
        )

    @patch("codecov_cli.services.patch_coverage.subprocess")
    def test_get_untracked_files(self, mock_subprocess, mocker):
        mocker.patch.object(
            Path,
            "stat",
            return_value=stat_result(
                [
                    33188,
                    39975008,
                    16777232,
                    1,
                    501,
                    20,
                    5225,
                    1692901142,
                    1692900660,
                    1692900660,
                ]
            ),
        )
        mock_subprocess.run.return_value = CompletedProcess(
            args=["git"], returncode=0, stdout=b"new_file.py\nsubmodule/awesome_idea.py"
        )
        patch_coverage_service = PatchCoverageService()
        untracked_files = patch_coverage_service.get_untracked_files()
        mock_subprocess.run.assert_called_with(
            ["git", "ls-files", "-o", "--exclude-standard"], capture_output=True
        )
        assert len(untracked_files) == 2
        for pair in zip(
            untracked_files, [Path("new_file.py"), Path("submodule/awesome_idea.py")]
        ):
            received, expected_path = pair
            assert isinstance(received, DiffFile)
            assert received.state == FileState.untracked
            assert received.path == expected_path
            assert received.last_modified == datetime.fromtimestamp(1692900660)

    def test_get_file_stats_and_uncovered_lines_untracked_file(self):
        untracked_file = DiffFile()
        untracked_file.path = Path("awesome.py")
        untracked_file.state = FileState.untracked
        coverage_info = {
            1: True,
            2: True,
            3: True,
            4: False,
            5: False,
            6: True,
            7: True,
            8: True,
        }
        patch_coverage_service = PatchCoverageService()
        stats_and_uncovered_lines = (
            patch_coverage_service.get_file_stats_and_uncovered_lines_untracked_file(
                untracked_file, coverage_info
            )
        )
        assert stats_and_uncovered_lines == (
            FileStats(
                total_lines_coverable=8,
                total_lines_covered=6,
                total_adds=8,
                total_removes=0,
            ),
            ["awesome.py:4", "awesome.py:5"],
        )

    def test_get_file_stats_and_uncovered_lines(self):
        untracked_file = DiffFile()
        untracked_file.path = Path("awesome.py")
        untracked_file.state = FileState.untracked
        coverage_info = {
            1: True,
            2: True,
            3: True,
            4: False,
            5: False,
            6: True,
            7: True,
            8: True,
        }
        patch_coverage_service = PatchCoverageService()
        stats_and_uncovered_lines = (
            patch_coverage_service.get_file_stats_and_uncovered_lines(
                untracked_file, coverage_info
            )
        )
        assert stats_and_uncovered_lines == (
            FileStats(
                total_lines_coverable=8,
                total_lines_covered=6,
                total_adds=8,
                total_removes=0,
            ),
            ["awesome.py:4", "awesome.py:5"],
        )
        modified_file = DiffFile()
        modified_file.path = Path("awesome.py")
        modified_file.state = FileState.modified
        modified_file.added_lines = [4, 5, 6, 7, 8, 20, 22]
        modified_file.removed_lines = [16, 17, 18]
        stats_and_uncovered_lines = (
            patch_coverage_service.get_file_stats_and_uncovered_lines(
                modified_file, coverage_info
            )
        )
        assert stats_and_uncovered_lines == (
            FileStats(
                total_lines_coverable=5,
                total_lines_covered=3,
                total_adds=7,
                total_removes=3,
            ),
            ["awesome.py:4", "awesome.py:5"],
        )

    @patch("codecov_cli.services.patch_coverage.ParseXMLReport")
    def test_run_command(self, mock_parse_report, mocker):
        untracked_file = DiffFileFactory(
            path=Path("untracked.py"),
            state=FileState.untracked,
            added_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            removed_lines=[],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )
        modified_file = DiffFileFactory(
            path=Path("modified.py"),
            state=FileState.modified,
            added_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            removed_lines=[2, 3, 4],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )
        deleted_file = DiffFileFactory(
            path=Path("deleted.py"),
            state=FileState.deleted,
            added_lines=[],
            removed_lines=[],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )

        mock_get_files_in_diff = mocker.patch.object(
            PatchCoverageService,
            "get_files_in_diff",
            return_value=[modified_file, deleted_file],
        )
        mock_get_untracked_files = mocker.patch.object(
            PatchCoverageService, "get_untracked_files", return_value=[untracked_file]
        )

        mock_echo = mocker.patch.object(click, "echo")

        def mock_coverage_info_for_file(file: DiffFile):
            if file == untracked_file:
                return {
                    1: True,
                    2: True,
                    3: True,
                    6: True,
                    7: True,
                    8: False,
                    9: False,
                    10: True,
                }
            if file == modified_file:
                return {
                    1: True,
                    2: True,
                    3: True,
                    5: False,
                    6: True,
                    8: False,
                    9: False,
                    10: True,
                }

        mock_get_covered_lines_in_patch_for_diff_file = (
            mock_parse_report.return_value.get_covered_lines_in_patch_for_diff_file
        )
        mock_get_covered_lines_in_patch_for_diff_file.side_effect = (
            mock_coverage_info_for_file
        )

        service = PatchCoverageService()
        service.run_patch_coverage_command(staged=False, diff_base=None)
        mock_get_files_in_diff.assert_called_with(False, None)
        mock_get_untracked_files.assert_called()
        assert mock_get_covered_lines_in_patch_for_diff_file.call_count == 2
        mock_get_covered_lines_in_patch_for_diff_file.assert_has_calls(
            [
                call(modified_file),
                call(untracked_file),
            ]
        )
        mock_echo.assert_has_calls(
            [
                call("\n5 Uncovered lines"),
                call(
                    "modified.py:5\nmodified.py:8\nmodified.py:9\nuntracked.py:8\nuntracked.py:9"
                ),
                call("5 Uncovered lines ☝️"),
                call(f"\nPatch coverage: {(11 / 16) * 100:.3f}%"),
                call(f"Lines coverable: {16}; Lines covered: {11}"),
                call(
                    f"Adds: {18}; Removes: {3} (doesn't include lines from deleted files)"
                ),
            ]
        )

    @patch("codecov_cli.services.patch_coverage.ParseXMLReport")
    def test_run_command_no_uncovered_lines(self, mock_parse_report, mocker):
        untracked_file = DiffFileFactory(
            path=Path("untracked.py"),
            state=FileState.untracked,
            added_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            removed_lines=[],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )
        modified_file = DiffFileFactory(
            path=Path("modified.py"),
            state=FileState.modified,
            added_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            removed_lines=[2, 3, 4],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )
        deleted_file = DiffFileFactory(
            path=Path("deleted.py"),
            state=FileState.deleted,
            added_lines=[],
            removed_lines=[],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )

        mock_get_files_in_diff = mocker.patch.object(
            PatchCoverageService,
            "get_files_in_diff",
            return_value=[modified_file, deleted_file],
        )
        mock_get_untracked_files = mocker.patch.object(
            PatchCoverageService, "get_untracked_files", return_value=[untracked_file]
        )

        mock_echo = mocker.patch.object(click, "echo")

        def mock_coverage_info_for_file(file: DiffFile):
            if file == untracked_file:
                return {
                    1: True,
                    2: True,
                    3: True,
                    6: True,
                    7: True,
                    8: True,
                    9: True,
                    10: True,
                }
            if file == modified_file:
                return {
                    1: True,
                    2: True,
                    3: True,
                    5: True,
                    6: True,
                    8: True,
                    9: True,
                    10: True,
                }

        mock_get_covered_lines_in_patch_for_diff_file = (
            mock_parse_report.return_value.get_covered_lines_in_patch_for_diff_file
        )
        mock_get_covered_lines_in_patch_for_diff_file.side_effect = (
            mock_coverage_info_for_file
        )

        service = PatchCoverageService()
        service.run_patch_coverage_command(staged=False, diff_base=None)
        mock_get_files_in_diff.assert_called_with(False, None)
        mock_get_untracked_files.assert_called()
        assert mock_get_covered_lines_in_patch_for_diff_file.call_count == 2
        mock_get_covered_lines_in_patch_for_diff_file.assert_has_calls(
            [
                call(modified_file),
                call(untracked_file),
            ]
        )
        mock_echo.assert_has_calls(
            [
                call("No uncovered lines :)"),
                call(f"\nPatch coverage: {(16 / 16) * 100:.3f}%"),
                call(f"Lines coverable: {16}; Lines covered: {16}"),
                call(
                    f"Adds: {18}; Removes: {3} (doesn't include lines from deleted files)"
                ),
            ]
        )

    @patch("codecov_cli.services.patch_coverage.ParseXMLReport")
    def test_run_command_no_coverable_lines(self, mock_parse_report, mocker):
        untracked_file = DiffFileFactory(
            path=Path("untracked.py"),
            state=FileState.untracked,
            added_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            removed_lines=[],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )
        modified_file = DiffFileFactory(
            path=Path("modified.py"),
            state=FileState.modified,
            added_lines=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            removed_lines=[2, 3, 4],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )
        deleted_file = DiffFileFactory(
            path=Path("deleted.py"),
            state=FileState.deleted,
            added_lines=[],
            removed_lines=[],
            last_modified=datetime(2023, 8, 25, 13, 44, 22, 840706),
        )

        mock_get_files_in_diff = mocker.patch.object(
            PatchCoverageService,
            "get_files_in_diff",
            return_value=[modified_file, deleted_file],
        )
        mock_get_untracked_files = mocker.patch.object(
            PatchCoverageService, "get_untracked_files", return_value=[untracked_file]
        )

        mock_echo = mocker.patch.object(click, "echo")

        mock_get_covered_lines_in_patch_for_diff_file = (
            mock_parse_report.return_value.get_covered_lines_in_patch_for_diff_file
        )
        mock_get_covered_lines_in_patch_for_diff_file.return_value = {}

        service = PatchCoverageService()
        service.run_patch_coverage_command(staged=False, diff_base=None)
        mock_get_files_in_diff.assert_called_with(False, None)
        mock_get_untracked_files.assert_called()
        assert mock_get_covered_lines_in_patch_for_diff_file.call_count == 2
        mock_get_covered_lines_in_patch_for_diff_file.assert_has_calls(
            [
                call(modified_file),
                call(untracked_file),
            ]
        )
        mock_echo.assert_has_calls(
            [
                call("No uncovered lines :)"),
                call("Could not find any coverable lines in the git diff"),
            ]
        )
