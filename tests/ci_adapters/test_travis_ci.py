import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.travis_ci import TravisCIAdapter


class TravisEnvEnum(str, Enum):
    TRAVIS_COMMIT = "TRAVIS_COMMIT"
    TRAVIS_BUILD_WEB_URL = "TRAVIS_BUILD_WEB_URL"
    TRAVIS_BUILD_NUMBER = "TRAVIS_BUILD_NUMBER"
    TRAVIS_JOB_NUMBER = "TRAVIS_JOB_NUMBER"
    TRAVIS_PULL_REQUEST = "TRAVIS_PULL_REQUEST"
    TRAVIS_REPO_SLUG = "TRAVIS_REPO_SLUG"
    TRAVIS_BRANCH = "TRAVIS_BRANCH"
    TRAVIS_PULL_REQUEST_SHA = "TRAVIS_PULL_REQUEST_SHA"
    TRAVIS_PULL_REQUEST_BRANCH = "TRAVIS_PULL_REQUEST_BRANCH"
    TRAVIS_JOB_ID = "TRAVIS_JOB_ID"
    CI = "CI"
    TRAVIS = "TRAVIS"
    SHIPPABLE = "SHIPPABLE"


class TestTravisCIAdapter(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {TravisEnvEnum.CI: "true", TravisEnvEnum.TRAVIS: "true"},
                True,
            ),
            (
                {
                    TravisEnvEnum.CI: "true",
                    TravisEnvEnum.TRAVIS: "true",
                    TravisEnvEnum.SHIPPABLE: "true",
                },
                False,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    TravisEnvEnum.TRAVIS_COMMIT: "commit-sha",
                    TravisEnvEnum.TRAVIS_PULL_REQUEST_SHA: "PR-commit-sha",
                },
                "PR-commit-sha",
            ),
            ({TravisEnvEnum.TRAVIS_COMMIT: "commit-sha"}, "commit-sha"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({TravisEnvEnum.TRAVIS_JOB_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().get_fallback_value(FallbackFieldEnum.build_code)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({TravisEnvEnum.TRAVIS_JOB_ID: "123"}, "123"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().get_fallback_value(FallbackFieldEnum.job_code)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({TravisEnvEnum.TRAVIS_PULL_REQUEST: "123"}, "123"),
            ({TravisEnvEnum.TRAVIS_PULL_REQUEST: "false"}, None),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({TravisEnvEnum.TRAVIS_REPO_SLUG: "abc"}, "abc"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    TravisEnvEnum.TRAVIS_BRANCH: "abc",
                    TravisEnvEnum.TRAVIS_PULL_REQUEST_BRANCH: "pr-branch",
                },
                "pr-branch",
            ),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = TravisCIAdapter().get_fallback_value(FallbackFieldEnum.branch)

        assert actual == expected

    def test_service(self):
        assert (
            TravisCIAdapter().get_fallback_value(FallbackFieldEnum.service) == "travis"
        )
