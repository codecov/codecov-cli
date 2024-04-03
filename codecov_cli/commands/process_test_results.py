import os
import pathlib
from dataclasses import dataclass

import click
from test_results_parser import Outcome, Testrun, parse_junit_xml

from codecov_cli.services.upload.file_finder import select_file_finder

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
]


def process_test_results_options(func):
    for option in reversed(_process_test_results_options):
        func = option(func)
    return func


@dataclass
class TestResultsNotificationPayload:
    failures: list[Testrun]
    failed: int = 0
    passed: int = 0
    skipped: int = 0


@click.command()
@process_test_results_options
def process_test_results(
    dir=None,
    files=None,
    exclude_folders=None,
    disable_search=None,
):
    file_finder = select_file_finder(
        dir, exclude_folders, files, disable_search, report_type="test_results"
    )
    upload_collection_results = file_finder.find_files()
    payload = TestResultsNotificationPayload(failures=[])

    for result in upload_collection_results:
        testruns = parse_junit_xml(result.get_content())
        for testrun in testruns:
            if testrun.outcome == Outcome.Failure or testrun.outcome == Outcome.Error:
                payload.failed += 1
                payload.failures.append(testrun)
            elif testrun.outcome == Outcome.Skip:
                payload.skipped += 1
            else:
                payload.passed += 1

    message = build_message(payload)

    os.environ["GITHUB_STEP_SUMMARY"] = message

    print("Done!")
    print(message)


def generate_test_description(
    fail: Testrun,
):
    test_description = (
        f"Testsuite:<br>{fail.testsuite}<br>" f"Test name:<br>{fail.name}<br>"
    )
    return test_description


def generate_failure_info(
    fail: Testrun,
):
    if fail.failure_message is not None:
        return fail.failure_message
    else:
        return "No failure message available"


def build_message(payload: TestResultsNotificationPayload) -> str:
    message = []

    message += [
        "### :x: Failed Test Results: ",
    ]

    completed = payload.failed + payload.passed + payload.skipped
    results = f"Completed {completed} tests with **`{payload.failed} failed`**, {payload.passed} passed and {payload.skipped} skipped."

    message.append(results)

    details = [
        "<details><summary>View the full list of failed tests</summary>",
        "",
        "| **Test Description** | **Failure message** |",
        "| :-- | :-- |",
    ]

    message += details

    for fail in payload.failures:
        test_description = generate_test_description(fail)
        failure_information = generate_failure_info(fail)
        single_test_row = (
            f"| <pre>{test_description}</pre> | <pre>{failure_information}</pre> |"
        )
        message.append(single_test_row)

    return "\n".join(message)
