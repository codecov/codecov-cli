import logging
import pathlib
import subprocess
import typing

import click

from codecov_cli.commands.commit import create_commit
from codecov_cli.commands.labelanalysis import label_analysis, label_analysis_options
from codecov_cli.commands.report import create_report
from codecov_cli.commands.staticanalysis import static_analysis, static_analysis_options
from codecov_cli.fallbacks import CodecovOption
from codecov_cli.helpers.options import global_options
from codecov_cli.helpers.validators import validate_commit_sha

logger = logging.getLogger("codecovcli")


@click.command()
@global_options
@static_analysis_options
@label_analysis_options
@click.option(
    "--static-token",
    required=True,
    envvar="CODECOV_STATIC_TOKEN",
    help="The static analysis token (NOT the same token as upload)",
)
@click.option(
    "--base-sha",
    "base_commit_sha",
    help="Base for comparing code changes to determine tests to run. If not provided we will try ancestors of the head commit.",
    required=False,
    cls=CodecovOption,
    callback=validate_commit_sha,
)
@click.pass_context
def automated_test_selection(
    ctx: click.Context,
    # create-commit and create-report options
    # come from @global-options
    commit_sha: str,
    report_code: str,
    token: typing.Optional[str],
    branch: typing.Optional[str],
    slug: typing.Optional[str],
    pull_request_number: typing.Optional[str],
    git_service: typing.Optional[str],
    parent_sha: typing.Optional[str],
    # static-analysis options
    # missing 'token' and 'commit-sha'
    foldertosearch: pathlib.Path,
    numberprocesses: typing.Optional[int],
    pattern: str,
    force: bool,
    folders_to_exclude: typing.List[pathlib.Path],
    # label-analysis options
    # missing 'token', 'base-sha' and 'head-sha'
    runner_name: str,
    max_wait_time: str,
    dry_run: bool,
    dry_run_format: str,
    # token for static-analysis and label-analysis
    static_token: str,
    # different from label-analysis because optional
    base_commit_sha: typing.Optional[str],
):
    """The Automated Test Selection command combines all the necessary commands to run ATS.
    learn more: https://docs.codecov.com/docs/automated-test-selection

    The commands executed are:
    1. create-commit
    2. create-report
    3. static-analysis
    4. label-analysis

    Things that aren't commands but are executed as well:
    - pick potential candidates for label-analysis base commits
    - writes results to files in `codecov_ats` folder
    """
    logger.info(
        "=> Starting Automated Test Selection process",
        extra=dict(
            extra_log_attributes=dict(
                head_commit=commit_sha, slug=slug, base_commit_sha=base_commit_sha
            )
        ),
    )
    ctx.invoke(
        create_commit,
        commit_sha=commit_sha,
        parent_sha=parent_sha,
        pull_request_number=pull_request_number,
        branch=branch,
        slug=slug,
        token=token,
        git_service=git_service,
        fail_on_error=True,
    )
    ctx.invoke(
        create_report,
        token=token,
        code=report_code,
        fail_on_error=True,
        commit_sha=commit_sha,
        slug=slug,
        git_service=git_service,
    )
    logger.info("=> Commit and Report created successfully")
    ctx.invoke(
        static_analysis,
        foldertosearch,
        numberprocesses,
        pattern,
        commit_sha,
        token,
        force,
        folders_to_exclude,
    )
    logger.info("=> Static Analysis sucessful")

    raise click.ClickException("Not implemented yet")


def get_candidate_base_commits() -> typing.Optional[typing.List[str]]:
    result = subprocess.run(
        ["git", "log", "--format=%H", "-n", "10"], capture_output=True, check=True
    )
    if result.returncode != 0:
        return
    return result.stdout.decode().strip().split("\n")
