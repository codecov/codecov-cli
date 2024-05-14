import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.cloudbuild import GoogleCloudBuildAdapter


class CloudBuildEnvEnum(str, Enum):
    BRANCH_NAME = "BRANCH_NAME"
    BUILD_ID = "BUILD_ID"
    COMMIT_SHA = "COMMIT_SHA"
    LOCATION = "LOCATION"
    PROJECT_ID = "PROJECT_ID"
    PROJECT_NUMBER = "PROJECT_NUMBER"
    REPO_FULL_NAME = "REPO_FULL_NAME"
    _PR_NUMBER = "_PR_NUMBER"
    TRIGGER_NAME = "TRIGGER_NAME"


class TestCloudBuild(object):
    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, False),
            (
                {
                    CloudBuildEnvEnum.LOCATION: "global",
                    CloudBuildEnvEnum.PROJECT_ID: "my_project",
                    CloudBuildEnvEnum.PROJECT_NUMBER: "123",
                },
                False,
            ),
            (
                {
                    CloudBuildEnvEnum.BUILD_ID: "fd02b20f-72a3-41b5-862d-2c15e5f289de",
                    CloudBuildEnvEnum.PROJECT_ID: "my_project",
                    CloudBuildEnvEnum.PROJECT_NUMBER: "123",
                },
                False,
            ),
            (
                {
                    CloudBuildEnvEnum.BUILD_ID: "fd02b20f-72a3-41b5-862d-2c15e5f289de",
                    CloudBuildEnvEnum.LOCATION: "global",
                    CloudBuildEnvEnum.PROJECT_NUMBER: "123",
                },
                False,
            ),
            (
                {
                    CloudBuildEnvEnum.BUILD_ID: "fd02b20f-72a3-41b5-862d-2c15e5f289de",
                    CloudBuildEnvEnum.LOCATION: "global",
                    CloudBuildEnvEnum.PROJECT_ID: "my_project",
                },
                False,
            ),
            (
                {
                    CloudBuildEnvEnum.BUILD_ID: "fd02b20f-72a3-41b5-862d-2c15e5f289de",
                    CloudBuildEnvEnum.LOCATION: "global",
                    CloudBuildEnvEnum.PROJECT_ID: "my_project",
                    CloudBuildEnvEnum.PROJECT_NUMBER: "123",
                },
                True,
            ),
        ],
    )
    def test_detect(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().detect()
        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CloudBuildEnvEnum.BRANCH_NAME: "abc"}, "abc"),
        ],
    )
    def test_branch(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().get_fallback_value(FallbackFieldEnum.branch)

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {CloudBuildEnvEnum.BUILD_ID: "52cbb633-aca0-4289-90bd-76e4e60baf82"},
                "52cbb633-aca0-4289-90bd-76e4e60baf82",
            ),
        ],
    )
    def test_build_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().get_fallback_value(
            FallbackFieldEnum.build_code
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            (
                {
                    CloudBuildEnvEnum.LOCATION: "global",
                    CloudBuildEnvEnum.PROJECT_ID: "my_project",
                },
                None,
            ),
            (
                {
                    CloudBuildEnvEnum.BUILD_ID: "fd02b20f-72a3-41b5-862d-2c15e5f289de",
                    CloudBuildEnvEnum.PROJECT_ID: "my_project",
                },
                None,
            ),
            (
                {
                    CloudBuildEnvEnum.BUILD_ID: "fd02b20f-72a3-41b5-862d-2c15e5f289de",
                    CloudBuildEnvEnum.LOCATION: "global",
                },
                None,
            ),
            (
                {
                    CloudBuildEnvEnum.BUILD_ID: "fd02b20f-72a3-41b5-862d-2c15e5f289de",
                    CloudBuildEnvEnum.LOCATION: "global",
                    CloudBuildEnvEnum.PROJECT_ID: "my_project",
                },
                "https://console.cloud.google.com/cloud-build/builds;region=global/fd02b20f-72a3-41b5-862d-2c15e5f289de?project=my_project",
            ),
        ],
    )
    def test_build_url(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().get_fallback_value(
            FallbackFieldEnum.build_url
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CloudBuildEnvEnum.COMMIT_SHA: "123456789000111"}, "123456789000111"),
        ],
    )
    def test_commit_sha(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().get_fallback_value(
            FallbackFieldEnum.commit_sha
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CloudBuildEnvEnum.TRIGGER_NAME: ""}, None),
            ({CloudBuildEnvEnum.TRIGGER_NAME: "build-job-name"}, "build-job-name"),
        ],
    )
    def test_job_code(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().get_fallback_value(
            FallbackFieldEnum.job_code
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CloudBuildEnvEnum._PR_NUMBER: ""}, None),
            ({CloudBuildEnvEnum._PR_NUMBER: "123"}, "123"),
        ],
    )
    def test_pull_request_number(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().get_fallback_value(
            FallbackFieldEnum.pull_request_number
        )

        assert actual == expected

    @pytest.mark.parametrize(
        "env_dict,expected",
        [
            ({}, None),
            ({CloudBuildEnvEnum.REPO_FULL_NAME: "owner/repo"}, "owner/repo"),
        ],
    )
    def test_slug(self, env_dict, expected, mocker):
        mocker.patch.dict(os.environ, env_dict)
        actual = GoogleCloudBuildAdapter().get_fallback_value(FallbackFieldEnum.slug)

        assert actual == expected

    def test_service(self):
        assert (
            GoogleCloudBuildAdapter().get_fallback_value(FallbackFieldEnum.service)
            == "google_cloud_build"
        )
