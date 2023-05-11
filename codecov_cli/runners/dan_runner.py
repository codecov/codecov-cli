import subprocess
from typing import List, Optional, Union

from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)


class DoAnythingNowConfigParams(dict):
    @property
    def collect_tests_command(self) -> Union[List[str], str]:
        return self.get("collect_tests_command", None)

    @property
    def process_labelanalysis_result_command(self) -> Union[List[str], str]:
        return self.get("process_labelanalysis_result_command", None)


class DoAnythingNowRunner(LabelAnalysisRunnerInterface):
    def __init__(self, config_params: Optional[dict] = None) -> None:
        super().__init__()
        if config_params is None:
            config_params = {}
        self.params = DoAnythingNowConfigParams(config_params)

    def collect_tests(self) -> List[str]:
        command = self.params.collect_tests_command
        if command is None:
            raise Exception(
                "DAN runner missing 'collect_tests_command' configuration value"
            )
        return subprocess.run(command, check=True, capture_output=True).stdout.decode()

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        command = self.params.process_labelanalysis_result_command
        if command is None:
            raise Exception(
                "DAN runner missing 'process_labelanalysis_result_command' configuration value"
            )
        return subprocess.run(command, check=True, capture_output=True).stdout.decode()
