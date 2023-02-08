import logging
import subprocess
import typing
from pathlib import Path

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.git import parse_git_service, parse_slug

logger = logging.getLogger("codecovcli")


class VersioningSystemInterface(object):
    def __repr__(self) -> str:
        return str(type(self))

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
            logger.debug(f"versioning system found: {klass}")
            return klass()


class GitVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def get_fallback_value(self, fallback_field: FallbackFieldEnum):
        if fallback_field == FallbackFieldEnum.commit_sha:
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
            # if there are multiple remotes, we will prioritize using the one called 'origin' if it exsits, else we will use the first one in 'git remote' list

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
            # if there are multiple remotes, we will prioritize using the one called 'origin' if it exsits, else we will use the first one in 'git remote' list

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
        self, root_folder: typing.Optional[Path] = None
    ) -> typing.List[str]:
        dir_to_use = root_folder or self.get_network_root()
        if dir_to_use is None:
            raise ValueError("Can't determine root folder")

        res = subprocess.run(
            ["git", "-C", str(dir_to_use), "ls-files"], capture_output=True
        )

        return [
            filename[1:-1]
            if filename.startswith('"') and filename.endswith('"')
            else filename
            for filename in res.stdout.decode("unicode_escape").strip().split()
        ]


class NoVersioningSystem(VersioningSystemInterface):
    @classmethod
    def is_available(cls):
        return True

    def get_network_root(self):
        return Path.cwd()
