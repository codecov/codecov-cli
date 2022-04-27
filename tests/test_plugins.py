import pathlib
from unittest.mock import MagicMock, Mock, PropertyMock

import pytest

from codecov_cli.plugins.pycoverage import Pycoverage


class TestPycoverage(object):
    def test_coverage_combine_called_if_coverage_data_exist(self, tmp_path, mocker):
        def combine_subprocess_side_effect(*args, **kwargs):
            try:
                if args[0][1] != "combine":
                    return MagicMock()
            except IndexError:
                return MagicMock()

            # path is the same as tmp_path
            path = kwargs["cwd"]

            (path / ".coverage").touch()
            return MagicMock()

        subprocess_mock = mocker.patch(
            "codecov_cli.plugins.pycoverage.subprocess.run",
            side_effect=combine_subprocess_side_effect,
        )

        # test coverage combine is not called if no coverage data exist
        Pycoverage()._generate_XML_report(tmp_path)

        with pytest.raises(AssertionError):
            subprocess_mock.assert_any_call(["coverage", "combine", "-a"], cwd=tmp_path)

        # test coverage combine is called if coverage data exist
        subprocess_mock.reset_mock()
        coverage_file_names = [".coverage.ac", ".coverage.a", ".coverage.b"]
        for name in coverage_file_names:
            p = tmp_path / name
            p.touch()

        Pycoverage()._generate_XML_report(tmp_path)

        subprocess_mock.assert_any_call(["coverage", "combine", "-a"], cwd=tmp_path)
        assert (tmp_path / ".coverage").exists()

    def test_xml_reports_generated_if_coverage_file_exists(self, tmp_path, mocker):
        def xml_subprocess_side_effect(*args, **kwargs):
            try:
                if args[0][1] != "xml":
                    return MagicMock()
            except IndexError:
                return MagicMock()

            # path is the same as tmp_path
            path = kwargs["cwd"]

            (path / "coverage.xml").touch()
            mock = MagicMock()
            mock.stdout = b"Wrote XML report to coverage.xml\n"

            return mock

        subprocess_mock = mocker.patch(
            "codecov_cli.plugins.pycoverage.subprocess.run",
            side_effect=xml_subprocess_side_effect,
        )

        # test returns false if .coverage file doesn't exist
        assert not Pycoverage()._generate_XML_report(tmp_path)
        subprocess_mock.assert_not_called()

        # test returns true if .coverage file exist
        (tmp_path / ".coverage").touch()
        assert Pycoverage()._generate_XML_report(tmp_path)
        subprocess_mock.assert_called_with(
            ["coverage", "xml", "-i"], cwd=tmp_path, capture_output=True
        )

    @pytest.fixture
    def mocked_generator(self, mocker):
        def generate_XML_report_side_effect(*args, **kwargs):
            working_dir = args[0]
            working_dir = pathlib.Path(
                working_dir
            )  # make sure it is of type Path not strings to avoid exceptions

            if (working_dir / ".coverage").exists():
                (working_dir / "coverage.xml").touch()
                return True

            return False

        yield mocker.patch(
            "codecov_cli.plugins.pycoverage.Pycoverage._generate_XML_report",
            side_effect=generate_XML_report_side_effect,
        )

    @pytest.fixture
    def mocked_getcwd(self, mocker, tmp_path):
        mocker.patch("codecov_cli.plugins.pycoverage.os.getcwd", return_value=tmp_path)

    @pytest.fixture
    def mocked_glob(self, mocker, tmp_path):
        def glob_side_effect(*args, **kwargs):
            # Ignore recursive argument since it is not defined in pathlib.Path.glob
            return list(tmp_path.glob(args[0]))

        mocker.patch(
            "codecov_cli.plugins.pycoverage.glob", side_effect=glob_side_effect
        )

    def test_run_preparation_creates_reports_in_root_dir(
        self, mocked_generator, mocked_getcwd, tmp_path, mocked_glob
    ):

        Pycoverage().run_preparation(None)
        assert not (tmp_path / "coverage.xml").exists()

        mocked_generator.reset_mock()

        (tmp_path / ".coverage").touch()
        Pycoverage().run_preparation(None)
        assert (tmp_path / "coverage.xml").exists()

        mocked_generator.assert_called_once()

    def test_run_preparation_creates_reports_in_sub_dirs(
        self, mocked_generator, mocked_getcwd, tmp_path, mocked_glob
    ):

        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / ".coverage").touch()
        Pycoverage().run_preparation(None)

        assert (tmp_path / "sub" / "coverage.xml").exists()

    def test_aborts_plugin_if_coverage_is_not_installed(self, mocker, mocked_generator):

        mocker.patch("codecov_cli.plugins.pycoverage.shutil.which", return_value=None)
        Pycoverage().run_preparation(None)

        mocked_generator.assert_not_called()
