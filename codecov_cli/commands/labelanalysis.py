import json
import logging
import pathlib
import time
from typing import Dict, List, Optional

import click
import requests

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers import request
from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.helpers.validators import validate_commit_sha
from codecov_cli.runners import get_runner
from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)

logger = logging.getLogger("codecovcli")


@click.command()
@click.option(
    "--token",
    required=True,
    envvar="CODECOV_STATIC_TOKEN",
    help="The static analysis token (NOT the same token as upload)",
)
@click.option(
    "--head-sha",
    "head_commit_sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    callback=validate_commit_sha,
    required=True,
)
@click.option(
    "--base-sha",
    "base_commit_sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    callback=validate_commit_sha,
    required=True,
)
@click.option(
    "--runner-name", "--runner", "runner_name", help="Runner to use", default="pytest"
)
@click.option(
    "--max-wait-time",
    "max_wait_time",
    help="Max time (in seconds) to wait for the label analysis result before falling back to running all tests. Default is to wait forever.",
    default=None,
    type=int,
)
@click.option(
    "--dry-run",
    "dry_run",
    help=(
        "Print list of tests to run AND tests skipped AND options that need to be added to the test runner to stdout. "
        + "Choose format with --dry-run-format option. Default is JSON. "
    ),
    is_flag=True,
)
@click.option(
    "--dry-run-format",
    "dry_run_format",
    type=click.Choice(["json", "space-separated-list"]),
    help="Format in which --dry-run data is printed. Default is JSON.",
    default="json",
)
@click.option(
    "--runner-param",
    "runner_params",
    multiple=True,
)
@click.pass_context
def label_analysis(
    ctx: click.Context,
    token: str,
    head_commit_sha: str,
    base_commit_sha: str,
    runner_name: str,
    max_wait_time: str,
    dry_run: bool,
    dry_run_format: str,
    runner_params: List[str],
):
    enterprise_url = ctx.obj.get("enterprise_url")
    logger.debug(
        "Starting label analysis",
        extra=dict(
            extra_log_attributes=dict(
                head_commit_sha=head_commit_sha,
                base_commit_sha=base_commit_sha,
                token=token,
                runner_name=runner_name,
                enterprise_url=enterprise_url,
                max_wait_time=max_wait_time,
                dry_run=dry_run,
            )
        ),
    )
    if head_commit_sha == base_commit_sha:
        logger.error(
            "Base and head sha can't be the same",
            extra=dict(
                extra_log_attributes=dict(
                    head_commit_sha=head_commit_sha,
                    base_commit_sha=base_commit_sha,
                )
            ),
        )
        raise click.ClickException(
            click.style("Unable to run label analysis", fg="red")
        )

    codecov_yaml = ctx.obj["codecov_yaml"] or {}
    cli_config = codecov_yaml.get("cli", {})
    # Raises error if no runner is found
    parsed_runner_params = _parse_runner_params(runner_params)
    runner = get_runner(cli_config, runner_name, parsed_runner_params)
    logger.debug(
        f"Selected runner: {runner}",
        extra=dict(extra_log_attributes=dict(config=runner.params)),
    )

    upload_url = enterprise_url or CODECOV_API_URL
    url = f"{upload_url}/labels/labels-analysis"
    token_header = f"Repotoken {token}"
    payload = {
        "base_commit": base_commit_sha,
        "head_commit": head_commit_sha,
        "requested_labels": None,
    }
    # Send the initial label analysis request without labels
    # Because labels might take a long time to collect
    eid = _send_labelanalysis_request(payload, url, token_header)

    logger.info("Collecting labels...")
    requested_labels = runner.collect_tests()
    logger.info(f"Collected {len(requested_labels)} test labels")
    logger.debug(
        "Labels collected",
        extra=dict(extra_log_attributes=dict(labels_collected=requested_labels)),
    )
    payload["requested_labels"] = requested_labels

    if eid:
        # Initial request with no labels was successful
        # Now we PATCH the labels in
        patch_url = f"{upload_url}/labels/labels-analysis/{eid}"
        _patch_labels(payload, patch_url, token_header)
    else:
        # Initial request with no labels failed
        # Retry it
        eid = _send_labelanalysis_request(payload, url, token_header)
        if eid is None:
            _fallback_to_collected_labels(
                requested_labels,
                runner,
                dry_run=dry_run,
                dry_run_format=dry_run_format,
                fallback_reason="codecov_unavailable",
            )
            return

    has_result = False
    logger.info("Waiting for list of tests to run...")
    start_wait = time.monotonic()
    time.sleep(1)
    while not has_result:
        resp_data = request.get(
            f"{upload_url}/labels/labels-analysis/{eid}",
            headers={"Authorization": token_header},
        )
        resp_json = resp_data.json()
        if resp_json["state"] == "finished":
            logger.info(
                "Received list of tests from Codecov",
                extra=dict(
                    extra_log_attributes=dict(
                        processing_errors=resp_json.get("errors", [])
                    )
                ),
            )
            request_result = _potentially_calculate_absent_labels(
                resp_json["result"], requested_labels
            )
            if not dry_run:
                runner.process_labelanalysis_result(request_result)
            else:
                _dry_run_output(
                    LabelAnalysisRequestResult(request_result),
                    runner,
                    dry_run_format,
                    # It's possible that the task had processing errors and fallback to all tests
                    # Even though it's marked as FINISHED (not ERROR) it's not a true success
                    fallback_reason=(
                        "test_list_processing_errors"
                        if resp_json.get("errors", None)
                        else None
                    ),
                )
            return
        if resp_json["state"] == "error":
            logger.error(
                "Request had problems calculating",
                extra=dict(
                    extra_log_attributes=dict(
                        base_commit=resp_json["base_commit"],
                        head_commit=resp_json["head_commit"],
                        external_id=resp_json["external_id"],
                    )
                ),
            )
            _fallback_to_collected_labels(
                collected_labels=requested_labels,
                runner=runner,
                dry_run=dry_run,
                dry_run_format=dry_run_format,
                fallback_reason="test_list_processing_failed",
            )
            return
        if max_wait_time and (time.monotonic() - start_wait) > max_wait_time:
            logger.error(
                f"Exceeded max waiting time of {max_wait_time} seconds. Running all tests.",
            )
            _fallback_to_collected_labels(
                collected_labels=requested_labels,
                runner=runner,
                dry_run=dry_run,
                dry_run_format=dry_run_format,
                fallback_reason="max_wait_time_exceeded",
            )
            return
        logger.info("Waiting more time for result...")
        time.sleep(5)


