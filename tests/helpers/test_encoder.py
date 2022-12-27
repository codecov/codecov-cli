import pytest

from codecov_cli.helpers.encoder import encode_slug, slug_is_invalid


def test_invalid_slug():
    slug = "invalid-slug"
    with pytest.raises(ValueError) as ex:
        encode_slug(slug)


def test_encode_slug():
    slug = "owner/repo"
    encoded_slug = encode_slug(slug)
    assert encoded_slug == "owner::::repo"


def test_encode_owner_with_subgroups_slug():
    slug = "owner/subgroup/repo"
    encoded_slug = encode_slug(slug)
    assert encoded_slug == "owner:::subgroup::::repo"


def test_invalid_slug2():
    slug = "invalid_slug"
    assert slug_is_invalid(slug)


def test_valid_slug():
    slug = "owner/repo"
    assert not slug_is_invalid(slug)
