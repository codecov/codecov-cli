import logging
import subprocess

from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)

logger = logging.getLogger("codecovcli")


class PythonStandardRunner(LabelAnalysisRunnerInterface):
    def collect_tests(self):
        return [
            x
            for x in subprocess.run(
                ["python", "-m", "pytest", "-q", "--collect-only"],
                capture_output=True,
                check=True,
            )
            .stdout.decode()
            .split()
            if "::" in x
        ]

    def process_labelanalysis_result(self, result: LabelAnalysisRequestResult):
        command_array = ["python", "-m", "pytest", "--cov=./", "--cov-context=test"]
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
        command_array.extend(all_labels)
        logger.info("Running tests")
        logger.debug(
            "Pytest command",
            extra=dict(extra_log_attributes=dict(command_array=command_array)),
        )
        subprocess.run(command_array, check=True)