def _parse_runner_params(runner_params: List[str]) -> Dict[str, str]:
    """Parses the structured list of dynamic runner params into a dictionary.
    Structure is `key=value`. If value is a list make it comma-separated.
    If the list item doesn't have '=' we consider it the key and set to None.

    EXAMPLE:
    runner_params = ['key=value', 'null_item', 'list=item1,item2,item3']
    _parse_runner_params(runner_params) == {
        'key': 'value',
        'null_item': None,
        'list': ['item1', 'item2', 'item3']
    }
    """
    final_params = {}
    for param in runner_params:
        # Emit warning if param is not well formatted
        # Using == 0 rather than != 1 because there might be
        # a good reason for the param to include '=' in the value.
        if param.count("=") == 0:
            logger.warning(
                f"Runner param {param} is not well formated. Setting value to None. Use '--runner-param key=value' to set value"
            )
            final_params[param] = None
        else:
            key, value = param.split("=", 1)
            # For list values we need to split the list too
            if "," in value:
                value = value.split(",")
            final_params[key] = value
    return final_params


def _potentially_calculate_absent_labels(
    request_result, requested_labels
) -> LabelAnalysisRequestResult:
    if request_result["absent_labels"]:
        # This means that Codecov already calculated everything for us
        final_result = LabelAnalysisRequestResult(request_result)
    else:
        # Here we have to calculate the absent labels
        # And also remove labels that maybe don't exist anymore from the set of labels to test
        # Because codecov didn't have this info previously
        requested_labels_set = set(requested_labels)
        present_diff_labels_set = set(request_result.get("present_diff_labels", []))
        present_report_labels_set = set(request_result.get("present_report_labels", []))
        global_level_labels_set = set(request_result.get("global_level_labels", []))
        final_result = LabelAnalysisRequestResult(
            {
                "present_report_labels": sorted(
                    present_report_labels_set & requested_labels_set
                ),
                "present_diff_labels": sorted(
                    present_diff_labels_set & requested_labels_set
                ),
                "absent_labels": sorted(
                    requested_labels_set - present_report_labels_set
                ),
                "global_level_labels": sorted(
                    global_level_labels_set & requested_labels_set
                ),
            }
        )
    logger.info(
        "Received information about tests to run",
        extra=dict(
            extra_log_attributes=dict(
                absent_labels=len(final_result.absent_labels),
                present_diff_labels=len(final_result.present_diff_labels),
                global_level_labels=len(final_result.global_level_labels),
                present_report_labels=len(final_result.present_report_labels),
            )
        ),
    )
    return final_result


