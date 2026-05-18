import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class TeamcityAdapter(CIAdapterBase):
    # https://www.jetbrains.com/help/teamcity/predefined-build-parameters.html#Predefined+Server+Build+Parameters

    def detect(self) -> bool:
        return bool(os.getenv("TEAMCITY_VERSION"))

    def _get_branch(self):
        return os.getenv("BRANCH_NAME")

    def _get_build_code(self):
        return os.getenv("BUILD_NUMBER")

    def _get_build_url(self):
        return None

    def _get_commit_sha(self):
        return os.getenv("BUILD_VCS_NUMBER")

    def _get_slug(self):
        return None

    def _get_service(self):
        return "teamcity"

    def _get_pull_request_number(self):
        return None

    def _get_job_code(self):
        return None

    def get_service_name(self):
        return "Teamcity"
