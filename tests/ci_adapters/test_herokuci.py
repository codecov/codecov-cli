import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import HerokuCIAdapter


class HerokuCIEnvEnum(str, Enum):
    HEROKU_TEST_RUN_BRANCH = "HEROKU_TEST_RUN_BRANCH"
    HEROKU_TEST_RUN_COMMIT_VERSION = "HEROKU_TEST_RUN_COMMIT_VERSION"
    HEROKU_TEST_RUN_ID = "HEROKU_TEST_RUN_ID"
    CI = "CI"


class TestHerokuCI(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {
                    HerokuCIEnvEnum.CI: "true",
                    HerokuCIEnvEnum.HEROKU_TEST_RUN_BRANCH: "123",
                },
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HerokuCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {HerokuCIEnvEnum.HEROKU_TEST_RUN_COMMIT_VERSION: "some_random_sha"},
                "some_random_sha",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HerokuCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({HerokuCIEnvEnum.HEROKU_TEST_RUN_ID: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HerokuCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected