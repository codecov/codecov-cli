import pathlib
import typing as t
from dataclasses import dataclass

import click

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.versioning_systems import VersioningSystemInterface


class ContextObject(t.TypedDict):
    ci_adapter: t.Optional[CIAdapterBase]
    versioning_system: t.Optional[VersioningSystemInterface]
    codecov_yaml: t.Optional[dict]
    enterprise_url: t.Optional[str]


class CommandContext(click.Context):
    obj: ContextObject


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
    fixed_lines_without_reason: t.Set[int]
    fixed_lines_with_reason: t.Optional[t.Set[t.Tuple[int, str]]]
    eof: t.Optional[int]


@dataclass
class UploadCollectionResult(object):
    __slots__ = ["network", "files", "file_fixes"]
    network: t.List[str]
    files: t.List[UploadCollectionResultFile]
    file_fixes: t.List[UploadCollectionResultFileFixer]


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
    params: t.Dict
    description: str


@dataclass
class RequestResult(object):
    __slots__ = ("error", "warnings", "status_code", "text")
    error: t.Optional[RequestError]
    warnings: t.List[RequestResultWarning]
    status_code: int
    text: str
