import logging
import os
import re
import subprocess

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase

logger = logging.getLogger("codecovcli")


class GithubActionsCIAdapter(CIAdapterBase):
    # https://docs.github.com/en/actions/learn-github-actions/environment-variables
    def detect(self) -> bool:
        return bool(os.getenv("GITHUB_ACTIONS"))

    def _get_commit_sha(self):
        pr = self._get_pull_request_number()
        commit = os.getenv("GITHUB_SHA")

        if not pr:
            return commit

        merge_commit_regex = r"^[a-z0-9]{40} [a-z0-9]{40}$"
        merge_commit_message = subprocess.run(
            ["git", "show", "--no-patch", "--format=%P"],
            capture_output=True,
        ).stdout

        try:
            merge_commit_message = merge_commit_message.decode("utf-8").strip()

            if re.match(merge_commit_regex, merge_commit_message) is not None:
                merge_commit = merge_commit_message.split(" ")[1]
                logger.info(f"    Fixing merge commit SHA ${commit} -> ${merge_commit}")
                commit = merge_commit
            elif merge_commit_message == "":
                logger.info(
                    "->  Issue detecting commit SHA. Please run actions/checkout with fetch-depth > 1 or set to 0"
                )
        except (AttributeError, TypeError):  # For the re.match and .decode
            logger.info(
                f"    Commit with SHA {commit} of PR {pr} is not a merge commit"
            )

        return commit

    def _get_build_url(self):
        server_url = os.getenv("GITHUB_SERVER_URL")
        slug = self._get_slug()
        build_code = self._get_build_code()

        if server_url and slug and build_code:
            return f"{server_url}/{slug}/actions/runs/{build_code}"

        return None

    def _get_build_code(self):
        return os.getenv("GITHUB_RUN_ID")

    def _get_job_code(self):
        return os.getenv("GITHUB_WORKFLOW")

    def _get_pull_request_number(self):
        if not os.getenv("GITHUB_HEAD_REF"):
            return None

        pr_ref = os.getenv("GITHUB_REF")

        if not pr_ref:
            return None

        match = re.search(r"refs/pull/(\d+)/merge", pr_ref)

        if match is None:
            return None

        pr = match.group(1)

        return pr or None

    def _get_slug(self):
        return os.getenv("GITHUB_REPOSITORY")

    def _get_branch(self):
        branch = os.getenv("GITHUB_HEAD_REF")
        if branch:
            return branch

        branch_ref = os.getenv("GITHUB_REF")

        if not branch_ref:
            return None

        match = re.search(r"refs/heads/(.*)", branch_ref)

        if match is None:
            return None

        branch = match.group(1)
        return branch or None

    def _get_service(self):
        return "github-actions"

    def get_service_name(self):
        return "GithubActions"
