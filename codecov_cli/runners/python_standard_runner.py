import logging
import subprocess
from contextlib import redirect_stdout
from io import StringIO
from os import getcwd
from sys import path
from typing import List, TypedDict

import pytest

from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)

logger = logging.getLogger("codecovcli")


class PythonStandardRunnerConfigParams(TypedDict):
    collect_tests_options: List[str]
    # include_dirs is to account for the difference described in
    # https://docs.pytest.org/en/7.1.x/how-to/usage.html#calling-pytest-through-python-m-pytest
    include_curr_dir: bool


def _include_curr_dir(method):
    def call_method(self, *args, **kwargs):
        include_curr_dir = self.params["include_curr_dir"]
        curr_dir = getcwd()
        if include_curr_dir:
            path.append(curr_dir)
        result = method(self, *args, **kwargs)
        if include_curr_dir:
            path.remove(curr_dir)
        return result

    return call_method


class PythonStandardRunner(LabelAnalysisRunnerInterface):
    def __init__(self, config_params: PythonStandardRunnerConfigParams = None) -> None:
        super().__init__()
        default_config: PythonStandardRunnerConfigParams = {
            "collect_tests_options": [],
            "include_curr_dir": True,
        }
        if config_params is None:
            config_params = PythonStandardRunnerConfigParams()
        self.params = {**default_config, **config_params}

    @_include_curr_dir
    def _execute_pytest(self, pytest_args: List[str]) -> str:
        with StringIO() as fd:
            with redirect_stdout(fd):
                result = pytest.main(pytest_args)
            output = fd.getvalue()
            if result != pytest.ExitCode.OK and result != 0:
                logger.error(
                    "Pytest did not run correctly",
                    extra=dict(
                        extra_log_attributes=dict(exit_code=result, output=output)
                    ),
                )
                raise Exception("Pytest did not run correctly")
        return output

    def collect_tests(self):
        default_options = ["-q", "--collect-only"]
        extra_args = self.params["collect_tests_options"]
        options_to_use = default_options + extra_args
        logger.debug(
            "Collecting tests",
            extra=dict(
                extra_log_attributes=dict(options=options_to_use),
            ),
        )

        output = self._execute_pytest(options_to_use)
        lines = output.split()
        test_names = list(line for line in lines if "::" in line)
        return test_names

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        default_options = ["--cov=./", "--cov-context=test"]
        logger.info(
            "Received information about tests to run",
            extra=dict(
                extra_log_attributes=dict(
                    absent_labels=len(result["absent_labels"] or []),
                    present_diff_labels=len(result["present_diff_labels"] or []),
                    global_level_labels=len(result["global_level_labels"] or []),
                    present_report_labels=len(result["present_report_labels"] or []),
                )
            ),
        )
        all_labels = (
            result["absent_labels"]
            + result["present_diff_labels"]
            + result["global_level_labels"]
        )
        skipped_tests = set(result["present_report_labels"]) - set(all_labels)
        if skipped_tests:
            logger.info(
                "Some tests are being skipped",
                extra=dict(
                    extra_log_attributes=dict(skipped_tests=sorted(skipped_tests))
                ),
            )
        all_labels = set(all_labels)
        all_labels = [x.rsplit("[", 1)[0] if "[" in x else x for x in all_labels]
        # Not safe from the customer perspective, in general, probably.
        # This is just to check it working
        command_array = default_options + all_labels
        logger.info("Running tests")
        logger.debug(
            "Pytest command",
            extra=dict(extra_log_attributes=dict(command_array=command_array)),
        )
        output = self._execute_pytest(command_array)
        logger.info("Finished running tests successfully")
        logger.debug(output)
