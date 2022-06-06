import re
from urllib.parse import urlparse

slug_regex = re.compile("[^/\s]+\/[^/\s]+$")


def parse_slug(remote_repo_url: str):
    """
    Extracts a slug from git remote urls. returns None if the url is invalid

    Examples:
    - https://github.com/codecov/codecov-cli.git returns codecov/codecov-cli
    - git@github.com:codecov/codecov-cli.git returns codecov/codecov-cli
    """
    parsed_url = urlparse(remote_repo_url)

    slug = parsed_url.path

    try:
        if slug.endswith(".git"):
            slug = slug.rsplit(".git", 1)[0]
        if slug.startswith("git@"):
            slug = slug.split(":", 1)[1]

        if slug.startswith("/"):
            slug = slug[1:]
    except IndexError:
        return None
    
    if not slug_regex.match(slug):
        return None

    return slug
