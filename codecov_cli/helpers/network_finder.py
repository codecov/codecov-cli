import pathlib

from codecov_cli.helpers.versioning_systems import VersioningSystemInterface


class NetworkFinder(object):
    def find_files(
        self,
        network_root: pathlib.Path = None,
        network_filter=None,
        network_adjuster=None,
    ):
        # TODO: Implement
        return []


def select_network_finder(versioning_system: VersioningSystemInterface):
    return NetworkFinder()
