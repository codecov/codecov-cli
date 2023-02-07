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

    def __repr__(self) -> str:
        return str(self.path)

    def __eq__(self, other):
        if not isinstance(other, UploadCollectionResultFile):
            return False

        return self.path == other.path

    def __hash__(self) -> int:
        return hash(str(self.path))


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


@dataclass
class RequestResultWarning(object):
    __slots__ = ("message",)
    message: str


@dataclass
class RequestError(object):
    __slots__ = ("code", "params", "description")
    code: str
    params: typing.Dict
    description: str


@dataclass
class RequestResult(object):
    __slots__ = ("error", "warnings", "status_code", "text")
    error: typing.Optional[RequestError]
    warnings: typing.List[RequestResultWarning]
    status_code: int
    text: str
