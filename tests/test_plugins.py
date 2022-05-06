import pathlib
import typing
from unittest.mock import MagicMock, Mock, PropertyMock

import pytest

from codecov_cli.plugins.gcov import GcovPlugin
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
        def generate_XML_report_side_effect(*args, **kwargs):
            working_dir = args[0]
            working_dir = pathlib.Path(
                working_dir
            )  # make sure it is of type Path not strings to avoid exceptions

            (working_dir / "coverage.xml").touch()

        yield mocker.patch(
            "codecov_cli.plugins.pycoverage.Pycoverage._generate_XML_report",
            side_effect=generate_XML_report_side_effect,
        )

    def test_run_preparation_creates_reports_in_root_dir(
        self, mocked_generator, tmp_path
    ):

        Pycoverage(tmp_path).run_preparation(None)
        assert not (tmp_path / "coverage.xml").exists()
        mocked_generator.not_called()

        (tmp_path / ".coverage").touch()
        Pycoverage(tmp_path).run_preparation(None)
        assert (tmp_path / "coverage.xml").exists()

    def test_run_preparation_creates_reports_in_sub_dirs(
        self, mocked_generator, tmp_path
    ):

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


class TestGcov(object):
    def create_and_add_paths(
        self,
        files: typing.List[str],
        dir: pathlib.Path,
        paths: typing.Set[pathlib.Path],
    ):
        for file in files:
            (dir / file).touch()
            paths.add(dir / file)

    def test_matched_paths_with_gcno_files_only(self, tmp_path):
        expected_matches = set()

        self.create_and_add_paths(
            ["a.cpp.gcno", "b.cpp.gcno", "c.gcno"], tmp_path, expected_matches
        )

        sub = tmp_path / "sub"
        sub.mkdir()

        self.create_and_add_paths(
            ["k.cpp.gcno", ".gcno", "random.gcno"], sub, expected_matches
        )

        actual_matches = set(GcovPlugin(tmp_path)._get_matched_paths())

        assert actual_matches == expected_matches

    def test_matched_paths_with_patterns_to_include(self, tmp_path):
        expected_matches = set()
        self.create_and_add_paths(
            [
                "a.cpp.gcno",
                "b.cpp.gcno",
                "c.gcno",
                "aaaab.txt",
                "k.txt",
                "package.json",
                "package-lock.json",
            ],
            tmp_path,
            expected_matches,
        )

        sub = tmp_path / "sub"
        sub.mkdir()

        self.create_and_add_paths(
            ["a.cpp.gcno", "b.cpp.gcno", "c.gcno", "package.json"],
            sub,
            expected_matches,
        )

        subsub = sub / "sub"
        subsub.mkdir()

        self.create_and_add_paths(
            ["a.cpp.gcno", "b.cpp.gcno", "c.gcno", "coverage.xml"],
            subsub,
            expected_matches,
        )

        actual_matches = set(
            GcovPlugin(
                tmp_path, ["*/*.gcno/*", "*.json", "*.txt", "*/coverage.xml"]
            )._get_matched_paths()
        )

        assert actual_matches == expected_matches

    def test_matched_paths_with_patterns_to_ignore(self, tmp_path):
        expected_matches = set()
        self.create_and_add_paths(
            [
                "a.cpp.gcno",
                "b.cpp.gcno",
                "c.gcno",
                "aaaab.txt",
                "k.txt",
                "package.json",
            ],
            tmp_path,
            expected_matches,
        )

        sub = tmp_path / "sub"
        sub.mkdir()

        self.create_and_add_paths(
            ["a.cpp.gcno", "b.cpp.gcno", "c.gcno", "package.json"],
            sub,
            expected_matches,
        )

        subsub = sub / "sub"
        subsub.mkdir()

        self.create_and_add_paths(
            ["a.cpp.gcno", "b.cpp.gcno", "c.gcno", "coverage.xml"],
            subsub,
            expected_matches,
        )

        # to ignore
        tmp_path.touch("package-lock.json")

        git = sub / ".git"
        git.mkdir()

        git.touch("a.gcno")
        git.touch("b.gcno")

        (git / "somedir").mkdir()
        (git / "somedir" / "f.gcno").mkdir()
        (git / "somedir" / "f.json").mkdir()

        actual_matches = set(
            GcovPlugin(
                tmp_path,
                ["*/*.gcno/*", "*.json", "*.txt", "*/coverage.xml"],
                ["*/.git/*", "*package-lock.json"],
            )._get_matched_paths()
        )

        assert actual_matches == expected_matches

    def test_run_preparation_gcov_not_installed(self, mocker, tmp_path):
        m = mocker.patch("codecov_cli.plugins.gcov.GcovPlugin._get_matched_paths")
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=None)

        GcovPlugin(tmp_path).run_preparation(collector=None)

        m.assert_not_called()

    def test_run_preparation_no_gcno_files(self, mocker, tmp_path):

        mocker.patch(
            "codecov_cli.plugins.gcov.GcovPlugin._get_matched_paths", return_value=[]
        )
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=True)

        res = GcovPlugin(tmp_path).run_preparation(collector=None)

        assert b"Usage: gcov [OPTION...] SOURCE|OBJ..." in res.stderr

    def test_run_preparation_with_gcno_files(self, mocker, tmp_path):
        mocker.patch(
            "codecov_cli.plugins.gcov.GcovPlugin._get_matched_paths", return_value=[]
        )
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=True)

        mock = MagicMock()
        mock.stdout = b"File 'main.c'\nLines executed:0.00% of 11\nBranches executed:0.00% of 4\nTaken at least once:0.00% of 4\nCalls executed:0.00% of 5\nCreating 'main.c.gcov'\n\nLines executed:0.00% of 11"

        moocked_subprocess = mocker.patch(
            "codecov_cli.plugins.gcov.subprocess.run", return_value=mock
        )

        res = GcovPlugin(tmp_path).run_preparation(collector=None)

        assert res.stdout == mock.stdout
