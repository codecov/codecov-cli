import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import GithubActionsCIAdapter


class GithubActionsEnvEnum(str, Enum):
    GITHUB_SHA = "GITHUB_SHA"
    GITHUB_SERVER_URL = "GITHUB_SERVER_URL"
    GITHUB_RUN_ID = "GITHUB_RUN_ID"
    GITHUB_WORKFLOW = "GITHUB_WORKFLOW"
    GITHUB_HEAD_REF = "GITHUB_HEAD_REF"
    GITHUB_REF = "GITHUB_REF"
    GITHUB_REPOSITORY = "GITHUB_REPOSITORY"
    GITHUB_ACTIONS = "GITHUB_ACTIONS"


class TestGithubActions(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            (
                {GithubActionsEnvEnum.GITHUB_ACTIONS: "true"},
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GithubActionsCIAdapter().detect()
        assert actual == expected

    def test_commit_sha_if_not_in_merge_commit(self, mocker):
        mocker.patch.dict(
            os.environ, {GithubActionsEnvEnum.GITHUB_SHA: "1234"}, clear=True
        )
        assert (
            GithubActionsCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
            == "1234"
        )

    def test_commit_sha_in_merge_commit_and_parents_hash_len_is_2(self, mocker):
        mocker.patch.dict(
            os.environ, {GithubActionsEnvEnum.GITHUB_SHA: "1234"}, clear=True
        )
        mocker.patch.object(
            GithubActionsCIAdapter, "_get_pull_request_number"
        ).return_value = "random_pr_number"

        fake_subprocess = mocker.MagicMock()
        mocker.patch(
            "codecov_cli.helpers.ci_adapters.github_actions.subprocess.run",
            return_value=fake_subprocess,
        )

        fake_subprocess.stdout = b"aa74b3ff0411086ee37e7a78f1b62984d7759077\n20e1219371dff308fd910b206f47fdf250621abf"
        assert (
            GithubActionsCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
            == "20e1219371dff308fd910b206f47fdf250621abf"
        )

    def test_commit_sha_in_merge_commit_and_parents_hash_len_is_not_2(self, mocker):
        mocker.patch.dict(
            os.environ, {GithubActionsEnvEnum.GITHUB_SHA: "1234"}, clear=True
        )
        mocker.patch.object(
            GithubActionsCIAdapter, "_get_pull_request_number"
        ).return_value = "random_pr_number"

        fake_subprocess = mocker.MagicMock()
        mocker.patch(
            "codecov_cli.helpers.ci_adapters.github_actions.subprocess.run",
            return_value=fake_subprocess,
        )

        fake_subprocess.stdout = b"commit\nparents\nnumber\nis_not_equal_to_2"
        assert (
            GithubActionsCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
            == "1234"
        )

    @pytest.mark.parametrize(
        "env_dict,slug,build_code,expected",
        [
            ({}, None, None, None),
            (
                {GithubActionsEnvEnum.GITHUB_SERVER_URL: "https://hello.org"},
                None,
                None,
                None,
            ),
            (
                {GithubActionsEnvEnum.GITHUB_SERVER_URL: "https://hello.org"},
                "a/b",
                None,
                None,
            ),
            (
                {GithubActionsEnvEnum.GITHUB_SERVER_URL: "https://hello.org"},
                "a/b",
                "123",
                "https://hello.org/a/b/actions/runs/123",
            ),
        ],
    )
    def test_build_url(self, env_dict, slug, build_code, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, clear=True)
        mocker.patch.object(GithubActionsCIAdapter, "_get_slug").return_value = slug
        mocker.patch.object(
            GithubActionsCIAdapter, "_get_build_code"
        ).return_value = build_code

        actual = GithubActionsCIAdapter().get_fallback_value(
            FallbackFieldEnum.build_url
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GithubActionsEnvEnum.GITHUB_RUN_ID: "random"}, "random"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, clear=True)

        actual = GithubActionsCIAdapter().get_fallback_value(
            FallbackFieldEnum.build_code
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GithubActionsEnvEnum.GITHUB_WORKFLOW: "random"}, "random"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, clear=True)

        actual = GithubActionsCIAdapter().get_fallback_value(FallbackFieldEnum.job_code)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GithubActionsEnvEnum.GITHUB_HEAD_REF: "aa"}, None),
            (
                {
                    GithubActionsEnvEnum.GITHUB_HEAD_REF: "aa",
                    GithubActionsEnvEnum.GITHUB_REF: "doesn't_match",
                },
                None,
            ),
            (
                {
                    GithubActionsEnvEnum.GITHUB_HEAD_REF: "aa",
                    GithubActionsEnvEnum.GITHUB_REF: "refs/pull//merge",
                },
                None,
            ),
            (
                {
                    GithubActionsEnvEnum.GITHUB_HEAD_REF: "aa",
                    GithubActionsEnvEnum.GITHUB_REF: "refs/pull/44/merge",
                },
                "44",
            ),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, clear=True)
        assert (
            GithubActionsCIAdapter().get_fallback_value(
                FallbackFieldEnum.pull_request_number
            )
            == expected
        )

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GithubActionsEnvEnum.GITHUB_REPOSITORY: "random"}, "random"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, clear=True)
        actual = GithubActionsCIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({GithubActionsEnvEnum.GITHUB_HEAD_REF: "random"}, "random"),
            ({GithubActionsEnvEnum.GITHUB_REF: r"doesn't_match"}, None),
            ({GithubActionsEnvEnum.GITHUB_REF: r"refs/heads/"}, None),
            ({GithubActionsEnvEnum.GITHUB_REF: r"refs/heads/abc"}, "abc"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict, clear=True)
        assert (
            GithubActionsCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
            == expected
        )

    def test_get_service(self, mocker):
        assert (
            GithubActionsCIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "github-actions"
        )
