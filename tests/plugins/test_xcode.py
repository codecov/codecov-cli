import pathlib

from codecov_cli.plugins.xcode import XcodePlugin


class TestXcode(object):
    def act_like_xcrun_ran_succesfully(self, proj, type):
        output_filename = f"{proj}.{type}.coverage.txt"
        result_file = open(output_filename, "w")
        result_file.close()

    def act_like_xcrun_is_not_installed(self, mocker):
        mocker.patch("codecov_cli.plugins.xcode.shutil.which", return_value=None)

    def act_like_xcrun_is_installed(self, mocker):
        mocker.patch("codecov_cli.plugins.xcode.shutil.which", return_value=True)

    def test_no_swift_data_found(self, mocker, tmp_path, capsys):
        self.act_like_xcrun_is_installed(mocker)
        xcode_plugin = XcodePlugin(derived_data_folder=tmp_path).run_preparation(
            collector=None
        )
        output = capsys.readouterr().err.splitlines()
        assert xcode_plugin is None
        assert f"debug: DerivedData folder: {tmp_path}" in output
        assert "warning: No swift data found." in output

    def test_run_preparation_xcrun_not_installed(self, mocker, tmp_path, capsys):
        self.act_like_xcrun_is_not_installed(mocker)
        assert (
            XcodePlugin(derived_data_folder=tmp_path).run_preparation(collector=None)
            is None
        )
        assert "xcrun is not installed or can't be found." in capsys.readouterr().err

    def test_swift_data_found(self, mocker, tmp_path, capsys):
        self.act_like_xcrun_is_installed(mocker)
        dir = tmp_path / "Build"
        dir.mkdir()
        (dir / "cov_data.profdata").touch()
        XcodePlugin(derived_data_folder=tmp_path).run_preparation(collector=None)
        output = capsys.readouterr().err.splitlines()
        expected = (
            'info: Running swift coverage on the following list of files: --- {"matched_paths": ["'
            + f"{dir}/cov_data.profdata"
            + '"]}'
        )
        assert expected in output

    def test_swift_cov(self, tmp_path, capsys, mocker):
        dir_path = tmp_path / "Build/folder.app/folder"
        dir_path.parent.mkdir(parents=True, exist_ok=True)
        dir_path.touch()
        mocked_subprocess = mocker.patch(
            "codecov_cli.plugins.xcode.XcodePlugin.run_llvm_cov"
        )
        XcodePlugin().swiftcov(dir_path, "")
        self.act_like_xcrun_ran_succesfully("folder", "app")
        file_path = pathlib.Path("folder.app.coverage.txt")
        assert file_path.is_file()
        mocked_subprocess.assert_called_once()
