import subprocess
from typing import List, TypedDict, Union

from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)


class DoAnythingNowConfigParams(TypedDict):
    collect_tests_command: Union[List[str], str]
    process_labelanalysis_result_command: Union[List[str], str]


class DoAnythingNowRunner(LabelAnalysisRunnerInterface):
    def __init__(self, config_params: DoAnythingNowConfigParams = None) -> None:
        super().__init__()
        if config_params is None:
            config_params = DoAnythingNowConfigParams()
        self.params = config_params

    def collect_tests(self) -> List[str]:
        command = self.params.get("collect_tests_command", None)
        if command is None:
            raise Exception(
                "DAN runner missing 'collect_tests_command' configuration value"
            )
        return subprocess.run(command, check=True, capture_output=True).stdout.decode()

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        command = self.params.get("process_labelanalysis_result_command", None)
        if command is None:
            raise Exception(
                "DAN runner missing 'process_labelanalysis_result_command' configuration value"
            )
        return subprocess.run(command, check=True, capture_output=True).stdout.decode()
