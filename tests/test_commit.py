from click.testing import CliRunner

from codecov_cli.services.commit import CommitSender, create_commit_logic
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning


def test_commit_command_with_warnings(mocker):
    mock_send_commit_data = mocker.patch.object(
        CommitSender,
        "send_commit_data",
        return_value=RequestResult(
            error=None,
            warnings=[RequestResultWarning(message="somewarningmessage")],
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
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == [
        "info: Commit creating process had 1 warning",
        "warning: Warning 1: somewarningmessage",
    ]
    assert res == CommitSender.send_commit_data.return_value
    mock_send_commit_data.assert_called_with(
        commit_sha="commit_sha",
        parent_sha="parent_sha",
        pr="pr_num",
        branch="branch",
        slug="owner::::repo",
    )


def test_commit_command_with_error(mocker):
    mock_send_commit_data = mocker.patch.object(
        CommitSender,
        "send_commit_data",
        return_value=RequestResult(
            error=RequestError(
                code="HTTP Error 403",
                description="Permission denied",
                params={},
            ),
            warnings=[],
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
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == ["error: Commit creating failed: Permission denied"]
    assert res == CommitSender.send_commit_data.return_value
    mock_send_commit_data.assert_called_with(
        commit_sha="commit_sha",
        parent_sha="parent_sha",
        pr="pr_num",
        branch="branch",
        slug="owner::::repo",
    )


def test_commit_sender_200(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.commit.commit_sender.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    sender = CommitSender()
    res = sender.send_commit_data("commit_sha", "parent_sha", "pr", "branch", "slug")
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_commit_sender_403(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.commit.commit_sender.requests.post",
        return_value=mocker.MagicMock(status_code=403, text="Permission denied"),
    )
    sender = CommitSender()
    res = sender.send_commit_data("commit_sha", "parent_sha", "pr", "branch", "slug")
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()
