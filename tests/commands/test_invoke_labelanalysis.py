import json
from contextlib import redirect_stdout
from io import StringIO

import pytest
import responses
from click.testing import CliRunner
from responses import matchers

from codecov_cli.commands.labelanalysis import (
    _dry_run_json_output,
    _dry_run_list_output,
    _fallback_to_collected_labels,
    _parse_runner_params,
)
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


FAKE_BASE_SHA = "0111111111111111111111111111111111111110"


class TestLabelAnalysisNotInvoke(object):
    def test__dry_run_json_output(self):
        list_to_run = ["label_1", "label_2"]
        list_to_skip = ["label_3", "label_4"]
        runner_options = ["--option=1", "--option=2"]

        with StringIO() as out:
            with redirect_stdout(out):
                _dry_run_json_output(
                    labels_to_run=list_to_run,
                    labels_to_skip=list_to_skip,
                    runner_options=runner_options,
                    fallback_reason=None,
                )
                stdout = out.getvalue()

        assert json.loads(stdout) == {
            "runner_options": ["--option=1", "--option=2"],
            "ats_tests_to_skip": ["label_3", "label_4"],
            "ats_tests_to_run": ["label_1", "label_2"],
            "ats_fallback_reason": None,
        }

    def test__dry_run_json_output_fallback_reason(self):
        list_to_run = ["label_1", "label_2", "label_3", "label_4"]
        list_to_skip = []
        runner_options = ["--option=1", "--option=2"]

        with StringIO() as out:
            with redirect_stdout(out):
                _dry_run_json_output(
                    labels_to_run=list_to_run,
                    labels_to_skip=list_to_skip,
                    runner_options=runner_options,
                    fallback_reason="test_list_processing_errors",
                )
                stdout = out.getvalue()

        assert json.loads(stdout) == {
            "runner_options": ["--option=1", "--option=2"],
            "ats_tests_to_skip": [],
            "ats_tests_to_run": ["label_1", "label_2", "label_3", "label_4"],
            "ats_fallback_reason": "test_list_processing_errors",
        }

    def test__dry_run_space_separated_list_output(self):
        list_to_run = ["label_1", "label_2"]
        list_to_skip = ["label_3", "label_4"]
        runner_options = ["--option=1", "--option=2"]

        with StringIO() as out:
            with redirect_stdout(out):
                _dry_run_list_output(
                    labels_to_run=list_to_run,
                    labels_to_skip=list_to_skip,
                    runner_options=runner_options,
                )
                stdout = out.getvalue()

        assert (
            stdout
            == "TESTS_TO_RUN='--option=1' '--option=2' 'label_1' 'label_2'\nTESTS_TO_SKIP='--option=1' '--option=2' 'label_3' 'label_4'\n"
        )

    def test_parse_dynamic_runner_options(self):
        params = [
            "wrong_param",
            "key=value",
            "list_key=val1,val2,val3",
            "point=somethingwith=sign",
        ]
        assert _parse_runner_params(params) == {
            "wrong_param": None,
            "key": "value",
            "list_key": ["val1", "val2", "val3"],
            "point": "somethingwith=sign",
        }


class TestLabelAnalysisCommand(object):
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
                "--base-sha=1111111111111111111111111111111111111111",
                "--head-sha=1111111111111111111111111111111111111111",
            ],
            obj={},
        )
        assert result.exit_code != 0
        assert "Base and head sha can't be the same" in result.output

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
