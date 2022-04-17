from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import CircleCIFallbacker


class TestCircleCi(object):
    class EnvEnum(str, Enum):
        CIRCLE_SHA1 = "CIRCLE_SHA1"
        CIRCLE_BUILD_URL = "CIRCLE_BUILD_URL"
        CIRCLE_BUILD_NUM = "CIRCLE_BUILD_NUM"
        CIRCLE_NODE_INDEX = "CIRCLE_NODE_INDEX"
        CIRCLE_PR_NUMBER = "CIRCLE_PR_NUMBER"
        CIRCLE_PROJECT_USERNAME = "CIRCLE_PROJECT_USERNAME"
        CIRCLE_PROJECT_REPONAME = "CIRCLE_PROJECT_REPONAME"
        CIRCLE_REPOSITORY_URL = "CIRCLE_REPOSITORY_URL"
        CIRCLE_BRANCH = "CIRCLE_BRANCH"

    # Test individual fields
    def test_commit_sha(self, monkeypatch):
        expected = "some_random_sha"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_SHA1, expected)

        actual = CircleCIFallbacker().get_fallback_value(FallbackFieldEnum.commit_sha)

        assert actual == expected

    def test_build_url(self, monkeypatch):
        expected = "test@test.org/test"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_BUILD_URL, expected)

        actual = CircleCIFallbacker().get_fallback_value(FallbackFieldEnum.build_url)

        assert actual == expected

    def test_build_code(self, monkeypatch):
        expected = "test_code"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_BUILD_NUM, expected)

        actual = CircleCIFallbacker().get_fallback_value(FallbackFieldEnum.build_code)

        assert actual == expected

    def test_job_code(self, monkeypatch):
        expected = "test_code"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_NODE_INDEX, expected)

        actual = CircleCIFallbacker().get_fallback_value(FallbackFieldEnum.job_code)

        assert actual == expected

    def test_pull_request_number(self, monkeypatch):
        expected = "random_number"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_PR_NUMBER, expected)

        actual = CircleCIFallbacker().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )

        assert actual == expected

    def test_slug_from_project_and_repo_names(self, monkeypatch):
        project_username = "myname"
        repo_name = "myrepo123"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_PROJECT_USERNAME, project_username)
        monkeypatch.setenv(self.EnvEnum.CIRCLE_PROJECT_REPONAME, repo_name)

        expected = f"{project_username}/{repo_name}"

        actual = CircleCIFallbacker().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_slug_from_repo_url(self, monkeypatch):
        repo_url = "git@github.com:codecov/codecov-cli.git"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_REPOSITORY_URL, repo_url)

        expected = "codecov/codecov-cli"

        actual = CircleCIFallbacker().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_branch(self, monkeypatch):
        expected = "random"
        monkeypatch.setenv(self.EnvEnum.CIRCLE_BRANCH, expected)

        actual = CircleCIFallbacker().get_fallback_value(FallbackFieldEnum.branch)

        assert actual == expected

    def test_returns_none_if_unvalid_field(self, monkeypatch):
        assert CircleCIFallbacker().get_fallback_value("some random key x 123") is None
