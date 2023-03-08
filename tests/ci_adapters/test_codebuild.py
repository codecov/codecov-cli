import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.codebuild import AWSCodeBuildCIAdapter


class CodeBuildEnvEnum(str, Enum):
    CODEBUILD_WEBHOOK_HEAD_REF = "CODEBUILD_WEBHOOK_HEAD_REF"
    CODEBUILD_BUILD_ID = "CODEBUILD_BUILD_ID"
    CODEBUILD_RESOLVED_SOURCE_VERSION = "CODEBUILD_RESOLVED_SOURCE_VERSION"
    CODEBUILD_SOURCE_REPO_URL = "CODEBUILD_SOURCE_REPO_URL"
    CODEBUILD_SOURCE_VERSION = "CODEBUILD_SOURCE_VERSION"
    CODEBUILD_CI = "CODEBUILD_CI"


class TestCodeBuild(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            ({CodeBuildEnvEnum.CODEBUILD_CI: "true"}, True),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AWSCodeBuildCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {CodeBuildEnvEnum.CODEBUILD_RESOLVED_SOURCE_VERSION: "some_random_sha"},
                "some_random_sha",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AWSCodeBuildCIAdapter().get_fallback_value(
            FallbackFieldEnum.commit_sha
        )
        assert actual == expected

    def test_build_url(self):
        assert (
            AWSCodeBuildCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
            is None
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CodeBuildEnvEnum.CODEBUILD_BUILD_ID: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AWSCodeBuildCIAdapter().get_fallback_value(
            FallbackFieldEnum.build_code
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CodeBuildEnvEnum.CODEBUILD_SOURCE_VERSION: "123"}, None),
            ({CodeBuildEnvEnum.CODEBUILD_SOURCE_VERSION: "pr/123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AWSCodeBuildCIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CodeBuildEnvEnum.CODEBUILD_SOURCE_REPO_URL: "123"}, "123"),
            (
                {
                    CodeBuildEnvEnum.CODEBUILD_SOURCE_REPO_URL: "www.github.com/org/repo.git"
                },
                "org/repo",
            ),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AWSCodeBuildCIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {CodeBuildEnvEnum.CODEBUILD_WEBHOOK_HEAD_REF: "refs/heads/branch"},
                "branch",
            ),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AWSCodeBuildCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            AWSCodeBuildCIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "AWS CodeBuild"
        )
