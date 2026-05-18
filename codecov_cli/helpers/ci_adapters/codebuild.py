import os
import re

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class AWSCodeBuildCIAdapter(CIAdapterBase):
    # https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-env-vars.html
    def detect(self) -> bool:
        return bool(os.getenv("CODEBUILD_CI"))

    def _get_branch(self):
        branch = os.getenv("CODEBUILD_WEBHOOK_HEAD_REF")
        if branch:
            return re.sub(r"^refs\/heads\/", "", branch)
        return None

    def _get_build_code(self):
        return os.getenv("CODEBUILD_BUILD_ID")

    def _get_build_url(self):
        return None

    def _get_commit_sha(self):
        return os.getenv("CODEBUILD_RESOLVED_SOURCE_VERSION")

    def _get_slug(self):
        slug = os.getenv("CODEBUILD_SOURCE_REPO_URL")
        if slug:
            slug = re.sub(r"^.*github.com\/", "", slug)
            slug = re.sub(r"^.*gitlab.com\/", "", slug)
            slug = re.sub(r"^.*bitbucket.com\/", "", slug)
            return re.sub(r"\.git$", "", slug)
        return None

    def _get_service(self):
        return "AWS CodeBuild"

    def _get_pull_request_number(self):
        pr = os.getenv("CODEBUILD_SOURCE_VERSION")
        if pr and pr.startswith("pr/"):
            return re.sub(r"^pr\/", "", pr)
        return None

    def _get_job_code(self):
        return os.getenv("CODEBUILD_BUILD_ID")

    def get_service_name(self):
        return "AWSCodeBuild"
