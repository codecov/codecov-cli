import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import GitlabCIAdapter


class GitlabCIEnvEnum(str, Enum):
    CI_MERGE_REQUEST_SOURCE_BRANCH_SHA = "CI_MERGE_REQUEST_SOURCE_BRANCH_SHA"
    CI_BUILD_REF = "CI_BUILD_REF"
    CI_COMMIT_REF_NAME = "CI_COMMIT_REF_NAME"
    CI_BUILD_REF_NAME = "CI_BUILD_REF_NAME"
    CI_REPOSITORY_URL = "CI_REPOSITORY_URL"
    CI_BUILD_REPO = "CI_BUILD_REPO"
    CI_PROJECT_PATH = "CI_PROJECT_PATH"
    CI_JOB_ID = "CI_JOB_ID"
    CI_BUILD_ID = "CI_BUILD_ID"
    CI_JOB_URL = "CI_JOB_URL"
    CI_COMMIT_SHA = "CI_COMMIT_SHA"
    CI_MERGE_REQUEST_IID = "CI_MERGE_REQUEST_IID"
    CI_PROJECT_NAMESPACE = "CI_PROJECT_NAMESPACE"
    CI_PROJECT_NAME = "CI_PROJECT_NAME"
    GITLAB_CI = "GITLAB_CI"


class TestGitlabCI(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            ({GitlabCIEnvEnum.GITLAB_CI: "true"}, True),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, expected)
        assert GitlabCIAdapter().detect() == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GitlabCIEnvEnum.CI_COMMIT_SHA: "random"}, "random"),
            ({GitlabCIEnvEnum.CI_BUILD_REF: "22"}, "22"),
            ({GitlabCIEnvEnum.CI_MERGE_REQUEST_SOURCE_BRANCH_SHA: "33"}, "33"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, expected)
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GitlabCIEnvEnum.CI_JOB_URL: "random"}, "random"),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GitlabCIEnvEnum.CI_JOB_ID: "123"}, "123"),
            ({GitlabCIEnvEnum.CI_BUILD_ID: "1234"}, "1234"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GitlabCIEnvEnum.CI_JOB_ID: "123"}, "123"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.job_code) == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GitlabCIEnvEnum.CI_MERGE_REQUEST_IID: "1234"}, "1234"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.pull_request_number)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {GitlabCIEnvEnum.CI_PROJECT_PATH: "codecov/codecov-cli"},
                "codecov/codecov-cli",
            ),
            (
                {
                    GitlabCIEnvEnum.CI_PROJECT_NAMESPACE: "codecov",
                    GitlabCIEnvEnum.CI_PROJECT_NAME: "codecov-cli",
                },
                "codecov/codecov-cli",
            ),
            (
                {
                    GitlabCIEnvEnum.CI_BUILD_REPO: "git@github.com:codecov/codecov-cli.git"
                },
                "codecov/codecov-cli",
            ),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(
            os.environ,
            env_dict,
        )

        assert GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.slug) == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GitlabCIEnvEnum.CI_COMMIT_REF_NAME: "aa"}, "aa"),
            ({GitlabCIEnvEnum.CI_BUILD_REF_NAME: "bb"}, "bb"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.branch) == expected
        )

    def test_service(self, mocker):
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.service) == "gitlab"
        )
