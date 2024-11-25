import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.local import LocalAdapter


class LocalEnvEnum(str, Enum):
    GIT_BRANCH = "GIT_BRANCH"
    BRANCH_NAME = "BRANCH_NAME"
    GIT_COMMIT = "GIT_COMMIT"


class TestLocalAdapter(object):
    def test_detect(self, mocker):
        mocked_subprocess = mocker.patch(
            "codecov_cli.helpers.ci_adapters.local.subprocess.run",
            return_value=mocker.MagicMock(returncode=0),
        )
        assert LocalAdapter().detect()
        mocked_subprocess.assert_called_once()

    def test_detect_git_not_installed(self, mocker):
        mocked_subprocess = mocker.patch(
            "codecov_cli.helpers.ci_adapters.local.subprocess.run",
            return_value=mocker.MagicMock(returncode=1),
        )
        assert not LocalAdapter().detect()
        mocked_subprocess.assert_called_once()

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {LocalEnvEnum.GIT_COMMIT: "some_random_sha"},
                "some_random_sha",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = LocalAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    def test_build_url(self):
        assert LocalAdapter().get_fallback_value(FallbackFieldEnum.build_url) is None

    def test_build_code(self):
        assert LocalAdapter().get_fallback_value(FallbackFieldEnum.build_code) is None

    def test_job_code(self):
        assert LocalAdapter().get_fallback_value(FallbackFieldEnum.job_code) is None

    def test_pull_request_number(self):
        assert (
            LocalAdapter().get_fallback_value(FallbackFieldEnum.pull_request_number)
            is None
        )

    def test_slug(self):
        assert LocalAdapter().get_fallback_value(FallbackFieldEnum.slug) is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({LocalEnvEnum.BRANCH_NAME: "branch"}, "branch"),
            ({LocalEnvEnum.GIT_BRANCH: "branch"}, "branch"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = LocalAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert LocalAdapter().get_fallback_value(FallbackFieldEnum.service) == "local"
