import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class BitbucketAdapter(CIAdapterBase):
    # https://support.atlassian.com/bitbucket-cloud/docs/variables-and-secrets/

    def detect(self) -> bool:
        return bool(os.getenv("CI")) and bool(os.getenv("BITBUCKET_BUILD_NUMBER"))

    def _get_commit_sha(self):
        commit = os.getenv("BITBUCKET_COMMIT")

        if not commit or len(commit) == 12:
            return None

        return commit

    def _get_build_url(self):
        return None

    def _get_build_code(self):
        return os.getenv("BITBUCKET_BUILD_NUMBER")

    def _get_job_code(self):
        return os.getenv("BITBUCKET_BUILD_NUMBER")

    def _get_pull_request_number(self):
        return os.getenv("BITBUCKET_PR_ID")

    def _get_slug(self):
        return os.getenv("BITBUCKET_REPO_FULL_NAME")

    def _get_branch(self):
        return os.getenv("BITBUCKET_BRANCH")

    def _get_service(self):
        return "bitbucket"

    def get_service_name(self):
        return "Bitbucket"
