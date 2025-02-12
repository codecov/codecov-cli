import uuid

import pytest
import requests
from requests import Response

from codecov_cli import __version__
from codecov_cli.helpers.request import (
    get,
    get_token_header,
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
)
from codecov_cli.helpers.request import logger as req_log
from codecov_cli.helpers.request import (
    patch,
    request_result,
    send_post_request,
    send_put_request,
)
from codecov_cli.types import RequestError, RequestResult


@pytest.fixture
def valid_response():
    valid_response = Response()
    valid_response.status_code = 200
    valid_response._content = b"response text"
    return valid_response


def test_log_error_no_raise(mocker):
    mock_log_error = mocker.patch.object(req_log, "error")
    error = RequestError(
        code=401, params={"some": "params"}, description="Unauthorized"
    )
    result = RequestResult(
        error=error, warnings=[], status_code=401, text="Unauthorized"
    )
    log_warnings_and_errors_if_any(result, "Process", fail_on_error=False)
    mock_log_error.assert_called_with("Process failed: Unauthorized")


def test_log_error_raise(mocker):
    mock_log_error = mocker.patch.object(req_log, "error")
    error = RequestError(
        code=401, params={"some": "params"}, description="Unauthorized"
    )
    result = RequestResult(
        error=error, warnings=[], status_code=401, text="Unauthorized"
    )
    with pytest.raises(SystemExit):
        log_warnings_and_errors_if_any(result, "Process", fail_on_error=True)
    mock_log_error.assert_called_with("Process failed: Unauthorized")


def test_log_result_without_token(mocker):
    mock_log_debug = mocker.patch.object(req_log, "debug")
    result = RequestResult(
        error=None,
        warnings=[],
        status_code=201,
        text='{"message":"commit","timestamp":"2024-03-25T15:41:07Z","ci_passed":true,"state":"complete","repository":{"name":"repo","is_private":false,"active":true,"language":"python","yaml":null},"author":{"avatar_url":"https://example.com","service":"github","username":null,"name":"dependabot[bot]","ownerid":2780265},"commitid":"commit","parent_commit_id":"parent","pullid":1,"branch":"main"}',
    )
    log_warnings_and_errors_if_any(result, "Commit creating", False)
    mock_log_debug.assert_called_with(
        "Commit creating result", extra={"extra_log_attributes": {"result": result}}
    )


def test_log_result_with_token(mocker):
    mock_log_debug = mocker.patch.object(req_log, "debug")
    result = RequestResult(
        error=None,
        warnings=[],
        status_code=201,
        text='{"message": "commit", "timestamp": "2024-07-16T20:51:07Z", "ci_passed": true, "state": "complete", "repository": {"name": "repo", "is_private": false, "active": true, "language": "python", "yaml": {"codecov": {"token": "faketoken"}}, "author": {"avatar_url": "https://example.com", "service": "github", "username": "author", "name": "author", "ownerid": 3461769}, "commitid": "commit", "parent_commit_id": "parent_commit", "pullid": null, "branch": "main"}}',
    )

    expected_text = '{"message": "commit", "timestamp": "2024-07-16T20:51:07Z", "ci_passed": true, "state": "complete", "repository": {"name": "repo", "is_private": false, "active": true, "language": "python", "yaml": {"codecov": {"token": "f******************"}}, "author": {"avatar_url": "https://example.com", "service": "github", "username": "author", "name": "author", "ownerid": 3461769}, "commitid": "commit", "parent_commit_id": "parent_commit", "pullid": null, "branch": "main"}}'
    expected = RequestResult(
        error=None,
        warnings=[],
        status_code=201,
        text=expected_text,
    )
    log_warnings_and_errors_if_any(result, "Commit creating", False)
    mock_log_debug.assert_called_with(
        "Commit creating result", extra={"extra_log_attributes": {"result": expected}}
    )


def test_get_token_header_or_fail():
    # Test with a valid UUID token
    token = uuid.uuid4()
    result = get_token_header_or_fail(token)
    assert result == {"Authorization": f"token {str(token)}"}

    # Test with a None token
    token = None
    with pytest.raises(Exception) as e:
        get_token_header_or_fail(token)

    assert (
        str(e.value)
        == "Codecov token not found. Please provide Codecov token with -t flag."
    )


def test_get_token_header():
    # Test with a valid UUID token
    token = uuid.uuid4()
    result = get_token_header(token)
    assert result == {"Authorization": f"token {str(token)}"}

    # Test with a None token
    token = None
    result = get_token_header(token)
    assert result is None


def test_request_retry(mocker, valid_response):
    expected_response = request_result(valid_response)
    mock_sleep = mocker.patch("codecov_cli.helpers.request.sleep")
    mocker.patch.object(
        requests,
        "post",
        side_effect=[
            requests.exceptions.ConnectionError(),
            requests.exceptions.Timeout(),
            valid_response,
        ],
    )
    resp = send_post_request("my_url")
    assert resp == expected_response
    mock_sleep.assert_called()


def test_request_retry_too_many_errors(mocker):
    _ = mocker.patch("codecov_cli.helpers.request.sleep")
    mocker.patch.object(
        requests,
        "post",
        side_effect=[
            requests.exceptions.ConnectionError(),
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
        ],
    )
    with pytest.raises(Exception) as exp:
        _ = send_post_request("my_url")
    assert str(exp.value) == "Request failed after too many retries. URL: my_url"


def test_user_agent(mocker):
    def mock_request(*args, headers={}, **kwargs):
        assert headers["User-Agent"] == f"codecov-cli/{__version__}"
        return RequestResult(status_code=200, error=None, warnings=[], text="")

    mocker.patch.object(
        requests,
        "post",
        side_effect=mock_request,
    )
    send_post_request("my_url")

    mocker.patch.object(
        requests,
        "get",
        side_effect=mock_request,
    )
    get("my_url")

    mocker.patch.object(
        requests,
        "put",
        side_effect=mock_request,
    )
    send_put_request("my_url")

    mocker.patch.object(
        requests,
        "patch",
        side_effect=mock_request,
    )
    patch("my_url")
