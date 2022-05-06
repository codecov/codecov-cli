import pathlib
import typing
from dataclasses import dataclass


class UploadCollectionResultFile(object):
    def __init__(self, path: pathlib.Path):
        self.path = path

    def get_filename(self) -> bytes:
        pass

    def get_content(self) -> bytes:
        pass


@dataclass
class UploadCollectionResult(object):
    __slots__ = ["network", "coverage_files", "file_fixes"]
    network: typing.List[str]
    coverage_files: typing.List[UploadCollectionResultFile]
    file_fixes: typing.List[typing.Dict]


class PreparationPluginInterface(object):
    def run_preparation(self) -> None:
        pass
