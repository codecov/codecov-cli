import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class CircleCICIAdapter(CIAdapterBase):
    # https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables
    def detect(self) -> bool:
        return bool(os.getenv("CI")) and bool(os.getenv("CIRCLECI"))

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

    def get_service_name(self):
        return "CircleCI"
