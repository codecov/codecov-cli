import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import CircleCICIAdapter


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
    def test_commit_sha(self, mocker):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual is None

        expected = "some_random_sha"
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_SHA1: expected})

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)

        assert actual == expected

    def test_build_url(self, mocker):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual is None

        expected = "test@test.org/test"
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_BUILD_URL: expected})

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_url)

        assert actual == expected

    def test_build_code(self, mocker):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual is None

        expected = "test_code"
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_BUILD_NUM: expected})

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_code)

        assert actual == expected

    def test_job_code(self, mocker):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.job_code)
        assert actual is None

        expected = "test_code"
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_NODE_INDEX: expected})

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.job_code)

        assert actual == expected

    def test_pull_request_number(self, mocker):
        actual = CircleCICIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual is None

        expected = "random_number"
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_PR_NUMBER: expected})

        actual = CircleCICIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )

        assert actual == expected

    def test_slug_from_project_and_repo_names(self, mocker):
        project_username = "myname"
        repo_name = "myrepo123"
        mocker.patch.dict(
            os.environ, {self.EnvEnum.CIRCLE_PROJECT_USERNAME: project_username}
        )
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_PROJECT_REPONAME: repo_name})

        expected = f"{project_username}/{repo_name}"

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_slug_from_repo_url(self, mocker):
        repo_url = "git@github.com:codecov/codecov-cli.git"
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_REPOSITORY_URL: repo_url})

        expected = "codecov/codecov-cli"

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_slug_doesnt_exist(self):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual is None

    def test_branch(self, mocker):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual is None

        expected = "random"
        mocker.patch.dict(os.environ, {self.EnvEnum.CIRCLE_BRANCH: expected})

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.branch)

        assert actual == expected

    def test_raises_value_error_if_unvalid_field(self, mocker):
        with pytest.raises(ValueError) as ex:
            CircleCICIAdapter().get_fallback_value("some random key x 123")
