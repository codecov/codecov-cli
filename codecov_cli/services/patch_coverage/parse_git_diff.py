""" Helper functions to parse a git diff
    Git diff is obtained via the `git diff` command.
    Files that are UNTRACKED are not part of the diff.
"""
import re
from pathlib import Path
from typing import List, Tuple

from codecov_cli.services.patch_coverage.types import DiffFile, FileState

# TODO: Handle renamed files
# TODO: Test file with removals only


def get_files_in_diff(diff_lines: List[str]) -> List[DiffFile]:
    diff_files: List[DiffFile] = []
    file_start_points = list(
        map(
            lambda pair: pair[0],
            filter(lambda pair: pair[1].startswith("diff"), enumerate(diff_lines)),
        )
    )
    # Add the length of diff_lines as the ending point of the last file
    file_start_points.append(len(diff_lines))
    for idx in range(1, len(file_start_points)):
        start_point = file_start_points[idx - 1]
        end_point = file_start_points[idx]
        file_diff_lines = diff_lines[start_point:end_point]
        diff_file = parse_diff_file(file_diff_lines)
        diff_files.append(diff_file)
    return diff_files


def parse_diff_file(raw_file_diff: List[str]) -> DiffFile:
    diff_file = DiffFile()
    idx = 0
    while idx < len(raw_file_diff):
        line = raw_file_diff[idx]
        if line.startswith("diff"):
            diff_file.path = get_file_path(line)
        elif line.startswith("---") and raw_file_diff[idx + 1].startswith("+++"):
            # This file was modified
            diff_file.state = FileState.modified
            idx += 1
        elif line.startswith("@@"):
            (
                start_line_adds,
                start_line_removes,
                max_context_size,
            ) = parse_diff_chunk_header(line)
            diff_chunk = raw_file_diff[idx + 1 : idx + max_context_size + 1]
            lines_added, lines_removed = get_lines_added_and_removed(
                start_line_adds, start_line_removes, diff_chunk
            )
            diff_file.added_lines.extend(lines_added)
            diff_file.removed_lines.extend(lines_removed)
            idx += max_context_size
        elif line.startswith("deleted"):
            diff_file.state = FileState.deleted
        elif line.startswith("new file mode"):
            diff_file.state = FileState.created
            # Skip the lines
            # "index 0000000..5e9b371",
            # "--- /dev/null",
            # "+++ b/path/to/file
            idx += 3
        idx += 1
    return diff_file


def get_file_path(diff_header: str) -> Path:
    line_parts = diff_header.split(" ")
    uncommited_changes_path = line_parts[3]
    return Path(uncommited_changes_path.replace("b/", ""))


def parse_diff_chunk_header(chunk_header: str) -> Tuple[int, int, int]:
    header_regex = r"@@ -(\d+,\d+) \+(\d+,\d+) @@"
    match = re.match(header_regex, chunk_header)
    lines_in_base = match.groups()[0]
    lines_in_head = match.groups()[1]
    start_line_removes, removes_context_size = lines_in_base.split(",")
    start_line_adds, adds_context_size = lines_in_head.split(",")
    return (
        int(start_line_adds),
        int(start_line_removes),
        max(int(removes_context_size), int(adds_context_size)),
    )


def get_lines_added_and_removed(
    start_line_adds, start_line_removes, lines
) -> Tuple[List[int], List[int]]:
    lines_added = []
    lines_removed = []
    idx_add = 0
    idx_remove = 0
    for line in lines:
        if line[0] == "+":
            lines_added.append(idx_add + start_line_adds)
            idx_add += 1
        elif line[0] == "-":
            lines_removed.append(idx_remove + start_line_removes)
            idx_remove += 1
        else:
            idx_add += 1
            idx_remove += 1
    return (lines_added, lines_removed)
