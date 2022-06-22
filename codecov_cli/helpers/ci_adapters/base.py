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
        }

    def get_fallback_value(
        self, fallback_field: FallbackFieldEnum
    ) -> typing.Optional[str]:
        if fallback_field not in self.fallback_to_method:
            raise ValueError("The provided fallback_field is not valid")

        return self.fallback_to_method[fallback_field]()
