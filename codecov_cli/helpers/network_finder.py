import pathlib

from codecov_cli.helpers.versioning_systems import VersioningSystemInterface


class NetworkFinder(object):
    def list_network_files(
        self, network_root: pathlib.Path, network_filter, network_adjuster
    ):
        pass


def select_network_finder(versioning_system: VersioningSystemInterface):
    return NetworkFinder()
