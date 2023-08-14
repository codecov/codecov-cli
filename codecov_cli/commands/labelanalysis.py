import json
import logging
import time
from typing import List

import click
import requests

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
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
    "--runner-name", "--runner", "runner_name", help="Runner to use", default="python"
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
    help="Userful during setup. This will run the label analysis, but will print the result to stdout and terminate instead of calling the runner.process_labelanalysis_result",
    is_flag=True,
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
    runner = get_runner(cli_config, runner_name)
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
            _fallback_to_collected_labels(requested_labels, runner, dry_run=dry_run)
            return

    has_result = False
    logger.info("Waiting for list of tests to run...")
    start_wait = time.monotonic()
    time.sleep(1)
    while not has_result:
        resp_data = requests.get(
            f"{upload_url}/labels/labels-analysis/{eid}",
            headers={"Authorization": token_header},
        )
        resp_json = resp_data.json()
        if resp_json["state"] == "finished":
            request_result = _potentially_calculate_absent_labels(
                resp_data.json()["result"], requested_labels
            )
            if not dry_run:
                runner.process_labelanalysis_result(request_result)
            else:
                _dry_run_output(LabelAnalysisRequestResult(request_result))
            return
        if resp_json["state"] == "error":
            logger.error(
                "Request had problems calculating",
                extra=dict(extra_log_attributes=dict(resp_json=resp_json)),
            )
            _fallback_to_collected_labels(
                collected_labels=requested_labels, runner=runner, dry_run=dry_run
            )
            return
        if max_wait_time and (time.monotonic() - start_wait) > max_wait_time:
            logger.error(
                f"Exceeded max waiting time of {max_wait_time} seconds. Running all tests.",
            )
            _fallback_to_collected_labels(
                collected_labels=requested_labels, runner=runner, dry_run=dry_run
            )
            return
        logger.info("Waiting more time for result...")
        time.sleep(5)


def _potentially_calculate_absent_labels(
    request_result, requested_labels
) -> LabelAnalysisRequestResult:
    logger.info(
        "Received list of tests from Codecov",
        extra=dict(
            extra_log_attributes=dict(
                processing_errors=request_result.get("errors", [])
            )
        ),
    )
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
        response = requests.patch(
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
        response = requests.post(
            url, json=payload, headers={"Authorization": token_header}
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


def _dry_run_output(result: LabelAnalysisRequestResult):
    logger.info(
        "Not executing tests because '--dry-run' is on. List of labels selected for running below."
    )
    logger.info("")
    logger.info("Label groups:")
    logger.info(
        "- absent_labels: Set of new labels found in HEAD that are not present in BASE"
    )
    logger.info("- present_diff_labels: Set of labels affected by the git diff")
    logger.info("- global_level_labels: Set of labels that possibly touch global code")
    logger.info("- present_report_labels: Set of labels previously uploaded")
    logger.info("")
    logger.info(json.dumps(result))


def _fallback_to_collected_labels(
    collected_labels: List[str],
    runner: LabelAnalysisRunnerInterface,
    *,
    dry_run: bool = False,
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
            return _dry_run_output(LabelAnalysisRequestResult(fake_response))
    logger.error("Cannot fallback to collected labels because no labels were collected")
    raise click.ClickException("Failed to get list of labels to run")
