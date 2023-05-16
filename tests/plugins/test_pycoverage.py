import pathlib
from unittest.mock import MagicMock

import pytest

from codecov_cli.helpers.folder_searcher import globs_to_regex
from codecov_cli.plugins.pycoverage import Pycoverage


@pytest.fixture
def xml_subprocess_mock(mocker):
    def xml_subprocess_side_effect(*args, cwd, **kwargs):
        (cwd / "coverage.xml").touch()
        return mocker.MagicMock(stdout=b"Wrote XML report to coverage.xml\n")

    yield mocker.patch(
        "codecov_cli.plugins.pycoverage.subprocess.run",
        side_effect=xml_subprocess_side_effect,
    )


@pytest.fixture
def json_subprocess_mock(mocker):
    def json_subprocess_side_effect(*args, cwd, **kwargs):
        (cwd / "coverage.json").touch()
        return mocker.MagicMock(stdout=b"Wrote JSON report to coverage.json\n")

    yield mocker.patch(
        "codecov_cli.plugins.pycoverage.subprocess.run",
        side_effect=json_subprocess_side_effect,
    )


@pytest.fixture
def combine_subprocess_mock(mocker):
    def combine_subprocess_side_effect(first_arg, *args, cwd, **kwargs):
        if first_arg[1] == "combine":
            (cwd / ".coverage").touch()
        return mocker.MagicMock()

    yield mocker.patch(
        "codecov_cli.plugins.pycoverage.subprocess.run",
        side_effect=combine_subprocess_side_effect,
    )


@pytest.fixture
def mocked_generator(mocker):
    def generate_XML_report_side_effect(working_dir, *args, **kwargs):
        (working_dir / "coverage.xml").touch()

    yield mocker.patch.object(
        Pycoverage,
        "_generate_XML_report",
        side_effect=generate_XML_report_side_effect,
    )


class TestPycoveragePathToCoverage(object):
    def test_path_from_config(self, tmp_path, mocker):
        (tmp_path / ".coverage").touch()
        config = {
            "project_root": tmp_path,
            "path_to_coverage_file": pathlib.Path.joinpath(tmp_path, ".coverage"),
        }
        plugin = Pycoverage(config)

        mock_search_path = mocker.patch("codecov_cli.plugins.pycoverage.search_files")
        path = plugin._get_path_to_coverage()
        assert path == pathlib.Path.joinpath(tmp_path, ".coverage")
        assert path.parent == tmp_path
        mock_search_path.assert_not_called()

    def test_path_from_config_fallback(self, tmp_path, mocker):
        config = {
            "project_root": tmp_path,
            "path_to_coverage_file": pathlib.Path.joinpath(tmp_path, ".coverage"),
        }
        plugin = Pycoverage(config)

        mock_search_path_return = MagicMock()
        mock_search_path = mocker.patch(
            "codecov_cli.plugins.pycoverage.search_files",
            return_value=mock_search_path_return,
        )
        path = plugin._get_path_to_coverage()
        mock_search_path.assert_called_with(
            tmp_path,
            [],
            filename_include_regex=globs_to_regex([".coverage", ".coverage.*"]),
            filename_exclude_regex=None,
        )
        assert path == mock_search_path_return.__next__.return_value


class TestPycoverageXMLReportGeneration(object):
    def test_coverage_combine_called_if_coverage_data_exist(
        self, tmp_path, mocker, combine_subprocess_mock
    ):
        config = {"project_root": tmp_path}
        Pycoverage(config)._generate_XML_report(tmp_path)
        assert not combine_subprocess_mock.called

        combine_subprocess_mock.reset_mock()

        coverage_file_names = [".coverage.ac", ".coverage.a", ".coverage.b"]
        for name in coverage_file_names:
            p = tmp_path / name
            p.touch()

        Pycoverage(config)._generate_XML_report(tmp_path)

        combine_subprocess_mock.assert_any_call(
            ["coverage", "combine", "-a"], cwd=tmp_path
        )
        assert (tmp_path / ".coverage").exists()

    def test_xml_reports_generated_if_coverage_file_exists(
        self, tmp_path, mocker, xml_subprocess_mock
    ):
        config = {"project_root": tmp_path}
        Pycoverage(config)._generate_XML_report(tmp_path)
        xml_subprocess_mock.assert_not_called()

        config = {"project_root": tmp_path}
        (tmp_path / ".coverage").touch()
        Pycoverage(config)._generate_XML_report(tmp_path)
        xml_subprocess_mock.assert_called_with(
            ["coverage", "xml", "-i"], cwd=tmp_path, capture_output=True
        )
        assert (tmp_path / ".coverage").exists()


class TestPycoverageJSONReportGeneration(object):
    def test_report_not_generated_if_coverage_not_there(
        self, tmp_path, mocker, json_subprocess_mock
    ):
        config = {"project_root": tmp_path}
        Pycoverage(config)._generate_JSON_report(tmp_path)
        json_subprocess_mock.assert_not_called()

    def test_reports_generated_if_coverage_file_exists(
        self, tmp_path, mocker, json_subprocess_mock
    ):
        config = {"project_root": tmp_path}
        (tmp_path / ".coverage").touch()
        Pycoverage(config)._generate_JSON_report(tmp_path)
        json_subprocess_mock.assert_called_with(
            ["coverage", "json", "--show-contexts"], cwd=tmp_path, capture_output=True
        )
        assert (tmp_path / ".coverage").exists()

    def test_reports_generated_with_no_context_if_option(
        self, tmp_path, mocker, json_subprocess_mock
    ):
        config = {"project_root": tmp_path, "include_contexts": False}
        (tmp_path / ".coverage").touch()
        Pycoverage(config)._generate_JSON_report(tmp_path)
        json_subprocess_mock.assert_called_with(
            ["coverage", "json"], cwd=tmp_path, capture_output=True
        )


class TestPycoverageRunPreparation(object):
    def test_run_preparation_creates_reports_in_root_dir(
        self, mocked_generator, tmp_path, mocker
    ):
        (tmp_path / ".coverage").touch()
        config = {"project_root": tmp_path}
        Pycoverage(config).run_preparation(None)
        assert (tmp_path / "coverage.xml").exists()
        mocked_generator.assert_called_with(tmp_path)

    def test_run_preparation_creates_reports_in_sub_dirs(
        self, mocked_generator, tmp_path, mocker
    ):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / ".coverage").touch()
        config = {"project_root": tmp_path}
        Pycoverage(config).run_preparation(None)

        assert (tmp_path / "sub" / "coverage.xml").exists()
        mocked_generator.assert_called_with(tmp_path / "sub")

    def test_aborts_plugin_if_coverage_is_not_installed(
        self, tmp_path, mocker, mocked_generator
    ):
        mocker.patch("codecov_cli.plugins.pycoverage.shutil.which", return_value=None)
        config = {"project_root": tmp_path}
        Pycoverage(config).run_preparation(None)
        assert not mocked_generator.called

    def test_run_preparation_creates_nothing_if_nothing(
        self, mocked_generator, tmp_path, mocker
    ):
        config = {"project_root": tmp_path}
        Pycoverage(config).run_preparation(None)
        assert not (tmp_path / "coverage.xml").exists()
        assert not mocked_generator.called
