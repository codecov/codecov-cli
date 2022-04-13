import sys
import traceback

from click.testing import CliRunner

from codecov_cli.main import cli


def test_upload_missing_commit_sha():
    runner = CliRunner()
    result = runner.invoke(cli, ["do-upload"], obj={})
    assert result.exit_code != 0
    assert "Error: Invalid value for '--commit-sha'" in result.output
