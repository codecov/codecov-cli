import pathlib
from unittest.mock import MagicMock

import pytest

from codecov_cli.plugins.pycoverage import Pycoverage


class TestPycoverage(object):
    @pytest.fixture
    def combine_subprocess_mock(self, mocker):
        def combine_subprocess_side_effect(*args, **kwargs):
            if args[0][1] != "combine":
                return MagicMock()

            # path is the same as tmp_path
            path = kwargs["cwd"]

            (path / ".coverage").touch()
            return MagicMock()

        yield mocker.patch(
            "codecov_cli.plugins.pycoverage.subprocess.run",
            side_effect=combine_subprocess_side_effect,
        )

    def test_coverage_combine_called_if_coverage_data_exist(
        self, tmp_path, mocker, combine_subprocess_mock
    ):
        Pycoverage(tmp_path)._generate_XML_report(tmp_path)

        with pytest.raises(AssertionError):
            combine_subprocess_mock.assert_any_call(
                ["coverage", "combine", "-a"], cwd=tmp_path
            )

        combine_subprocess_mock.reset_mock()

        coverage_file_names = [".coverage.ac", ".coverage.a", ".coverage.b"]
        for name in coverage_file_names:
            p = tmp_path / name
            p.touch()

        Pycoverage(tmp_path)._generate_XML_report(tmp_path)

        combine_subprocess_mock.assert_any_call(
            ["coverage", "combine", "-a"], cwd=tmp_path
        )
        assert (tmp_path / ".coverage").exists()

    @pytest.fixture
    def xml_subprocess_mock(self, mocker):
        def xml_subprocess_side_effect(*args, **kwargs):
            # path is the same as tmp_path
            path = kwargs["cwd"]

            (path / "coverage.xml").touch()
            mock = MagicMock()
            mock.stdout = b"Wrote XML report to coverage.xml\n"

            return mock

        yield mocker.patch(
            "codecov_cli.plugins.pycoverage.subprocess.run",
            side_effect=xml_subprocess_side_effect,
        )

    def test_xml_reports_generated_if_coverage_file_exists(
        self, tmp_path, mocker, xml_subprocess_mock
    ):

        Pycoverage(tmp_path)._generate_XML_report(tmp_path)
        xml_subprocess_mock.assert_not_called()

        (tmp_path / ".coverage").touch()
        Pycoverage(tmp_path)._generate_XML_report(tmp_path)
        xml_subprocess_mock.assert_called_with(
            ["coverage", "xml", "-i"], cwd=tmp_path, capture_output=True
        )
        assert (tmp_path / ".coverage").exists()

    @pytest.fixture
    def mocked_generator(self, mocker):
        def generate_XML_report_side_effect(working_dir, *args, **kwargs):
            working_dir = pathlib.Path(
                working_dir
            )  # make sure it is of type Path not strings to avoid exceptions

            (working_dir / "coverage.xml").touch()

        yield mocker.patch(
            "codecov_cli.plugins.pycoverage.Pycoverage._generate_XML_report",
            side_effect=generate_XML_report_side_effect,
        )

    def test_run_preparation_creates_reports_in_root_dir(
        self, mocked_generator, tmp_path, mocker
    ):

        mocker.patch(
            "codecov_cli.plugins.pycoverage.search_files", return_value=iter([])
        )
        Pycoverage(tmp_path).run_preparation(None)
        assert not (tmp_path / "coverage.xml").exists()
        mocked_generator.not_called()

        (tmp_path / ".coverage").touch()

        mocker.patch(
            "codecov_cli.plugins.pycoverage.search_files",
            return_value=iter([(tmp_path / ".coverage")]),
        )
        Pycoverage(tmp_path).run_preparation(None)
        assert (tmp_path / "coverage.xml").exists()

    def test_run_preparation_creates_reports_in_sub_dirs(
        self, mocked_generator, tmp_path, mocker
    ):
        mocker.patch(
            "codecov_cli.plugins.pycoverage.search_files",
            return_value=iter([(tmp_path / "sub" / ".coverage")]),
        )

        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / ".coverage").touch()
        Pycoverage(tmp_path).run_preparation(None)

        assert (tmp_path / "sub" / "coverage.xml").exists()

    def test_aborts_plugin_if_coverage_is_not_installed(
        self, tmp_path, mocker, mocked_generator
    ):

        mocker.patch("codecov_cli.plugins.pycoverage.shutil.which", return_value=None)
        Pycoverage(tmp_path).run_preparation(None)

        mocked_generator.assert_not_called()
