import os
import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import List

import click
import regex
from test_results_parser import Outcome, Testrun, parse_junit_xml

from codecov_cli.services.upload.file_finder import select_file_finder


class EscapeEnum(Enum):
    APPEND = "append"
    PREPEND = "prepend"
    REPLACE = "replace"


@dataclass
class Replacement:
    strings: List[str]
    output: str
    method: EscapeEnum


class StringEscaper:
    """
    Class to use to escape strings using format defined
    through a dict.

    Args:
        escape_def: list of Replacement that defines how to escape
        characters

        string is escaped by applying method in each Replacement
        to each char in Replacement.chars using the char in output

        for example:
            escape_def = [
                Replacement(["1"], "2", EscapeEnum.APPEND),
                Replacement(["3"], "4", EscapeEnum.PREPEND),
                Replacement(["5", "6"], "6", EscapeEnum.REPLACE),
            ]

            escaper = StringEscaper(escape_def)

            escaper.replace("123456")

            will give: "12243466"
    """

    def __init__(self, escape_def: List[Replacement]):
        self.escape_def = escape_def

    def replace(self, replacement_target):
        for replacement in self.escape_def:
            for string in replacement.strings:
                if replacement.method == EscapeEnum.PREPEND:
                    replacement_target = replacement_target.replace(
                        string, f"{replacement.output}{string}"
                    )
                elif replacement.method == EscapeEnum.APPEND:
                    replacement_target = replacement_target.replace(
                        string, f"{string}{replacement.output}"
                    )
                elif replacement.method == EscapeEnum.REPLACE:
                    replacement_target = replacement_target.replace(
                        string, replacement.output
                    )
        return replacement_target


MAX_PATH_COMPONENTS = 3


# matches file paths with an optional line number and column at the end:
# /Users/josephsawaya/dev/test-result-action/demo/calculator/calculator.test.ts:10:31
# /Users/josephsawaya/dev/test-result-action/demo/calculator/calculator.test.ts
# Users/josephsawaya/dev/test-result-action/demo/calculator/calculator.test.ts
file_path_regex = regex.compile(
    r"((\/*[\w\-]+\/)+([\w\.]+)(:\d+:\d+)*)",
)


def shorten_file_paths(string):
    """
    This function takes in a string and returns it with all the paths
    it contains longer than 3 components shortened to 3 components

    Example:
        string =    '''
            Expected: 1
            Received: -1
                at Object.&lt;anonymous&gt; (/Users/josephsawaya/dev/test-result-action/demo/calculator/calculator.test.ts:10:31)
                at Promise.then.completed (/Users/josephsawaya/dev/test-result-action/node_modules/jest-circus/build/utils.js:298:28)
        '''
        shortened_string = shorten_file_paths(string)
        print(shortened_string)

        will print:
            Expected: 1
            Received: -1
                at Object.&lt;anonymous&gt; (.../demo/calculator/calculator.test.ts:10:31)
                at Promise.then.completed (.../jest-circus/build/utils.js:298:28)
    """

    matches = file_path_regex.findall(string)
    for match_tuple in matches:
        file_path = match_tuple[0]
        split_file_path = file_path.split("/")

        # if the file_path has more than 3 components we should shorten it
        if len(split_file_path) > MAX_PATH_COMPONENTS:
            last_path_components = split_file_path[-MAX_PATH_COMPONENTS:]
            no_dots_shortened_file_path = "/".join(last_path_components)

            # possibly remove leading / because we're adding it with the dots
            if no_dots_shortened_file_path.startswith("/"):
                no_dots_shortened_file_path = no_dots_shortened_file_path[1:]

            shortened_path = ".../" + no_dots_shortened_file_path

            string = string.replace(file_path, shortened_path)

    return string


ESCAPE_FAILURE_MESSAGE_DEFN = [
    Replacement(['"'], "&quot;", EscapeEnum.REPLACE),
    Replacement(["'"], "&apos;", EscapeEnum.REPLACE),
    Replacement(["<"], "&lt;", EscapeEnum.REPLACE),
    Replacement([">"], "&gt;", EscapeEnum.REPLACE),
    Replacement(["?"], "&amp;", EscapeEnum.REPLACE),
    Replacement(["\r"], "", EscapeEnum.REPLACE),
    Replacement(["\n"], "<br>", EscapeEnum.REPLACE),
]

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
    escaper = StringEscaper(ESCAPE_FAILURE_MESSAGE_DEFN)

    if fail.failure_message is not None:
        failure_message = escaper.replace(fail.failure_message)
        return failure_message
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
