from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from codecov_cli.services.patch_coverage import PatchCoverageService
from codecov_cli.services.patch_coverage.types import DiffFile, FileState, FileStats


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
        files_in_diff = patch_coverage_service.get_files_in_diff()
        assert files_in_diff == ["DiffFile_1", "DiffFIle_2"]
        mock_subprocess.run.assert_called_with(["git", "diff"], capture_output=True)
        mock_get_files_in_diff.assert_called_with(
            ["diff line 1", "diff line 2", "diff line 3"]
        )

    @patch("codecov_cli.services.patch_coverage.subprocess")
    def test_get_untracked_files(self, mock_subprocess):
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
