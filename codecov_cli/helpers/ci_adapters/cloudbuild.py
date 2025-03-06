import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class GoogleCloudBuildAdapter(CIAdapterBase):
    """
    Google Cloud Build uses variable substitutions in the builds
    https://cloud.google.com/build/docs/configuring-builds/substitute-variable-values
    For these to be available as environment variables, so this adapter
    can read the values, you have to manually map the substitution variables to
    environment variables on the build step, like this
    env:
    - '_PR_NUMBER=$_PR_NUMBER'
    - 'BRANCH_NAME=$BRANCH_NAME'
    - 'BUILD_ID=$BUILD_ID'
    - 'COMMIT_SHA=$COMMIT_SHA'
    - 'LOCATION=$LOCATION'
    - 'PROJECT_ID=$PROJECT_ID'
    - 'PROJECT_NUMBER=$PROJECT_NUMBER'
    - 'REF_NAME=$REF_NAME'
    - 'REPO_FULL_NAME=$REPO_FULL_NAME'
    - 'TRIGGER_NAME=$TRIGGER_NAME'
    Read more about manual substitution mapping here:
    https://cloud.google.com/build/docs/configuring-builds/substitute-variable-values#map_substitutions_manually
    """

    def detect(self) -> bool:
        return all(
            list(
                map(os.getenv, ["LOCATION", "PROJECT_NUMBER", "PROJECT_ID", "BUILD_ID"])
            )
        )

    def _get_branch(self):
        return os.getenv("BRANCH_NAME")

    def _get_build_code(self):
        return os.getenv("BUILD_ID")

    def _get_commit_sha(self):
        return os.getenv("COMMIT_SHA")

    def _get_slug(self):
        return os.getenv("REPO_FULL_NAME")

    def _get_build_url(self):
        # to build the url, the environment variables LOCATION, PROJECT_ID and BUILD_ID are needed
        if not all(list(map(os.getenv, ["LOCATION", "PROJECT_ID", "BUILD_ID"]))):
            return None

        location = os.getenv("LOCATION")
        project_id = os.getenv("PROJECT_ID")
        build_id = os.getenv("BUILD_ID")

        return f"https://console.cloud.google.com/cloud-build/builds;region={location}/{build_id}?project={project_id}"

    def _get_pull_request_number(self):
        pr_num = os.getenv("_PR_NUMBER")
        return pr_num if pr_num != "" else None

    def _get_job_code(self):
        job_code = os.getenv("TRIGGER_NAME")
        return job_code if job_code != "" else None

    def _get_service(self):
        return "google_cloud_build"

    def get_service_name(self):
        return "GoogleCloudBuild"
