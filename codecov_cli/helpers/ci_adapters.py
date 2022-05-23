import os
import re
import subprocess
import typing
from abc import ABC

from codecov_cli.fallbacks import FallbackFieldEnum


class CIAdapterBase(ABC):
    def __init__(self):
        # If a fallbacker has extra fields, they should be added to this dictionary in the fallbacker's constructor.
        self.fallback_to_method = {
            FallbackFieldEnum.branch: self._get_branch,
            FallbackFieldEnum.build_code: self._get_build_code,
            FallbackFieldEnum.build_url: self._get_build_url,
            FallbackFieldEnum.commit_sha: self._get_commit_sha,
            FallbackFieldEnum.slug: self._get_slug,
            FallbackFieldEnum.service: self._get_service,
            FallbackFieldEnum.pull_request_number: self._get_pull_request_number,
            FallbackFieldEnum.job_code: self._get_job_code,
        }

    def get_fallback_value(
        self, fallback_field: FallbackFieldEnum
    ) -> typing.Optional[str]:

        if not fallback_field in self.fallback_to_method:
            raise ValueError("The provided fallback_field is not valid")

        return self.fallback_to_method[fallback_field]()


class CircleCICIAdapter(CIAdapterBase):
    # https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables

    def _get_commit_sha(self):
        return os.getenv("CIRCLE_SHA1")

    def _get_build_url(self):
        return os.getenv("CIRCLE_BUILD_URL")

    def _get_build_code(self):
        return os.getenv("CIRCLE_BUILD_NUM")

    def _get_job_code(self):
        return os.getenv("CIRCLE_NODE_INDEX")

    def _get_pull_request_number(self):
        return os.getenv("CIRCLE_PR_NUMBER")

    def _get_slug(self):
        project_username = os.getenv("CIRCLE_PROJECT_USERNAME")
        project_repo_name = os.getenv("CIRCLE_PROJECT_REPONAME")

        if project_repo_name and project_username:
            return f"{project_username}/{project_repo_name}"

        repo_url = os.getenv("CIRCLE_REPOSITORY_URL")

        if repo_url:
            return repo_url.split(":")[1].split(".git")[0]

        return None

    def _get_branch(self):
        return os.getenv("CIRCLE_BRANCH")

    def _get_service(self):
        return "circleci"


class GithubActionsCIAdapter(CIAdapterBase):
    # https://docs.github.com/en/actions/learn-github-actions/environment-variables

    def _get_commit_sha(self):
        print("Calling get pr num")
        pr = self._get_pull_request_number()
        print("after get pr num")
        commit = os.getenv("GITHUB_SHA")

        if not pr:
            print("not pr, returning this commit")
            return commit




        completed_subprocess = subprocess.run(
            ["pwd"], capture_output=True
        )
        print(completed_subprocess.stdout)
        completed_subprocess = subprocess.run(
            ["which", "codecov"], capture_output=True
        )
        print(completed_subprocess.stdout)
        
        completed_subprocess = subprocess.run(
            ["git", "status"], capture_output=True
        )
        print(completed_subprocess.stdout)
        
        completed_subprocess = subprocess.run(
            ["git", "rev-parse", "HEAD^4"], capture_output=True
        )
        
        print(completed_subprocess.returncode)
        print(completed_subprocess.stdout)
        print(completed_subprocess.stderr)
        parents_hash = completed_subprocess.stdout.decode().strip().splitlines()
        print(f"parent hash {parents_hash}")
        
        if len(parents_hash) == 2:
            h = parents_hash[1]
            print(f"returning parent commit {h}")
            return h


        print("just retruning commit at the end")
        return commit

    def _get_build_url(self):
        server_url = os.getenv("GITHUB_SERVER_URL")
        slug = self._get_slug()
        build_code = self._get_build_code()

        if all(value for value in [server_url, slug, build_code]):
            return f"{server_url}/{slug}/actions/runs/{build_code}"

        return None

    def _get_build_code(self):
        return os.getenv("GITHUB_RUN_ID")

    def _get_job_code(self):
        return os.getenv("GITHUB_WORKFLOW")

    def _get_pull_request_number(self):
        if not os.getenv("GITHUB_HEAD_REF"):
            print("GITHUB_HEAD_REF is fine")
            return None

        pr_ref = os.getenv("GITHUB_REF")
        print(pr_ref)
        if not pr_ref:
            print("GITHUB_REF is fine")
            return None

        match = re.search(r"refs/pull/(\d+)/merge", pr_ref)

        if match is None:
            print("doesn't match")
            return None

        pr = match.group(1)
        print(f"pr number is {pr}")
        return pr or None

    def _get_slug(self):
        return os.getenv("GITHUB_REPOSITORY")

    def _get_branch(self):
        if branch := os.getenv("GITHUB_HEAD_REF"):
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


def get_ci_adapter(provider_name):
    if provider_name == "circleci":
        return CircleCICIAdapter()
    if provider_name == "githubactions":
        return GithubActionsCIAdapter()
    return None
