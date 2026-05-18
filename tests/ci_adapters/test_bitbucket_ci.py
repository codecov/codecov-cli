import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.bitbucket_ci import BitbucketAdapter


class BitbucketEnvEnum(str, Enum):
    BITBUCKET_BUILD_NUMBER = "BITBUCKET_BUILD_NUMBER"
    BITBUCKET_BRANCH = "BITBUCKET_BRANCH"
    BITBUCKET_PR_ID = "BITBUCKET_PR_ID"
    BITBUCKET_COMMIT = "BITBUCKET_COMMIT"
    BITBUCKET_REPO_FULL_NAME = "BITBUCKET_REPO_FULL_NAME"
    CI = "CI"


class TestBitbucket(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {
                    BitbucketEnvEnum.CI: "true",
                    BitbucketEnvEnum.BITBUCKET_BUILD_NUMBER: "123",
                },
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitbucketAdapter().detect()

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitbucketEnvEnum.BITBUCKET_COMMIT: "123456789000"}, None),
            ({BitbucketEnvEnum.BITBUCKET_COMMIT: "123456789000111"}, "123456789000111"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitbucketAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)

        assert actual == expected

    def test_build_url(self):
        assert (
            BitbucketAdapter().get_fallback_value(FallbackFieldEnum.build_url) is None
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitbucketEnvEnum.BITBUCKET_BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitbucketAdapter().get_fallback_value(FallbackFieldEnum.build_code)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitbucketEnvEnum.BITBUCKET_BUILD_NUMBER: "123"}, "123"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitbucketAdapter().get_fallback_value(FallbackFieldEnum.job_code)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitbucketEnvEnum.BITBUCKET_PR_ID: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitbucketAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitbucketEnvEnum.BITBUCKET_REPO_FULL_NAME: "abc"}, "abc"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitbucketAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({BitbucketEnvEnum.BITBUCKET_BRANCH: "abc"}, "abc"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = BitbucketAdapter().get_fallback_value(FallbackFieldEnum.branch)

        assert actual == expected

    def test_service(self):
        assert (
            BitbucketAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "bitbucket"
        )
