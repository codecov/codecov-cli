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
