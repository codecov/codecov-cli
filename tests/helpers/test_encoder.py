import pytest

from codecov_cli.helpers.encoder import encode_slug


def test_invalid_slug():
    slug = "invalid-slug"
    with pytest.raises(ValueError) as ex:
        encode_slug(slug)


def test_owner_repo_slug():
    slug = "owner/repo"
    encoded_slug = encode_slug(slug)
    assert encoded_slug == "owner::::repo"


def test_owner_with_subgroups_slug():
    slug = "owner/subgroup/repo"
    encoded_slug = encode_slug(slug)
    assert encoded_slug == "owner:::subgroup::::repo"
