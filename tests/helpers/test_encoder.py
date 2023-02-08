import pytest

from codecov_cli.helpers.encoder import encode_slug, slug_without_subgroups_is_invalid


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
    with pytest.raises(ValueError) as ex:
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
