import logging
import pprint
import subprocess
import time

import click
import requests

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum

logger = logging.getLogger("codecovcli")


@click.command()
@click.option(
    "--token",
    required=True,
    help="The static analysis token (NOT the same token as upload)",
)
@click.option(
    "--head-sha",
    "head_commit_sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    required=True,
)
@click.option(
    "--base-sha",
    "base_commit_sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    required=True,
)
def label_analysis(token, head_commit_sha, base_commit_sha):
    logger.debug(
        "Starting label analysis",
        extra=dict(
            extra_log_attributes=dict(
                head_commit_sha=head_commit_sha,
                base_commit_sha=base_commit_sha,
                token="NOTOKEN" if not token else (str(token)[:1] + 18 * "*"),
            )
        ),
    )
    url = "https://api.codecov.io/labels/labels-analysis"
    token_header = f"Repotoken {token}"
    # this needs to be more flexible to support multiple elements
    runner = PythonStandardRunner()
    requested_labels = runner.collect_tests()
    logger.info(f"Collected {len(requested_labels)} tests")
    logger.debug(
        "Labels collected.",
        extra=dict(extra_log_attributes=dict(labels_collected=requested_labels)),
    )
    payload = {
        "base_commit": base_commit_sha,
        "head_commit": head_commit_sha,
        "requested_labels": requested_labels,
    }
    try:
        response = requests.post(
            url, json=payload, headers={"Authorization": token_header}
        )
        if response.status_code >= 500:
            logger.warning(
                "Sorry. Codecov is having problems",
                extra=dict(extra_log_attributes=dict(status_code=response.status_code)),
            )
            if requested_labels:
                logger.info(
                    "Could not get set of tests to run. Falling back to running all collected tests."
                )
                fake_response = {
                    "present_report_labels": [],
                    "absent_labels": requested_labels,
                    "present_diff_labels": [],
                    "global_level_labels": [],
                }
                return runner.do_something_with_result(fake_response)
            raise click.ClickException("Sorry. Codecov is having problems")
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
    has_result = False
    logger.info("Label request sent")
    time.sleep(2)
    while not has_result:
        resp_data = requests.get(
            f"https://api.codecov.io/labels/labels-analysis/{eid}",
            headers={"Authorization": token_header},
        )
        resp_json = resp_data.json()
        if resp_json["state"] == "finished":
            runner.do_something_with_result(resp_data.json()["result"])
            return
        if resp_json["state"] == "error":
            logger.error(
                "Request had problems calculating",
                extra=dict(extra_log_attributes=dict(resp_json=resp_json)),
            )
            if requested_labels:
                logger.info("Using requested labels as tests to run")
                fake_response = {
                    "present_report_labels": [],
                    "absent_labels": requested_labels,
                    "present_diff_labels": [],
                    "global_level_labels": [],
                }
                return runner.do_something_with_result(fake_response)
            return
        logger.info("Waiting more time for result")
        time.sleep(5)


class PythonStandardRunner(object):
    def collect_tests(self):
        return [
            x
            for x in subprocess.run(
                ["python", "-m", "pytest", "-q", "--collect-only"],
                capture_output=True,
                check=True,
            )
            .stdout.decode()
            .split()
            if "::" in x
        ]

    def do_something_with_result(self, result):
        command_array = ["python", "-m", "pytest", "--cov=./", "--cov-context=test"]
        logger.info(
            "Received information about tests to run",
            extra=dict(
                extra_log_attributes=dict(
                    absent_labels=len(result["absent_labels"] or []),
                    present_diff_labels=len(result["present_diff_labels"] or []),
                    global_level_labels=len(result["global_level_labels"] or []),
                    present_report_labels=len(result["present_report_labels"] or []),
                )
            ),
        )
        all_labels = (
            result["absent_labels"]
            + result["present_diff_labels"]
            + result["global_level_labels"]
        )
        skipped_tests = set(result["present_report_labels"]) - set(all_labels)
        if skipped_tests:
            logger.info(
                "Some tests are being skipped",
                extra=dict(
                    extra_log_attributes=dict(skipped_tests=sorted(skipped_tests))
                ),
            )
        all_labels = set(all_labels)
        all_labels = [x.rsplit("[", 1)[0] if "[" in x else x for x in all_labels]
        # Not safe from the customer perspective, in general, probably.
        # This is just to check it working
        command_array.extend(all_labels)
        logger.info("Running tests")
        logger.debug(
            "Pytest command",
            extra=dict(extra_log_attributes=dict(command_array=command_array)),
        )
        subprocess.run(command_array, check=True)
