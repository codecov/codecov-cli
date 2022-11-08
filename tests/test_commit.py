import uuid

from click.testing import CliRunner

from codecov_cli.services.commit import create_commit_logic, send_commit_data
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning


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
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == [
        "info: Commit creating process had 1 warning",
        "warning: Warning 1: somewarningmessage",
    ]
    assert res == mock_send_commit_data.return_value
    mock_send_commit_data.assert_called_with(
        commit_sha="commit_sha",
        parent_sha="parent_sha",
        pr="pr_num",
        branch="branch",
        slug="owner::::repo",
        token="token",
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
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == ["error: Commit creating failed: Permission denied"]
    assert res == mock_send_commit_data.return_value
    mock_send_commit_data.assert_called_with(
        commit_sha="commit_sha",
        parent_sha="parent_sha",
        pr="pr_num",
        branch="branch",
        slug="owner::::repo",
        token="token",
    )


def test_commit_sender_200(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    token = uuid.uuid4()
    res = send_commit_data("commit_sha", "parent_sha", "pr", "branch", "slug", token)
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_commit_sender_403(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=403, text="Permission denied"),
    )
    token = uuid.uuid4()
    res = send_commit_data("commit_sha", "parent_sha", "pr", "branch", "slug", token)
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()
