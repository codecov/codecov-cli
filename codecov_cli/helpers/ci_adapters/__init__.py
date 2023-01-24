from codecov_cli.helpers.ci_adapters.appveyor_ci import AppveyorCIAdapter
from codecov_cli.helpers.ci_adapters.circleci import CircleCICIAdapter
from codecov_cli.helpers.ci_adapters.github_actions import GithubActionsCIAdapter
from codecov_cli.helpers.ci_adapters.gitlab_ci import GitlabCIAdapter
from codecov_cli.helpers.ci_adapters.local import LocalAdapter


def get_ci_adapter(provider_name):
    if provider_name == "circleci":
        return CircleCICIAdapter()
    if provider_name == "githubactions":
        return GithubActionsCIAdapter()
    if provider_name == "gitlabCI":
        return GitlabCIAdapter()
    if provider_name == "appveyor":
        return AppveyorCIAdapter()
    if provider_name == "local":
        return LocalAdapter()
    return None
