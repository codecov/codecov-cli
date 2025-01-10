import pathlib
from unittest.mock import Mock

from codecov_cli.helpers.config import _find_codecov_yamls, load_cli_config


def test_load_config(mocker):
    path = pathlib.Path("samples/example_cli_config.yml")
    result = load_cli_config(path)
    assert result == {
        "runners": {"python": {"collect_tests_options": ["--ignore", "batata"]}}
    }


def test_load_config_doesnt_exist(mocker):
    path = pathlib.Path("doesnt/exist")
    result = load_cli_config(path)
    assert result is None


def test_load_config_not_file(mocker):
    path = pathlib.Path("samples/")
    result = load_cli_config(path)
    assert result is None


def test_find_codecov_yaml(mocker):
    fake_project_root = pathlib.Path.cwd() / "samples" / "fake_project"

    mock_vcs = Mock()
    mock_vcs.get_network_root.return_value = fake_project_root
    mocker.patch(
        "codecov_cli.helpers.config.get_versioning_system", return_value=mock_vcs
    )

    expected_yamls = [
        fake_project_root / "codecov.yaml",
        fake_project_root / ".codecov.yaml",
        fake_project_root / "codecov.yml",
        fake_project_root / ".codecov.yml",
        fake_project_root / ".github" / "codecov.yaml",
        fake_project_root / ".github" / ".codecov.yaml",
        fake_project_root / ".github" / "codecov.yml",
        fake_project_root / ".github" / ".codecov.yml",
        fake_project_root / "dev" / "codecov.yaml",
        fake_project_root / "dev" / ".codecov.yaml",
        fake_project_root / "dev" / "codecov.yml",
        fake_project_root / "dev" / ".codecov.yml",
    ]

    assert sorted(_find_codecov_yamls()) == sorted(expected_yamls)


def test_load_config_finds_yaml(mocker):
    fake_project_root = pathlib.Path.cwd() / "samples" / "fake_project"

    mock_vcs = Mock()
    mock_vcs.get_network_root.return_value = fake_project_root
    mocker.patch(
        "codecov_cli.helpers.config.get_versioning_system", return_value=mock_vcs
    )

    result = load_cli_config(None)
    assert result == {
        "runners": {"python": {"collect_tests_options": ["--ignore", "batata"]}}
    }
