from unittest.mock import patch

import pytest

from codecov_cli.runners import _load_runner_from_yaml, get_runner
from codecov_cli.runners.dan_runner import DoAnythingNowRunner
from codecov_cli.runners.pytest_standard_runner import PytestStandardRunner
from tests.factory import FakeRunner


class TestRunners(object):
    def test_get_standard_runners(self):
        assert isinstance(get_runner({}, "pytest"), PytestStandardRunner)
        assert isinstance(get_runner({}, "dan"), DoAnythingNowRunner)
        # TODO: Extend with other standard runners once we create them (e.g. JS)

    def test_pytest_standard_runner_with_options(self):
        config_params = dict(
            collect_tests_options=["--option=value", "-option"],
        )
        runner_instance = get_runner({"runners": {"pytest": config_params}}, "pytest")
        assert isinstance(runner_instance, PytestStandardRunner)
        assert (
            runner_instance.params.collect_tests_options
            == config_params["collect_tests_options"]
        )
        assert runner_instance.params.coverage_root == "./"

    def test_pytest_standard_runner_with_options_and_dynamic_options(self):
        config_params = dict(
            collect_tests_options=["--option=value", "-option"],
        )
        runner_instance = get_runner(
            {"runners": {"pytest": config_params}},
            "pytest",
            {"python_path": "path/to/python"},
        )
        assert isinstance(runner_instance, PytestStandardRunner)
        assert (
            runner_instance.params.collect_tests_options
            == config_params["collect_tests_options"]
        )
        assert runner_instance.params.python_path == "path/to/python"
        assert runner_instance.params.coverage_root == "./"

    def test_pytest_standard_runner_with_options_backwards_compatible(self):
        config_params = dict(
            collect_tests_options=["--option=value", "-option"],
        )
        runner_instance = get_runner({"runners": {"python": config_params}}, "pytest")
        assert isinstance(runner_instance, PytestStandardRunner)
        assert (
            runner_instance.params.collect_tests_options
            == config_params["collect_tests_options"]
        )
        assert runner_instance.params.coverage_root == "./"

    def test_get_dan_runner_with_params(self):
        config = {
            "runners": {
                "dan": {
                    "collect_tests_command": ["mycommand", "--collect"],
                    "process_labelanalysis_result_command": ["mycommand", "--process"],
                }
            }
        }
        runner = get_runner(config, "dan")
        assert isinstance(runner, DoAnythingNowRunner)
        assert runner.params == config["runners"]["dan"]

    @patch("codecov_cli.runners._load_runner_from_yaml")
    def test_get_runner_from_yaml(self, mock_load_runner):
        config = {"runners": {"my_runner": {"path": "path_to_my_runner"}}}
        mock_load_runner.return_value = "MyRunner()"
        assert get_runner(config, "my_runner") == "MyRunner()"
        mock_load_runner.assert_called_with(
            {"path": "path_to_my_runner"}, dynamic_params={}
        )

    def test_load_runner_from_yaml(self, mocker):
        fake_module = mocker.MagicMock(FakeRunner=FakeRunner)
        mocker.patch("codecov_cli.runners.import_module", return_value=fake_module)
        res = _load_runner_from_yaml(
            {
                "module": "mymodule.runner",
                "class": "FakeRunner",
                "params": {"collect_tests_response": ["list", "of", "labels"]},
            },
            {},
        )
        assert isinstance(res, FakeRunner)
        assert res.collect_tests() == ["list", "of", "labels"]
        assert res.process_labelanalysis_result({}) == "I ran tests :D"

    def test_load_runner_from_yaml_module_not_found(self, mocker):
        def side_effect(*args, **kwargs):
            raise ModuleNotFoundError()

        mocker.patch("codecov_cli.runners.import_module", side_effect=side_effect)
        with pytest.raises(ModuleNotFoundError):
            _load_runner_from_yaml(
                {
                    "module": "mymodule.runner",
                    "class": "FakeRunner",
                    "params": {"collect_tests_response": ["list", "of", "labels"]},
                },
                {},
            )

    def test_load_runner_from_yaml_class_not_found(self, mocker):
        import tests.factory as fake_module

        mocker.patch("codecov_cli.runners.import_module", return_value=fake_module)

        with pytest.raises(AttributeError):
            _load_runner_from_yaml(
                {
                    "module": "mymodule.runner",
                    "class": "WrongClassName",
                    "params": {"collect_tests_response": ["list", "of", "labels"]},
                },
                {},
            )

    def test_load_runner_from_yaml_fail_instantiate_class(self, mocker):
        fake_module = mocker.MagicMock(FakeRunner=FakeRunner)
        mocker.patch("codecov_cli.runners.import_module", return_value=fake_module)
        with pytest.raises(TypeError):
            _load_runner_from_yaml(
                {
                    "module": "mymodule.runner",
                    "class": "FakeRunner",
                    "params": {"wrong_params": ["list", "of", "labels"]},
                },
                {},
            )
