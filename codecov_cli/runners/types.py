from typing import List, TypedDict


class LabelAnalysisRequestResult(TypedDict):
    present_report_labels: List[str]
    absent_labels: List[str]
    present_diff_labels: List[str]
    global_level_labels: List[str]


class LabelAnalysisRunnerInterface(object):
    params = None

    def collect_tests(self) -> List[str]:
        raise NotImplementedError()

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        raise NotImplementedError()
