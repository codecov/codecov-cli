import pytest

from codecov_cli.helpers.request import log_warnings_and_errors_if_any
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
