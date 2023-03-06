import logging

from codecov_cli.helpers.ci_adapters.appveyor_ci import AppveyorCIAdapter
from codecov_cli.helpers.ci_adapters.azure_pipelines import AzurePipelinesCIAdapter
from codecov_cli.helpers.ci_adapters.bitbucket_ci import BitbucketAdapter
from codecov_cli.helpers.ci_adapters.bitrise_ci import BitriseCIAdapter
from codecov_cli.helpers.ci_adapters.buildkite import BuildkiteAdapter
from codecov_cli.helpers.ci_adapters.circleci import CircleCICIAdapter
from codecov_cli.helpers.ci_adapters.cirrus_ci import CirrusCIAdapter
from codecov_cli.helpers.ci_adapters.codebuild import AWSCodeBuildCIAdapter
from codecov_cli.helpers.ci_adapters.droneci import DroneCIAdapter
from codecov_cli.helpers.ci_adapters.github_actions import GithubActionsCIAdapter
from codecov_cli.helpers.ci_adapters.gitlab_ci import GitlabCIAdapter
from codecov_cli.helpers.ci_adapters.heroku import HerokuCIAdapter
from codecov_cli.helpers.ci_adapters.jenkins import JenkinsAdapter
from codecov_cli.helpers.ci_adapters.local import LocalAdapter
from codecov_cli.helpers.ci_adapters.teamcity import TeamcityAdapter
from codecov_cli.helpers.ci_adapters.travis_ci import TravisCIAdapter
from codecov_cli.helpers.ci_adapters.woodpeckerci import WoodpeckerCIAdapter

logger = logging.getLogger("codecovcli")


def get_ci_adapter(provider_name: str = None):
    if provider_name:
        for provider in get_ci_providers_list():
            if provider.get_service_name().lower() == provider_name.lower():
                logger.debug(f"Using ci service from provider name: {provider_name}")
                return provider
    else:
        for provider in get_ci_providers_list():
            if provider.detect():
                logger.info(f"ci service found: {provider._get_service()}")
                return provider
    logger.warning("No ci adapter found")
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
        TeamcityAdapter(),
        TravisCIAdapter(),
        AWSCodeBuildCIAdapter(),
        # local adapter should always be the last one
        LocalAdapter(),
    ]
