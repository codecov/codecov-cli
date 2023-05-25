import pytest
import responses
from click.testing import CliRunner
from responses import matchers

from codecov_cli.commands.labelanalysis import _fallback_to_collected_labels
from codecov_cli.commands.labelanalysis import time as labelanalysis_time
from codecov_cli.main import cli
from codecov_cli.runners.types import LabelAnalysisRequestResult
from tests.factory import FakeProvider, FakeRunner, FakeVersioningSystem


@pytest.fixture
def fake_ci_provider():
    return FakeProvider()


@pytest.fixture
def get_labelanalysis_deps(mocker):
    fake_ci_provider = FakeProvider()
    fake_versioning_system = FakeVersioningSystem()
    collected_labels = [
        "test_present",
        "test_absent",
        "test_in_diff",
        "test_global",
    ]
    fake_runner = FakeRunner(collect_tests_response=collected_labels)
    fake_runner.process_labelanalysis_result = mocker.MagicMock()

    mocker.patch.object(labelanalysis_time, "sleep")
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
    mocker.patch(
        "codecov_cli.main.get_versioning_system",
        return_value=fake_versioning_system,
    )
    mock_get_runner = mocker.patch(
        "codecov_cli.commands.labelanalysis.get_runner", return_value=fake_runner
    )
    return {
        "mock_get_runner": mock_get_runner,
        "fake_runner": fake_runner,
        "collected_labels": collected_labels,
    }


class TestLabelAnalysisCommand(object):
    def test_labelanalysis_help(self, mocker, fake_ci_provider):
        mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
        runner = CliRunner()

        result = runner.invoke(cli, ["label-analysis", "--help"], obj={})
        assert result.exit_code == 0
        print(result.output)
        assert result.output.split("\n") == [
            "Usage: cli label-analysis [OPTIONS]",
            "",
            "Options:",
            "  --token TEXT                  The static analysis token (NOT the same token as",
            "                                upload)  [required]",
            "  --head-sha TEXT               Commit SHA (with 40 chars)  [required]",
            "  --base-sha TEXT               Commit SHA (with 40 chars)  [required]",
            "  --runner-name, --runner TEXT  Runner to use",
            "  --max-wait-time INTEGER       Max time (in seconds) to wait for the label",
            "                                analysis result before falling back to running",
            "                                all tests. Default is to wait forever.",
            "  --help                        Show this message and exit.",
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

    def test_invoke_label_analysis_base_sha_same_as_head_sha(
        self, mocker, fake_ci_provider
    ):
        mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
        runner = CliRunner()

        result = runner.invoke(
            cli,
            [
                "label-analysis",
                "--token=STATIC_TOKEN",
                "--base-sha=commit-sha",
                "--head-sha=commit-sha",
            ],
            obj={},
        )
        assert result.exit_code != 0
        assert "Base and head sha can't be the same" in result.output

    def test_invoke_label_analysis(self, get_labelanalysis_deps, mocker):
        mock_get_runner = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]
        collected_labels = get_labelanalysis_deps["collected_labels"]

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
            cli_runner = CliRunner()
            result = cli_runner.invoke(
                cli,
                ["-v", "label-analysis", "--token=STATIC_TOKEN", "--base-sha=BASE_SHA"],
                obj={},
            )
            mock_get_runner.assert_called()
            fake_runner.process_labelanalysis_result.assert_called_with(
                label_analysis_result
            )
            print(result.output)
        assert result.exit_code == 0

    def test_fallback_to_collected_labels(self, mocker):
        mock_runner = mocker.MagicMock()
        collected_labels = ["label_1", "label_2", "label_3"]
        fake_response = LabelAnalysisRequestResult(
            {
                "present_report_labels": [],
                "absent_labels": collected_labels,
                "present_diff_labels": [],
                "global_level_labels": [],
            }
        )
        _fallback_to_collected_labels(collected_labels, mock_runner)
        mock_runner.process_labelanalysis_result.assert_called_with(fake_response)

    def test_fallback_to_collected_labels_no_labels(self, mocker):
        mock_runner = mocker.MagicMock()
        with pytest.raises(Exception) as exp:
            _fallback_to_collected_labels([], mock_runner)
        mock_runner.process_labelanalysis_result.assert_not_called()
        assert str(exp.value) == "Failed to get list of labels to run"

    def test_fallback_collected_labels_covecov_500_error(
        self, get_labelanalysis_deps, mocker
    ):
        mock_get_runner = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]
        collected_labels = get_labelanalysis_deps["collected_labels"]
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/labels/labels-analysis",
                status=500,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            cli_runner = CliRunner()
            result = cli_runner.invoke(
                cli,
                ["-v", "label-analysis", "--token=STATIC_TOKEN", "--base-sha=BASE_SHA"],
                obj={},
            )
            mock_get_runner.assert_called()
            fake_runner.process_labelanalysis_result.assert_called_with(
                {
                    "present_report_labels": [],
                    "absent_labels": collected_labels,
                    "present_diff_labels": [],
                    "global_level_labels": [],
                }
            )
            print(result.output)
        assert result.exit_code == 0

    def test_fallback_collected_labels_codecov_error_processing_label_analysis(
        self, get_labelanalysis_deps, mocker
    ):
        mock_get_runner = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]
        collected_labels = get_labelanalysis_deps["collected_labels"]

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
                json={"state": "error"},
            )
            cli_runner = CliRunner()
            result = cli_runner.invoke(
                cli,
                ["-v", "label-analysis", "--token=STATIC_TOKEN", "--base-sha=BASE_SHA"],
                obj={},
            )
            mock_get_runner.assert_called()
            fake_runner.process_labelanalysis_result.assert_called_with(
                {
                    "present_report_labels": [],
                    "absent_labels": collected_labels,
                    "present_diff_labels": [],
                    "global_level_labels": [],
                }
            )
            print(result.output)
        assert result.exit_code == 0

    def test_fallback_collected_labels_codecov_max_wait_time_exceeded(
        self, get_labelanalysis_deps, mocker
    ):
        mock_get_runner = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]
        collected_labels = get_labelanalysis_deps["collected_labels"]
        mocker.patch.object(labelanalysis_time, "monotonic", side_effect=[0, 6])

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
                json={"state": "processing"},
            )
            cli_runner = CliRunner()
            result = cli_runner.invoke(
                cli,
                [
                    "-v",
                    "label-analysis",
                    "--token=STATIC_TOKEN",
                    "--base-sha=BASE_SHA",
                    "--max-wait-time=5",
                ],
                obj={},
            )
            print(result)
            assert result.exit_code == 0
        mock_get_runner.assert_called()
        fake_runner.process_labelanalysis_result.assert_called_with(
            {
                "present_report_labels": [],
                "absent_labels": collected_labels,
                "present_diff_labels": [],
                "global_level_labels": [],
            }
        )
