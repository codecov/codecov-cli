import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class AppveyorCIAdapter(CIAdapterBase):
    # https://www.appveyor.com/docs/environment-variables/

    def detect(self) -> bool:
        return bool(os.getenv("CI")) and bool(os.getenv("APPVEYOR"))

    def _get_commit_sha(self):
        return os.getenv("APPVEYOR_PULL_REQUEST_HEAD_COMMIT") or os.getenv(
            "APPVEYOR_REPO_COMMIT"
        )

    def _get_build_url(self):
        url = os.getenv("APPVEYOR_URL")
        repo_name = os.getenv("APPVEYOR_REPO_NAME")
        build_id = os.getenv("APPVEYOR_BUILD_ID")
        job_id = os.getenv("APPVEYOR_JOB_ID")

        if url and repo_name and build_id and job_id:
            return f"{url}/project/{repo_name}/builds/{build_id}/job/{job_id}"

        return None

    def _get_build_code(self):
        return os.getenv("APPVEYOR_JOB_ID")

    def _get_job_code(self):
        account_name = os.getenv("APPVEYOR_ACCOUNT_NAME")
        slug = os.getenv("APPVEYOR_PROJECT_SLUG")
        build_version = os.getenv("APPVEYOR_BUILD_VERSION")

        if account_name and slug and build_version:
            return f"{account_name}/{slug}/{build_version}"

        return None

    def _get_pull_request_number(self):
        return os.getenv("APPVEYOR_PULL_REQUEST_NUMBER")

    def _get_slug(self):
        return os.getenv("APPVEYOR_REPO_NAME")

    def _get_branch(self):
        return os.getenv("APPVEYOR_REPO_BRANCH")

    def _get_service(self):
        return "appveyor"

    def get_service_name(self):
        return "AppVeyor"
