import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class AzurePipelinesCIAdapter(CIAdapterBase):
    # https://learn.microsoft.com/en-us/azure/devops/pipelines/build/variables?view=azure-devops&tabs=yaml#build-variables-devops-services

    def detect(self) -> bool:
        return bool(os.getenv("SYSTEM_TEAMFOUNDATIONCOLLECTIONURI"))

    def _get_commit_sha(self):
        return os.getenv("BUILD_SOURCEVERSION")

    def _get_build_url(self):
        if os.getenv("SYSTEM_TEAMPROJECT") and os.getenv("BUILD_BUILDID"):
            return f'{os.getenv("SYSTEM_TEAMFOUNDATIONCOLLECTIONURI")}{os.getenv("SYSTEM_TEAMPROJECT")}/_build/results?buildId={os.getenv("BUILD_BUILDID")}'

    def _get_build_code(self):
        return os.getenv("BUILD_BUILDNUMBER")

    def _get_job_code(self):
        return os.getenv("BUILD_BUILDID")

    def _get_pull_request_number(self):
        return os.getenv("SYSTEM_PULLREQUEST_PULLREQUESTNUMBER") or os.getenv(
            "SYSTEM_PULLREQUEST_PULLREQUESTID"
        )

    def _get_slug(self):
        return os.getenv("BUILD_REPOSITORY_NAME")

    def _get_branch(self):
        branch = os.getenv("BUILD_SOURCEBRANCH")
        if branch:
            return branch.replace("refs/heads/", "")

    def _get_service(self):
        return "azure_pipelines"

    def get_service_name(self):
        return "AzurePipelines"
