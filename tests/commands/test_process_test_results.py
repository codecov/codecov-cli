import logging
import os

from click.testing import CliRunner

from codecov_cli.main import cli
from codecov_cli.types import RequestResult


def test_process_test_results(
    mocker,
    tmpdir,
):

    tmp_file = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/pull",
            "GITHUB_STEP_SUMMARY": tmp_file.dirname + tmp_file.basename,
        },
    )
    mocked_post = mocker.patch(
        "codecov_cli.commands.process_test_results.send_post_request",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text="yay it worked"
        ),
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "process-test-results",
            "--provider-token",
            "whatever",
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 0

    mocked_post.assert_called_with(
        url="https://api.github.com/repos/fake/repo/issues/pull/comments",
        data={
            "body": "### :x: Failed Test Results: \nCompleted 4 tests with **`1 failed`**, 3 passed and 0 skipped.\n<details><summary>View the full list of failed tests</summary>\n\n| **Test Description** | **Failure message** |\n| :-- | :-- |\n| <pre>Testsuite:<br>api.temp.calculator.test_calculator::test_divide<br><br>Test name:<br>pytest<br></pre> | <pre>def<br>                test_divide():<br>                &amp;gt; assert Calculator.divide(1, 2) == 0.5<br>                E assert 1.0 == 0.5<br>                E + where 1.0 = &amp;lt;function Calculator.divide at 0x104c9eb90&amp;gt;(1, 2)<br>                E + where &amp;lt;function Calculator.divide at 0x104c9eb90&amp;gt; = Calculator.divide<br>                .../temp/calculator/test_calculator.py:30: AssertionError</pre> |"
        },
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer whatever",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def test_process_test_results_non_existent_file(mocker, tmpdir):
    tmp_file = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/pull",
            "GITHUB_STEP_SUMMARY": tmp_file.dirname + tmp_file.basename,
        },
    )
    mocked_post = mocker.patch(
        "codecov_cli.commands.process_test_results.send_post_request",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text="yay it worked"
        ),
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "process-test-results",
            "--provider-token",
            "whatever",
            "--file",
            "samples/fake.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 1
    expected_logs = [
        "ci service found",
        "Some files were not found",
    ]
    for log in expected_logs:
        assert log in result.output


def test_process_test_results_missing_repo(mocker, tmpdir):
    tmp_file = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REF": "pull/fake/pull",
            "GITHUB_STEP_SUMMARY": tmp_file.dirname + tmp_file.basename,
        },
    )
    if "GITHUB_REPOSITORY" in os.environ:
        del os.environ["GITHUB_REPOSITORY"]
    mocked_post = mocker.patch(
        "codecov_cli.commands.process_test_results.send_post_request",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text="yay it worked"
        ),
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "process-test-results",
            "--provider-token",
            "whatever",
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 1
    expected_logs = [
        "ci service found",
        "Error: Error getting repo slug from environment. Can't find GITHUB_REPOSITORY environment variable.",
    ]
    for log in expected_logs:
        assert log in result.output


def test_process_test_results_missing_ref(mocker, tmpdir):
    tmp_file = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_STEP_SUMMARY": tmp_file.dirname + tmp_file.basename,
        },
    )

    if "GITHUB_REF" in os.environ:
        del os.environ["GITHUB_REF"]
    mocked_post = mocker.patch(
        "codecov_cli.commands.process_test_results.send_post_request",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text="yay it worked"
        ),
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "process-test-results",
            "--provider-token",
            "whatever",
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 1
    expected_logs = [
        "ci service found",
        "Error: Error getting PR number from environment. Can't find GITHUB_REF environment variable.",
    ]
    for log in expected_logs:
        assert log in result.output


def test_process_test_results_missing_step_summary(mocker, tmpdir):
    tmp_file = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/pull",
        },
    )
    if "GITHUB_STEP_SUMMARY" in os.environ:
        del os.environ["GITHUB_STEP_SUMMARY"]
    mocked_post = mocker.patch(
        "codecov_cli.commands.process_test_results.send_post_request",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text="yay it worked"
        ),
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "process-test-results",
            "--provider-token",
            "whatever",
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 1
    expected_logs = [
        "ci service found",
        "Error: Error getting step summary file path from environment. Can't find GITHUB_STEP_SUMMARY environment variable.",
    ]
    for log in expected_logs:
        assert log in result.output
