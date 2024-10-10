import json
import logging
import os
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import click
from test_results_parser import (
    Outcome,
    ParserError,
    Testrun,
    build_message,
    parse_junit_xml,
)

from codecov_cli.helpers.args import get_cli_args
from codecov_cli.helpers.request import (
    log_warnings_and_errors_if_any,
    send_get_request,
    send_post_request,
)
from codecov_cli.services.upload.file_finder import select_file_finder
from codecov_cli.types import CommandContext, RequestResult, UploadCollectionResultFile

logger = logging.getLogger("codecovcli")

# Search marker so that we can find the comment when looking for previously created comments
CODECOV_SEARCH_MARKER = "<!-- Codecov -->"


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
        "--github-token",
        help="If specified, output the message to the specified GitHub PR.",
        type=str,
        default=None,
    ),
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
@click.pass_context
def process_test_results(
    ctx: CommandContext,
    dir=None,
    files=None,
    exclude_folders=None,
    disable_search=None,
    github_token=None,
):
    file_finder = select_file_finder(
        dir, exclude_folders, files, disable_search, report_type="test_results"
    )

    upload_collection_results: List[
        UploadCollectionResultFile
    ] = file_finder.find_files()
    if len(upload_collection_results) == 0:
        raise click.ClickException(
            "No JUnit XML files were found. Make sure to specify them using the --file option."
        )

    payload: TestResultsNotificationPayload = generate_message_payload(
        upload_collection_results
    )

    message: str = f"{build_message(payload)} {CODECOV_SEARCH_MARKER}"

    args: Dict[str, str] = get_cli_args(ctx)

    maybe_write_to_github_action(message, github_token, args)

    click.echo(message)


def maybe_write_to_github_action(
    message: str, github_token: str, args: Dict[str, str]
) -> None:
    if github_token is None:
        # If no token is passed, then we will assume users are not running in a GitHub Action
        return

    maybe_write_to_github_comment(message, github_token, args)


def maybe_write_to_github_comment(
    message: str, github_token: str, args: Dict[str, str]
) -> None:
    slug = os.getenv("GITHUB_REPOSITORY")
    if slug is None:
        raise click.ClickException(
            "Error getting repo slug from environment. "
            "Can't find GITHUB_REPOSITORY environment variable."
        )

    ref = os.getenv("GITHUB_REF")
    if ref is None or "pull" not in ref:
        raise click.ClickException(
            "Error getting PR number from environment. "
            "Can't find GITHUB_REF environment variable."
        )
    # GITHUB_REF is documented here: https://docs.github.com/en/actions/learn-github-actions/variables#default-environment-variables
    pr_number = ref.split("/")[2]

    existing_comment = find_existing_github_comment(github_token, slug, pr_number)
    comment_id = None
    if existing_comment is not None:
        comment_id = existing_comment.get("id")

    create_or_update_github_comment(
        github_token, slug, pr_number, message, comment_id, args
    )


def find_existing_github_comment(
    github_token: str, repo_slug: str, pr_number: int
) -> Optional[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{repo_slug}/issues/{pr_number}/comments"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    page = 1

    results = get_github_response_or_error(url, headers, page)
    while results != []:
        for comment in results:
            comment_user = comment.get("user")
            if (
                CODECOV_SEARCH_MARKER in comment.get("body", "")
                and comment_user
                and comment_user.get("login", "") == "github-actions[bot]"
            ):
                return comment

        page += 1
        results = get_github_response_or_error(url, headers, page)

    # No matches, return None
    return None


def get_github_response_or_error(
    url: str, headers: Dict[str, str], page: int
) -> Dict[str, Any]:
    request_results: RequestResult = send_get_request(
        url, headers, params={"page": page}
    )
    if request_results.status_code != 200:
        raise click.ClickException("Cannot find existing GitHub comment for PR.")
    results = json.loads(request_results.text)
    return results


def create_or_update_github_comment(
    token: str,
    repo_slug: str,
    pr_number: str,
    message: str,
    comment_id: Optional[str],
    args: Dict[str, Any],
) -> None:
    if comment_id is not None:
        url = f"https://api.github.com/repos/{repo_slug}/issues/comments/{comment_id}"
    else:
        url = f"https://api.github.com/repos/{repo_slug}/issues/{pr_number}/comments"

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    logger.info(f"Posting GitHub comment {comment_id}")

    log_warnings_and_errors_if_any(
        send_post_request(
            url=url,
            data={
                "body": message,
                "cli_args": args,
            },
            headers=headers,
        ),
        "Posting test results comment",
    )


def generate_message_payload(
    upload_collection_results: List[UploadCollectionResultFile],
) -> TestResultsNotificationPayload:
    payload = TestResultsNotificationPayload(failures=[])

    for result in upload_collection_results:
        try:
            logger.info(f"Parsing {result.get_filename()}")
            parsed_info = parse_junit_xml(result.get_content())
            for testrun in parsed_info.testruns:
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
