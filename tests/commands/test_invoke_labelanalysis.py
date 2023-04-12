import pytest
import responses
from click.testing import CliRunner
from responses import matchers

from codecov_cli.commands.labelanalysis import PythonStandardRunner
from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
from codecov_cli.main import cli
from codecov_cli.types import RequestError, RequestResult
from tests.factory import FakeProvider, FakeVersioningSystem
from tests.test_helpers import parse_outstreams_into_log_lines


@pytest.fixture
def fake_ci_provider():
    return FakeProvider()


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

    def test_invoke_label_analysis(self, mocker):
        fake_ci_provider = FakeProvider()
        fake_versioning_system = FakeVersioningSystem()
        mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
        mocker.patch(
            "codecov_cli.main.get_versioning_system",
            return_value=fake_versioning_system,
        )
        mocker.patch.object(
            PythonStandardRunner,
            "collect_tests",
            return_value=["test_present", "test_absent", "test_in_diff", "test_global"],
        )
        patch_do_something = mocker.patch.object(
            PythonStandardRunner,
            "do_something_with_result",
            return_value=None,
        )
        label_analysis_result = {
            "present_report_labels": ["test_present"],
            "absent_labels": ["test_absent"],
            "present_diff_labels": ["test_in_diff"],
            "global_level_labels": ["test_global"],
        }
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/labels/labels-analysis",
                json={"external_id": "label-analysis-request-id"},
                status=201,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.GET,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
                json={"state": "finished", "result": label_analysis_result},
            )
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["label-analysis", "--token=STATIC_TOKEN", "--base-sha=BASE_SHA"],
                obj={},
            )
        print(result.output)
        assert result.exit_code == 0
        patch_do_something.assert_called_with(label_analysis_result)
