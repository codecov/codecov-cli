from codecov_cli.plugins.gcov import GcovPlugin


class TestGcov(object):
    def test_run_preparation_gcov_not_installed(self, mocker, tmp_path, capsys):
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=None)
        assert GcovPlugin(tmp_path).run_preparation(collector=None) is None
        assert "gcov is not installed or can't be found." in capsys.readouterr().err

    def test_run_preparation_no_coverage_data(self, mocker, tmp_path, capsys):
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=True)
        assert GcovPlugin(tmp_path).run_preparation(collector=None) is None
        assert "No gcov data found." in capsys.readouterr().err

    def test_run_preparation_with_coverage_data(self, mocker, tmp_path):
        (tmp_path / "main.gcno").touch()
        mocker.patch("codecov_cli.plugins.gcov.shutil.which", return_value=True)

        mock = mocker.MagicMock(
            stdout=b"File 'main.c'\nLines executed:0.00% of 11\nBranches executed:0.00% of 4\nTaken at least once:0.00% of 4\nCalls executed:0.00% of 5\nCreating 'main.c.gcov'\n\nLines executed:0.00% of 11"
        )

        mocker.patch("codecov_cli.plugins.gcov.subprocess.run", return_value=mock)

        res = GcovPlugin(tmp_path).run_preparation(collector=None)

        assert res.messages == [mock.stdout]
