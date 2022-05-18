import pytest

from codecov_cli.helpers import git


@pytest.mark.parametrize(
    "address",
    [
        ("origin    https://github.com/codecov/codecov-cli.git (fetch)"),
        ("https://github.com/codecov/codecov-cli.git"),
        ("origin  git@github.com:codecov/codecov-cli.git (fetch)"),
        ("git@github.com:codecov/codecov-cli.git"),
    ],
)
def test_parse_slug_valid_address(address):
    assert git.parse_slug(address) == "codecov/codecov-cli"


@pytest.mark.parametrize(
    "address",
    [("https://github.com"), ("test@test.org"), ("aa")],
)
def test_parse_slug_invalid_address(address):
    with pytest.raises(ValueError):
        assert git.parse_slug(address)
