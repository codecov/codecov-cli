import json
import uuid

import click
import pytest
from click.testing import CliRunner

from codecov_cli.services.empty_upload import empty_upload_logic
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning
from tests.test_helpers import parse_outstreams_into_log_lines


def test_empty_upload_with_warnings(mocker):
    mock_send_commit_data = mocker.patch(
        "codecov_cli.services.empty_upload.send_post_request",
        return_value=RequestResult(
            error=None,
            warnings=[RequestResultWarning(message="somewarningmessage")],
            status_code=201,
            text="",
        ),
    )
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = empty_upload_logic(
            "commit_sha",
            "owner/repo",
            uuid.uuid4(),
            "service",
            None,
            False,
            False,
            None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Empty Upload complete"),
        ("info", "Empty Upload process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]
    assert res == mock_send_commit_data.return_value
    mock_send_commit_data.assert_called_once()


def test_empty_upload_with_error(mocker):
    mock_send_commit_data = mocker.patch(
        "codecov_cli.services.empty_upload.send_post_request",
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
        res = empty_upload_logic(
            "commit_sha",
            "owner/repo",
            uuid.uuid4(),
            "service",
            None,
            False,
            False,
            None,
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Empty Upload complete"),
        ("error", "Empty Upload failed: Permission denied"),
    ]
    assert res == mock_send_commit_data.return_value
    mock_send_commit_data.assert_called_once()


def test_empty_upload_200(mocker):
    res = {
        "result": "All changed files are ignored. Triggering passing notifications.",
        "non_ignored_files": [],
    }
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text=json.dumps(res)
        ),
    )
    token = uuid.uuid4()
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = empty_upload_logic(
            "commit_sha", "owner/repo", token, "service", None, False, False, None
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Empty Upload complete"),
        ("info", "All changed files are ignored. Triggering passing notifications."),
        ("info", "Non ignored files []"),
    ]
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_empty_upload_403(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=403, text="Permission denied"),
    )
    token = uuid.uuid4()
    res = empty_upload_logic(
        "commit_sha", "owner/repo", token, "service", None, False, False, None
    )
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()


def test_empty_upload_force(mocker):
    res = {
        "result": "Force option was enabled. Triggering passing notifications.",
        "non_ignored_files": [],
    }
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text=json.dumps(res)
        ),
    )
    token = uuid.uuid4()
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = empty_upload_logic(
            "commit_sha", "owner/repo", token, "service", None, False, True, None
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Empty Upload complete"),
        ("info", "Force option was enabled. Triggering passing notifications."),
        ("info", "Non ignored files []"),
    ]
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_empty_upload_no_token(mocker):
    res = {
        "result": "All changed files are ignored. Triggering passing notifications.",
        "non_ignored_files": [],
    }
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=RequestResult(
            status_code=200, error=None, warnings=[], text=json.dumps(res)
        ),
    )
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = empty_upload_logic(
            "commit_sha", "owner/repo", None, "service", None, False, False, None
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Empty Upload complete"),
        ("info", "All changed files are ignored. Triggering passing notifications."),
        ("info", "Non ignored files []"),
    ]
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()
