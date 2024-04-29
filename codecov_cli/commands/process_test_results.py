import logging
import os
import pathlib
from dataclasses import dataclass
from typing import List
from json import loads

import click
from test_results_parser import (
    Outcome,
    ParserError,
    Testrun,
    build_message,
    parse_junit_xml,
)

from codecov_cli.helpers.request import (
    log_warnings_and_errors_if_any,
    send_post_request,
    send_get_request,
    send_patch_request
)
from codecov_cli.services.upload.file_finder import select_file_finder

logger = logging.getLogger("codecovcli")


_process_test_results_options = [
    click.option(
        "-s",
        "--dir",
        "--files-search-root-folder",
        "dir",
        help="Folder where to search for test results files",
        type=click.Path(path_type=pathlib.Path),
        default=pathlib.Path.cwd,
        show_default="Current Working Directory",
    ),
    click.option(
        "-f",
        "--file",
        "--files-search-direct-file",
        "files",
        help="Explicit files to upload. These will be added to the test results files to be processed. If you wish to only process the specified files, please consider using --disable-search to disable processing other files.",
        type=click.Path(path_type=pathlib.Path),
        multiple=True,
        default=[],
    ),
    click.option(
        "--exclude",
        "--files-search-exclude-folder",
        "exclude_folders",
        help="Folders to exclude from search",
        type=click.Path(path_type=pathlib.Path),
        multiple=True,
        default=[],
    ),
    click.option(
        "--disable-search",
        help="Disable search for coverage files. This is helpful when specifying what files you want to upload with the --file option.",
        is_flag=True,
        default=False,
    ),
    click.option(
        "--provider-token",
        help="Token used to make calls to Repo provider API",
        type=str,
        default=None,
    ),
    click.option(
        "--matrix",
        help="github actions matrix",
        type=str,
        default=None
    )
]


def process_test_results_options(func):
    for option in reversed(_process_test_results_options):
        func = option(func)
    return func


@dataclass
class TestResultsNotificationPayload:
    failures: List[Testrun]
    failed: int = 0
    passed: int = 0
    skipped: int = 0


@click.command()
@process_test_results_options
def process_test_results(
    dir=None, files=None, exclude_folders=None, disable_search=None, provider_token=None, matrix=None
):

    if provider_token is None:
        raise click.ClickException(
            "Provider token was not provided. Make sure to pass --provider-token option with the contents of the GITHUB_TOKEN secret, so we can make a comment."
        )

    summary_file_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file_path is None:
        raise click.ClickException(
            "Error getting step summary file path from environment. Can't find GITHUB_STEP_SUMMARY environment variable."
        )

    slug = os.getenv("GITHUB_REPOSITORY")
    if slug is None:
        raise click.ClickException(
            "Error getting repo slug from environment. Can't find GITHUB_REPOSITORY environment variable."
        )

    ref = os.getenv("GITHUB_REF")
    if ref is None or "pull" not in ref:
        raise click.ClickException(
            "Error getting PR number from environment. Can't find GITHUB_REF environment variable."
        )

    file_finder = select_file_finder(
        dir, exclude_folders, files, disable_search, report_type="test_results"
    )

    upload_collection_results = file_finder.find_files()
    if len(upload_collection_results) == 0:
        raise click.ClickException(
            "No JUnit XML files were found. Make sure to specify them using the --file option."
        )

    payload = generate_message_payload(upload_collection_results)

    message = build_message(payload)

    # write to step summary file
    with open(summary_file_path, "w") as f:
        f.write(message)

    # GITHUB_REF is documented here: https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
    pr_number = ref.split("/")[2]

    create_github_comment(provider_token, slug, pr_number, message, matrix)


def create_github_comment(token, repo_slug, pr_number, message, matrix: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url = f"https://api.github.com/repos/{repo_slug}/issues/{pr_number}/comments"
    # list comments
    result = send_get_request(url=url, headers=headers)
    comments = loads(result.text)
    matrix = matrix.strip()
    for comment in comments:        
        if f"<!-- Codecov comment for {matrix} -->" in comment:
            logger.info("Patching github comment")
            
            url = comment['url']
            log_warnings_and_errors_if_any(
                send_patch_request(url=url, json={"body": message}, headers=headers),
                "Patching test results comment",
            )
        else:
            logger.info("Posting github comment")

            log_warnings_and_errors_if_any(
                send_post_request(url=url, data={"body": message}, headers=headers),
                "Posting test results comment",
            )


def generate_message_payload(upload_collection_results):
    payload = TestResultsNotificationPayload(failures=[])

    for result in upload_collection_results:
        testruns = []
        try:
            logger.info(f"Parsing {result.get_filename()}")
            testruns = parse_junit_xml(result.get_content())
            for testrun in testruns:
                if (
                    testrun.outcome == Outcome.Failure
                    or testrun.outcome == Outcome.Error
                ):
                    payload.failed += 1
                    payload.failures.append(testrun)
                elif testrun.outcome == Outcome.Skip:
                    payload.skipped += 1
                else:
                    payload.passed += 1
        except ParserError as err:
            raise click.ClickException(
                f"Error parsing {str(result.get_filename(), 'utf8')} with error: {err}"
            )
    return payload
