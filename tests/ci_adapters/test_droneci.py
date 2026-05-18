import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.droneci import DroneCIAdapter


class DroneCIEnvEnum(str, Enum):
    DRONE_BRANCH = "DRONE_BRANCH"
    DRONE_BUILD_NUMBER = "DRONE_BUILD_NUMBER"
    DRONE_BUILD_LINK = "DRONE_BUILD_LINK"
    DRONE_COMMIT_SHA = "DRONE_COMMIT_SHA"
    DRONE_REPO = "DRONE_REPO"
    DRONE_PULL_REQUEST = "DRONE_PULL_REQUEST"
    DRONE = "DRONE"


class TestDroneCI(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            ({DroneCIEnvEnum.DRONE: "true"}, True),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = DroneCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({DroneCIEnvEnum.DRONE_COMMIT_SHA: "some_random_sha"}, "some_random_sha"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = DroneCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {DroneCIEnvEnum.DRONE_BUILD_LINK: "test@test.org/test"},
                "test@test.org/test",
            ),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = DroneCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({DroneCIEnvEnum.DRONE_BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = DroneCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    def test_job_code(self):
        assert DroneCIAdapter().get_fallback_value(FallbackFieldEnum.job_code) is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({DroneCIEnvEnum.DRONE_PULL_REQUEST: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = DroneCIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({DroneCIEnvEnum.DRONE_REPO: "myorg/myrepo"}, "myorg/myrepo"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = DroneCIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({DroneCIEnvEnum.DRONE_BRANCH: "random"}, "random"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = DroneCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            DroneCIAdapter().get_fallback_value(FallbackFieldEnum.service) == "droneci"
        )
