import json

import pytest
import requests
from requests import Response

from codecov_cli.helpers import git
from codecov_cli.helpers.git_services.github import Github


@pytest.mark.parametrize(
    "address,slug",
    [
        ("https://github.com/codecov/codecov-cli/", "codecov/codecov-cli"),
        ("https://github.com/codecov/codecov-cli.git/", "codecov/codecov-cli"),
        ("https://gitlab.com/gitlab-org/gitlab.git", "gitlab-org/gitlab"),
        (
            "https://user-name@bitbucket.org/namespace-codecov/first_repo.git",
            "namespace-codecov/first_repo",
        ),
        ("http://host.xz:40/owner/repo.git/", "owner/repo"),
        (
            "https://username-codecov@bitbucket.org/username-codecov/fasdf.git.git",
            "username-codecov/fasdf.git",  # bitbucket allows repo name to end with ".git"
        ),
        (
            "https://username-codecov@bitbucket.org/username-codecov/fasdf.git.git.git",
            "username-codecov/fasdf.git.git",
        ),
        (
            "https://gitlab-ci-token:testtokenaaabbbccc@gitlab.com/abc_xyz/testing_env_vars.git",
            "abc_xyz/testing_env_vars",
        ),
        ("git@github.com:codecov/codecov-cli.git/", "codecov/codecov-cli"),
        ("git@gitlab.com:gitlab-org/gitlab.git", "gitlab-org/gitlab"),
        ("git@github.com:gitcodecov/codecov-cli", "gitcodecov/codecov-cli"),
        ("git@github.com:git-codecov/codecov-cli", "git-codecov/codecov-cli"),
        ("git@github.com:git-codecov/codecov-cli-git", "git-codecov/codecov-cli-git"),
        ("git@github.com:codecov/git.", "codecov/git."),
        (
            "git@bitbucket.org:namespace-codecov/first_repo.git",
            "namespace-codecov/first_repo",
        ),
        ("git@bitbucket.org:name-codecov/abc.git.git", "name-codecov/abc.git"),
        ("git://host.xz:80/path/repo.git/", "path/repo"),
        ("git://host.xz:80/path/repo.git", "path/repo"),
        ("git://host.xz.abc/owner/repo.git", "owner/repo"),
        (
            "ssh://user-abc@host.xz:port/owner-xyz_abc/repo_123.git/",
            "owner-xyz_abc/repo_123",
        ),
        ("ssh://host.abc.xz/owner/repo.git/", "owner/repo"),
        ("ssh://host.abc.xz/owner/repo.git", "owner/repo"),
        ("user-name@host.xz:owner/repo.git/", "owner/repo"),
        ("host.xz:owner/repo.git/", "owner/repo"),
        ("ssh://git@github.com/gitcodecov/codecov-cli", "gitcodecov/codecov-cli"),
    ],
)
def test_parse_slug_valid_address(address, slug):
    assert git.parse_slug(address) == slug


@pytest.mark.parametrize(
    "address",
    [
        ("https://github.com/codecov"),
        ("https://github.com/codecov.git"),
        ("git@github.com:codecov"),
        ("git@github.com:codecov.git"),
        ("https://www.google.com"),
        ("random string"),
    ],
)
def test_parse_slug_invalid_address(address):
    assert git.parse_slug(address) is None


