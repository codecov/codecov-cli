import typing

from codecov_cli.helpers.coverage_file_finder import CoverageFileFinder
from codecov_cli.helpers.network_finder import NetworkFinder
from codecov_cli.types import PreparationPluginInterface, UploadCollectionResult


class UploadCollector(object):
    def __init__(
        self,
        preparation_plugins: typing.List[PreparationPluginInterface],
        network_finder: NetworkFinder,
        coverage_file_finder: CoverageFileFinder,
    ):
        self.preparation_plugins = preparation_plugins
        self.network_finder = network_finder
        self.coverage_file_finder = coverage_file_finder

    def _produce_file_fixes_for_network(self, network) -> typing.List[typing.Dict]:
        return []

    def generate_upload_data(self):
        for prep in self.preparation_plugins:
            prep.run_preparation(self)
        network = self.network_finder.find_files()
        coverage_files = self.coverage_file_finder.find_coverage_files()
        return UploadCollectionResult(
            network=network,
            coverage_files=coverage_files,
            file_fixes=self._produce_file_fixes_for_network(network),
        )
