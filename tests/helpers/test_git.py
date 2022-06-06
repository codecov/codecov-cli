import pytest

from codecov_cli.helpers import git


@pytest.mark.parametrize(
    "address,slug",
    [
        ("https://github.com/codecov/codecov-cli", "codecov/codecov-cli"),
        ("https://github.com/codecov/codecov-cli.git", "codecov/codecov-cli"),
        ("git@github.com:codecov/codecov-cli.git", "codecov/codecov-cli"),
        ("git@gitlab.com:gitlab-org/gitlab.git", "gitlab-org/gitlab"),
        ("https://gitlab.com/gitlab-org/gitlab.git", "gitlab-org/gitlab"),
        ("git@github.com:gitcodecov/codecov-cli", "gitcodecov/codecov-cli"),
        ("git@github.com:git-codecov/codecov-cli", "git-codecov/codecov-cli"),
        ("git@github.com:git-codecov/codecov-cli-git", "git-codecov/codecov-cli-git"),
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
        ("random string")
    ],
)
def test_parse_slug_invalid_address(address):
    assert git.parse_slug(address) is None