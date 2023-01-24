from codecov_cli.helpers.ci_adapters.appveyor_ci import AppveyorCIAdapter
from codecov_cli.helpers.ci_adapters.bitbucket_ci import BitbucketAdapter
from codecov_cli.helpers.ci_adapters.bitrise_ci import BitriseCIAdapter
from codecov_cli.helpers.ci_adapters.circleci import CircleCICIAdapter
from codecov_cli.helpers.ci_adapters.github_actions import GithubActionsCIAdapter
from codecov_cli.helpers.ci_adapters.gitlab_ci import GitlabCIAdapter
from codecov_cli.helpers.ci_adapters.heroku import HerokuCIAdapter


def get_ci_adapter(provider_name):
    if provider_name == "circleci":
        return CircleCICIAdapter()
    if provider_name == "githubactions":
        return GithubActionsCIAdapter()
    if provider_name == "gitlabCI":
        return GitlabCIAdapter()
    if provider_name == "bitbucket":
        return BitbucketAdapter()
    if provider_name == "bitrise":
        return BitriseCIAdapter()
    if provider_name == "appveyor":
        return AppveyorCIAdapter()
    if provider_name == "heroku":
        return HerokuCIAdapter()
    return None
