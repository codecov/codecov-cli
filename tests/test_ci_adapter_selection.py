import os

from codecov_cli.helpers.ci_adapters import (
    AppveyorCIAdapter,
    AWSCodeBuildCIAdapter,
    AzurePipelinesCIAdapter,
    BitbucketAdapter,
    BitriseCIAdapter,
    BuildkiteAdapter,
    CircleCICIAdapter,
    CirrusCIAdapter,
    DroneCIAdapter,
    GithubActionsCIAdapter,
    GitlabCIAdapter,
    HerokuCIAdapter,
    JenkinsAdapter,
    LocalAdapter,
    TeamcityAdapter,
    TravisCIAdapter,
    WoodpeckerCIAdapter,
    get_ci_adapter,
)


class TestCISelector(object):
    def test_returns_none_if_name_is_invalid(self):
        assert get_ci_adapter("random ci adapter name") is None

    def test_returns_circleCI(self):
        assert isinstance(get_ci_adapter("circleci"), CircleCICIAdapter)

    def test_returns_githubactions(self):
        assert isinstance(get_ci_adapter("githubactions"), GithubActionsCIAdapter)

    def test_returns_gitlabCI(self):
        assert isinstance(get_ci_adapter("gitlabCI"), GitlabCIAdapter)

    def test_returns_bitbucket(self):
        assert isinstance(get_ci_adapter("bitbucket"), BitbucketAdapter)

    def test_returns_bitrise(self):
        assert isinstance(get_ci_adapter("bitrise"), BitriseCIAdapter)

    def test_returns_appveyor(self):
        assert isinstance(get_ci_adapter("appveyor"), AppveyorCIAdapter)

    def test_returns_local(self):
        assert isinstance(get_ci_adapter("local"), LocalAdapter)

    def test_returns_woodpecker(self):
        assert isinstance(get_ci_adapter("woodpecker"), WoodpeckerCIAdapter)

    def test_returns_teamcity(self):
        assert isinstance(get_ci_adapter("teamcity"), TeamcityAdapter)

    def test_returns_herokuci(self):
        assert isinstance(get_ci_adapter("heroku"), HerokuCIAdapter)

    def test_returns_travis(self):
        assert isinstance(get_ci_adapter("travis"), TravisCIAdapter)

    def test_returns_droneci(self):
        assert isinstance(get_ci_adapter("droneci"), DroneCIAdapter)

    def test_returns_buildkite(self):
        assert isinstance(get_ci_adapter("buildkite"), BuildkiteAdapter)

    def test_returns_azurepipelines(self):
        assert isinstance(get_ci_adapter("azurepipelines"), AzurePipelinesCIAdapter)

    def test_returns_jenkins(self):
        assert isinstance(get_ci_adapter("jenkins"), JenkinsAdapter)

    def test_returns_cirrusci(self):
        assert isinstance(get_ci_adapter("cirrusci"), CirrusCIAdapter)

    def test_returns_codebuild(self):
        assert isinstance(get_ci_adapter("AWScodebuild"), AWSCodeBuildCIAdapter)

    def test_auto_return_gh_actions(self, mocker):
        mocker.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True)
        assert isinstance(get_ci_adapter(), GithubActionsCIAdapter)

    def test_auto_return_circle_ci(self, mocker):
        mocker.patch.dict(os.environ, {"CIRCLECI": "true", "CI": "true"}, clear=True)
        assert isinstance(get_ci_adapter(), CircleCICIAdapter)
