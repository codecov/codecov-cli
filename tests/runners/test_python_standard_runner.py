from subprocess import CalledProcessError
from typing import List
from unittest.mock import MagicMock, call, patch

import pytest
from pytest import ExitCode

from codecov_cli.runners.python_standard_runner import (
    PythonStandardRunner,
    PythonStandardRunnerConfigParams,
    _execute_pytest_subprocess,
)
from codecov_cli.runners.python_standard_runner import stdout as pyrunner_stdout


@patch("codecov_cli.runners.python_standard_runner.pytest")
def test_execute_pytest_subprocess(mock_pytest, mocker):
    def side_effect(*args, **kwargs):
        print("Pytest output")
        return ExitCode.OK

    mock_pytest.main.side_effect = side_effect
    mock_queue = MagicMock()
    _execute_pytest_subprocess(["pytest", "args"], mock_queue, MagicMock())
    mock_pytest.main.assert_called_with(["pytest", "args"])
    assert mock_queue.put.call_count == 2
    mock_queue.put.assert_has_calls(
        [call({"output": "Pytest output\n"}), call({"result": ExitCode.OK})]
    )


@patch("codecov_cli.runners.python_standard_runner.pytest")
def test_execute_pytest_subprocess_no_capture_stdout(mock_pytest, mocker):
    def side_effect(*args, **kwargs):
        print("Pytest output")
        return ExitCode.OK

    mock_pytest.main.side_effect = side_effect
    mock_queue = MagicMock()
    _execute_pytest_subprocess(["pytest", "args"], mock_queue, MagicMock(), False)
    mock_pytest.main.assert_called_with(["pytest", "args"])
    assert mock_queue.put.call_count == 1
    mock_queue.put.assert_has_calls([call({"result": ExitCode.OK})])


