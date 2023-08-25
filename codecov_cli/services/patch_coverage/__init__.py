import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from codecov_cli.services.patch_coverage.parse_coverage_report import ParseXMLReport
from codecov_cli.services.patch_coverage.parse_git_diff import get_files_in_diff
from codecov_cli.services.patch_coverage.types import DiffFile, FileState, FileStats


class PatchCoverageService(object):
    def __init__(self) -> None:
        pass

    def get_file_stats_and_uncovered_lines_untracked_file(
        self, file: DiffFile, coverage_info: Dict[int, bool]
    ):
        total_lines_coverable = 0
        total_lines_covered = 0
        uncovered_lines = []
        for line_number in coverage_info.keys():
            total_lines_coverable += 1
            total_lines_covered += int(coverage_info[line_number])
            if coverage_info[line_number] is False:
                uncovered_lines.append(f"{file.path}:{line_number}")
        return (
            FileStats(
                total_lines_coverable=total_lines_coverable,
                total_lines_covered=total_lines_covered,
                total_adds=total_lines_coverable,
                total_removes=0,
            ),
            uncovered_lines,
        )

    def get_file_stats_and_uncovered_lines(
        self, file: DiffFile, coverage_info: Dict[int, bool]
    ) -> Tuple[FileStats, List[str]]:
        if file.state == FileState.untracked:
            return self.get_file_stats_and_uncovered_lines_untracked_file(
                file, coverage_info
            )
        total_lines_coverable = 0
        total_lines_covered = 0
        uncovered_lines = []
        for line_number in file.added_lines:
            total_lines_coverable += int(line_number in coverage_info)
            total_lines_covered += int(coverage_info.get(line_number, False))
            if line_number in coverage_info and coverage_info[line_number] is False:
                uncovered_lines.append(f"{file.path}:{line_number}")

        return (
            FileStats(
                total_lines_coverable=total_lines_coverable,
                total_lines_covered=total_lines_covered,
                total_adds=len(file.added_lines),
                total_removes=len(file.removed_lines),
            ),
            uncovered_lines,
        )

    def run_patch_coverage_command(self, staged: bool, diff_base: str):
        parse_xml_report = ParseXMLReport()
        parse_xml_report.load_reports()
        files_in_diff = self.get_files_in_diff(staged, diff_base)
        untracked_files = self.get_untracked_files()

        total_lines_coverable = 0
        total_lines_covered = 0
        total_adds = 0
        total_removes = 0
        all_uncovered_lines = []
        for file in files_in_diff + untracked_files:
            if file.state in [
                FileState.modified,
                FileState.untracked,
                FileState.created,
            ]:
                coverage_info = (
                    parse_xml_report.get_covered_lines_in_patch_for_diff_file(file)
                )
                file_stats, uncovered_lines = self.get_file_stats_and_uncovered_lines(
                    file, coverage_info
                )
                total_lines_coverable += file_stats.total_lines_coverable
                total_lines_covered += file_stats.total_lines_covered
                total_adds += file_stats.total_adds
                total_removes += file_stats.total_removes
                all_uncovered_lines.extend(uncovered_lines)

        if all_uncovered_lines:
            print(f"\n{len(all_uncovered_lines)} Uncovered lines")
            print("\n".join(all_uncovered_lines))
            print(f"{len(all_uncovered_lines)} Uncovered lines ☝️")
        else:
            print("No uncovered lines :)")

        if total_lines_coverable:
            print(
                f"\nPatch coverage: {(total_lines_covered / total_lines_coverable) * 100:.3f}%"
            )
            print(
                f"Lines coverable: {total_lines_coverable}; Lines covered: {total_lines_covered}"
            )
            print(
                f"Adds: {total_adds}; Removes: {total_removes} (doesn't include lines from deleted files)"
            )
        else:
            print("Could not find any coverable lines in the git diff")

    def _execute_git(self, command_args: List[str]):
        # TODO: Handle errors
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

    def get_files_in_diff(
        self, staged: bool, diff_base: Optional[str] = None
    ) -> List[DiffFile]:
        cmd_options = ["diff"]
        if staged:
            cmd_options.append("--staged")
        if diff_base:
            cmd_options.append(diff_base)
        raw_diff = self._execute_git(cmd_options).splitlines()
        return get_files_in_diff(raw_diff)
