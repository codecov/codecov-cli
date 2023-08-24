import xml.etree.ElementTree as ET
from enum import Enum
from pathlib import Path
from typing import Dict, List, NamedTuple


class FileState(Enum):
    created = "CREATED"
    modified = "MODIFIED"
    deleted = "DELETED"
    untracked = "UNTRACKED"


FileStats = NamedTuple(
    "FileStats",
    total_lines_coverable=int,
    total_lines_covered=int,
    total_adds=int,
    total_removes=int,
)

ReportAndTree = NamedTuple(
    "ReportAndTree", report=Path, tree=ET.Element, file_map=Dict[str, ET.Element]
)


class DiffFile(object):
    added_lines: List[int]
    added_lines_covered: List[int]
    removed_lines: List[int]
    state: FileState
    path: Path

    def __init__(self) -> None:
        self.added_lines = []
        self.added_lines_covered = []
        self.removed_lines = []
        self.state = None
        self.path = None
