from click.testing import CliRunner

from codecov_cli.main import cli


def test_upload_missing_commit_sha(mocker):
    fake_versioning_system, fake_ci_provider = mocker.MagicMock(), mocker.MagicMock()
    mocker.patch(
        "codecov_cli.main.get_versioning_system", return_value=fake_versioning_system
    )
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
    fake_versioning_system.get_fallback_value.return_value = None
    fake_ci_provider.get_fallback_value.return_value = None
    runner = CliRunner()
    result = runner.invoke(cli, ["do-upload"], obj={})
    assert result.exit_code != 0
    assert "Missing option '-C' / '--sha' / '--commit-sha'" in result.output
