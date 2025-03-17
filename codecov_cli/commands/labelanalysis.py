import json
import logging
import pathlib
from typing import Dict, List, Optional

import click
import sentry_sdk

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.validators import validate_commit_sha
from codecov_cli.runners import get_runner
from codecov_cli.runners.types import (
    LabelAnalysisRequestResult,
    LabelAnalysisRunnerInterface,
)
from codecov_cli.types import CommandContext

logger = logging.getLogger("codecovcli")


@click.command(hidden=True, deprecated=True)
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
    ctx: CommandContext,
    token: str,
    head_commit_sha: str,
    base_commit_sha: str,
    runner_name: str,
    max_wait_time: str,
    dry_run: bool,
    dry_run_format: str,
    runner_params: List[str],
):
    with sentry_sdk.start_transaction(op="task", name="Label Analysis"):
        with sentry_sdk.start_span(name="labelanalysis"):
            args = get_cli_args(ctx)
            logger.debug(
                "Starting label analysis",
                extra=dict(
                    extra_log_attributes=args,
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

            logger.info("Collecting labels...")
            requested_labels = runner.collect_tests()
            logger.info(f"Collected {len(requested_labels)} test labels")
            logger.debug(
                "Labels collected",
                extra=dict(
                    extra_log_attributes=dict(labels_collected=requested_labels)
                ),
            )

            _fallback_to_collected_labels(
                requested_labels,
                runner,
                dry_run=dry_run,
                dry_run_format=dry_run_format,
                fallback_reason="codecov_unavailable",
            )
            return


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
                f"Runner param {param} is not well formatted. Setting value to None. Use '--runner-param key=value' to set value"
            )
            final_params[param] = None
        else:
            key, value = param.split("=", 1)
            # For list values we need to split the list too
            if "," in value:
                value = value.split(",")
            final_params[key] = value
    return final_params


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
        sorted(map(lambda option: f"'{option}'", runner_options))
        + sorted(map(lambda label: f"'{label}'", labels_to_run))
    )
    to_skip_line = " ".join(
        sorted(map(lambda option: f"'{option}'", runner_options))
        + sorted(map(lambda label: f"'{label}'", labels_to_skip))
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
