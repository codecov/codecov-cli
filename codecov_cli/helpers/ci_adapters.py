import os
import typing
from abc import ABC, abstractmethod

from codecov_cli.fallbacks import FallbackFieldEnum


class FallbackerBase(ABC):
    def __init__(self):
        # If a fallbacker has extra fields, they should be added to this dictionary in the fallbacker's constructor.
        self.fallback_to_prop = {
            FallbackFieldEnum.branch: self.branch,
            FallbackFieldEnum.build_code: self.build_code,
            FallbackFieldEnum.build_url: self.build_url,
            FallbackFieldEnum.commit_sha: self.commit_sha,
            FallbackFieldEnum.slug: self.slug,
            FallbackFieldEnum.service: self.service,
            FallbackFieldEnum.pull_request_number: self.pull_request_number,
            FallbackFieldEnum.job_code: self.job_code,
        }

    def get_fallback_value(
        self, fallback_field: FallbackFieldEnum
    ) -> typing.Optional[str]:
        return self.fallback_to_prop[fallback_field]

    @property
    @abstractmethod
    def commit_sha(self):
        pass

    @property
    @abstractmethod
    def build_url(self):
        pass

    @property
    @abstractmethod
    def build_code(self):
        pass

    @property
    @abstractmethod
    def job_code(self):
        pass

    @property
    @abstractmethod
    def pull_request_number(self):
        pass

    @property
    @abstractmethod
    def slug(self):
        pass

    @property
    @abstractmethod
    def branch(self):
        pass

    @property
    @abstractmethod
    def service(self):
        pass


class CircleCIFallbacker(FallbackerBase):
    # https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables

    @property
    def commit_sha(self):
        return os.getenv("CIRCLE_SHA1")

    @property
    def build_url(self):
        return os.getenv("CIRCLE_BUILD_URL")

    @property
    def build_code(self):
        return os.getenv("CIRCLE_BUILD_NUM")

    @property
    def job_code(self):
        return os.getenv("CIRCLE_NODE_INDEX")

    @property
    def pull_request_number(self):
        return os.getenv("CIRCLE_PR_NUMBER")

    @property
    def slug(self):
        project_username = os.getenv("CIRCLE_PROJECT_USERNAME")
        project_repo_name = os.getenv("CIRCLE_PROJECT_REPONAME")

        if project_repo_name and project_username:
            return f"{project_username}/{project_repo_name}"

        repo_url = os.getenv("CIRCLE_REPOSITORY_URL")

        if repo_url:
            return repo_url.split(":")[1].split(".git")[0]

        return None

    @property
    def branch(self):
        return os.getenv("CIRCLE_BRANCH")

    @property
    def service(self):
        return "circleci"


def get_ci_adapter(provider_name):
    if provider_name == "circleci":
        return CircleCIFallbacker()
    return None
