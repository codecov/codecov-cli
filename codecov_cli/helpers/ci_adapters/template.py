import os

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase


class TemplateAdapter(CIAdapterBase):
    # link for env variables

    def _get_branch(self):
        """
        Determine the branch of the repository based on envs
        Returns: string
        """
        return None

    def _get_commit_sha(self):
        """
        Determine the commit SHA that is being uploaded, based on envs
        Returns: string
        """
        return None

    def _get_slug(self):
        """
        Determine the slug (org/repo) based on envs
        Returns: string
        """
        return None

    def _get_service(self):
        """
        The CI service name that gets sent to the Codecov uploader as part of the query string
        It gets displayed in the Codecov UI
        Returns: string
        """
        return None

    def _get_build_url(self):
        """
        Determine the build URL for use in the Codecov UI
        Returns: string
        """
        return None

    def _get_build_code(self):
        """
        Determine the build number, based on envs
        Returns: string
        """
        return None

    def _get_job_code(self):
        """
        Determine the job number, based on envs
        Returns: string
        """
        return None

    def _get_pull_request_number(self):
        """
        Determine the PR number, based on envs
        Returns: string
        """
        return None
