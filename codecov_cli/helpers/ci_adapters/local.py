import os
import subprocess

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.git import parse_git_service

SUCCESS = 0


class LocalAdapter(CIAdapterBase):
    def detect(self) -> bool:
        s = subprocess.run(["git", "help"], capture_output=True)
        return s.returncode == SUCCESS

    def _get_branch(self):
        return os.getenv("GIT_BRANCH") or os.getenv("BRANCH_NAME")

    def _get_build_code(self):
        return None

    def _get_build_url(self):
        return None

    def _get_commit_sha(self):
        return os.getenv("GIT_COMMIT")

    def _get_slug(self):
        return None

    def _get_service(self):
        return "local"

    def _get_pull_request_number(self):
        return None

    def _get_job_code(self):
        return None

    def get_service_name(self):
        return "Local"

    def _get_git_service(self):
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
