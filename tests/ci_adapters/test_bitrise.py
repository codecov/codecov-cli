import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.bitrise_ci import BitriseCIAdapter


class BitriseEnvEnum(str, Enum):
    BITRISE_GIT_BRANCH = "BITRISE_GIT_BRANCH"
    BITRISE_PULL_REQUEST = "BITRISE_PULL_REQUEST"
    BITRISE_BUILD_NUMBER = "BITRISE_BUILD_NUMBER"
    BITRISE_BUILD_URL = "BITRISE_BUILD_URL"
    GIT_CLONE_COMMIT_HASH = "GIT_CLONE_COMMIT_HASH"
    CI = "CI"
    BITRISE_IO = "BITRISE_IO"


class TestBitrise(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {BitriseEnvEnum.CI: "true", BitriseEnvEnum.BITRISE_IO: "true"},
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitriseCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {BitriseEnvEnum.GIT_CLONE_COMMIT_HASH: "some_random_sha"},
                "some_random_sha",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitriseCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitriseEnvEnum.BITRISE_BUILD_URL: "test@test.com"}, "test@test.com"),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitriseCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitriseEnvEnum.BITRISE_BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitriseCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    def test_job_code(self):
        assert BitriseCIAdapter().get_fallback_value(FallbackFieldEnum.job_code) is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitriseEnvEnum.BITRISE_PULL_REQUEST: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitriseCIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    def test_slug(self):
        assert BitriseCIAdapter().get_fallback_value(FallbackFieldEnum.slug) is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitriseEnvEnum.BITRISE_GIT_BRANCH: "branch"}, "branch"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitriseCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            BitriseCIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "bitrise"
        )
