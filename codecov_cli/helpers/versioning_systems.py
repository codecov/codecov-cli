import subprocess
import typing
from pathlib import Path

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.git import parse_slug


class VersioningSystemInterface(object):
    def get_fallback_value(
        self, fallback_field: FallbackFieldEnum
    ) -> typing.Optional[str]:
        pass

    def get_network_root(self) -> typing.Optional[Path]:
        pass

    def list_relevant_files(
        self, directory: typing.Optional[Path] = None
    ) -> typing.List[str]:
        pass


def get_versioning_system() -> VersioningSystemInterface:
    for klass in [GitVersioningSystem, NoVersioningSystem]:
        if klass.is_available():
            return klass()


class GitVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def get_fallback_value(self, fallback_field: FallbackFieldEnum):
        if fallback_field == FallbackFieldEnum.commit_sha:
            p = subprocess.run(["git", "log", "-1", "--format=%H"], capture_output=True)
            if p.stdout:
                return p.stdout.decode().rstrip()

        return None

    def get_network_root(self):
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
        if p.stdout:
            return Path(p.stdout.decode().rstrip())
        return None

    def list_relevant_files(
        self, root_folder: typing.Optional[Path] = None
    ) -> typing.List[str]:
        dir_to_use = root_folder or self.get_network_root()
        if dir_to_use is None:
            raise ValueError("Can't determine root folder")

        res = subprocess.run(
            ["git", "-C", str(dir_to_use), "ls-files"], capture_output=True
        )

        adjust_file_name = (
            lambda filename: filename[1:-1]
            if filename.startswith('"') and filename.endswith('"')
            else filename
        )

        return [
            adjust_file_name(filename)
            for filename in res.stdout.decode("unicode_escape").strip().split()
        ]


class NoVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def get_network_root(self):
        return Path.cwd()
