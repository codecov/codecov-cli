from pathlib import Path
import subprocess
from typing import List

from codecov_cli.services.patch_coverage.parse_git_diff import get_files_in_diff
from codecov_cli.services.patch_coverage.types import DiffFile, FileState


class PatchCoverageService(object):
    def __init__(self) -> None:
        pass

    def run_patch_coverage_command(self):
        files_in_diff = self.get_files_in_diff()
        untracked_files = self.get_untracked_files()
        for file in (files_in_diff + untracked_files):
            print(f"File {file.path} - {file.state}")
            if file.state == FileState.modified:
                print(f"Added lines: {file.added_lines}")
                print(f"Removed lines: {file.removed_lines}")
            print("")

    def _execute_git(self, command_args):
        command = ["git"] + command_args
        completed_process = subprocess.run(command, capture_output=True)
        return completed_process.stdout.decode()

    def get_untracked_files(self) -> List[DiffFile]:
        untracked_files = self._execute_git(
            ["ls-files", "-o", "--exclude-standard"]
        ).splitlines()
        diff_files = []
        for file in untracked_files:
            diff_file = DiffFile()
            diff_file.path = Path(file)
            diff_file.state = FileState.untracked
            diff_files.append(diff_file)
        return diff_files

    def get_files_in_diff(self) -> List[DiffFile]:
        raw_diff = self._execute_git(["diff"]).splitlines()
        return get_files_in_diff(raw_diff)
