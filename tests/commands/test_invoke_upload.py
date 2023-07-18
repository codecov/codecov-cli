from click.testing import CliRunner

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.main import cli
from codecov_cli.services.upload import UploadCollector, UploadSender
from codecov_cli.types import RequestError, RequestResult
from tests.factory import FakeProvider, FakeVersioningSystem
from tests.test_helpers import parse_outstreams_into_log_lines


def test_upload_missing_commit_sha(mocker, use_verbose_option):
    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: None})
    fake_versioning_system = FakeVersioningSystem({FallbackFieldEnum.commit_sha: None})
    mocker.patch(
        "codecov_cli.main.get_versioning_system", return_value=fake_versioning_system
    )
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
    runner = CliRunner()
    result = runner.invoke(cli, ["do-upload"], obj={})
    assert result.exit_code != 0
    print(result.output)
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
    upload_collector = mocker.patch.object(UploadCollector, "generate_upload_data")
    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: None})
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)

    runner = CliRunner()
    result = runner.invoke(cli, ["do-upload", "--fail-on-error"], obj={})
    upload_sender.assert_called()
    upload_collector.assert_called()
    assert ("error", "Upload failed: Unauthorized") in parse_outstreams_into_log_lines(
        result.output
    )
    assert str(result) == "<Result SystemExit(1)>"
