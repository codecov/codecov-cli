import pathlib
import typing
from dataclasses import dataclass


class UploadCollectionResultFile(object):
    def __init__(self, path: pathlib.Path):
        self.path = path

    def get_filename(self) -> bytes:
        return bytes(self.path)

    def get_content(self) -> bytes:
        with open(self.path, "rb") as f:
            return f.read()

    def __eq__(self, other):
        if not isinstance(other, UploadCollectionResultFile):
            return False

        return self.path == other.path

    def __hash__(self) -> int:
        return hash(str(self.path))


@dataclass
class UploadCollectionResult(object):
    __slots__ = ["network", "coverage_files", "file_fixes"]
    network: typing.List[str]
    coverage_files: typing.List[UploadCollectionResultFile]
    file_fixes: typing.List[typing.Dict]


class PreparationPluginInterface(object):
    def run_preparation(self) -> None:
        pass
