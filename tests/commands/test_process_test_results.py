import json
import os

from click.testing import CliRunner

from codecov_cli.main import cli
from codecov_cli.types import RequestResult


def test_process_test_results(
    mocker,
    tmpdir,
):
    _ = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/pull",
        },
    )
    _ = mocker.patch(
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
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 0
    # Ensure that there's an output
    assert result.output


def test_process_test_results_create_github_message(
    mocker,
    tmpdir,
):
    _ = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/123",
        },
    )

    mocker.patch(
        "codecov_cli.commands.process_test_results.send_get_request",
        return_value=RequestResult(status_code=200, error=None, warnings=[], text="[]"),
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
            "--github-token",
            "fake-token",
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 0
    assert (
        mocked_post.call_args.kwargs["url"]
        == "https://api.github.com/repos/fake/repo/issues/123/comments"
    )


def test_process_test_results_update_github_message(
    mocker,
    tmpdir,
):
    _ = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/123",
        },
    )

    github_fake_comments1 = [
        {"id": 54321, "user": {"login": "fake"}, "body": "some text"},
    ]
    github_fake_comments2 = [
        {
            "id": 12345,
            "user": {"login": "github-actions[bot]"},
            "body": "<!-- Codecov --> and some other fake body",
        },
    ]

    mocker.patch(
        "codecov_cli.commands.process_test_results.send_get_request",
        side_effect=[
            RequestResult(
                status_code=200,
                error=None,
                warnings=[],
                text=json.dumps(github_fake_comments1),
            ),
            RequestResult(
                status_code=200,
                error=None,
                warnings=[],
                text=json.dumps(github_fake_comments2),
            ),
        ],
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
            "--github-token",
            "fake-token",
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 0
    assert (
        mocked_post.call_args.kwargs["url"]
        == "https://api.github.com/repos/fake/repo/issues/comments/12345"
    )


def test_process_test_results_errors_getting_comments(
    mocker,
    tmpdir,
):
    _ = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/123",
        },
    )

    mocker.patch(
        "codecov_cli.commands.process_test_results.send_get_request",
        return_value=RequestResult(
            status_code=400,
            error=None,
            warnings=[],
            text="",
        ),
    )

    _ = mocker.patch(
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
            "--github-token",
            "fake-token",
            "--file",
            "samples/junit.xml",
            "--disable-search",
        ],
        obj={},
    )

    assert result.exit_code == 1


def test_process_test_results_non_existent_file(mocker, tmpdir):
    _ = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
            "GITHUB_REF": "pull/fake/pull",
        },
    )
    _ = mocker.patch(
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
    _ = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REF": "pull/fake/pull",
        },
    )
    if "GITHUB_REPOSITORY" in os.environ:
        del os.environ["GITHUB_REPOSITORY"]
    _ = mocker.patch(
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
            "--github-token",
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
    _ = tmpdir.mkdir("folder").join("summary.txt")

    mocker.patch.dict(
        os.environ,
        {
            "GITHUB_REPOSITORY": "fake/repo",
        },
    )

    if "GITHUB_REF" in os.environ:
        del os.environ["GITHUB_REF"]
    _ = mocker.patch(
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
            "--github-token",
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
