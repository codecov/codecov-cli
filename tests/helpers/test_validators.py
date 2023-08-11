from unittest.mock import MagicMock

import click
import pytest

from codecov_cli.helpers.validators import validate_commit_sha


@pytest.mark.parametrize(
    "input,should_raise",
    [
        (
            None,
            True,
        ),
        (
            "",
            True,
        ),
        ("f39802d4", True),
        ("!39802d4d87---de18968d1753dd4a6402866  7", True),
        ("f39802d4d87508de18968d1753dd4a64028662b7", False),
    ],
)
def test_commit_validator(input, should_raise):
    if should_raise:
        with pytest.raises(click.BadParameter):
            validate_commit_sha(MagicMock(), "commit_sha", input)
    else:
        assert validate_commit_sha(MagicMock(), "commit_sha", input) == input
