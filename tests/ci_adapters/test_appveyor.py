import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.appveyor_ci import AppveyorCIAdapter


class AppveyorCIEnvEnum(str, Enum):
    APPVEYOR_ACCOUNT_NAME = "APPVEYOR_ACCOUNT_NAME"
    APPVEYOR_BUILD_ID = "APPVEYOR_BUILD_ID"
    APPVEYOR_BUILD_VERSION = "APPVEYOR_BUILD_VERSION"
    APPVEYOR_JOB_ID = "APPVEYOR_JOB_ID"
    APPVEYOR_PROJECT_SLUG = "APPVEYOR_PROJECT_SLUG"
    APPVEYOR_PULL_REQUEST_HEAD_COMMIT = "APPVEYOR_PULL_REQUEST_HEAD_COMMIT"
    APPVEYOR_PULL_REQUEST_NUMBER = "APPVEYOR_PULL_REQUEST_NUMBER"
    APPVEYOR_REPO_BRANCH = "APPVEYOR_REPO_BRANCH"
    APPVEYOR_REPO_COMMIT = "APPVEYOR_REPO_COMMIT"
    APPVEYOR_REPO_NAME = "APPVEYOR_REPO_NAME"
    APPVEYOR_URL = "APPVEYOR_URL"
    CI = "CI"
    APPVEYOR = "APPVEYOR"


class TestAppveyorCI(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {AppveyorCIEnvEnum.CI: "True", AppveyorCIEnvEnum.APPVEYOR: "True"},
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    AppveyorCIEnvEnum.APPVEYOR_PULL_REQUEST_HEAD_COMMIT: "some_random_sha"
                },
                "some_random_sha",
            ),
            (
                {AppveyorCIEnvEnum.APPVEYOR_REPO_COMMIT: "another_random_one"},
                "another_random_one",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    AppveyorCIEnvEnum.APPVEYOR_URL: "test@test.org/test",
                    AppveyorCIEnvEnum.APPVEYOR_REPO_NAME: "name",
                    AppveyorCIEnvEnum.APPVEYOR_BUILD_ID: "build",
                    AppveyorCIEnvEnum.APPVEYOR_JOB_ID: "job",
                },
                "test@test.org/test/project/name/builds/build/job/job",
            ),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AppveyorCIEnvEnum.APPVEYOR_JOB_ID: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    AppveyorCIEnvEnum.APPVEYOR_ACCOUNT_NAME: "abc",
                    AppveyorCIEnvEnum.APPVEYOR_PROJECT_SLUG: "ff",
                    AppveyorCIEnvEnum.APPVEYOR_BUILD_VERSION: "aa",
                },
                "abc/ff/aa",
            ),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().get_fallback_value(FallbackFieldEnum.job_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AppveyorCIEnvEnum.APPVEYOR_PULL_REQUEST_NUMBER: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AppveyorCIEnvEnum.APPVEYOR_REPO_NAME: "abc"}, "abc"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AppveyorCIEnvEnum.APPVEYOR_REPO_BRANCH: "abc"}, "abc"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AppveyorCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            AppveyorCIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "appveyor"
        )
