import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class TravisCIAdapter(CIAdapterBase):
    # https://docs.travis-ci.com/user/environment-variables/#default-environment-variables
    def detect(self) -> bool:
        return (
            bool(os.getenv("CI"))
            and bool(os.getenv("TRAVIS"))
            and not bool(os.getenv("SHIPPABLE"))
        )

    def _get_commit_sha(self):
        return os.getenv("TRAVIS_PULL_REQUEST_SHA") or os.getenv("TRAVIS_COMMIT")

    def _get_build_url(self):
        return os.getenv("TRAVIS_BUILD_WEB_URL")

    def _get_build_code(self):
        return os.getenv("TRAVIS_JOB_NUMBER")

    def _get_job_code(self):
        return os.getenv("TRAVIS_JOB_ID")

    def _get_pull_request_number(self):
        # The pull request number if the current job is a pull request, “false” if it’s not a pull request.
        pr_num = os.getenv("TRAVIS_PULL_REQUEST")
        return pr_num if pr_num != "false" else None

    def _get_slug(self):
        return os.getenv("TRAVIS_REPO_SLUG")

    def _get_branch(self):
        if os.getenv("TRAVIS_BRANCH") != os.getenv("TRAVIS_TAG"):
            return os.getenv("TRAVIS_PULL_REQUEST_BRANCH") or os.getenv("TRAVIS_BRANCH")
        return None

    def _get_service(self):
        return "travis"

    def get_service_name(self):
        return "Travis"
