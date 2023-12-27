import inspect
import logging
import random
import subprocess
from subprocess import CalledProcessError
from sys import stdout
from typing import List, Optional

import click

from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)

logger = logging.getLogger("codecovcli")


class PytestStandardRunnerConfigParams(dict):
    @property
    def python_path(self) -> str:
        python_path = self.get("python_path")
        return python_path or "python"

    @property
    def collect_tests_options(self) -> List[str]:
        return self.get("collect_tests_options", [])

    @property
    def execute_tests_options(self) -> List[str]:
        options = self.get("execute_tests_options", [])
        if any(map(lambda option: option.startswith("--cov"), options)):
            logger.warning(
                "--cov option detected when running tests. Please use coverage_root config option instead"
            )
        return options

    @property
    def coverage_root(self) -> str:
        """
        The coverage root. This will be passed to --cov=<coverage_root_dir>
        Default: ./
        """
        return self.get("coverage_root", "./")

    @classmethod
    def get_available_params(cls) -> List[str]:
        """Lists all the @property attribute names of this class.
        These attributes are considered the 'valid config options'
        """
        klass_methods = [
            x
            for x in dir(cls)
            if (inspect.isdatadescriptor(getattr(cls, x)) and not x.startswith("__"))
        ]
        return klass_methods


class PytestStandardRunner(LabelAnalysisRunnerInterface):

    dry_run_runner_options = ["--cov-context=test"]
    params: PytestStandardRunnerConfigParams

    def __init__(self, config_params: Optional[dict] = None) -> None:
        super().__init__()
        if config_params is None:
            config_params = {}
        # Before we create the config params we emit warnings if any param is unknown
        # So the user knows something is wrong with their config
        self._possibly_warn_bad_config(config_params)
        self.params = PytestStandardRunnerConfigParams(config_params)

    def _possibly_warn_bad_config(self, config_params: dict):
        available_config_params = (
            PytestStandardRunnerConfigParams.get_available_params()
        )
        provided_config_params = config_params.keys()
        for provided_param in provided_config_params:
            if provided_param not in available_config_params:
                logger.warning(f"Config parameter '{provided_param}' is unknonw.")

    def parse_captured_output_error(self, exp: CalledProcessError) -> str:
        result = ""
        for out_stream in [exp.stdout, exp.stderr]:
            if out_stream:
                if type(out_stream) is bytes:
                    out_stream = out_stream.decode()
                result += "\n" + out_stream
        return result

    def _execute_pytest(self, pytest_args: List[str], capture_output: bool = True):
        """Handles calling pytest using subprocess.run.
        Raises Exception if pytest fails
        Returns the complete pytest output
        """
        command = [self.params.python_path, "-m", "pytest"] + pytest_args
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                check=True,
                stdout=(stdout if not capture_output else None),
            )
        except CalledProcessError as exp:
            message = f"Pytest exited with non-zero code {exp.returncode}."
            message += "\nThis is likely not a problem with label-analysis. Check pytest's output and options."

            if capture_output:
                # If pytest failed but we captured its output the user won't know what's wrong
                # So we need to include that in the error message
                message += "\nPYTEST OUTPUT:"
                message += self.parse_captured_output_error(exp)
            else:
                message += "\n(you can check pytest options on the logs before the test session start)"
            raise click.ClickException(message)
        if capture_output:
            return result.stdout.decode()

    def collect_tests(self):
        default_options = ["-q", "--collect-only"]
        extra_args = self.params.collect_tests_options
        options_to_use = default_options + extra_args
        logger.info(
            "Collecting tests",
            extra=dict(
                extra_log_attributes=dict(
                    pytest_command=[self.params.python_path, "-m", "pytest"],
                    pytest_options=options_to_use,
                ),
            ),
        )

        output = self._execute_pytest(options_to_use)
        lines = output.split(sep="\n")
        test_names = list(line for line in lines if ("::" in line and "test" in line))
        return test_names

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        default_options = [
            f"--cov={self.params.coverage_root}",
            "--cov-context=test",
        ] + self.params.execute_tests_options
        all_labels = set(
            result.absent_labels
            + result.present_diff_labels
            + result.global_level_labels
        )
        skipped_tests = set(result.present_report_labels) - all_labels
        if skipped_tests:
            logger.info(
                "Some tests are being skipped. (run in verbose mode to get list of tests skipped)",
                extra=dict(
                    extra_log_attributes=dict(skipped_tests_count=len(skipped_tests))
                ),
            )
            logger.debug(
                "List of skipped tests",
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
        tests_to_run = [
            label.split("[")[0] if "[" in label else label for label in all_labels
        ]
        command_array = default_options + tests_to_run
        logger.info(
            "Running tests. (run in verbose mode to get list of tests executed)"
        )
        logger.info(f"  pytest options: \"{' '.join(default_options)}\"")
        logger.info(f"  executed tests: {len(tests_to_run)}")
        logger.debug(
            "List of tests executed",
            extra=dict(extra_log_attributes=dict(executed_tests=tests_to_run)),
        )
        output = self._execute_pytest(command_array, capture_output=False)
        logger.info(f"Finished running {len(tests_to_run)} tests successfully")
        logger.info(f"  pytest options: \"{' '.join(default_options)}\"")
        logger.debug(output)
