from click.testing import CliRunner

from codecov_cli.main import cli
from codecov_cli.services.legacy_upload import UploadSender
from codecov_cli.types import RequestError, RequestResult


def test_upload_missing_commit_sha(mocker):
    fake_versioning_system = mocker.MagicMock()
    mocker.patch(
        "codecov_cli.main.get_versioning_system", return_value=fake_versioning_system
    )
    fake_versioning_system.get_fallback_value.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ["do-upload"], obj={})
    assert result.exit_code != 0
    assert "Missing option '-C' / '--sha' / '--commit-sha'" in result.output


def test_upload_raise_Z_option(mocker):
    error = RequestError(
        code=401, params={"some": "params"}, description="Unauthorized"
    )
    result = RequestResult(
        error=error, warnings=[], status_code=401, text="Unauthorized"
    )
    upload_sender = mocker.patch.object(
        UploadSender, "send_upload_data", return_value=result
    )
    runner = CliRunner()
    result = runner.invoke(
        cli, ["do-upload", "--fail-on-error", "--use-new-uploader=True"], obj={}
    )
    upload_sender.assert_called
    assert str(result) == "<Result SystemExit(1)>"
