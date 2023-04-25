from typing import List
from unittest.mock import MagicMock, patch

import pytest
from pytest import ExitCode

from codecov_cli.runners.python_standard_runner import (
    PythonStandardRunner,
    PythonStandardRunnerConfigParams,
)


class TestPythonStandardRunner(object):
    runner = PythonStandardRunner()
    output_noise = "\n\n========================================================== warnings summary ===========================================================\n../codecov-api/venv/lib/python3.9/site-packages/pytest_asyncio/plugin.py:191\n  /Users/giovannimguidini/Projects/GitHub/codecov-api/venv/lib/python3.9/site-packages/pytest_asyncio/plugin.py:191: DeprecationWarning: The 'asyncio_mode' default value will change to 'strict' in future, please explicitly use 'asyncio_mode=strict' or 'asyncio_mode=auto' in pytest configuration file.\n    config.issue_config_time_warning(LEGACY_MODE, stacklevel=2)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n508 tests collected in 0.26s\n<ExitCode.OK: 0>\n"

    def test_init_with_params(self):
        assert self.runner.params == PythonStandardRunnerConfigParams(
            collect_tests_options=[], include_curr_dir=True
        )
        config_params = PythonStandardRunnerConfigParams(
            collect_tests_options=["--option=value", "-option"], include_curr_dir=True
        )
        runner_with_params = PythonStandardRunner(config_params)
        assert runner_with_params.params == config_params

    @patch(
        "codecov_cli.runners.python_standard_runner.getcwd",
        return_value="current directory",
    )
    @patch("codecov_cli.runners.python_standard_runner.path")
    @patch("codecov_cli.runners.python_standard_runner.StringIO")
    @patch("codecov_cli.runners.python_standard_runner.pytest")
    def test_execute_pytest(
        self, mock_pytest, mock_stringio, mock_sys_path, mock_getcwd
    ):
        output = "Output in stdout"
        mock_getvalue = MagicMock(return_value=output)
        mock_stringio.return_value.__enter__.return_value.getvalue = mock_getvalue
        mock_pytest.main.return_value = ExitCode.OK

        result = self.runner._execute_pytest(["--option", "--ignore=batata"])
        mock_pytest.main.assert_called_with(["--option", "--ignore=batata"])
        mock_stringio.assert_called()
        mock_getvalue.assert_called()
        mock_sys_path.append.assert_called_with("current directory")
        mock_sys_path.remove.assert_called_with("current directory")
        assert result == output

    @patch(
        "codecov_cli.runners.python_standard_runner.getcwd",
        return_value="current directory",
    )
    @patch("codecov_cli.runners.python_standard_runner.path")
    @patch("codecov_cli.runners.python_standard_runner.StringIO")
    @patch("codecov_cli.runners.python_standard_runner.pytest")
    def test_execute_pytest_fail(
        self, mock_pytest, mock_stringio, mock_sys_path, mock_getcwd
    ):
        output = "Output in stdout"
        mock_getvalue = MagicMock(return_value=output)
        mock_stringio.return_value.__enter__.return_value.getvalue = mock_getvalue
        mock_pytest.main.return_value = ExitCode.INTERNAL_ERROR

        with pytest.raises(Exception) as exp:
            result = self.runner._execute_pytest(["--option", "--ignore=batata"])
        assert str(exp.value) == "Pytest did not run correctly"
        mock_pytest.main.assert_called_with(["--option", "--ignore=batata"])
        mock_stringio.assert_called()
        mock_getvalue.assert_called()
        mock_sys_path.append.assert_called_with("current directory")

    @patch("codecov_cli.runners.python_standard_runner.getcwd")
    @patch("codecov_cli.runners.python_standard_runner.path")
    @patch("codecov_cli.runners.python_standard_runner.StringIO")
    @patch("codecov_cli.runners.python_standard_runner.pytest")
    def test_execute_pytest_NOT_include_curr_dir(
        self, mock_pytest, mock_stringio, mock_sys_path, mock_getcwd
    ):
        output = "Output in stdout"
        mock_getcwd.return_value = "current directory"
        mock_getvalue = MagicMock(return_value=output)
        mock_stringio.return_value.__enter__.return_value.getvalue = mock_getvalue
        mock_pytest.main.return_value = ExitCode.OK

        config_params = PythonStandardRunnerConfigParams(include_curr_dir=False)
        runner = PythonStandardRunner(config_params)
        result = runner._execute_pytest(["--option", "--ignore=batata"])
        mock_pytest.main.assert_called_with(["--option", "--ignore=batata"])
        mock_stringio.assert_called()
        mock_getvalue.assert_called()
        mock_sys_path.append.assert_not_called()
        mock_getcwd.assert_called()
        assert result == output

    @patch("codecov_cli.runners.python_standard_runner.StringIO")
    @patch("codecov_cli.runners.python_standard_runner.pytest")
    def test_collect_tests(self, mock_pytest, mock_stringio):
        collected_test_list = [
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path_legacy_uploader"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_dry_run"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_verbose"
        ]
        mock_getvalue = MagicMock(
            return_value="\n".join(collected_test_list + [self.output_noise])
        )
        mock_stringio.return_value.__enter__.return_value.getvalue = mock_getvalue
        mock_pytest.main.return_value = ExitCode.OK

        collected_tests_from_runner = self.runner.collect_tests()
        mock_pytest.main.assert_called_with(["-q", "--collect-only"])
        mock_stringio.assert_called()
        mock_getvalue.assert_called()
        assert collected_tests_from_runner == collected_test_list

    @patch("codecov_cli.runners.python_standard_runner.StringIO")
    @patch("codecov_cli.runners.python_standard_runner.pytest")
    def test_collect_tests_with_options(self, mock_pytest, mock_stringio):
        collected_test_list = [
            "tests/services/upload/test_upload_collector.py::test_fix_go_files"
            "tests/services/upload/test_upload_collector.py::test_fix_php_files"
        ]
        mock_getvalue = MagicMock(
            return_value="\n".join(collected_test_list + [self.output_noise])
        )
        mock_stringio.return_value.__enter__.return_value.getvalue = mock_getvalue
        mock_pytest.main = MagicMock(return_value=ExitCode.OK)

        config_params = PythonStandardRunnerConfigParams(
            collect_tests_options=["--option=value", "-option"],
        )
        runner_with_params = PythonStandardRunner(config_params)

        collected_tests_from_runner = runner_with_params.collect_tests()
        mock_pytest.main.assert_called_with(
            ["-q", "--collect-only", "--option=value", "-option"]
        )
        mock_stringio.assert_called()
        mock_getvalue.assert_called()
        assert collected_tests_from_runner == collected_test_list

    @patch("codecov_cli.runners.python_standard_runner.StringIO")
    @patch("codecov_cli.runners.python_standard_runner.pytest")
    def test_process_label_analysis_result(self, mock_pytest, mock_stringio):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        mock_pytest.main.return_value = ExitCode.OK

        self.runner.process_labelanalysis_result(label_analysis_result)
        mock_stringio.assert_called()
        mock_pytest.main.assert_called()
        args, kwargs = mock_pytest.main.call_args
        assert kwargs == {}
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
