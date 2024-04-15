import logging
import re
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

from codecov_cli.helpers.encoder import decode_slug
from codecov_cli.helpers.git_services import PullDict
from codecov_cli.helpers.git_services.github import Github

slug_regex = re.compile(r"[^/\s]+\/[^/\s]+$")

logger = logging.getLogger("codecovcli")


class GitService(Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    GITHUB_ENTERPRISE = "github_enterprise"
    GITLAB_ENTERPRISE = "gitlab_enterprise"
    BITBUCKET_SERVER = "bitbucket_server"


def get_git_service(git):
    if git == "github":
        return Github()


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


def parse_git_service(remote_repo_url: str):
    """
    Extracts git service from git remote urls. returns None if the url is invalid

    Possible cases we're considering:
    - https://github.com/codecov/codecov-cli.git returns github
    - git@github.com:codecov/codecov-cli.git returns github
    - ssh://git@github.com/gitcodecov/codecov-cli returns github
    - ssh://git@github.com:gitcodecov/codecov-cli returns github
    - https://user-name@bitbucket.org/namespace-codecov/first_repo.git returns bitbucket
    """
    services = [service.value for service in GitService]
    parsed_url = urlparse(remote_repo_url)
    service = None

    scheme = parsed_url.scheme
    if scheme in ("https", "ssh"):
        netloc = parsed_url.netloc
        if "@" in netloc:
            netloc = netloc.split("@", 1)[1]
        if "." in netloc:
            netloc = netloc.split(".", 1)[0]
        service = netloc
    elif remote_repo_url.startswith("git@"):
        path = parsed_url.path
        if "@" in path:
            path = path.split("@", 1)[1]
        if ":" in path:
            path = path.split(":", 1)[0]
        if "." in path:
            path = path.split(".", 1)[0]
        service = path

    if service in services:
        return service
    else:
        logger.warning(
            f"Service not found: {service}. Possible services are {services}",
            extra=dict(remote_repo_url=remote_repo_url),
        )
        return None


def is_fork_pr(pull_dict: PullDict) -> bool:
    """
    takes in dict: pull_dict
    returns true if PR is made in a fork context, false if not.
    """
    return pull_dict and pull_dict["head"]["slug"] != pull_dict["base"]["slug"]


def get_pull(service, slug, pr_num) -> Optional[PullDict]:
    """
    takes in str git service e.g. github, gitlab etc., slug in the owner/repo format, and the pull request number
    returns the pull request info gotten from the git service provider if successful, None if not
    """
    git_service = get_git_service(service)
    if git_service:
        pull_dict = git_service.get_pull_request(slug, pr_num)
        return pull_dict
