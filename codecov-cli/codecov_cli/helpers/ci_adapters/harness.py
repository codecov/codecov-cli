import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.git import parse_slug

# https://developer.harness.io/docs/continuous-integration/troubleshoot-ci/ci-env-var/

# Uses CI_ prefixed environment variables variant if available and DRONE_ prefixed environment variables variant if not
# The DRONE variables overlap with the Drone CI Adapter as Harness CI is built on top 
class HarnessAdapter(CIAdapterBase):
    def detect(self) -> bool:
        return bool(os.getenv("HARNESS_BUILD_ID"))

    def _get_branch(self):
        return os.getenv("DRONE_COMMIT_BRANCH")

    def _get_commit_sha(self):
        return os.getenv("DRONE_COMMIT_SHA")

    def _get_pull_request_number(self):
        return os.getenv("DRONE_PULL_REQUEST")

    def _get_job_code(self):
        return None

    def _get_build_code(self):
        return os.getenv("CI_BUILD_NUMBER")

    def _get_build_url(self):
        return os.getenv("CI_BUILD_LINK")

    def _get_slug(self):
        ci_repo = os.getenv("CI_REPO")
        if ci_repo and "/" in ci_repo:
            return ci_repo
        for env_var in (
            "CI_REPO_REMOTE",
            "CI_REMOTE_URL",
            "CI_REPO_LINK",
            "DRONE_GIT_HTTP_URL",
            "DRONE_REMOTE_URL",
        ):
            if url := os.getenv(env_var):
                if slug := parse_slug(url):
                    return slug
        return None

    def _get_service(self):
        return "harness"

    def get_service_name(self):
        return "Harness"