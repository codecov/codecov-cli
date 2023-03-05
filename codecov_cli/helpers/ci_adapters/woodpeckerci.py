import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class WoodpeckerCIAdapter(CIAdapterBase):
    # https://woodpecker-ci.org/docs/usage/environment
    def detect(self) -> bool:
        return os.getenv("CI") == "woodpecker"

    def _get_branch(self):
        return os.getenv("CI_COMMIT_SOURCE_BRANCH") or os.getenv("CI_COMMIT_BRANCH")

    def _get_build_code(self):
        return os.getenv("CI_BUILD_NUMBER")

    def _get_build_url(self):
        return os.getenv("CI_BUILD_LINK")

    def _get_commit_sha(self):
        return os.getenv("CI_COMMIT_SHA")

    def _get_slug(self):
        return os.getenv("CI_REPO")

    def _get_service(self):
        return "woodpecker"

    def _get_pull_request_number(self):
        return os.getenv("CI_COMMIT_PULL_REQUEST")

    def _get_job_code(self):
        return os.getenv("CI_JOB_NUMBER")

    def get_service_name(self):
        return "Woodpecker"
