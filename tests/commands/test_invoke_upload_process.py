from unittest.mock import MagicMock

from click.testing import CliRunner

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.main import cli
from codecov_cli.types import RequestError, RequestResult
from tests.factory import FakeProvider, FakeVersioningSystem
from tests.test_helpers import parse_outstreams_into_log_lines


def test_upload_process_missing_commit_sha(mocker):
    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: None})
    fake_versioning_system = FakeVersioningSystem({FallbackFieldEnum.commit_sha: None})
    mocker.patch(
        "codecov_cli.main.get_versioning_system", return_value=fake_versioning_system
    )
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
    runner = CliRunner()
    result = runner.invoke(cli, ["upload-process"], obj={})
    assert result.exit_code != 0
    assert "Missing option '-C' / '--sha' / '--commit-sha'" in result.output


def test_upload_process_raise_Z_option(mocker):
    error = RequestError(
        code=401, params={"some": "params"}, description="Unauthorized"
    )
    result = RequestResult(
        error=error, warnings=[], status_code=401, text="Unauthorized"
    )
    send_commit_data = mocker.patch(
        "codecov_cli.services.commit.send_commit_data", return_value=result
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["upload-process", "--fail-on-error"], obj={})
    send_commit_data.assert_called_once()
    assert (
        "error",
        "Commit creating failed: Unauthorized",
    ) in parse_outstreams_into_log_lines(result.output)
    assert str(result) == "<Result SystemExit(1)>"
