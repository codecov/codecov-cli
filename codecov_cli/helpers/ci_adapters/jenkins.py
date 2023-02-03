import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class JenkinsAdapter(CIAdapterBase):
    # https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#using-environment-variables
    # https://www.jenkins.io/doc/book/pipeline/multibranch/

    def detect(self) -> bool:
        return bool(os.getenv("JENKINS_URL"))

    def _get_commit_sha(self):
        return None

    def _get_build_url(self):
        return os.getenv("BUILD_URL")

    def _get_build_code(self):
        return os.getenv("BUILD_NUMBER")

    def _get_job_code(self):
        return None

    def _get_pull_request_number(self):
        return os.getenv("CHANGE_ID")

    def _get_slug(self):
        return None

    def _get_branch(self):
        return os.getenv("BRANCH_NAME")

    def _get_service(self):
        return "jenkins"

    def get_service_name(self):
        return "Jenkins"
