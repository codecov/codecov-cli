import logging
import random
import subprocess
from contextlib import redirect_stdout
from io import StringIO, TextIOWrapper
from multiprocessing import Process, Queue, get_context
from os import getcwd
from queue import Empty
from subprocess import CalledProcessError
from sys import path, stdout
from typing import List, Optional

import pytest

from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)

logger = logging.getLogger("codecovcli")


class PythonStandardRunnerConfigParams(dict):
    @property
    def collect_tests_options(self) -> List[str]:
        return self.get("collect_tests_options", [])

    @property
    def coverage_root(self) -> str:
        """
        The coverage root. This will be passed to --cov=<coverage_root_dir>
        Default: ./
        """
        return self.get("coverage_root", "./")

    @property
    def strict_mode(self) -> bool:
        """
        Run pytest from within Python instead of using subprocess.run
        This is potentailly safer than using subprocess.run because it guarantees better that
        the program running is indeed pytest.
        But it might not work everytime due to import issues related to Python caching modules.
        """
        return self.get("strict_mode", False)

    @property
    def include_curr_dir(self) -> bool:
        """
        Only valid for 'strict mode'
        Account for the difference 'pytest' vs 'python -m pytest'
        https://docs.pytest.org/en/7.1.x/how-to/usage.html#calling-pytest-through-python-m-pytest
        """
        return self.get("include_curr_dir", True)


def _include_curr_dir(method):
    """
    Account for the difference 'pytest' vs 'python -m pytest'
    https://docs.pytest.org/en/7.1.x/how-to/usage.html#calling-pytest-through-python-m-pytest
    """

    def call_method(self, *args, **kwargs):
        include_curr_dir = self.params.include_curr_dir
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
        queue.put({"output": subproces_stdout.getvalue()})
    queue.put({"result": result})


class PythonStandardRunner(LabelAnalysisRunnerInterface):
    def __init__(self, config_params: Optional[dict] = None) -> None:
        super().__init__()
        if config_params is None:
            config_params = {}
        self.params = PythonStandardRunnerConfigParams(config_params)

    def _wait_pytest(self, pytest_process: Process, queue: Queue):
        pytest_process.start()
        result = None
        output = None
        while pytest_process.exitcode == 0 or pytest_process.exitcode == None:
            from_queue = None
            try:
                from_queue = queue.get(timeout=1)
            except Empty:
                pass
            if from_queue and "output" in from_queue:
                output = from_queue["output"]
            if from_queue and "result" in from_queue:
                result = from_queue["result"]
            if result is not None:
                break
        pytest_process.join()
        return result, output

    @_include_curr_dir
    def _execute_pytest_strict(
        self, pytest_args: List[str], capture_output: bool = True
    ) -> str:
        """Handles calling pytest from Python in a subprocess.
        Raises Exception if pytest fails
        Returns the complete pytest output
        """
        ctx = get_context(method="fork")
        queue = ctx.Queue(2)
        p = ctx.Process(
            target=_execute_pytest_subprocess,
            args=[pytest_args, queue, stdout, capture_output],
        )
        result, output = self._wait_pytest(p, queue)

        if p.exitcode != 0 or (result != pytest.ExitCode.OK and result != 0):
            logger.error(
                "Pytest did not run correctly",
                extra=dict(extra_log_attributes=dict(exit_code=result, output=output)),
            )
            raise Exception("Pytest did not run correctly")
        return output

    def _execute_pytest(self, pytest_args: List[str], capture_output: bool = True):
        """Handles calling pytest using subprocess.run.
        Raises Exception if pytest fails
        Returns the complete pytest output
        """
        command = ["python", "-m", "pytest"] + pytest_args
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                check=True,
                stdout=(stdout if not capture_output else None),
            )
        except CalledProcessError as exp:
            logger.error(exp.stderr)
            logger.error(
                "Pytest did not run correctly",
                extra=dict(extra_log_attributes=dict(exit_code=exp.returncode)),
            )
            raise Exception("Pytest did not run correctly")
        if capture_output:
            return result.stdout.decode()

    def collect_tests(self):
        default_options = ["-q", "--collect-only"]
        extra_args = self.params.collect_tests_options
        options_to_use = default_options + extra_args
        logger.debug(
            "Collecting tests",
            extra=dict(
                extra_log_attributes=dict(options=options_to_use),
            ),
        )

        if self.params.strict_mode:
            output = self._execute_pytest_strict(options_to_use)
        else:
            output = self._execute_pytest(options_to_use)
        lines = output.split(sep="\n")
        test_names = list(line for line in lines if ("::" in line and "test" in line))
        return test_names

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        default_options = [f"--cov={self.params.coverage_root}", "--cov-context=test"]
        all_labels = set(
            result.absent_labels
            + result.present_diff_labels
            + result.global_level_labels
        )
        skipped_tests = set(result.present_report_labels) - all_labels
        if skipped_tests:
            logger.info(
                "Some tests are being skipped",
                extra=dict(
                    extra_log_attributes=dict(skipped_tests=sorted(skipped_tests))
                ),
            )

        if len(all_labels) == 0:
            all_labels = [random.choice(result.present_report_labels)]
            logger.info(
                "All tests are being skipped. Selected random label to run",
                extra=dict(extra_log_attributes=dict(selected_label=all_labels[0])),
            )
        command_array = default_options + [
            label.split("[")[0] if "[" in label else label for label in all_labels
        ]
        logger.info("Running tests")
        logger.debug(
            "Pytest command",
            extra=dict(extra_log_attributes=dict(command_array=command_array)),
        )
        if self.params.strict_mode:
            output = self._execute_pytest_strict(command_array, capture_output=False)
        else:
            output = self._execute_pytest(command_array, capture_output=False)
        logger.info("Finished running tests successfully")
        logger.debug(output)
