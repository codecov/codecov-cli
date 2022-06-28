import pathlib
import typing
from dataclasses import dataclass


class UploadCollectionResultFile(object):
    def get_filename(self) -> bytes:
        pass

    def get_content(self) -> bytes:
        pass


@dataclass
class UploadCollectionResultFileFixer(object):
    __slots__ = ["path", "fixed_lines_without_reason", "fixed_lines_with_reason", "eof"]
    path: pathlib.Path
    fixed_lines_without_reason: typing.Set[int]
    fixed_lines_with_reason: typing.Optional[typing.Set[typing.Tuple[int, str]]]
    eof: typing.Optional[int]


@dataclass
class UploadCollectionResult(object):
    __slots__ = ["network", "coverage_files", "file_fixes"]
    network: typing.List[str]
    coverage_files: typing.List[UploadCollectionResultFile]
    file_fixes: typing.List[UploadCollectionResultFileFixer]


class PreparationPluginInterface(object):
    def run_preparation(self) -> None:
        pass