def _patch_labels(payload, url, token_header):
    logger.info("Sending collected labels to Codecov...")
    try:
        response = request.patch(
            url, json=payload, headers={"Authorization": token_header}
        )
        if response.status_code < 300:
            logger.info("Labels successfully sent to Codecov")
    except requests.RequestException:
        raise click.ClickException(click.style("Unable to reach Codecov", fg="red"))


def _send_labelanalysis_request(payload, url, token_header):
    logger.info(
        "Requesting set of labels to run...",
        extra=dict(
            extra_log_attributes=dict(
                with_labels=(payload["requested_labels"] is not None)
            )
        ),
    )
    try:
        response = request.post(
            url, data=payload, headers={"Authorization": token_header}
        )
        if response.status_code >= 500:
            logger.warning(
                "Sorry. Codecov is having problems",
                extra=dict(extra_log_attributes=dict(status_code=response.status_code)),
            )
            return None
        if response.status_code >= 400:
            logger.warning(
                "Got a 4XX status code back from Codecov",
                extra=dict(
                    extra_log_attributes=dict(
                        status_code=response.status_code, response_json=response.json()
                    )
                ),
            )
            raise click.ClickException(
                "There is some problem with the submitted information"
            )
    except requests.RequestException:
        raise click.ClickException(click.style("Unable to reach Codecov", fg="red"))
    eid = response.json()["external_id"]
    logger.info(
        "Label Analysis request successful",
        extra=dict(extra_log_attributes=dict(request_id=eid)),
    )
    return eid


def _dry_run_json_output(
    labels_to_run: set,
    labels_to_skip: set,
    runner_options: List[str],
    fallback_reason: str = None,
) -> None:
    output_as_dict = dict(
        runner_options=runner_options,
        ats_tests_to_run=sorted(labels_to_run),
        ats_tests_to_skip=sorted(labels_to_skip),
        ats_fallback_reason=fallback_reason,
    )
    # ⚠️ DON'T use logger
    # logger goes to stderr, we want it in stdout
    click.echo(json.dumps(output_as_dict))


def _dry_run_list_output(
    labels_to_run: set,
    labels_to_skip: set,
    runner_options: List[str],
    fallback_reason: str = None,
) -> None:
    if fallback_reason:
        logger.warning(f"label-analysis didn't run correctly. Error: {fallback_reason}")

    to_run_line = " ".join(
        sorted(map(lambda l: f"'{l}'", runner_options))
        + sorted(map(lambda l: f"'{l}'", labels_to_run))
    )
    to_skip_line = " ".join(
        sorted(map(lambda l: f"'{l}'", runner_options))
        + sorted(map(lambda l: f"'{l}'", labels_to_skip))
    )
    # ⚠️ DON'T use logger
    # logger goes to stderr, we want it in stdout
    click.echo(f"TESTS_TO_RUN={to_run_line}")
    click.echo(f"TESTS_TO_SKIP={to_skip_line}")


def _dry_run_output(
    result: LabelAnalysisRequestResult,
    runner: LabelAnalysisRunnerInterface,
    dry_run_format: str,
    *,
    # If we have a fallback reason it means that calculating the list of tests to run
    # failed at some point. So it was not a completely successful task.
    fallback_reason: str = None,
):
    labels_to_run = set(
        result.absent_labels + result.global_level_labels + result.present_diff_labels
    )
    labels_to_skip = set(result.present_report_labels) - labels_to_run

    format_lookup = {
        "json": _dry_run_json_output,
        "space-separated-list": _dry_run_list_output,
    }
    # Because dry_run_format is a click.Choice we can
    # be sure the value will be in the dict of choices
    fn_to_use = format_lookup[dry_run_format]
    fn_to_use(
        labels_to_run, labels_to_skip, runner.dry_run_runner_options, fallback_reason
    )


def _fallback_to_collected_labels(
    collected_labels: List[str],
    runner: LabelAnalysisRunnerInterface,
    *,
    fallback_reason: str = None,
    dry_run: bool = False,
    dry_run_format: Optional[pathlib.Path] = None,
) -> dict:
    logger.info("Trying to fallback on collected labels")
    if collected_labels:
        logger.info("Using collected labels as tests to run")
        fake_response = LabelAnalysisRequestResult(
            {
                "present_report_labels": [],
                "absent_labels": collected_labels,
                "present_diff_labels": [],
                "global_level_labels": [],
            }
        )
        if not dry_run:
            return runner.process_labelanalysis_result(fake_response)
        else:
            return _dry_run_output(
                LabelAnalysisRequestResult(fake_response),
                runner,
                dry_run_format,
                fallback_reason=fallback_reason,
            )
    logger.error("Cannot fallback to collected labels because no labels were collected")
    raise click.ClickException("Failed to get list of labels to run")
