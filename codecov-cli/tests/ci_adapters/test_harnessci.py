import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import HarnessAdapter


class HarnessEnvEnum(str, Enum):
    HARNESS_BUILD_ID = "HARNESS_BUILD_ID"
    CI_BUILD_LINK = "CI_BUILD_LINK"
    CI_BUILD_NUMBER = "CI_BUILD_NUMBER"
    CI_REMOTE_URL = "CI_REMOTE_URL"
    CI_REPO = "CI_REPO"
    CI_REPO_LINK = "CI_REPO_LINK"
    CI_REPO_REMOTE = "CI_REPO_REMOTE"
    DRONE_COMMIT_BRANCH = "DRONE_COMMIT_BRANCH"
    DRONE_COMMIT_SHA = "DRONE_COMMIT_SHA"
    DRONE_PULL_REQUEST = "DRONE_PULL_REQUEST"
    DRONE_GIT_HTTP_URL = "DRONE_GIT_HTTP_URL"
    DRONE_REMOTE_URL = "DRONE_REMOTE_URL"

class TestHarnessCI(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
        ({}, False),
        ({HarnessEnvEnum.HARNESS_BUILD_ID: "123"}, True),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HarnessAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
        ({}, None),
        ({HarnessEnvEnum.DRONE_COMMIT_BRANCH: "branch"}, "branch"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HarnessAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
        ({}, None),
        ({HarnessEnvEnum.DRONE_COMMIT_SHA: "sha"}, "sha"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HarnessAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
        ({}, None),
        ({HarnessEnvEnum.DRONE_PULL_REQUEST: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HarnessAdapter().get_fallback_value(FallbackFieldEnum.pull_request_number)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
        ({}, None),
        ({HarnessEnvEnum.CI_BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HarnessAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected
        
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
        ({}, None),
        ({HarnessEnvEnum.CI_BUILD_LINK: "https://example.com"}, "https://example.com"),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HarnessAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({HarnessEnvEnum.CI_REPO: "owner/repo"}, "owner/repo"),
            ({HarnessEnvEnum.CI_REPO: "repo"}, None),
            (
                {
                    HarnessEnvEnum.CI_REPO_REMOTE: "https://gitlab.com/mygroup/myrepo.git",
                },
                "mygroup/myrepo",
            ),
            (
                {
                    HarnessEnvEnum.CI_REMOTE_URL: "https://github.com/from-remote-url/from-remote-url",
                },
                "from-remote-url/from-remote-url",
            ),
            (
                {
                    HarnessEnvEnum.CI_REPO_LINK: "https://github.com/from-repo-link/from-repo-link",
                },
                "from-repo-link/from-repo-link",
            ),
            (
                {
                    HarnessEnvEnum.DRONE_GIT_HTTP_URL: "https://github.com/myorg/myrepo.git",
                },
                "myorg/myrepo",
            ),
            (
                {
                    HarnessEnvEnum.DRONE_REMOTE_URL: "git@github.com:acme/coverage.git",
                },
                "acme/coverage",
            ),
            (
                {
                    HarnessEnvEnum.CI_REPO_REMOTE: "https://github.com/first/first.git",
                    HarnessEnvEnum.DRONE_GIT_HTTP_URL: "https://github.com/second/second.git",
                },
                "first/first",
            ),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = HarnessAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual == expected

    def test_service(self):
        assert (
            HarnessAdapter().get_fallback_value(FallbackFieldEnum.service) == "harness"
        )