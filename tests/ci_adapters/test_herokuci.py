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

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({HerokuCIEnvEnum.HEROKU_TEST_RUN_BRANCH: "random"}, "random"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HerokuCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_raises_value_error_if_invalid_field(self):
        with pytest.raises(ValueError):
            HerokuCIAdapter().get_fallback_value("some_random_key")

    def test_service(self):
        assert (
            HerokuCIAdapter().get_fallback_value(FallbackFieldEnum.service) == "heroku"
        )

    def test_other_values_fallback_to_none(self):
        assert HerokuCIAdapter()._get_slug() is None
        assert HerokuCIAdapter()._get_build_url() is None
        assert HerokuCIAdapter()._get_job_code() is None
        assert HerokuCIAdapter()._get_pull_request_number() is None
