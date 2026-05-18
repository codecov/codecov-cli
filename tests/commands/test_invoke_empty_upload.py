from click.testing import CliRunner

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.main import cli
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

