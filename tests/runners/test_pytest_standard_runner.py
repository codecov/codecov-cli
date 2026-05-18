from subprocess import CalledProcessError
from unittest.mock import MagicMock, call, patch

import click
import pytest
from pytest import ExitCode

from codecov_cli.runners.pytest_standard_runner import (
    PytestStandardRunner,
    PytestStandardRunnerConfigParams,
)
from codecov_cli.runners.pytest_standard_runner import logger as runner_logger
from codecov_cli.runners.pytest_standard_runner import stdout as pyrunner_stdout
from codecov_cli.runners.types import LabelAnalysisRequestResult


class TestPythonStandardRunner(object):
    runner = PytestStandardRunner()

    def test_init_with_params(self):
        assert self.runner.params.collect_tests_options == []
        assert self.runner.params.coverage_root == "./"

        config_params = dict(
            collect_tests_options=["--option=value", "-option"],
        )
        runner_with_params = PytestStandardRunner(config_params)
        assert runner_with_params.params == config_params

    @patch("codecov_cli.runners.pytest_standard_runner.subprocess")
    def test_execute_pytest(self, mock_subprocess):
        output = "Output in stdout"
        return_value = MagicMock(stdout=output.encode("utf-8"))
        mock_subprocess.run.return_value = return_value

        result = self.runner._execute_pytest(["--option", "--ignore=batata"])
        mock_subprocess.run.assert_called_with(
            ["python", "-m", "pytest", "--option", "--ignore=batata"],
            capture_output=True,
            check=True,
            stdout=None,
        )
        assert result == output

    @patch("codecov_cli.runners.pytest_standard_runner.logger.warning")
    def test_warning_bad_config(self, mock_warning):
        available_config = PytestStandardRunnerConfigParams.get_available_params()
        assert "python_path" in available_config
        assert "collect_tests_options" in available_config
        assert "some_missing_option" not in available_config
        params = dict(
            python_path="path_to_python",
            collect_tests_options=["option1", "option2"],
            some_missing_option="option",
        )
        runner = PytestStandardRunner(params)
        # Adding invalid config options emits a warning
        mock_warning.assert_called_with(
            "Config parameter 'some_missing_option' is unknown."
        )
        # Warnings don't change the config
        assert runner.params == {**params, "some_missing_option": "option"}
        # And we can still access the config as usual
        assert runner.params.python_path == "path_to_python"
        assert runner.params.collect_tests_options == ["option1", "option2"]

    @pytest.mark.parametrize("python_path", ["/usr/bin/python", "venv/bin/python"])
    @patch("codecov_cli.runners.pytest_standard_runner.subprocess")
    def test_execute_pytest_user_provided_python_path(
        self, mock_subprocess, python_path
    ):
        output = "Output in stdout"
        return_value = MagicMock(stdout=output.encode("utf-8"))
        mock_subprocess.run.return_value = return_value

        runner = PytestStandardRunner(dict(python_path=python_path))

        result = runner._execute_pytest(["--option", "--ignore=batata"])
        mock_subprocess.run.assert_called_with(
            [python_path, "-m", "pytest", "--option", "--ignore=batata"],
            capture_output=True,
            check=True,
            stdout=None,
        )
        assert result == output

    @patch("codecov_cli.runners.pytest_standard_runner.subprocess")
    def test_execute_pytest_fail_collection(self, mock_subprocess):
        def side_effect(command, *args, **kwargs):
            raise CalledProcessError(
                cmd=command,
                returncode=2,
                output=b"Process running up to here...",
                stderr=b"Some error occurred",
            )

        mock_subprocess.run.side_effect = side_effect

        with pytest.raises(Exception) as exp:
            _ = self.runner._execute_pytest(["--option", "--ignore=batata"])
        assert (
            str(exp.value)
            == "Pytest exited with non-zero code 2.\nThis is likely not a problem with label-analysis. Check pytest's output and options.\nPYTEST OUTPUT:\nProcess running up to here...\nSome error occurred"
        )

    @patch("codecov_cli.runners.pytest_standard_runner.subprocess")
    def test_execute_pytest_fail_execution(self, mock_subprocess):
        def side_effect(command, *args, **kwargs):
            # In this scenario the regular output AND the stderr message will have been printed
            # to the user terminal already
            click.echo("Regular pytest output")
            raise CalledProcessError(
                cmd=command,
                returncode=2,
                stderr=b"Some error occurred",
            )

        mock_subprocess.run.side_effect = side_effect

        with pytest.raises(Exception) as exp:
            _ = self.runner._execute_pytest(
                ["--option", "--ignore=batata"], capture_output=False
            )
        assert (
            str(exp.value)
            == "Pytest exited with non-zero code 2.\nThis is likely not a problem with label-analysis. Check pytest's output and options.\n(you can check pytest options on the logs before the test session start)"
        )

    @pytest.mark.parametrize(
        "error, expected",
        [
            (
                CalledProcessError(
                    cmd=["python", "-m", "pytest", "missing_label"],
                    returncode=2,
                    output=b"Process running up to here...",
                    stderr=b"Some error occurred",
                ),
                "\nProcess running up to here...\nSome error occurred",
            ),
            (
                CalledProcessError(
                    cmd=["python", "-m", "pytest", "missing_label"],
                    returncode=2,
                    output="Process running up to here...",
                    stderr="Some error occurred",
                ),
                "\nProcess running up to here...\nSome error occurred",
            ),
            (
                CalledProcessError(
                    cmd=["python", "-m", "pytest", "missing_label"],
                    returncode=2,
                    stderr=b"Some error occurred",
                ),
                "\nSome error occurred",
            ),
        ],
    )
    def test_parse_captured_output_error(self, error, expected):
        assert self.runner.parse_captured_output_error(error) == expected

    def test_collect_tests(self, mocker):
        collected_test_list = [
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path_legacy_uploader"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_dry_run"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_verbose"
        ]
        mock_execute = mocker.patch.object(
            PytestStandardRunner,
            "_execute_pytest",
            return_value="\n".join(collected_test_list),
        )

        collected_tests_from_runner = self.runner.collect_tests()
        mock_execute.assert_called_with(["-q", "--collect-only"])
        assert collected_tests_from_runner == collected_test_list

    def test_collect_tests_with_options(self, mocker):
        collected_test_list = [
            "tests/services/upload/test_upload_collector.py::test_fix_go_files"
            "tests/services/upload/test_upload_collector.py::test_fix_php_files"
        ]
        mock_execute = mocker.patch.object(
            PytestStandardRunner,
            "_execute_pytest",
            return_value="\n".join(collected_test_list),
        )

        config_params = dict(collect_tests_options=["--option=value", "-option"])
        runner_with_params = PytestStandardRunner(config_params)

        collected_tests_from_runner = runner_with_params.collect_tests()
        mock_execute.assert_called_with(
            ["-q", "--collect-only", "--option=value", "-option"]
        )
        assert collected_tests_from_runner == collected_test_list

    def test_process_label_analysis_result(self, mocker):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        mock_execute = mocker.patch.object(PytestStandardRunner, "_execute_pytest")

        self.runner.process_labelanalysis_result(
            LabelAnalysisRequestResult(label_analysis_result)
        )
        args, kwargs = mock_execute.call_args
        assert kwargs == {"capture_output": False}
        assert isinstance(args[0], list)
        actual_command = args[0]
        assert actual_command[:2] == [
            "--cov=./",
            "--cov-context=test",
        ]
        assert sorted(actual_command[2:]) == [
            "test_absent",
            "test_global",
            "test_in_diff",
        ]

    def test_process_label_analysis_result_diff_coverage_root(self, mocker):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        mock_execute = mocker.patch.object(PytestStandardRunner, "_execute_pytest")

        config_params = dict(coverage_root="coverage_root/")
        runner_with_params = PytestStandardRunner(config_params)
        runner_with_params.process_labelanalysis_result(
            LabelAnalysisRequestResult(label_analysis_result)
        )
        args, kwargs = mock_execute.call_args
        assert kwargs == {"capture_output": False}
        assert isinstance(args[0], list)
        actual_command = args[0]
        assert actual_command[:2] == [
            "--cov=coverage_root/",
            "--cov-context=test",
        ]
        assert sorted(actual_command[2:]) == [
            "test_absent",
            "test_global",
            "test_in_diff",
        ]

    def test_process_label_analysis_result_with_options(self, mocker):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        mock_execute = mocker.patch.object(PytestStandardRunner, "_execute_pytest")
        mock_warning = mocker.patch.object(runner_logger, "warning")

        runner_config = {
            "execute_tests_options": ["-s", "--cov-report=xml", "--cov=something"]
        }
        runner = PytestStandardRunner(runner_config)
        runner.process_labelanalysis_result(
            LabelAnalysisRequestResult(label_analysis_result)
        )
        args, kwargs = mock_execute.call_args
        assert kwargs == {"capture_output": False}
        assert isinstance(args[0], list)
        actual_command = args[0]
        assert actual_command[:5] == [
            "--cov=./",
            "--cov-context=test",
            "-s",
            "--cov-report=xml",
            "--cov=something",
        ]
        assert sorted(actual_command[5:]) == [
            "test_absent",
            "test_global",
            "test_in_diff",
        ]
        # The --cov option should trigger a warning
        mock_warning.assert_called_with(
            "--cov option detected when running tests. Please use coverage_root config option instead"
        )

    def test_process_label_analysis_skip_all_tests(self, mocker):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": [],
            "present_diff_labels": [],
            "global_level_labels": [],
        }
        mock_execute = mocker.patch.object(PytestStandardRunner, "_execute_pytest")

        self.runner.process_labelanalysis_result(
            LabelAnalysisRequestResult(label_analysis_result)
        )
        args, kwargs = mock_execute.call_args
        assert kwargs == {"capture_output": False}
        assert isinstance(args[0], list)
        actual_command = args[0]
        assert actual_command[:2] == [
            "--cov=./",
            "--cov-context=test",
        ]
        assert sorted(actual_command[2:]) == [
            "test_present",
        ]