class TestPythonStandardRunner(object):
    runner = PythonStandardRunner()

    def test_init_with_params(self):
        assert self.runner.params.collect_tests_options == []
        assert self.runner.params.include_curr_dir == True

        config_params = dict(
            collect_tests_options=["--option=value", "-option"],
            include_curr_dir=False,
        )
        runner_with_params = PythonStandardRunner(config_params)
        assert runner_with_params.params == config_params

    @patch("codecov_cli.runners.python_standard_runner.subprocess")
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

    @patch(
        "codecov_cli.runners.python_standard_runner.getcwd",
        return_value="current directory",
    )
    @patch("codecov_cli.runners.python_standard_runner.path")
    @patch("codecov_cli.runners.python_standard_runner.get_context")
    def test_execute_pytest_strict_mode(
        self, mock_get_context, mock_sys_path, mock_getcwd
    ):
        output = "Output in stdout"
        mock_queue = MagicMock()
        mock_queue.get.side_effect = [{"output": output}, {"result": ExitCode.OK}]
        mock_process = MagicMock()
        mock_process.exitcode = 0
        mock_get_context.return_value.Queue.return_value = mock_queue
        mock_get_context.return_value.Process.return_value = mock_process

        result = self.runner._execute_pytest_strict(["--option", "--ignore=batata"])
        mock_get_context.return_value.Queue.assert_called_with(2)
        mock_get_context.return_value.Process.assert_called_with(
            target=_execute_pytest_subprocess,
            args=[["--option", "--ignore=batata"], mock_queue, pyrunner_stdout, True],
        )
        mock_sys_path.append.assert_called_with("current directory")
        mock_sys_path.remove.assert_called_with("current directory")
        assert mock_queue.get.call_count == 2
        assert result == output

    @patch(
        "codecov_cli.runners.python_standard_runner.getcwd",
        return_value="current directory",
    )
    @patch("codecov_cli.runners.python_standard_runner.path")
    @patch("codecov_cli.runners.python_standard_runner.get_context")
    def test_execute_pytest_fail_strict_mode(
        self, mock_get_context, mock_sys_path, mock_getcwd
    ):
        output = "Output in stdout"
        mock_queue = MagicMock()
        mock_queue.get.side_effect = [
            {"output": output},
            {"result": ExitCode.INTERNAL_ERROR},
        ]
        mock_process = MagicMock()
        mock_process.exitcode = 0
        mock_get_context.return_value.Queue.return_value = mock_queue
        mock_get_context.return_value.Process.return_value = mock_process

        with pytest.raises(Exception) as exp:
            _ = self.runner._execute_pytest_strict(["--option", "--ignore=batata"])
        assert str(exp.value) == "Pytest did not run correctly"
        mock_get_context.return_value.Queue.assert_called_with(2)
        mock_get_context.return_value.Process.assert_called_with(
            target=_execute_pytest_subprocess,
            args=[["--option", "--ignore=batata"], mock_queue, pyrunner_stdout, True],
        )
        mock_sys_path.append.assert_called_with("current directory")

    @patch("codecov_cli.runners.python_standard_runner.subprocess")
    def test_execute_pytest_fail(self, mock_subprocess):
        def side_effect(command, *args, **kwargs):
            raise CalledProcessError(
                cmd=command, returncode=2, stderr="Some error occured"
            )

        mock_subprocess.run.side_effect = side_effect

        with pytest.raises(Exception) as exp:
            _ = self.runner._execute_pytest(["--option", "--ignore=batata"])
        assert str(exp.value) == "Pytest did not run correctly"

    @patch("codecov_cli.runners.python_standard_runner.getcwd")
    @patch("codecov_cli.runners.python_standard_runner.path")
    @patch("codecov_cli.runners.python_standard_runner.get_context")
    def test_execute_pytest_strict_NOT_include_curr_dir(
        self, mock_get_context, mock_sys_path, mock_getcwd
    ):
        output = "Output in stdout"
        mock_queue = MagicMock()
        mock_queue.get.side_effect = [{"output": output}, {"result": ExitCode.OK}]
        mock_process = MagicMock()
        mock_process.exitcode = 0
        mock_get_context.return_value.Queue.return_value = mock_queue
        mock_get_context.return_value.Process.return_value = mock_process

        config_params = dict(include_curr_dir=False)
        runner = PythonStandardRunner(config_params=config_params)
        result = runner._execute_pytest_strict(["--option", "--ignore=batata"])
        mock_get_context.return_value.Queue.assert_called_with(2)
        mock_get_context.return_value.Process.assert_called_with(
            target=_execute_pytest_subprocess,
            args=[["--option", "--ignore=batata"], mock_queue, pyrunner_stdout, True],
        )
        assert mock_queue.get.call_count == 2
        assert result == output
        mock_sys_path.append.assert_not_called()
        mock_getcwd.assert_called()
        assert result == output

    def test_collect_tests(self, mocker):
        collected_test_list = [
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path_legacy_uploader"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_dry_run"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_verbose"
        ]
        mock_execute = mocker.patch.object(
            PythonStandardRunner,
            "_execute_pytest",
            return_value="\n".join(collected_test_list),
        )
        mock_execute_strict = mocker.patch.object(
            PythonStandardRunner,
            "_execute_pytest_strict",
            return_value="\n".join(collected_test_list),
        )

        collected_tests_from_runner = self.runner.collect_tests()
        mock_execute.assert_called_with(["-q", "--collect-only"])
        mock_execute_strict.assert_not_called()
        assert collected_tests_from_runner == collected_test_list

    def test_collect_tests_strict(self, mocker):
        collected_test_list = [
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path_legacy_uploader"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_dry_run"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_verbose"
        ]
        mock_execute = mocker.patch.object(
            PythonStandardRunner,
            "_execute_pytest",
            return_value="\n".join(collected_test_list),
        )
        mock_execute_strict = mocker.patch.object(
            PythonStandardRunner,
            "_execute_pytest_strict",
            return_value="\n".join(collected_test_list),
        )

        runner_config = {"strict_mode": True}
        runner = PythonStandardRunner(runner_config)
        collected_tests_from_runner = runner.collect_tests()
        mock_execute_strict.assert_called_with(["-q", "--collect-only"])
        mock_execute.assert_not_called()
        assert collected_tests_from_runner == collected_test_list

    def test_collect_tests_with_options(self, mocker):
        collected_test_list = [
            "tests/services/upload/test_upload_collector.py::test_fix_go_files"
            "tests/services/upload/test_upload_collector.py::test_fix_php_files"
        ]
        mock_execute = mocker.patch.object(
            PythonStandardRunner,
            "_execute_pytest",
            return_value="\n".join(collected_test_list),
        )

        config_params = dict(collect_tests_options=["--option=value", "-option"])
        runner_with_params = PythonStandardRunner(config_params)

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
        mock_execute = mocker.patch.object(PythonStandardRunner, "_execute_pytest")

        self.runner.process_labelanalysis_result(label_analysis_result)
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

    def test_process_label_analysis_result_strict(self, mocker):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        mock_execute = mocker.patch.object(PythonStandardRunner, "_execute_pytest")
        mock_execute_strict = mocker.patch.object(
            PythonStandardRunner, "_execute_pytest_strict"
        )

        runner_config = {"strict_mode": True}
        runner = PythonStandardRunner(runner_config)
        runner.process_labelanalysis_result(label_analysis_result)
        mock_execute.assert_not_called()
        args, kwargs = mock_execute_strict.call_args
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

    def test_process_label_analysis_skip_all_tests(self, mocker):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": [],
            "present_diff_labels": [],
            "global_level_labels": [],
        }
        mock_execute = mocker.patch.object(PythonStandardRunner, "_execute_pytest")

        self.runner.process_labelanalysis_result(label_analysis_result)
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
