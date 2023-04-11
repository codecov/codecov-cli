import pytest
from click.testing import CliRunner

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.main import cli
from codecov_cli.types import RequestError, RequestResult
from tests.test_helpers import parse_outstreams_into_log_lines


@pytest.fixture
def fake_versioning_system(mocker):
    return mocker.MagicMock()


class TestLabelAnalysisCommand(object):
    def test_labelanalysis_help(self, mocker, fake_ci_provider):
        mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
        runner = CliRunner()

        result = runner.invoke(cli, ["label-analysis", "--help"], obj={})
        assert result.exit_code == 0
        assert result.output.split("\n") == [
            "Usage: cli label-analysis [OPTIONS]",
            "",
            "Options:",
            "  --token TEXT     The static analysis token (NOT the same token as upload)",
            "                   [required]",
            "  --head-sha TEXT  Commit SHA (with 40 chars)  [required]",
            "  --base-sha TEXT  Commit SHA (with 40 chars)  [required]",
            "  --help           Show this message and exit.",
            "",
        ]

    def test_invoke_label_analysis_missing_token(self, mocker, fake_ci_provider):
        mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
        runner = CliRunner()

        result = runner.invoke(cli, ["label-analysis"], obj={})
        print(result.output)
        assert result.exit_code != 0
        assert "Error: Missing option '--token'." in result.output

    def test_invoke_label_analysis_missing_base_sha(self, mocker, fake_ci_provider):
        mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
        runner = CliRunner()

        result = runner.invoke(cli, ["label-analysis", "--token=STATIC_TOKEN"], obj={})
        print(result.output)
        assert result.exit_code != 0
        assert "Error: Missing option '--base-sha'." in result.output
