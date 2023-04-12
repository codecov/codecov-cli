from unittest.mock import MagicMock, patch

from codecov_cli.runners.python_standard_runner import PythonStandardRunner


class TestPythonStandardRunner(object):
    runner = PythonStandardRunner()

    @patch("codecov_cli.runners.python_standard_runner.subprocess.run")
    def test_collect_tests(self, mock_run):
        collected_test_list = [
            "tests/services/upload/test_upload_collector.py::test_fix_go_files"
            "tests/services/upload/test_upload_collector.py::test_fix_php_files"
            "tests/services/upload/test_upload_collector.py::test_fix_for_cpp_swift_vala"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path_legacy_uploader"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_happy_path"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_dry_run"
            "tests/services/upload/test_upload_service.py::test_do_upload_logic_verbose"
        ]
        mock_stdout = MagicMock()
        mock_stdout.configure_mock(
            **{"stdout.decode.return_value": "\n".join(collected_test_list)}
        )
        mock_run.return_value = mock_stdout
        collected_tests_from_runner = self.runner.collect_tests()
        assert collected_tests_from_runner == collected_test_list
        mock_run.assert_called_with(
            ["python", "-m", "pytest", "-q", "--collect-only"],
            capture_output=True,
            check=True,
        )

    @patch("codecov_cli.runners.python_standard_runner.subprocess.run")
    def test_process_label_analysis_result(self, mock_run):
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        self.runner.process_labelanalysis_result(label_analysis_result)
        args, kwargs = mock_run.call_args
        assert kwargs == {"check": True}
        assert isinstance(args[0], list)
        actual_command = args[0]
        assert actual_command[:5] == [
            "python",
            "-m",
            "pytest",
            "--cov=./",
            "--cov-context=test",
        ]
        assert sorted(actual_command[5:]) == [
            "test_absent",
            "test_global",
            "test_in_diff",
        ]
