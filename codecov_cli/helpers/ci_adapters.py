import os
import typing
from abc import ABC

from codecov_cli.fallbacks import FallbackFieldEnum


class CIAdapterBase(ABC):
    def __init__(self):
        # If a fallbacker has extra fields, they should be added to this dictionary in the fallbacker's constructor.
        self.fallback_to_method = {
            FallbackFieldEnum.branch: self._get_branch,
            FallbackFieldEnum.build_code: self._get_build_code,
            FallbackFieldEnum.build_url: self._get_build_url,
            FallbackFieldEnum.commit_sha: self._get_commit_sha,
            FallbackFieldEnum.slug: self._get_slug,
            FallbackFieldEnum.service: self._get_service,
            FallbackFieldEnum.pull_request_number: self._get_pull_request_number,
            FallbackFieldEnum.job_code: self._get_job_code,
        }

    def get_fallback_value(
        self, fallback_field: FallbackFieldEnum
    ) -> typing.Optional[str]:

        if not fallback_field in self.fallback_to_method:
            raise ValueError("The provided fallback_field is not valid")

        return self.fallback_to_method[fallback_field]()


class CircleCICIAdapter(CIAdapterBase):
    # https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables

    def _get_commit_sha(self):
        return os.getenv("CIRCLE_SHA1")

    def _get_build_url(self):
        return os.getenv("CIRCLE_BUILD_URL")

    def _get_build_code(self):
        return os.getenv("CIRCLE_BUILD_NUM")

    def _get_job_code(self):
        return os.getenv("CIRCLE_NODE_INDEX")

    def _get_pull_request_number(self):
        return os.getenv("CIRCLE_PR_NUMBER")

    def _get_slug(self):
        project_username = os.getenv("CIRCLE_PROJECT_USERNAME")
        project_repo_name = os.getenv("CIRCLE_PROJECT_REPONAME")

        if project_repo_name and project_username:
            return f"{project_username}/{project_repo_name}"

        repo_url = os.getenv("CIRCLE_REPOSITORY_URL")

        if repo_url:
            return repo_url.split(":")[1].split(".git")[0]

        return None

    def _get_branch(self):
        return os.getenv("CIRCLE_BRANCH")

    def _get_service(self):
        return "circleci"


def get_ci_adapter(provider_name):
    if provider_name == "circleci":
        return CircleCICIAdapter()
    return None
