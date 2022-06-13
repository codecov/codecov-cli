import re
from urllib.parse import urlparse

slug_regex = re.compile(r"[^/\s]+\/[^/\s]+$")


def parse_slug(remote_repo_url: str):
    """
    Extracts a slug from git remote urls. returns None if the url is invalid

    Examples:
    - https://github.com/codecov/codecov-cli.git returns codecov/codecov-cli
    - git@github.com:codecov/codecov-cli.git returns codecov/codecov-cli
    """
    parsed_url = urlparse(remote_repo_url)

    path_to_parse = parsed_url.path

    if path_to_parse.endswith("/"):
        path_to_parse = path_to_parse.rsplit("/", 1)[0]
    if path_to_parse.endswith(".git"):
        path_to_parse = path_to_parse.rsplit(".git", 1)[0]
    if ":" in path_to_parse:
        path_to_parse = path_to_parse.split(":", 1)[1]
    if path_to_parse.startswith("/"):
        path_to_parse = path_to_parse[1:]

    if not slug_regex.match(path_to_parse):
        return None

    return path_to_parse
