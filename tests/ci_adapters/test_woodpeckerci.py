import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.woodpeckerci import WoodpeckerCIAdapter


class WoodpeckerEnvEnum(str, Enum):
    CI_COMMIT_SOURCE_BRANCH = "CI_COMMIT_SOURCE_BRANCH"
    CI_COMMIT_BRANCH = "CI_COMMIT_BRANCH"
    CI_BUILD_NUMBER = "CI_BUILD_NUMBER"
    CI_BUILD_LINK = "CI_BUILD_LINK"
    CI_COMMIT_SHA = "CI_COMMIT_SHA"
    CI_REPO = "CI_REPO"
    CI_COMMIT_PULL_REQUEST = "CI_COMMIT_PULL_REQUEST"
    CI_JOB_NUMBER = "CI_JOB_NUMBER"
    CI = "CI"


class TestWoodpecker(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            ({WoodpeckerEnvEnum.CI: "woodpecker"}, True),
            ({WoodpeckerEnvEnum.CI: "true"}, False),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, expected)
        assert WoodpeckerCIAdapter().detect() == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({WoodpeckerEnvEnum.CI_COMMIT_SHA: "random"}, "random"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, expected)
        assert (
            WoodpeckerCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({WoodpeckerEnvEnum.CI_BUILD_LINK: "random"}, "random"),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            WoodpeckerCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({WoodpeckerEnvEnum.CI_BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            WoodpeckerCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({WoodpeckerEnvEnum.CI_JOB_NUMBER: "123"}, "123"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            WoodpeckerCIAdapter().get_fallback_value(FallbackFieldEnum.job_code)
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({WoodpeckerEnvEnum.CI_COMMIT_PULL_REQUEST: "1234"}, "1234"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            WoodpeckerCIAdapter().get_fallback_value(
                FallbackFieldEnum.pull_request_number
            )
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {WoodpeckerEnvEnum.CI_REPO: "codecov/codecov-cli"},
                "codecov/codecov-cli",
            ),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            WoodpeckerCIAdapter().get_fallback_value(FallbackFieldEnum.slug) == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({WoodpeckerEnvEnum.CI_COMMIT_SOURCE_BRANCH: "aa"}, "aa"),
            ({WoodpeckerEnvEnum.CI_COMMIT_BRANCH: "bb"}, "bb"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        assert (
            WoodpeckerCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
            == expected
        )

    def test_service(self, mocker):
        assert (
            WoodpeckerCIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "woodpecker"
        )
