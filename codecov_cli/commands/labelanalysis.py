import logging
import time

import click
import requests

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.runners import get_runner

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
@click.pass_context
def label_analysis(
    ctx: click.Context,
    token: str,
    head_commit_sha: str,
    base_commit_sha: str,
    runner_name: str = "python",
):
    logger.debug(
        "Starting label analysis",
        extra=dict(
            extra_log_attributes=dict(
                head_commit_sha=head_commit_sha,
                base_commit_sha=base_commit_sha,
                token="NOTOKEN" if not token else (str(token)[:1] + 18 * "*"),
                runner_name=runner_name,
            )
        ),
    )
    url = "https://api.codecov.io/labels/labels-analysis"
    token_header = f"Repotoken {token}"

    codecov_yaml = ctx.obj["codecov_yaml"] or {}
    cli_config = codecov_yaml.get("cli", {})
    runner = get_runner(cli_config, runner_name)
    logger.debug(
        f"Selected runner: {runner}",
        extra=dict(extra_log_attributes=dict(config=runner.params)),
    )
    logger.info("Collecting labels...")
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
    logger.info("Requesting set of labels to run...")
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
                return runner.process_labelanalysis_result(fake_response)
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
    logger.info("Label request sent. Waiting for result.")
    time.sleep(2)
    while not has_result:
        resp_data = requests.get(
            f"https://api.codecov.io/labels/labels-analysis/{eid}",
            headers={"Authorization": token_header},
        )
        resp_json = resp_data.json()
        if resp_json["state"] == "finished":
            runner.process_labelanalysis_result(resp_data.json()["result"])
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
                return runner.process_labelanalysis_result(fake_response)
            return
        logger.info("Waiting more time for result")
        time.sleep(5)
