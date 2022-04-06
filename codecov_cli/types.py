import typing
import uuid
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class UploadCollectionResultFile(object):
    def get_filename(self) -> bytes:
        pass

    def get_content(self) -> bytes:
        pass


@dataclass
class UploadCollectionResult(object):
    network: typing.List[str]
    coverage_files: typing.List[UploadCollectionResultFile]
    token: uuid.UUID
    commit_sha: str
    env_vars_clargs: typing.Dict[str, str]
    toggled_features: frozenset[str]
    network_prefix: typing.Optional[str]
    network_filter: typing.Optional[str]


class PreparationPluginInterface(object):
    def run_preparation(self) -> None:
        pass


class CoverageFileFinderInterface(object):
    def find_coverage_files(self) -> typing.List[UploadCollectionResultFile]:
        pass


class NetworkFinderInterface(object):
    def __init__(
        self, network_root_folder: Path, patterns_to_search, patterns_to_exclude
    ):
        pass

    def find_files(self) -> typing.List[str]:
        pass


class Feature(str, Enum):
    GCOV = "gcov"
    COVERAGEPY = "coveragepy"
    FIX = "fix"
    SEARCH = "search"
    XCODE = "xcode"
    NETWORK = "network"
    GCOVOUT = "gcovout"
    HTML = "html"
    RECURSESUBS = "recursesubs"
    YAML = "yaml"
