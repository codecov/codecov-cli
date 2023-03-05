import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class CirrusCIAdapter(CIAdapterBase):
    # https://cirrus-ci.org/guide/writing-tasks/#environment-variables
    def detect(self) -> bool:
        return bool(os.getenv("CIRRUS_CI"))

    def _get_branch(self):
        return os.getenv("CIRRUS_BRANCH")

    def _get_build_code(self):
        return os.getenv("CIRRUS_BUILD_ID")

    def _get_build_url(self):
        return None

    def _get_commit_sha(self):
        return os.getenv("CIRRUS_CHANGE_IN_REPO")

    def _get_slug(self):
        return os.getenv("CIRRUS_REPO_FULL_NAME")

    def _get_service(self):
        return "cirrus"

    def _get_pull_request_number(self):
        return os.getenv("CIRRUS_PR")

    def _get_job_code(self):
        return os.getenv("CIRRUS_TASK_ID")

    def get_service_name(self):
        return "CirrusCI"
