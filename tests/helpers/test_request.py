import uuid

import pytest

from codecov_cli.helpers.request import (
    get_token_header_or_fail,
    log_warnings_and_errors_if_any,
)
from codecov_cli.helpers.request import logger as req_log
from codecov_cli.types import RequestError, RequestResult


def test_log_error_no_raise(mocker):
    mock_log_error = mocker.patch.object(req_log, "error")
    error = RequestError(
        code=401, params={"some": "params"}, description="Unauthorized"
    )
    result = RequestResult(
        error=error, warnings=[], status_code=401, text="Unauthorized"
    )
    log_warnings_and_errors_if_any(result, "Process", fail_on_error=False)
    mock_log_error.assert_called_with(f"Process failed: Unauthorized")


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
    mock_log_error.assert_called_with(f"Process failed: Unauthorized")


def test_get_token_header_or_fail():
    # Test with a valid UUID token
    token = uuid.uuid4()
    result = get_token_header_or_fail(token)
    assert result == {"Authorization": f"token {token.hex}"}

    # Test with a None token
    token = None
    with pytest.raises(Exception) as e:
        get_token_header_or_fail(token)

    assert str(e.value) == "Codecov token not found."

    # Test with an invalid token type
    token = "invalid_token"
    with pytest.raises(Exception) as e:
        get_token_header_or_fail(token)

    assert str(e.value) == f"Token must be UUID. Received {type(token)}"
