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
        # DRONE_REPO is the canonical org/repo slug on Harness CI (Drone-compatible).
        # CI_REPO is often equivalent but some setups only set the repo name; then use
        # DRONE_REPO_NAMESPACE + DRONE_REPO_NAME (or short CI_REPO as the name part).
        if drone_repo := os.getenv("DRONE_REPO"):
            return drone_repo
        ci_repo = os.getenv("CI_REPO")
        if ci_repo and "/" in ci_repo:
            return ci_repo
        namespace = os.getenv("DRONE_REPO_NAMESPACE") or os.getenv("CI_REPO_NAMESPACE")
        name = os.getenv("DRONE_REPO_NAME") or (
            ci_repo if ci_repo and "/" not in ci_repo else None
        )
        if namespace and name:
            return f"{namespace}/{name}"
        # Many Harness builds omit CI_REPO / *_NAMESPACE but still set clone/remotes:
        # https://developer.harness.io/docs/continuous-integration/troubleshoot-ci/ci-env-var/
        for env_var in (
            "DRONE_GIT_HTTP_URL",
            "CI_REPO_REMOTE",
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