import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class BitriseCIAdapter(CIAdapterBase):
    def _get_commit_sha(self):
        return os.getenv("GIT_CLONE_COMMIT_HASH")

    def _get_build_url(self):
        return os.getenv("BITRISE_BUILD_URL")

    def _get_build_code(self):
        return os.getenv("BITRISE_BUILD_NUMBER")

    def _get_job_code(self):
        return None

    def _get_pull_request_number(self):
        return os.getenv("BITRISE_PULL_REQUEST")

    def _get_slug(self):
        return None

    def _get_branch(self):
        return os.getenv("BITRISE_GIT_BRANCH")

    def _get_service(self):
        return "bitrise"
