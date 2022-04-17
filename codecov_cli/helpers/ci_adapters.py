import os
import typing
from abc import ABC, abstractmethod

from codecov_cli.fallbacks import FallbackFieldEnum


class FallbackerBase(ABC):
    def __init__(self):
        # If a fallbacker has extra fields, they should be added to this dictionary in the fallbacker's constructor.
        self.fallback_to_prop = {
            FallbackFieldEnum.branch: self._branch,
            FallbackFieldEnum.build_code: self._build_code,
            FallbackFieldEnum.build_url: self._build_url,
            FallbackFieldEnum.commit_sha: self._commit_sha,
            FallbackFieldEnum.slug: self._slug,
            FallbackFieldEnum.service: self._service,
            FallbackFieldEnum.pull_request_number: self._pull_request_number,
            FallbackFieldEnum.job_code: self._job_code,
        }

    def get_fallback_value(
        self, fallback_field: FallbackFieldEnum
    ) -> typing.Optional[str]:
        return self.fallback_to_prop.get(fallback_field)

    @property
    @abstractmethod
    def _commit_sha(self):
        pass

    @property
    @abstractmethod
    def _build_url(self):
        pass

    @property
    @abstractmethod
    def _build_code(self):
        pass

    @property
    @abstractmethod
    def _job_code(self):
        pass

    @property
    @abstractmethod
    def _pull_request_number(self):
        pass

    @property
    @abstractmethod
    def _slug(self):
        pass

    @property
    @abstractmethod
    def _branch(self):
        pass

    @property
    @abstractmethod
    def _service(self):
        pass


class CircleCIFallbacker(FallbackerBase):
    # https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables

    @property
    def _commit_sha(self):
        return os.getenv("CIRCLE_SHA1")

    @property
    def _build_url(self):
        return os.getenv("CIRCLE_BUILD_URL")

    @property
    def _build_code(self):
        return os.getenv("CIRCLE_BUILD_NUM")

    @property
    def _job_code(self):
        return os.getenv("CIRCLE_NODE_INDEX")

    @property
    def _pull_request_number(self):
        return os.getenv("CIRCLE_PR_NUMBER")

    @property
    def _slug(self):
        project_username = os.getenv("CIRCLE_PROJECT_USERNAME")
        project_repo_name = os.getenv("CIRCLE_PROJECT_REPONAME")

        if project_repo_name and project_username:
            return f"{project_username}/{project_repo_name}"

        repo_url = os.getenv("CIRCLE_REPOSITORY_URL")

        if repo_url:
            return repo_url.split(":")[1].split(".git")[0]

        return None

    @property
    def _branch(self):
        return os.getenv("CIRCLE_BRANCH")

    @property
    def _service(self):
        return "circleci"


def get_ci_adapter(provider_name):
    if provider_name == "circleci":
        return CircleCIFallbacker()
    return None
