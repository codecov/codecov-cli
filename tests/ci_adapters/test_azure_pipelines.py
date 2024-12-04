import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.azure_pipelines import AzurePipelinesCIAdapter


class AzurePipelinesEnvEnum(str, Enum):
    BUILD_BUILDID = "BUILD_BUILDID"
    BUILD_BUILDNUMBER = "BUILD_BUILDNUMBER"
    BUILD_SOURCEBRANCH = "BUILD_SOURCEBRANCH"
    BUILD_SOURCEVERSION = "BUILD_SOURCEVERSION"
    SYSTEM_PULLREQUEST_PULLREQUESTID = "SYSTEM_PULLREQUEST_PULLREQUESTID"
    SYSTEM_PULLREQUEST_PULLREQUESTNUMBER = "SYSTEM_PULLREQUEST_PULLREQUESTNUMBER"
    SYSTEM_PULLREQUEST_SOURCECOMMITID = "SYSTEM_PULLREQUEST_SOURCECOMMITID"
    SYSTEM_TEAMFOUNDATIONCOLLECTIONURI = "SYSTEM_TEAMFOUNDATIONCOLLECTIONURI"
    SYSTEM_TEAMPROJECT = "SYSTEM_TEAMPROJECT"
    BUILD_REPOSITORY_NAME = "BUILD_REPOSITORY_NAME"


class TestAzurePipelines(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {AzurePipelinesEnvEnum.SYSTEM_TEAMFOUNDATIONCOLLECTIONURI: "1234"},
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {AzurePipelinesEnvEnum.BUILD_SOURCEVERSION: "123456789000111"},
                "123456789000111",
            ),
            (
                {
                    AzurePipelinesEnvEnum.BUILD_SOURCEVERSION: "123456789000111",
                    AzurePipelinesEnvEnum.SYSTEM_PULLREQUEST_SOURCECOMMITID: "111000987654321",
                },
                "111000987654321",
            ),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().get_fallback_value(
            FallbackFieldEnum.commit_sha
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    AzurePipelinesEnvEnum.SYSTEM_TEAMPROJECT: "test_project",
                    AzurePipelinesEnvEnum.BUILD_BUILDID: "2",
                    AzurePipelinesEnvEnum.SYSTEM_TEAMFOUNDATIONCOLLECTIONURI: "https://dev.azure.com/fabrikamfiber/",
                },
                "https://dev.azure.com/fabrikamfiber/test_project/_build/results?buildId=2",
            ),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().get_fallback_value(
            FallbackFieldEnum.build_url
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AzurePipelinesEnvEnum.BUILD_BUILDNUMBER: "123"}, "123"),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().get_fallback_value(
            FallbackFieldEnum.build_code
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AzurePipelinesEnvEnum.BUILD_BUILDID: "123"}, "123"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().get_fallback_value(
            FallbackFieldEnum.job_code
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {AzurePipelinesEnvEnum.SYSTEM_PULLREQUEST_PULLREQUESTNUMBER: "123"},
                "123",
            ),
            ({AzurePipelinesEnvEnum.SYSTEM_PULLREQUEST_PULLREQUESTID: "111"}, "111"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AzurePipelinesEnvEnum.BUILD_REPOSITORY_NAME: "owner/repo"}, "owner/repo"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().get_fallback_value(FallbackFieldEnum.slug)
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({AzurePipelinesEnvEnum.BUILD_SOURCEBRANCH: "refs/heads/main"}, "main"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = AzurePipelinesCIAdapter().get_fallback_value(FallbackFieldEnum.branch)
        assert actual == expected

    def test_service(self):
        assert (
            AzurePipelinesCIAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "azure_pipelines"
        )
