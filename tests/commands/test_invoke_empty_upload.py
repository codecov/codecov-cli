from click.testing import CliRunner

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.main import cli
from codecov_cli.types import RequestResult
from tests.factory import FakeProvider, FakeVersioningSystem

def test_invoke_empty_upload_with_create_commit(mocker):
    create_commit_mock = mocker.patch("codecov_cli.commands.empty_upload.create_commit_logic")
    empty_upload_mock = mocker.patch("codecov_cli.commands.empty_upload.empty_upload_logic")

    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: None})
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)

    runner = CliRunner()
    result = runner.invoke(cli, ["empty-upload",
                    "-C", "command-sha",
                    "--slug", "owner/repo",
                    "--parent-sha", "asdf",
                    "--branch", "main",
                    "--pr", 1234], obj={})
    assert result.exit_code == 0

    create_commit_mock.assert_called_once()
    empty_upload_mock.assert_called_once()


def test_invoke_empty_upload_send_commit_data_called_with_options(mocker):
    """Verify that send_commit_data is called with the correct options when
    empty-upload is invoked with create-commit related options.

    Regression test for: AssertionError: create_commit SHOULD be called with options
    The root cause was that test_reproduce.py was patching send_commit_data but
    invoking empty-upload with invalid CLI arguments (exit code 2), preventing
    the command body — and therefore create_commit_logic/send_commit_data — from
    ever executing. This test uses the correct invocation with all required args.
    """
    send_commit_data_mock = mocker.patch(
        "codecov_cli.services.commit.send_commit_data"
    )
    send_commit_data_mock.return_value = RequestResult(
        error=None, warnings=[], status_code=200, text=""
    )
    empty_upload_mock = mocker.patch("codecov_cli.commands.empty_upload.empty_upload_logic")

    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: None})
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "empty-upload",
            "-C", "abc1234567890abc1234567890abc1234567890ab",
            "--slug", "owner/repo",
            "--parent-sha", "deadbeef12345678deadbeef12345678deadbeef",
            "--branch", "main",
            "--pr", "42",
            "--token", "test-token",
        ],
        obj={},
    )

    assert result.exit_code == 0, result.output
    assert send_commit_data_mock.called, "create_commit SHOULD be called with options"
    assert empty_upload_mock.called, "empty_upload should be called"

    call_kwargs = send_commit_data_mock.call_args
    assert call_kwargs.kwargs.get("branch") == "main"
    assert call_kwargs.kwargs.get("parent_sha") == "deadbeef12345678deadbeef12345678deadbeef"
    assert call_kwargs.kwargs.get("pr") == "42"

