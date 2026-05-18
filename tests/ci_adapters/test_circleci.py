import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import CircleCICIAdapter


class CircleCIEnvEnum(str, Enum):
    CIRCLE_SHA1 = "CIRCLE_SHA1"
    CIRCLE_BUILD_URL = "CIRCLE_BUILD_URL"
    CIRCLE_BUILD_NUM = "CIRCLE_BUILD_NUM"
    CIRCLE_NODE_INDEX = "CIRCLE_NODE_INDEX"
    CIRCLE_PR_NUMBER = "CIRCLE_PR_NUMBER"
    CIRCLE_PROJECT_USERNAME = "CIRCLE_PROJECT_USERNAME"
    CIRCLE_PROJECT_REPONAME = "CIRCLE_PROJECT_REPONAME"
    CIRCLE_REPOSITORY_URL = "CIRCLE_REPOSITORY_URL"
    CIRCLE_BRANCH = "CIRCLE_BRANCH"
    CI = "CI"
    CIRCLECI = "CIRCLECI"


class TestCircleCI(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            ({CircleCIEnvEnum.CI: "true", CircleCIEnvEnum.CIRCLECI: "true"}, True),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_SHA1: "some_random_sha"}, "some_random_sha"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {CircleCIEnvEnum.CIRCLE_BUILD_URL: "test@test.org/test"},
                "test@test.org/test",
            ),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_BUILD_NUM: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_NODE_INDEX: "test_code"}, "test_code"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.job_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_PR_NUMBER: "random_number"}, "random_number"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    def test_slug_from_project_and_repo_names(self, mocker):
        project_username = "myname"
        repo_name = "myrepo123"
        mocker.patch.dict(
            os.environ,
            {
                CircleCIEnvEnum.CIRCLE_PROJECT_USERNAME: project_username,
                CircleCIEnvEnum.CIRCLE_PROJECT_REPONAME: repo_name,
            },
        )

        expected = f"{project_username}/{repo_name}"

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_slug_from_repo_url(self, mocker):
        repo_url = "git@github.com:codecov/codecov-cli.git"
        mocker.patch.dict(os.environ, {CircleCIEnvEnum.CIRCLE_REPOSITORY_URL: repo_url})

        expected = "codecov/codecov-cli"

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_slug_doesnt_exist(self):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_BRANCH: "random"}, "random"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_raises_value_error_if_invalid_field(self):
        with pytest.raises(ValueError):
            CircleCICIAdapter().get_fallback_value("some random key x 123")

    def test_service(self):
        assert (
            CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "circleci"
        )
