from datetime import datetime
from pathlib import Path
from typing import List

from codecov_cli.services.patch_coverage.types import DiffFile, FileState


def DiffFileFactory(
    added_lines: List[int],
    removed_lines: List[int],
    state: FileState,
    path: Path,
    last_modified: datetime,
) -> DiffFile:
    obj = DiffFile()
    obj.added_lines = added_lines
    obj.removed_lines = removed_lines
    obj.state = state
    obj.path = path
    obj.last_modified = last_modified
    return obj
