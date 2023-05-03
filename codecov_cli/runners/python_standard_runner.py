import logging
from contextlib import redirect_stdout
from io import StringIO, TextIOWrapper
from multiprocessing import Queue, get_context
from os import getcwd
from sys import path, stdout
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


def _execute_pytest_subprocess(
    pytest_args: List[str],
    queue: Queue,
    parent_stdout: TextIOWrapper,
    capture_output: bool = True,
):
    """Runs pytest from python in a subprocess.
    This is because we call it twice in the label-analysis process,
    so we might have import errors if calling it directly.
    Check the warning: https://docs.pytest.org/en/7.1.x/how-to/usage.html#calling-pytest-from-python-code

    Returns the output value and pytest exit code via queue
    """
    subproces_stdout = parent_stdout
    if capture_output:
        subproces_stdout = StringIO()
    with redirect_stdout(subproces_stdout):
        result = pytest.main(pytest_args)
    if capture_output:
        queue.put(subproces_stdout.getvalue())
    queue.put(result)


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
    def _execute_pytest(
        self, pytest_args: List[str], capture_output: bool = True, numprocess: int = 1
    ) -> str:
        """Handles calling pytest from Python in a subprocess.
        Raises Exception if pytest fails
        Returns the complete pytest output
        """
        ctx = get_context("fork")
        output = None
        queue = ctx.Queue(2)
        p = ctx.Process(
            target=_execute_pytest_subprocess,
            args=[pytest_args, queue, stdout, capture_output],
        )
        p.start()
        if capture_output:
            output = queue.get()  # Output from pytest emitted by subprocess
        result = queue.get()  # Pytest exit code emitted by subprocess
        p.join()

        if p.exitcode != 0 or (result != pytest.ExitCode.OK and result != 0):
            logger.error(
                "Pytest did not run correctly",
                extra=dict(extra_log_attributes=dict(exit_code=result, output=output)),
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
        lines = output.split(sep="\n")
        test_names = list(line for line in lines if ("::" in line and "test" in line))
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
        all_labels = set(
            result["absent_labels"]
            + result["present_diff_labels"]
            + result["global_level_labels"]
        )
        skipped_tests = set(result["present_report_labels"]) - all_labels
        if skipped_tests:
            logger.info(
                "Some tests are being skipped",
                extra=dict(
                    extra_log_attributes=dict(skipped_tests=sorted(skipped_tests))
                ),
            )

        command_array = default_options + [
            label.split("[")[0] if "[" in label else label for label in all_labels
        ]
        logger.info("Running tests")
        logger.debug(
            "Pytest command",
            extra=dict(extra_log_attributes=dict(command_array=command_array)),
        )
        output = self._execute_pytest(command_array, capture_output=False)
        logger.info("Finished running tests successfully")
        logger.debug(output)
