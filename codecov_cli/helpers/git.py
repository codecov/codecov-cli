from urllib.parse import urlparse


def parse_slug(remote_repo_url: str):
    """
    Extracts a slug from git remote urls

    Examples:
    - https://github.com/codecov/codecov-cli.git returns codecov/codecov-cli
    - git@github.com:codecov/codecov-cli.git returns codecov/codecov-cli
    """
    parsed_url = urlparse(remote_repo_url)

    slug = parsed_url.path

    if slug.endswith(".git"):
        slug = slug.rsplit(".git", 1)[0]
    if slug.startswith("git@"):
        slug = slug.split(":", 1)[1]

    if slug.startswith("/"):
        slug = slug[1:]

    return slug
