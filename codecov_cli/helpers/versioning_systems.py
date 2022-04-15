import subprocess
from pathlib import Path

from codecov_cli.fallbacks import FallbackFieldEnum


class VersioningSystemInterface(object):
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

    def list_relevant_files(self):
        res = subprocess.run(
            ["git", "-C", str(self.folder_name), "ls-files"], capture_output=True
        )
        return res.stdout.decode().split()


class NoVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def get_network_root(self):
        return Path.cwd()
