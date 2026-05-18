import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.cirrus_ci import CirrusCIAdapter


class CirrusEnvEnum(str, Enum):
    CIRRUS_BRANCH = "CIRRUS_BRANCH"
    CIRRUS_BUILD_ID = "CIRRUS_BUILD_ID"
    CIRRUS_CHANGE_IN_REPO = "CIRRUS_CHANGE_IN_REPO"
    CIRRUS_REPO_FULL_NAME = "CIRRUS_REPO_FULL_NAME"
    CIRRUS_PR = "CIRRUS_PR"
    CIRRUS_TASK_ID = "CIRRUS_TASK_ID"
    CIRRUS_CI = "CIRRUS_CI"


class TestCirrus(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {CirrusEnvEnum.CIRRUS_CI: "true"},
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CirrusCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {CirrusEnvEnum.CIRRUS_CHANGE_IN_REPO: "some_random_sha"},
                "some_random_sha",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CirrusCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    def test_build_url(self):
        assert CirrusCIAdapter().get_fallback_value(FallbackFieldEnum.build_url) is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CirrusEnvEnum.CIRRUS_BUILD_ID: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CirrusCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CirrusEnvEnum.CIRRUS_TASK_ID: "123"}, "123"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CirrusCIAdapter().get_fallback_value(FallbackFieldEnum.job_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CirrusEnvEnum.CIRRUS_PR: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CirrusCIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CirrusEnvEnum.CIRRUS_REPO_FULL_NAME: "123"}, "123"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CirrusCIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CirrusEnvEnum.CIRRUS_BRANCH: "branch"}, "branch"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CirrusCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            CirrusCIAdapter().get_fallback_value(FallbackFieldEnum.service) == "cirrus"
        )
