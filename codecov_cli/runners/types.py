from typing import Dict, List


# This is supposed to be a TypedDict,
# But that is Python >= 3.7 only
# So we are not using those
class LabelAnalysisRequestResult(dict):
    @property
    def present_report_labels(self) -> List[str]:
        return self.get("present_report_labels", [])

    @property
    def absent_labels(self) -> List[str]:
        return self.get("absent_labels", [])

    @property
    def present_diff_labels(self) -> List[str]:
        return self.get("present_diff_labels", [])

    @property
    def global_level_labels(self) -> List[str]:
        return self.get("global_level_labels", [])


class LabelAnalysisRunnerInterface(object):
    params: Dict = None
    dry_run_runner_options: List[str] = []

    def collect_tests(self) -> List[str]:
        raise NotImplementedError()

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        raise NotImplementedError()
