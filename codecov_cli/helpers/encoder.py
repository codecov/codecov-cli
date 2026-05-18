import re

slug_without_subgroups_regex = re.compile(r"[^/\s]+\/[^/\s]+$")
slug_with_subgroups_regex = re.compile(r"[^/\s]+(\/[^/\s]+)+$")
encoded_slug_regex = re.compile(r"[^:\s]+(:::[^:\s]+)*(::::[^:\s]+){1}$")


def encode_slug(slug: str):
    if slug_with_subgroups_is_invalid(slug):
        raise ValueError("The provided slug is invalid")
    owner, repo = slug.rsplit("/", 1)
    encoded_owner = ":::".join(owner.split("/"))
    encoded_slug = "::::".join([encoded_owner, repo])
    return encoded_slug


def decode_slug(slug: str):
    if slug_encoded_incorrectly(slug):
        raise ValueError("The slug is not encoded correctly")

    owner, repo = slug.split("::::", 1)
    decoded_owner = "/".join(owner.split(":::"))
    decoded_slug = "/".join([decoded_owner, repo])
    return decoded_slug


def slug_without_subgroups_is_invalid(slug: str):
    """
    Checks if slug is in the form of owner/repo
    Returns True if it's invalid, otherwise return False
    """
    return not slug or not slug_without_subgroups_regex.match(slug)


def slug_with_subgroups_is_invalid(slug: str):
    """
    Checks if slug is in the form of owner/repo or owner/subgroup/repo
    Returns True if it's invalid, otherwise return False
    """
    return not slug or not slug_with_subgroups_regex.match(slug)


def slug_encoded_incorrectly(slug: str):
    """
    Checks if slug is encoded incorrectly based on the encoding mechanism we use.
    Checks if slug is in the form of owner:::subowner::::repo or owner::::repo
    Returns True if invalid, otherwise returns False
    """
    return not slug or not encoded_slug_regex.match(slug)
