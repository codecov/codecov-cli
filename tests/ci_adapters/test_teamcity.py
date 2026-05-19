import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.teamcity import TeamcityAdapter


class TeamcityEnvEnum(str, Enum):
    BRANCH_NAME = "BRANCH_NAME"
    BUILD_NUMBER = "BUILD_NUMBER"
    BUILD_VCS_NUMBER = "BUILD_VCS_NUMBER"
    TEAMCITY_VERSION = "TEAMCITY_VERSION"


class TestBuildkite(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {TeamcityEnvEnum.BUILD_VCS_NUMBER: "some_random_sha"},
                "some_random_sha",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TeamcityAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    def test_build_url(self):
        assert TeamcityAdapter().get_fallback_value(FallbackFieldEnum.build_url) is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {TeamcityEnvEnum.TEAMCITY_VERSION: "1.1"},
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TeamcityAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({TeamcityEnvEnum.BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TeamcityAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    def test_job_code(self):
        assert TeamcityAdapter().get_fallback_value(FallbackFieldEnum.job_code) is None

    def test_pull_request_number(self):
        assert (
            TeamcityAdapter().get_fallback_value(FallbackFieldEnum.pull_request_number)
            is None
        )

    def test_slug(self):
        assert TeamcityAdapter().get_fallback_value(FallbackFieldEnum.slug) is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({TeamcityEnvEnum.BRANCH_NAME: "branch"}, "branch"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TeamcityAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            TeamcityAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "teamcity"
        )