@pytest.mark.parametrize(
    "address,git_service",
    [
        ("https://github.com/codecov/codecov-cli/", "github"),
        ("https://github.com/codecov/codecov-cli.git/", "github"),
        ("https://gitlab.com/gitlab-org/gitlab.git", "gitlab"),
        (
            "https://user-name@bitbucket.org/namespace-codecov/first_repo.git",
            "bitbucket",
        ),
        (
            "https://username-codecov@bitbucket.org/username-codecov/fasdf.git.git",
            "bitbucket",
        ),
        (
            "https://username-codecov@bitbucket.org/username-codecov/fasdf.git.git.git",
            "bitbucket",
        ),
        (
            "https://gitlab-ci-token:testtokenaabbcc@gitlab.com/abc_xyz/testing_env_vars.git",
            "gitlab",
        ),
        ("git@github.com:codecov/codecov-cli.git/", "github"),
        ("git@gitlab.com:gitlab-org/gitlab.git", "gitlab"),
        ("git@github.com:gitcodecov/codecov-cli", "github"),
        ("git@github.com:git-codecov/codecov-cli", "github"),
        ("git@github.com:git-codecov/codecov-cli-git", "github"),
        ("git@github.com:codecov/git.", "github"),
        (
            "git@bitbucket.org:namespace-codecov/first_repo.git",
            "bitbucket",
        ),
        ("git@bitbucket.org:name-codecov/abc.git.git", "bitbucket"),
        ("ssh://git@github.com/gitcodecov/codecov-cli", "github"),
        ("ssh://git@github.com:gitcodecov/codecov-cli", "github"),
    ],
)
def test_parse_git_service_valid_address(address, git_service):
    assert git.parse_git_service(address) == git_service


@pytest.mark.parametrize(
    "url",
    [
        ("ssh://host.abc.xz/owner/repo.git/"),
        ("ssh://host.abc.xz/owner/repo.git"),
        ("user-name@host.xz:owner/repo.git/"),
        ("host.xz:owner/repo.git/"),
    ],
)
def test_parse_git_service_invalid_service(url):
    assert git.parse_git_service(url) is None


def test_get_git_service_class():
    assert isinstance(git.get_git_service("github"), Github)
    assert git.get_git_service("gitlab") == None
    assert git.get_git_service("bitbucket") == None


def test_pr_is_not_fork_pr(mocker):
    def mock_request(*args, headers={}, **kwargs):
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
        res = {
            "url": "https://api.github.com/repos/codecov/codecov-cli/pulls/1",
            "head": {
                "sha": "123",
                "label": "codecov-cli:branch",
                "ref": "branch",
                "repo": {"full_name": "codecov/codecov-cli"},
            },
            "base": {
                "sha": "123",
                "label": "codecov-cli:main",
                "ref": "main",
                "repo": {"full_name": "codecov/codecov-cli"},
            },
        }
        response = Response()
        response.status_code = 200
        response._content = json.dumps(res).encode("utf-8")
        return response

    mocker.patch.object(
        requests,
        "get",
        side_effect=mock_request,
    )
    pull_dict = git.get_pull("github", "codecov/codecov-cli", 1)
    assert not git.is_fork_pr(pull_dict)


def test_pr_is_fork_pr(mocker):
    def mock_request(*args, headers={}, **kwargs):
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
        res = {
            "url": "https://api.github.com/repos/codecov/codecov-cli/pulls/1",
            "head": {
                "sha": "123",
                "label": "codecov-cli:branch",
                "ref": "branch",
                "repo": {"full_name": "user_forked_repo/codecov-cli"},
            },
            "base": {
                "sha": "123",
                "label": "codecov-cli:main",
                "ref": "main",
                "repo": {"full_name": "codecov/codecov-cli"},
            },
        }
        response = Response()
        response.status_code = 200
        response._content = json.dumps(res).encode("utf-8")
        return response

    mocker.patch.object(
        requests,
        "get",
        side_effect=mock_request,
    )
    pull_dict = git.get_pull("github", "codecov/codecov-cli", 1)
    assert git.is_fork_pr(pull_dict)


def test_pr_not_found(mocker):
    def mock_request(*args, headers={}, **kwargs):
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
        response = Response()
        response.status_code = 404
        response._content = b"not-found"
        return response

    mocker.patch.object(
        requests,
        "get",
        side_effect=mock_request,
    )
    pull_dict = git.get_pull("github", "codecov/codecov-cli", 1)
    assert not git.is_fork_pr(pull_dict)
