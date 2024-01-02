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

    @property
    def collected_labels_in_order(self) -> List[str]:
        """The list of collected labels, in the order returned by the testing tool.
        This is a superset of all other lists.
        """
        return self.get("collected_labels_in_order", [])

    def get_tests_to_run_in_collection_order(self) -> List[str]:
        labels_to_run = set(
            self.absent_labels + self.global_level_labels + self.present_diff_labels
        )
        output = []
        for test_name in self.collected_labels_in_order:
            if test_name in labels_to_run:
                output.append(test_name)
        return output

    def get_tests_to_skip_in_collection_order(self) -> List[str]:
        labels_to_run = set(
            self.absent_labels + self.global_level_labels + self.present_diff_labels
        )
        labels_to_skip = set(self.present_report_labels) - labels_to_run
        output = []
        for test_name in self.collected_labels_in_order:
            if test_name in labels_to_skip:
                output.append(test_name)
        return output


class LabelAnalysisRunnerInterface(object):
    params: Dict = None
    dry_run_runner_options: List[str] = []

    def collect_tests(self) -> List[str]:
        raise NotImplementedError()

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        raise NotImplementedError()
