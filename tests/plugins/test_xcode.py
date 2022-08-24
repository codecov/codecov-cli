import pathlib

from codecov_cli.plugins.xcode import XcodePlugin


class TestXcode(object):
    def test_no_swift_data_found(self, mocker, tmp_path, capsys):
        xcode_plugin = XcodePlugin(derived_data_folder=tmp_path).run_preparation(
            collector=None
        )
        output = capsys.readouterr().err
        assert xcode_plugin is None
        assert f"DerivedData folder: {tmp_path}" in output
        assert "No swift data found." in output

    def test_swift_data_found(self, mocker, tmp_path, capsys):
        dir = tmp_path / "Build"
        dir.mkdir()
        (dir / "cov_data.profdata").touch()
        XcodePlugin(derived_data_folder=tmp_path).run_preparation(collector=None)
        output = capsys.readouterr().err
        print(output)
        assert "Running swift coverage on the following list of files:" in output
        assert f"{dir}/cov_data.profdata" in output

    def test_swift_cov(self, tmp_path, capsys, mocker):
        dir_path = tmp_path / "Build/folder.app/folder"
        dir_path.parent.mkdir(parents=True, exist_ok=True)
        dir_path.touch()
        mock = mocker.MagicMock(
            stdout=b"   11|      1|public func sayHello() {12|      1|    print('Hello!')13|      1|}",
            returncode=0,
        )
        mocker.patch("codecov_cli.plugins.xcode.subprocess.run", return_value=mock)
        XcodePlugin().swiftcov(dir_path, "")
        file_path = pathlib.Path("folder.app.coverage.txt")
        assert file_path.is_file()
        output = capsys.readouterr().err.splitlines()
        assert "info: + Building reports for folder app" in output
        assert "info: Generated folder.app.coverage.txt file successfully" in output
