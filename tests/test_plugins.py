import pathlib
from unittest.mock import MagicMock


from codecov_cli.plugins.gcov import GcovPlugin


class TestGcov(object):
    def create_and_add_paths(
        self, files: list[str], dir: pathlib.Path, paths: set[pathlib.Path]
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
