import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.buildkite import BuildkiteAdapter


class BuildkiteEnvEnum(str, Enum):
    BUILDKITE_BRANCH = "BUILDKITE_BRANCH"
    BUILDKITE_BUILD_NUMBER = "BUILDKITE_BUILD_NUMBER"
    BUILDKITE_BUILD_URL = "BUILDKITE_BUILD_URL"
    BUILDKITE_COMMIT = "BUILDKITE_COMMIT"
    BUILDKITE_ORGANIZATION_SLUG = "BUILDKITE_ORGANIZATION_SLUG"
    BUILDKITE_PIPELINE_SLUG = "BUILDKITE_PIPELINE_SLUG"
    BUILDKITE_PULL_REQUEST = "BUILDKITE_PULL_REQUEST"
    BUILDKITE_JOB_ID = "BUILDKITE_JOB_ID"
    BUILDKITE = "BUILDKITE"


class TestBuildkite(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {BuildkiteEnvEnum.BUILDKITE: "true"},
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {BuildkiteEnvEnum.BUILDKITE_COMMIT: "some_random_sha"},
                "some_random_sha",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BuildkiteEnvEnum.BUILDKITE_BUILD_URL: "test@test.com"}, "test@test.com"),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BuildkiteEnvEnum.BUILDKITE_BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BuildkiteEnvEnum.BUILDKITE_JOB_ID: "123"}, "123"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().get_fallback_value(FallbackFieldEnum.job_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BuildkiteEnvEnum.BUILDKITE_PULL_REQUEST: "123"}, "123"),
            ({BuildkiteEnvEnum.BUILDKITE_PULL_REQUEST: "false"}, None),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    BuildkiteEnvEnum.BUILDKITE_ORGANIZATION_SLUG: "myorg",
                    BuildkiteEnvEnum.BUILDKITE_PIPELINE_SLUG: "myrepo",
                },
                "myorg/myrepo",
            ),
            (
                {
                    BuildkiteEnvEnum.BUILDKITE_ORGANIZATION_SLUG: "myorg/subteam",
                    BuildkiteEnvEnum.BUILDKITE_PIPELINE_SLUG: "myrepo",
                },
                "myorg/subteam/myrepo",
            ),
            (
                {
                    BuildkiteEnvEnum.BUILDKITE_ORGANIZATION_SLUG: "myorg",
                    BuildkiteEnvEnum.BUILDKITE_PIPELINE_SLUG: "",
                },
                None,
            ),
            (
                {
                    BuildkiteEnvEnum.BUILDKITE_ORGANIZATION_SLUG: "",
                    BuildkiteEnvEnum.BUILDKITE_PIPELINE_SLUG: "myrepo",
                },
                None,
            ),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BuildkiteEnvEnum.BUILDKITE_BRANCH: "branch"}, "branch"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BuildkiteAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            BuildkiteAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "buildkite"
        )
