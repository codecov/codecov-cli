import logging

from codecov_cli.helpers.ci_adapters.appveyor_ci import AppveyorCIAdapter
from codecov_cli.helpers.ci_adapters.azure_pipelines import AzurePipelinesCIAdapter
from codecov_cli.helpers.ci_adapters.bitbucket_ci import BitbucketAdapter
from codecov_cli.helpers.ci_adapters.bitrise_ci import BitriseCIAdapter
from codecov_cli.helpers.ci_adapters.buildkite import BuildkiteAdapter
from codecov_cli.helpers.ci_adapters.circleci import CircleCICIAdapter
from codecov_cli.helpers.ci_adapters.cirrus_ci import CirrusCIAdapter
from codecov_cli.helpers.ci_adapters.droneci import DroneCIAdapter
from codecov_cli.helpers.ci_adapters.github_actions import GithubActionsCIAdapter
from codecov_cli.helpers.ci_adapters.gitlab_ci import GitlabCIAdapter
from codecov_cli.helpers.ci_adapters.heroku import HerokuCIAdapter
from codecov_cli.helpers.ci_adapters.jenkins import JenkinsAdapter
from codecov_cli.helpers.ci_adapters.local import LocalAdapter
from codecov_cli.helpers.ci_adapters.woodpeckerci import WoodpeckerCIAdapter

logger = logging.getLogger("codecovcli")


def get_ci_adapter(provider_name: str = None):
    if provider_name:
        for provider in get_ci_providers_list():
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
            if provider_name == "local":
                return LocalAdapter()
            if provider_name == "woodpecker":
                return WoodpeckerCIAdapter()
            if provider_name == "heroku":
                return HerokuCIAdapter()
            if provider_name == "droneci":
                return DroneCIAdapter()
            if provider_name == "buildkite":
                return BuildkiteAdapter()
            if provider_name == "azurepipelines":
                return AzurePipelinesCIAdapter()
            if provider_name == "jenkins":
                return JenkinsAdapter()
            if provider_name == "cirrusci":
                return CirrusCIAdapter()
    else:
        for provider in get_ci_providers_list():
            if provider.detect():
                logger.info(f"Found ci service {provider._get_service()}")
                return provider
    return None


def get_ci_providers_list():
    return [
        CircleCICIAdapter(),
        GithubActionsCIAdapter(),
        GitlabCIAdapter(),
        BitbucketAdapter(),
        BitriseCIAdapter(),
        AppveyorCIAdapter(),
        WoodpeckerCIAdapter(),
        HerokuCIAdapter(),
        DroneCIAdapter(),
        BuildkiteAdapter(),
        AzurePipelinesCIAdapter(),
        JenkinsAdapter(),
        CirrusCIAdapter(),
        # local adapter should always be the last one
        LocalAdapter(),
    ]
