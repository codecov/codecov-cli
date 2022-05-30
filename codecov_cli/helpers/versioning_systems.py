import subprocess
import typing

from pathlib import Path

from codecov_cli.fallbacks import FallbackFieldEnum


class VersioningSystemInterface(object):
    def get_fallback_value(self, fallback_field: FallbackFieldEnum) -> typing.Optional[str]:
        pass
    
    def get_network_root(self) -> typing.Optional[Path]:
        pass

    def list_relevant_files(self, directory: typing.Optional[Path] = None) -> typing.List[str]:
        pass

def get_versioning_system() -> VersioningSystemInterface:
    for klass in [GitVersioningSystem, NoVersioningSystem]:
        if klass.is_available():
            return klass()


class GitVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def __init__(self, lookup_directory: typing.Optional[Path] = None):
        self.lookup_directory = lookup_directory or self.get_network_root()
    
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

    def list_relevant_files(self, directory: typing.Optional[Path] = None):
        dir_to_use = directory or self.lookup_directory
        
        if dir_to_use is None:
            raise ValueError("Couldn't determine lookup directory")
        
        res = subprocess.run(
            ["git", "-C", str(dir_to_use), "ls-files"], capture_output=True
        )
        return res.stdout.decode().split()


class NoVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def get_network_root(self):
        return Path.cwd()
