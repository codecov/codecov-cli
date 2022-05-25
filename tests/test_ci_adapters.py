import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import (
    CircleCICIAdapter,
    GithubActionsCIAdapter,
    GitlabCIAdapter,
    get_ci_adapter,
)


class TestCISelector(object):
    def test_returns_none_if_name_is_invalid(self):
        assert get_ci_adapter("random ci adapter name") is None

    def test_returns_circleCI(self):
        assert type(get_ci_adapter("circleci")) is CircleCICIAdapter

    def test_returns_githubactions(self):
        assert type(get_ci_adapter("githubactions")) is GithubActionsCIAdapter

    def test_returns_gitlabCI(self):
        assert type(get_ci_adapter("gitlabCI")) is GitlabCIAdapter


class CircleCIEnvEnum(str, Enum):
    CIRCLE_SHA1 = "CIRCLE_SHA1"
    CIRCLE_BUILD_URL = "CIRCLE_BUILD_URL"
    CIRCLE_BUILD_NUM = "CIRCLE_BUILD_NUM"
    CIRCLE_NODE_INDEX = "CIRCLE_NODE_INDEX"
    CIRCLE_PR_NUMBER = "CIRCLE_PR_NUMBER"
    CIRCLE_PROJECT_USERNAME = "CIRCLE_PROJECT_USERNAME"
    CIRCLE_PROJECT_REPONAME = "CIRCLE_PROJECT_REPONAME"
    CIRCLE_REPOSITORY_URL = "CIRCLE_REPOSITORY_URL"
    CIRCLE_BRANCH = "CIRCLE_BRANCH"


class TestCircleCI(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_SHA1: "some_random_sha"}, "some_random_sha"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {CircleCIEnvEnum.CIRCLE_BUILD_URL: "test@test.org/test"},
                "test@test.org/test",
            ),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_BUILD_NUM: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.build_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_NODE_INDEX: "test_code"}, "test_code"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.job_code)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_PR_NUMBER: "random_number"}, "random_number"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    def test_slug_from_project_and_repo_names(self, mocker):
        project_username = "myname"
        repo_name = "myrepo123"
        mocker.patch.dict(
            os.environ,
            {
                CircleCIEnvEnum.CIRCLE_PROJECT_USERNAME: project_username,
                CircleCIEnvEnum.CIRCLE_PROJECT_REPONAME: repo_name,
            },
        )

        expected = f"{project_username}/{repo_name}"

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_slug_from_repo_url(self, mocker):
        repo_url = "git@github.com:codecov/codecov-cli.git"
        mocker.patch.dict(os.environ, {CircleCIEnvEnum.CIRCLE_REPOSITORY_URL: repo_url})

        expected = "codecov/codecov-cli"

        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_slug_doesnt_exist(self):
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual is None

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CircleCIEnvEnum.CIRCLE_BRANCH: "random"}, "random"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_raises_value_error_if_invalid_field(self):
        with pytest.raises(ValueError) as ex:
            CircleCICIAdapter().get_fallback_value("some random key x 123")

    def test_service(self):
        assert (
            CircleCICIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "circleci"
        )


class GithubActionsEnvEnum(str, Enum):
    GITHUB_SHA = "GITHUB_SHA"
    GITHUB_SERVER_URL = "GITHUB_SERVER_URL"
    GITHUB_RUN_ID = "GITHUB_RUN_ID"
    GITHUB_WORKFLOW = "GITHUB_WORKFLOW"
    GITHUB_HEAD_REF = "GITHUB_HEAD_REF"
    GITHUB_REF = "GITHUB_REF"
    GITHUB_REPOSITORY = "GITHUB_REPOSITORY"


class TestGithubActions(object):
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
            "codecov_cli.helpers.ci_adapters.subprocess.run",
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
            "codecov_cli.helpers.ci_adapters.subprocess.run",
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


class TestGitlabCI(object):
    class EnvEnum(str, Enum):
        CI_MERGE_REQUEST_SOURCE_BRANCH_SHA = "CI_MERGE_REQUEST_SOURCE_BRANCH_SHA"
        CI_BUILD_REF = "CI_BUILD_REF"
        CI_COMMIT_REF_NAME = "CI_COMMIT_REF_NAME"
        CI_BUILD_REF_NAME = "CI_BUILD_REF_NAME"
        CI_REPOSITORY_URL = "CI_REPOSITORY_URL"
        CI_BUILD_REPO = "CI_BUILD_REPO"
        CI_PROJECT_PATH = "CI_PROJECT_PATH"
        CI_JOB_ID = "CI_JOB_ID"
        CI_BUILD_ID = "CI_BUILD_ID"
        CI_JOB_URL = "CI_JOB_URL"
        CI_COMMIT_SHA = "CI_COMMIT_SHA"

    def test_commit_sha(self, mocker):
        mocker.patch.dict(os.environ, {self.EnvEnum.CI_COMMIT_SHA: "1234"})
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha) == "1234"
        )

        mocker.patch.dict(os.environ, {self.EnvEnum.CI_BUILD_REF: "44"})
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha) == "44"
        )

        mocker.patch.dict(
            os.environ, {self.EnvEnum.CI_MERGE_REQUEST_SOURCE_BRANCH_SHA: "11"}
        )
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.commit_sha) == "11"
        )

    def test_build_url(self, mocker):
        mocker.patch.dict(os.environ, {self.EnvEnum.CI_JOB_URL: "test@test.org"})
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.build_url)
            == "test@test.org"
        )

    def test_build_code(self, mocker):
        mocker.patch.dict(os.environ, {self.EnvEnum.CI_JOB_ID: "123"})
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.build_code) == "123"
        )

        mocker.patch.dict(os.environ, {self.EnvEnum.CI_BUILD_ID: "44"})
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.build_code) == "44"
        )

    def test_job_code(self, mocker):
        assert GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.job_code) is None

    def test_pull_request_number(self, mocker):
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.pull_request_number)
            is None
        )

    def test_slug(self, mocker):
        assert GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.slug) is None

        mocker.patch.dict(
            os.environ,
            {self.EnvEnum.CI_BUILD_REPO: "git@github.com:codecov/codecov-cli.git"},
        )

        mocker.patch(
            f"codecov_cli.helpers.ci_adapters.parse_slug",
            return_value="codecov/codecov-cli",
        )

        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.slug)
            == "codecov/codecov-cli"
        )

        mocker.patch.dict(os.environ, {self.EnvEnum.CI_PROJECT_PATH: "123"})
        assert GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.slug) == "123"

    def test_branch(self, mocker):
        mocker.patch.dict(os.environ, {self.EnvEnum.CI_COMMIT_REF_NAME: "aa"})
        assert GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.branch) == "aa"

        mocker.patch.dict(os.environ, {self.EnvEnum.CI_BUILD_REF_NAME: "bb"})
        assert GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.branch) == "bb"

    def test_service(self, mocker):
        assert (
            GitlabCIAdapter().get_fallback_value(FallbackFieldEnum.service) == "gitlab"
        )
