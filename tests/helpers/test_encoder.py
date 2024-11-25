import pytest

from codecov_cli.helpers.encoder import (
    decode_slug,
    encode_slug,
    slug_encoded_incorrectly,
    slug_without_subgroups_is_invalid,
)


@pytest.mark.parametrize(
    "slug",
    [
        ("invalid_slug"),
        (""),
        ("/"),
        ("//"),
        ("///"),
        ("random string"),
        (None),
    ],
)
def test_encode_invalid_slug(slug):
    with pytest.raises(ValueError):
        encode_slug(slug)


@pytest.mark.parametrize(
    "slug, encoded_slug",
    [
        ("owner/repo", "owner::::repo"),
        ("owner/subgroup/repo", "owner:::subgroup::::repo"),
    ],
)
def test_encode_valid_slug(slug, encoded_slug):
    expected_encoded_slug = encode_slug(slug)
    assert expected_encoded_slug == encoded_slug


@pytest.mark.parametrize(
    "slug",
    [
        ("invalid_slug"),
        (""),
        ("/"),
        ("//"),
        ("///"),
        ("random string"),
        ("owner/subgroup/repo"),
        ("owner//repo"),
        (None),
    ],
)
def test_invalid_slug(slug):
    assert slug_without_subgroups_is_invalid(slug)


def test_valid_slug():
    slug = "owner/repo"
    assert not slug_without_subgroups_is_invalid(slug)


@pytest.mark.parametrize(
    "slug",
    [
        ("invalid_slug"),
        (""),
        (":"),
        (":::"),
        ("::::"),
        ("random string"),
        ("owner:::subgroup:::repo"),
        ("owner:::repo"),
        ("owner::::subgroup::::repo"),
        (None),
    ],
)
def test_invalid_encoded_slug(slug):
    assert slug_encoded_incorrectly(slug)
    with pytest.raises(ValueError):
        decode_slug(slug)


@pytest.mark.parametrize(
    "encoded_slug",
    [
        ("owner::::repo"),
        ("owner:::subgroup::::repo"),
    ],
)
def test_valid_encoded_slug(encoded_slug):
    assert not slug_encoded_incorrectly(encoded_slug)


@pytest.mark.parametrize(
    "encoded_slug, decoded_slug",
    [
        ("owner::::repo", "owner/repo"),
        ("owner:::subgroup::::repo", "owner/subgroup/repo"),
    ],
)
def test_decode_slug(encoded_slug, decoded_slug):
    expected_encoded_slug = decode_slug(encoded_slug)
    assert expected_encoded_slug == decoded_slug
