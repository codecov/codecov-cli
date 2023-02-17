import typing
from abc import ABC

from codecov_cli.fallbacks import FallbackFieldEnum


class CIAdapterBase(ABC):
    def __init__(self):
        # If a fallbacker has extra fields, they should be added to this dictionary in the fallbacker's constructor.
        self.fallback_to_method = {
            FallbackFieldEnum.branch: self._get_branch,
            FallbackFieldEnum.build_code: self._get_build_code,
            FallbackFieldEnum.build_url: self._get_build_url,
            FallbackFieldEnum.commit_sha: self._get_commit_sha,
            FallbackFieldEnum.slug: self._get_slug,
            FallbackFieldEnum.service: self._get_service,
            FallbackFieldEnum.pull_request_number: self._get_pull_request_number,
            FallbackFieldEnum.job_code: self._get_job_code,
            FallbackFieldEnum.git_service: self._get_git_service,
        }

    def get_fallback_value(
        self, fallback_field: FallbackFieldEnum
    ) -> typing.Optional[str]:
        if fallback_field not in self.fallback_to_method:
            raise ValueError("The provided fallback_field is not valid")

        return self.fallback_to_method[fallback_field]()

    def detect(self) -> bool:
        """
        Detects if this CI provider is being used
        Returns bool
        """
        raise NotImplementedError("`detect()` must be implemented.")

    def _get_branch(self):
        """
        Determine the branch of the repository based on envs
        Returns: string
        """
        raise NotImplementedError("`_get_branch()` must be implemented.")

    def _get_commit_sha(self):
        """
        Determine the commit SHA that is being uploaded, based on envs
        Returns: string
        """
        raise NotImplementedError("`_get_commit_sha()` must be implemented.")

    def _get_slug(self):
        """
        Determine the slug (org/repo) based on envs
        Returns: string
        """
        raise NotImplementedError("`_get_slug()` must be implemented.")

    def _get_service(self):
        """
        The CI service name that gets sent to the Codecov uploader as part of the query string
        It gets displayed in the Codecov UI
        Returns: string
        """
        raise NotImplementedError("`_get_service()` must be implemented.")

    def _get_build_url(self):
        """
        Determine the build URL for use in the Codecov UI
        Returns: string
        """
        raise NotImplementedError("`_get_build_url()` must be implemented.")

    def _get_build_code(self):
        """
        Determine the build number, based on envs
        Returns: string
        """
        raise NotImplementedError("`_get_build_code()` must be implemented.")

    def _get_job_code(self):
        """
        Determine the job number, based on envs
        Returns: string
        """
        raise NotImplementedError("`_get_job_code()` must be implemented.")

    def _get_pull_request_number(self):
        """
        Determine the PR number, based on envs
        Returns: string
        """
        raise NotImplementedError("`_get_pull_request_number()` must be implemented.")

    def get_service_name(self):
        """
        The CI Service name that gets displayed when running the uploader
        Returns: string
        """
        raise NotImplementedError("`get_service_name()` must be implemented.")

    def _get_git_service(self):
        return None
