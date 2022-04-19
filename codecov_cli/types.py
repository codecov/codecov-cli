import typing
import uuid
from dataclasses import dataclass
from pathlib import Path


class UploadCollectionResultFile(object):
    def get_filename(self) -> bytes:
        pass

    def get_content(self) -> bytes:
        pass


@dataclass
class UploadCollectionResult(object):
    network: typing.List[str]
    coverage_files: typing.List[UploadCollectionResultFile]


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
