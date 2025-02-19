from typing import List, Optional

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.helpers.versioning_systems import VersioningSystemInterface
from codecov_cli.runners.types import LabelAnalysisRunnerInterface
from pathlib import Path


class FakeProvider(CIAdapterBase):
    def __init__(self, values_dict: Optional[dict] = None):
        if values_dict is None:
            values_dict = {}
        super().__init__()
        default_values = {
            FallbackFieldEnum.branch: "BUILD_BRANCH",
            FallbackFieldEnum.build_code: "BUILD_CODE",
            FallbackFieldEnum.build_url: "BUILD_URL",
            FallbackFieldEnum.commit_sha: "1111111111111111111111111111111111111111",
            FallbackFieldEnum.slug: "REPO_SLUG",
            FallbackFieldEnum.service: "FAKE_PROVIDER",
            FallbackFieldEnum.pull_request_number: "PR_NUMBER",
            FallbackFieldEnum.job_code: "JOB_CODE",
            FallbackFieldEnum.git_service: "FAKE_PROVIDER",
        }
        final_values = {**default_values, **values_dict}
        self.values_dict = final_values

    def detect(self) -> bool:
        return True

    def _get_branch(self):
        return self.values_dict[FallbackFieldEnum.branch]

    def _get_build_code(self):
        return self.values_dict[FallbackFieldEnum.build_code]

    def _get_build_url(self):
        return self.values_dict[FallbackFieldEnum.build_url]

    def _get_commit_sha(self):
        return self.values_dict[FallbackFieldEnum.commit_sha]

    def _get_slug(self):
        return self.values_dict[FallbackFieldEnum.slug]

    def _get_service(self):
        return self.values_dict[FallbackFieldEnum.service]

    def _get_pull_request_number(self):
        return self.values_dict[FallbackFieldEnum.pull_request_number]

    def _get_job_code(self):
        return self.values_dict[FallbackFieldEnum.job_code]

    def get_service_name(self):
        return self.values_dict[FallbackFieldEnum.git_service]


class FakeVersioningSystem(VersioningSystemInterface):
    def __init__(self, values_dict: Optional[dict] = None):
        if values_dict is None:
            values_dict = {}
        super().__init__()
        default_values = {
            FallbackFieldEnum.branch: "BUILD_BRANCH",
            FallbackFieldEnum.commit_sha: "COMMIT_SHA",
            FallbackFieldEnum.slug: "REPO_SLUG",
            FallbackFieldEnum.git_service: "FAKE_VERSIONING_SYSTEM",
        }
        final_values = {**default_values, **values_dict}
        self.values_dict = final_values

    def get_fallback_value(self, fallback_field: FallbackFieldEnum) -> Optional[str]:
        return self.values_dict[fallback_field]

    def get_network_root(self) -> Optional[Path]:
        return None

    def list_relevant_files(self, directory: Optional[Path] = None) -> List[str]:
        return []


class FakeRunner(LabelAnalysisRunnerInterface):
    dry_run_runner_options = ["--labels"]

    def __init__(self, collect_tests_response: List[str]) -> None:
        super().__init__()
        self.collect_tests_response = collect_tests_response

    def collect_tests(self) -> List[str]:
        return self.collect_tests_response

    def process_labelanalysis_result(self, result):
        return "I ran tests :D"
