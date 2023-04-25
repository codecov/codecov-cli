import pathlib

from codecov_cli.helpers.config import load_cli_config


def test_load_config(mocker):
    path = pathlib.Path("samples/example_cli_config.yml")
    result = load_cli_config(path)
    assert result == {
        "runners": {"python": {"collect_tests_options": ["--ignore", "batata"]}}
    }


def test_load_config_doesnt_exist(mocker):
    path = pathlib.Path("doesnt/exist")
    result = load_cli_config(path)
    assert result == None


def test_load_config_not_file(mocker):
    path = pathlib.Path("samples/")
    result = load_cli_config(path)
    assert result == None
