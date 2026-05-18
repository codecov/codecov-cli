from unittest.mock import MagicMock, patch

import pytest

from codecov_cli.runners.dan_runner import DoAnythingNowRunner


class TestDoAnythingNowRunner(object):
    @patch("codecov_cli.runners.dan_runner.subprocess.run")
    def test_collect_tests(self, mock_run):
        test_list = ["test_1", "test_2", "test_3"]
        mock_stdout = MagicMock()
        mock_stdout.configure_mock(
            **{"stdout.decode.return_value": "\n".join(test_list)}
        )
        mock_run.return_value = mock_stdout

        config_options = {"collect_tests_command": ["mycommand", "--option"]}
        runner = DoAnythingNowRunner(config_options)
        assert runner.params == config_options
        resp = runner.collect_tests()
        assert resp == test_list
        mock_run.assert_called_with(
            ["mycommand", "--option"],
            capture_output=True,
            check=True,
        )

    def test_collect_test_no_config(self):
        runner = DoAnythingNowRunner()
        with pytest.raises(Exception) as exp:
            runner.collect_tests()
        assert (
            str(exp.value)
            == "DAN runner missing 'collect_tests_command' configuration value"
        )

    @patch("codecov_cli.runners.dan_runner.subprocess.run")
    def test_process_labelanalysis_result(self, mock_run):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        cmd_output = "My command output"
        mock_stdout = MagicMock()
        mock_stdout.configure_mock(**{"stdout.decode.return_value": cmd_output})
        mock_run.return_value = mock_stdout
        config_options = {
            "process_labelanalysis_result_command": ["mycommand", "--option"]
        }
        runner = DoAnythingNowRunner(config_options)
        runner.process_labelanalysis_result(label_analysis_result)
        assert runner.params == config_options
        mock_run.assert_called_with(
            [
                "mycommand",
                "--option",
                '{"present_report_labels": ["test_present"], "absent_labels": ["test_absent"], "present_diff_labels": ["test_in_diff"], "global_level_labels": ["test_global"]}',
            ],
            capture_output=True,
            check=True,
        )

    @patch("codecov_cli.runners.dan_runner.subprocess.run")
    def test_process_labelanalysis_result_string_command(self, mock_run):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        cmd_output = "My command output"
        mock_stdout = MagicMock()
        mock_stdout.configure_mock(**{"stdout.decode.return_value": cmd_output})
        mock_run.return_value = mock_stdout
        config_options = {"process_labelanalysis_result_command": "mycommand --option"}
        runner = DoAnythingNowRunner(config_options)
        runner.process_labelanalysis_result(label_analysis_result)
        assert runner.params == config_options
        mock_run.assert_called_with(
            [
                "mycommand --option",
                '{"present_report_labels": ["test_present"], "absent_labels": ["test_absent"], "present_diff_labels": ["test_in_diff"], "global_level_labels": ["test_global"]}',
            ],
            capture_output=True,
            check=True,
        )

    def test_process_labelanalysis_result_no_config(self):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        runner = DoAnythingNowRunner()
        with pytest.raises(Exception) as exp:
            runner.process_labelanalysis_result(label_analysis_result)
        assert (
            str(exp.value)
            == "DAN runner missing 'process_labelanalysis_result_command' configuration value"
        )
