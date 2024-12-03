import uuid

from click.testing import CliRunner

from codecov_cli.services.commit import create_commit_logic, send_commit_data
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning
from tests.test_helpers import parse_outstreams_into_log_lines


def test_commit_command_with_warnings(mocker):
    mock_send_commit_data = mocker.patch(
        "codecov_cli.services.commit.send_commit_data",
        return_value=RequestResult(
            error=None,
            warnings=[RequestResultWarning(message="somewarningmessage")],
            status_code=201,
            text="",
        ),
    )
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = create_commit_logic(
            commit_sha="commit_sha",
            parent_sha="parent_sha",
            pr="pr_num",
            branch="branch",
            slug="owner/repo",
            token="token",
            service="service",
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Commit creating complete"),
        ("info", "Commit creating process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]
    assert res == mock_send_commit_data.return_value
    mock_send_commit_data.assert_called_with(
        commit_sha="commit_sha",
        parent_sha="parent_sha",
        pr="pr_num",
        branch="branch",
        slug="owner::::repo",
        token="token",
        service="service",
        enterprise_url=None,
        args=None,
    )


def test_commit_command_with_error(mocker):
    mock_send_commit_data = mocker.patch(
        "codecov_cli.services.commit.send_commit_data",
        return_value=RequestResult(
            error=RequestError(
                code="HTTP Error 403",
                description="Permission denied",
                params={},
            ),
            warnings=[],
            status_code=403,
            text="Permission denied",
        ),
    )
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = create_commit_logic(
            commit_sha="commit_sha",
            parent_sha="parent_sha",
            pr="pr_num",
            branch="branch",
            slug="owner/repo",
            token="token",
            service="service",
            enterprise_url=None,
            args={},
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        (
            "info",
            "Process Commit creating complete",
        ),
        ("error", "Commit creating failed: Permission denied"),
    ]
    assert res == mock_send_commit_data.return_value
    mock_send_commit_data.assert_called_with(
        commit_sha="commit_sha",
        parent_sha="parent_sha",
        pr="pr_num",
        branch="branch",
        slug="owner::::repo",
        token="token",
        service="service",
        enterprise_url=None,
        args={},
    )


def test_commit_sender_200(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    token = uuid.uuid4()
    res = send_commit_data(
        "commit_sha",
        "parent_sha",
        "pr",
        "branch",
        "owner::::repo",
        token,
        "service",
        None,
        None,
    )
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_commit_sender_403(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=403, text="Permission denied"),
    )
    token = uuid.uuid4()
    res = send_commit_data(
        "commit_sha",
        "parent_sha",
        "pr",
        "branch",
        "owner::::repo",
        token,
        "service",
        None,
        None,
    )
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()


def test_commit_sender_with_forked_repo(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.commit.send_post_request",
        return_value=mocker.MagicMock(status_code=200, text="success"),
    )

    _ = send_commit_data(
        "commit_sha",
        "parent_sha",
        "1",
        "user_forked_repo/codecov-cli:branch",
        "codecov::::codecov-cli",
        None,
        "github",
        None,
        None,
    )
    mocked_response.assert_called_with(
        url="https://ingest.codecov.io/upload/github/codecov::::codecov-cli/commits",
        data={
            "branch": "user_forked_repo/codecov-cli:branch",
            "cli_args": None,
            "commitid": "commit_sha",
            "parent_commit_id": "parent_sha",
            "pullid": "1",
        },
        headers=None,
    )


def test_commit_without_token(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.commit.send_post_request",
        return_value=mocker.MagicMock(status_code=200, text="success"),
    )

    send_commit_data(
        "commit_sha",
        "parent_sha",
        "1",
        "branch",
        "codecov::::codecov-cli",
        None,
        "github",
        None,
        None,
    )
    mocked_response.assert_called_with(
        url="https://ingest.codecov.io/upload/github/codecov::::codecov-cli/commits",
        data={
            "branch": "branch",
            "cli_args": None,
            "commitid": "commit_sha",
            "parent_commit_id": "parent_sha",
            "pullid": "1",
        },
        headers=None,
    )


def test_commit_sender_with_forked_repo_bad_branch(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.commit.send_post_request",
        return_value=mocker.MagicMock(status_code=200, text="success"),
    )
    mocker.patch("os.environ", dict(TOKENLESS="user_forked_repo/codecov-cli:branch"))
    _res = send_commit_data(
        "commit_sha",
        "parent_sha",
        "1",
        "branch",
        "codecov::::codecov-cli",
        None,
        "github",
        None,
        None,
    )

    mocked_response.assert_called_with(
        url="https://ingest.codecov.io/upload/github/codecov::::codecov-cli/commits",
        data={
            "branch": "user_forked_repo/codecov-cli:branch",
            "cli_args": None,
            "commitid": "commit_sha",
            "parent_commit_id": "parent_sha",
            "pullid": "1",
        },
        headers=None,
    )
