from itertools import chain
import logging
import re
import subprocess
import typing as t
from pathlib import Path
from shutil import which

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.folder_searcher import search_files
from codecov_cli.helpers.git import parse_git_service, parse_slug
from abc import ABC, abstractmethod

logger = logging.getLogger("codecovcli")

IGNORE_DIRS = [
    "*.egg-info",
    ".DS_Store",
    ".circleci",
    ".env",
    ".envs",
    ".git",
    ".gitignore",
    ".mypy_cache",
    ".nvmrc",
    ".nyc_output",
    ".ruff_cache",
    ".venv",
    ".venvns",
    ".virtualenv",
    ".virtualenvs",
    "__pycache__",
    "bower_components",
    "build/lib/",
    "jspm_packages",
    "node_modules",
    "vendor",
    "virtualenv",
    "virtualenvs",
]

IGNORE_PATHS = [
    "*.gif",
    "*.jpeg",
    "*.jpg",
    "*.md",
    "*.png",
    "shunit2*",
]


class VersioningSystemInterface(ABC):
    def __repr__(self) -> str:
        return str(type(self))

    @abstractmethod
    def get_fallback_value(self, fallback_field: FallbackFieldEnum) -> t.Optional[str]:
        pass

    @abstractmethod
    def get_network_root(self) -> t.Optional[Path]:
        pass

    @abstractmethod
    def list_relevant_files(
        self, directory: t.Optional[Path] = None, recurse_submodules: bool = False
    ) -> t.Optional[t.List[str]]:
        pass


def get_versioning_system() -> t.Optional[VersioningSystemInterface]:
    for klass in [GitVersioningSystem, NoVersioningSystem]:
        if klass.is_available():
            logger.debug(f"versioning system found: {klass}")
            return klass()


class GitVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        if which("git") is not None:
            p = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"], capture_output=True
            )
            if p.stdout:
                return True
        return False

    def get_fallback_value(self, fallback_field: FallbackFieldEnum):
        if fallback_field == FallbackFieldEnum.commit_sha:
            # here we will get the commit SHA of the latest commit
            # that is NOT a merge commit
            p = subprocess.run(
                # List current commit parent's SHA
                ["git", "rev-parse", "HEAD^@"],
                capture_output=True,
            )
            parents_hash = p.stdout.decode().strip().splitlines()
            if len(parents_hash) == 2:
                # IFF the current commit is a merge commit it will have 2 parents
                # We return the 2nd one - The commit that came from the branch merged into ours
                return parents_hash[1]
            # At this point we know the current commit is not a merge commit
            # so we get it's SHA and return that
            p = subprocess.run(["git", "log", "-1", "--format=%H"], capture_output=True)
            if p.stdout:
                return p.stdout.decode().strip()

        if fallback_field == FallbackFieldEnum.branch:
            p = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True
            )
            if p.stdout:
                branch_name = p.stdout.decode().strip()
                # branch_name will be 'HEAD' if we are in 'detached HEAD' state
                return branch_name if branch_name != "HEAD" else None

        if fallback_field == FallbackFieldEnum.slug:
            # if there are multiple remotes, we will prioritize using the one called 'origin' if it exists, else we will use the first one in 'git remote' list

            p = subprocess.run(["git", "remote"], capture_output=True)

            if not p.stdout:
                return None

            remotes = p.stdout.decode().strip().splitlines()

            remote_name = "origin" if "origin" in remotes else remotes[0]

            p = subprocess.run(
                ["git", "ls-remote", "--get-url", remote_name], capture_output=True
            )
            if not p.stdout:
                return None

            remote_url = p.stdout.decode().strip()

            return parse_slug(remote_url)

        if fallback_field == FallbackFieldEnum.git_service:
            # if there are multiple remotes, we will prioritize using the one called 'origin' if it exists, else we will use the first one in 'git remote' list

            p = subprocess.run(["git", "remote"], capture_output=True)
            if not p.stdout:
                return None

            remotes = p.stdout.decode().strip().splitlines()
            remote_name = "origin" if "origin" in remotes else remotes[0]
            p = subprocess.run(
                ["git", "ls-remote", "--get-url", remote_name], capture_output=True
            )
            if not p.stdout:
                return None

            remote_url = p.stdout.decode().strip()
            return parse_git_service(remote_url)

        return None

    def get_network_root(self):
        p = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
        if p.stdout:
            return Path(p.stdout.decode().rstrip())
        return None

    def list_relevant_files(
        self, directory: t.Optional[Path] = None, recurse_submodules: bool = False
    ) -> t.List[str]:
        dir_to_use = directory or self.get_network_root()
        if dir_to_use is None:
            raise ValueError("Can't determine root folder")

        cmd = ["git", "-C", str(dir_to_use), "ls-files", "-z"]
        if recurse_submodules:
            cmd.append("--recurse-submodules")
        res = subprocess.run(cmd, capture_output=True)
        return res.stdout.decode().split("\0")


class NoVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def get_network_root(self):
        return Path.cwd()

    def get_fallback_value(self, fallback_field: FallbackFieldEnum):
        return None

    def list_relevant_files(
        self, directory: t.Optional[Path] = None, recurse_submodules: bool = False
    ) -> t.List[str]:
        dir_to_use = directory or self.get_network_root()
        if dir_to_use is None:
            raise ValueError("Can't determine root folder")

        files = search_files(
            dir_to_use, folders_to_ignore=[], filename_include_regex=re.compile("")
        )
        return [f.relative_to(dir_to_use).as_posix() for f in files]
