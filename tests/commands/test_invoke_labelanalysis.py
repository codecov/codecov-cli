import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import click
import pytest
import responses
from click.testing import CliRunner
from responses import matchers

from codecov_cli.commands.labelanalysis import (
    _dry_run_json_output,
    _dry_run_list_output,
    _fallback_to_collected_labels,
    _parse_runner_params,
    _potentially_calculate_absent_labels,
    _send_labelanalysis_request,
)
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


FAKE_BASE_SHA = "0111111111111111111111111111111111111110"


class TestLabelAnalysisNotInvoke(object):
    def test_potentially_calculate_labels_recalculate(self):
        request_result = {
            "present_report_labels": [
                "label_1",
                "label_2",
                "label_3",
                "label_old",
                "label_older",
            ],
            "absent_labels": [],
            "present_diff_labels": ["label_2", "label_3", "label_old"],
            "global_level_labels": ["label_1", "label_older"],
        }
        collected_labels = ["label_1", "label_2", "label_3", "label_4"]
        expected = {
            "present_diff_labels": ["label_2", "label_3"],
            "global_level_labels": ["label_1"],
            "absent_labels": ["label_4"],
            "present_report_labels": ["label_1", "label_2", "label_3"],
        }
        assert (
            _potentially_calculate_absent_labels(request_result, collected_labels)
            == expected
        )

    def test_send_label_analysis_bad_payload(self):
        payload = {
            "base_commit": "base_commit",
            "head_commit": "head_commit",
            "requested_labels": [],
        }
        url = "https://api.codecov.io/labels/labels-analysis"
        header = "Repotoken STATIC_TOKEN"
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/labels/labels-analysis",
                json={"error": "list field cannot be empty list"},
                status=400,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            with pytest.raises(click.ClickException):
                _send_labelanalysis_request(payload, url, header)

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

    def test_invoke_label_analysis(
        self, get_labelanalysis_deps, mocker, use_verbose_option
    ):
        mock_get_runner = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]
        _ = get_labelanalysis_deps["collected_labels"]

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
                responses.PATCH,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
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
                [
                    "label-analysis",
                    "--token=STATIC_TOKEN",
                    f"--base-sha={FAKE_BASE_SHA}",
                ],
                obj={},
            )
            assert result.exit_code == 0
        mock_get_runner.assert_called()
        fake_runner.process_labelanalysis_result.assert_called_with(
            label_analysis_result
        )
        print(result.output)

    @pytest.mark.parametrize("processing_errors", [[], [{"error": "missing_data"}]])
    def test_invoke_label_analysis_dry_run(
        self, processing_errors, get_labelanalysis_deps, mocker
    ):
        mock_get_runner = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]

        label_analysis_result = {
            "present_report_labels": ["test_present", "test_in_diff", "test_global"],
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
                responses.PATCH,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
                json={"external_id": "label-analysis-request-id"},
                status=201,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.GET,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
                json={
                    "state": "finished",
                    "result": label_analysis_result,
                    "errors": processing_errors,
                },
            )
            cli_runner = CliRunner(mix_stderr=False)
            with cli_runner.isolated_filesystem():
                result = cli_runner.invoke(
                    cli,
                    [
                        "label-analysis",
                        "--token=STATIC_TOKEN",
                        f"--base-sha={FAKE_BASE_SHA}",
                        "--dry-run",
                    ],
                    obj={},
                )
                mock_get_runner.assert_called()
                fake_runner.process_labelanalysis_result.assert_not_called()
        # Dry run format defaults to json
        print(result.stdout)
        ats_fallback_reason = (
            "test_list_processing_errors" if processing_errors else None
        )
        assert json.loads(result.stdout) == {
            "runner_options": ["--labels"],
            "ats_tests_to_run": ["test_absent", "test_global", "test_in_diff"],
            "ats_tests_to_skip": ["test_present"],
            "ats_fallback_reason": ats_fallback_reason,
        }

    def test_invoke_label_analysis_dry_run_pytest_format(
        self, get_labelanalysis_deps, mocker
    ):
        _ = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]

        label_analysis_result = {
            "present_report_labels": ["test_present", "test_in_diff", "test_global"],
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
                responses.PATCH,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
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
            cli_runner = CliRunner(mix_stderr=False)
            with cli_runner.isolated_filesystem():
                result = cli_runner.invoke(
                    cli,
                    [
                        "label-analysis",
                        "--token=STATIC_TOKEN",
                        f"--base-sha={FAKE_BASE_SHA}",
                        "--dry-run",
                        "--dry-run-format=space-separated-list",
                    ],
                    obj={},
                )
                fake_runner.process_labelanalysis_result.assert_not_called()
        print(result.stdout)
        assert result.exit_code == 0
        assert (
            result.stdout
            == "TESTS_TO_RUN='--labels' 'test_absent' 'test_global' 'test_in_diff'\nTESTS_TO_SKIP='--labels' 'test_present'\n"
        )

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
        self, get_labelanalysis_deps, mocker, use_verbose_option
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
                [
                    "label-analysis",
                    "--token=STATIC_TOKEN",
                    f"--base-sha={FAKE_BASE_SHA}",
                ],
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

    def test_fallback_collected_labels_covecov_500_error_dry_run(
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
            cli_runner = CliRunner(mix_stderr=False)
            with cli_runner.isolated_filesystem():
                result = cli_runner.invoke(
                    cli,
                    [
                        "label-analysis",
                        "--token=STATIC_TOKEN",
                        f"--base-sha={FAKE_BASE_SHA}",
                        "--dry-run",
                    ],
                    obj={},
                )
                mock_get_runner.assert_called()
                fake_runner.process_labelanalysis_result.assert_not_called()
        # Dry run format defaults to json
        assert json.loads(result.stdout) == {
            "runner_options": ["--labels"],
            "ats_tests_to_run": sorted(collected_labels),
            "ats_tests_to_skip": [],
            "ats_fallback_reason": "codecov_unavailable",
        }
        assert result.exit_code == 0

    def test_fallback_collected_labels_codecov_error_processing_label_analysis(
        self, get_labelanalysis_deps, mocker, use_verbose_option
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
                responses.PATCH,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
                json={"external_id": "label-analysis-request-id"},
                status=201,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.GET,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
                json={
                    "state": "error",
                    "external_id": "uuid4-external-id",
                    "base_commit": "BASE_COMMIT_SHA",
                    "head_commit": "HEAD_COMMIT_SHA",
                },
            )
            cli_runner = CliRunner()
            result = cli_runner.invoke(
                cli,
                [
                    "label-analysis",
                    "--token=STATIC_TOKEN",
                    f"--base-sha={FAKE_BASE_SHA}",
                ],
                obj={},
            )
            print(result)
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

    def test_fallback_collected_labels_codecov_error_processing_label_analysis_dry_run(
        self, get_labelanalysis_deps, mocker, use_verbose_option
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
                responses.PATCH,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
                json={"external_id": "label-analysis-request-id"},
                status=201,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.GET,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
                json={
                    "state": "error",
                    "external_id": "uuid4-external-id",
                    "base_commit": "BASE_COMMIT_SHA",
                    "head_commit": "HEAD_COMMIT_SHA",
                },
            )
            cli_runner = CliRunner(mix_stderr=False)
            with cli_runner.isolated_filesystem():
                result = cli_runner.invoke(
                    cli,
                    [
                        "label-analysis",
                        "--token=STATIC_TOKEN",
                        f"--base-sha={FAKE_BASE_SHA}",
                        "--dry-run",
                    ],
                    obj={},
                )
                mock_get_runner.assert_called()
                fake_runner.process_labelanalysis_result.assert_not_called()
        # Dry run format defaults to json
        assert json.loads(result.stdout) == {
            "runner_options": ["--labels"],
            "ats_tests_to_run": sorted(collected_labels),
            "ats_tests_to_skip": [],
            "ats_fallback_reason": "test_list_processing_failed",
        }
        assert result.exit_code == 0

    def test_fallback_collected_labels_codecov_max_wait_time_exceeded(
        self, get_labelanalysis_deps, mocker, use_verbose_option
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
                responses.PATCH,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
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
                    "label-analysis",
                    "--token=STATIC_TOKEN",
                    f"--base-sha={FAKE_BASE_SHA}",
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

    def test_fallback_collected_labels_codecov_max_wait_time_exceeded_dry_run(
        self, get_labelanalysis_deps, mocker, use_verbose_option
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
                responses.PATCH,
                "https://api.codecov.io/labels/labels-analysis/label-analysis-request-id",
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
            cli_runner = CliRunner(mix_stderr=False)
            result = cli_runner.invoke(
                cli,
                [
                    "label-analysis",
                    "--token=STATIC_TOKEN",
                    f"--base-sha={FAKE_BASE_SHA}",
                    "--max-wait-time=5",
                    "--dry-run",
                ],
                obj={},
            )
            mock_get_runner.assert_called()
            fake_runner.process_labelanalysis_result.assert_not_called()
        # Dry run format defaults to json
        assert json.loads(result.stdout) == {
            "runner_options": ["--labels"],
            "ats_tests_to_run": sorted(collected_labels),
            "ats_tests_to_skip": [],
            "ats_fallback_reason": "max_wait_time_exceeded",
        }
        assert result.exit_code == 0

    def test_first_labelanalysis_request_fails_but_second_works(
        self, get_labelanalysis_deps, mocker, use_verbose_option
    ):
        mock_get_runner = get_labelanalysis_deps["mock_get_runner"]
        fake_runner = get_labelanalysis_deps["fake_runner"]
        _ = get_labelanalysis_deps["collected_labels"]

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
                status=502,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
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
                [
                    "label-analysis",
                    "--token=STATIC_TOKEN",
                    f"--base-sha={FAKE_BASE_SHA}",
                ],
                obj={},
            )
            assert result.exit_code == 0
        mock_get_runner.assert_called()
        fake_runner.process_labelanalysis_result.assert_called_with(
            label_analysis_result
        )
        print(result.output)
