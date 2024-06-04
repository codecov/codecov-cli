import pathlib
import typing

from codecov_cli.helpers.versioning_systems import VersioningSystemInterface


class NetworkFinder(object):
    def __init__(
        self,
        versioning_system: VersioningSystemInterface,
        network_filter: typing.Optional[str],
        network_prefix: typing.Optional[str],
        network_root_folder: pathlib.Path,
    ):
        self.versioning_system = versioning_system
        self.network_filter = network_filter
        self.network_prefix = network_prefix
        self.network_root_folder = network_root_folder

    def find_files(self, ignore_filters=False) -> typing.List[str]:
        files = self.versioning_system.list_relevant_files(self.network_root_folder)

        if not ignore_filters:
            if self.network_filter:
                files = [file for file in files if file.startswith(self.network_filter)]
            if self.network_prefix:
                files = [self.network_prefix + file for file in files]

        return files


def select_network_finder(
    versioning_system: VersioningSystemInterface,
    network_filter: typing.Optional[str],
    network_prefix: typing.Optional[str],
    network_root_folder: pathlib.Path,
):
    return NetworkFinder(
        versioning_system,
        network_filter,
        network_prefix,
        network_root_folder,
    )
