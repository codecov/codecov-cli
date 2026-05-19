import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.jenkins import JenkinsAdapter


class JenkinsCIEnvEnum(str, Enum):
    BUILD_URL = "BUILD_URL"
    BUILD_NUMBER = "BUILD_NUMBER"
    CHANGE_ID = "CHANGE_ID"
    BRANCH_NAME = "BRANCH_NAME"
    JENKINS_URL = "JENKINS_URL"


class TestJenkins(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            ({JenkinsCIEnvEnum.JENKINS_URL: "url"}, True),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = JenkinsAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({JenkinsCIEnvEnum.BUILD_URL: "url"}, "url"),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = JenkinsAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({JenkinsCIEnvEnum.BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = JenkinsAdapter().get_fallback_value(FallbackFieldEnum.build_code)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({JenkinsCIEnvEnum.CHANGE_ID: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = JenkinsAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({JenkinsCIEnvEnum.BRANCH_NAME: "abc"}, "abc"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = JenkinsAdapter().get_fallback_value(FallbackFieldEnum.branch)

        assert actual == expected

    def test_service(self):
        assert (
            JenkinsAdapter().get_fallback_value(FallbackFieldEnum.service) == "jenkins"
        )

    def test_none_values(self):
        JenkinsAdapter().get_fallback_value(FallbackFieldEnum.slug) is None
        JenkinsAdapter().get_fallback_value(FallbackFieldEnum.commit_sha) is None
        JenkinsAdapter().get_fallback_value(FallbackFieldEnum.job_code) is None
