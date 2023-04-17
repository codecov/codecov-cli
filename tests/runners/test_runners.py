from unittest.mock import patch

from codecov_cli.runners import get_runner
from codecov_cli.runners.python_standard_runner import PythonStandardRunner


class TestRunners(object):
    def test_get_standard_runners(self):
        assert isinstance(get_runner({}, "python"), PythonStandardRunner)
        # TODO: Extend with other standard runners once we create them (e.g. JS)

    def test_python_standard_runner_with_options(self):
        config_params = dict(
            collect_tests_options=["--option=value", "-option"],
        )
        runner_instance = get_runner({"runners": {"python": config_params}}, "python")
        assert isinstance(runner_instance, PythonStandardRunner)
        assert runner_instance.params == {**config_params, "include_curr_dir": False}

    @patch("codecov_cli.runners._load_runner_from_yaml")
    def test_get_runner_from_yaml(self, mock_load_runner):
        config = {"runners": {"my_runner": {"path": "path_to_my_runner"}}}
        mock_load_runner.return_value = "MyRunner()"
        assert get_runner(config, "my_runner") == "MyRunner()"
        mock_load_runner.assert_called_with({"path": "path_to_my_runner"})
