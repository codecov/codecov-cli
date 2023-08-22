from enum import Enum
from pathlib import Path
from typing import List


class FileState(Enum):
    created = "C"
    modified = "M"
    deleted = "D"
    untracked = "U"


class DiffFile(object):
    added_lines: List[int]
    removed_lines: List[int]
    state: FileState
    path: Path

    def __init__(self) -> None:
        self.added_lines = []
        self.removed_lines = []
        self.state = None
        self.path = None
