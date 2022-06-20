import pathlib
import typing

from codecov_cli.helpers.versioning_systems import VersioningSystemInterface


class NetworkFinder(object):
    def __init__(self, versioning_system: VersioningSystemInterface):
        self.versioning_system = versioning_system

    def find_files(
        self,
        network_root: typing.Optional[pathlib.Path] = None,
        network_filter=None,
        network_adjuster=None,
    ) -> typing.List[str]:
        return self.versioning_system.list_relevant_files(network_root)


def select_network_finder(versioning_system: VersioningSystemInterface):
    return NetworkFinder(versioning_system)
