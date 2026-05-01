import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase

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
        return os.getenv("CI_REPO")

    def _get_service(self):
        return "harness"

    def get_service_name(self):
        return "Harness"