import pathlib
import typing
from unittest.mock import MagicMock

from codecov_cli.plugins.gcov import GcovPlugin


class TestGcov(object):
    def test_run_preparation_gcov_not_installed(self, mocker, tmp_path, capsys):
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=None)

        GcovPlugin(tmp_path).run_preparation(collector=None)

        assert "gcov is not installed or can't be found." in capsys.readouterr().out

    def test_run_preparation_no_coverage_data(self, mocker, tmp_path, capsys):

        mocker.patch("codecov_cli.plugins.gcov.search_files", return_value=[])
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=True)

        GcovPlugin(tmp_path).run_preparation(collector=None)

        assert "No gcov data found." in capsys.readouterr().out

    def test_run_preparation_with_coverage_data(self, mocker, tmp_path):
        mocker.patch(
            "codecov_cli.plugins.gcov.search_files", return_value=["main.gcno"]
        )
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=True)

        mock = MagicMock()
        mock.stdout = b"File 'main.c'\nLines executed:0.00% of 11\nBranches executed:0.00% of 4\nTaken at least once:0.00% of 4\nCalls executed:0.00% of 5\nCreating 'main.c.gcov'\n\nLines executed:0.00% of 11"

        mocker.patch(
            "codecov_cli.plugins.gcov.subprocess.run", return_value=mock
        )

        res = GcovPlugin(tmp_path).run_preparation(collector=None)

        assert res.stdout == mock.stdout
