import typing

from codecov_cli.types import (
    CoverageFileFinderInterface,
    NetworkFinderInterface,
    PreparationPluginInterface,
    UploadCollectionResult,
)


class UploadCollector(object):
    def __init__(
        self,
        preparation_plugins: typing.List[PreparationPluginInterface],
        network_finder: NetworkFinderInterface,
        coverage_file_finder: CoverageFileFinderInterface,
    ):
        self.preparation_plugins = preparation_plugins
        self.network_finder = network_finder
        self.coverage_file_finder = coverage_file_finder

    def generate_upload_data(self):
        for prep in self.preparation_plugins:
            prep.run_preparation(self)
        network = self.network_finder.find_files()
        coverage_files = self.coverage_file_finder.find_coverage_files()
        return UploadCollectionResult(network=network, coverage_files=coverage_files)
