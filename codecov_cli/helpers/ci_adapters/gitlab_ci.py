import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.git import parse_slug


class GitlabCIAdapter(CIAdapterBase):
    # https://docs.gitlab.com/ee/ci/variables/predefined_variables.html
    def detect(self) -> bool:
        return bool(os.getenv("GITLAB_CI"))

    def _get_commit_sha(self):
        return (
            os.getenv("CI_MERGE_REQUEST_SOURCE_BRANCH_SHA")
            or os.getenv("CI_BUILD_REF")
            or os.getenv("CI_COMMIT_SHA")
        )

    def _get_build_url(self):
        return os.getenv("CI_JOB_URL")

    def _get_build_code(self):
        return os.getenv("CI_BUILD_ID") or os.getenv("CI_JOB_ID")

    def _get_job_code(self):
        return os.getenv("CI_JOB_ID")

    def _get_pull_request_number(self):
        return os.getenv("CI_MERGE_REQUEST_IID")

    def _get_slug(self):
        slug = os.getenv("CI_PROJECT_PATH")
        if slug:
            return slug

        owner = os.getenv("CI_PROJECT_NAMESPACE")
        project_name = os.getenv("CI_PROJECT_NAME")

        if owner and project_name:
            return f"{owner}/{project_name}"

        remote_address = os.getenv("CI_BUILD_REPO") or os.getenv("CI_REPOSITORY_URL")

        if remote_address:
            return parse_slug(remote_address)

        return None

    def _get_branch(self):
        return os.getenv("CI_BUILD_REF_NAME") or os.getenv("CI_COMMIT_REF_NAME")

    def _get_service(self):
        return "gitlab"

    def get_service_name(self):
        return "GitlabCI"
