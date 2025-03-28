import uuid
from unittest.mock import patch

from click.testing import CliRunner

from codecov_cli.services.report import (
    create_report_results_logic,
    send_reports_result_get_request,
    send_reports_result_request,
)
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning
from tests.test_helpers import parse_outstreams_into_log_lines


def test_report_results_command_with_warnings(mocker):
    mock_send_reports_result_request = mocker.patch(
        "codecov_cli.services.report.send_reports_result_request",
        return_value=RequestResult(
            error=None,
            warnings=[RequestResultWarning(message="somewarningmessage")],
            status_code=201,
            text="",
        ),
    )
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = create_report_results_logic(
            commit_sha="commit_sha",
            code="code",
            service="service",
            slug="owner/repo",
            token="token",
            enterprise_url=None,
            args=None,
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Report results creating complete"),
        ("info", "Report results creating process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]

    assert res == mock_send_reports_result_request.return_value
    mock_send_reports_result_request.assert_called_with(
        args=None,
        commit_sha="commit_sha",
        report_code="code",
        service="service",
        encoded_slug="owner::::repo",
        token="token",
        enterprise_url=None,
    )


def test_report_results_command_with_error(mocker):
    mock_send_reports_result_request = mocker.patch(
        "codecov_cli.services.report.send_reports_result_request",
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
        res = create_report_results_logic(
            commit_sha="commit_sha",
            code="code",
            service="service",
            slug="owner/repo",
            token="token",
            enterprise_url=None,
            args=None,
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Report results creating complete"),
        ("error", "Report results creating failed: Permission denied"),
    ]
    assert res == mock_send_reports_result_request.return_value
    mock_send_reports_result_request.assert_called_with(
        args=None,
        commit_sha="commit_sha",
        report_code="code",
        service="service",
        encoded_slug="owner::::repo",
        token="token",
        enterprise_url=None,
    )


def test_report_results_request_200(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    token = uuid.uuid4()
    res = send_reports_result_request(
        "commit_sha", "report_code", "encoded_slug", "service", token, None, None
    )
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_report_results_request_no_token(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    res = send_reports_result_request(
        "commit_sha", "report_code", "encoded_slug", "service", None, None, None
    )
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_report_results_403(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=403, text="Permission denied"),
    )
    token = uuid.uuid4()
    res = send_reports_result_request(
        "commit_sha", "report_code", "encoded_slug", "service", token, None, None
    )
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()


def test_get_report_results_200_completed(mocker, capsys):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.get",
        return_value=mocker.MagicMock(
            status_code=200,
            text='{"state": "completed", "result": {"state": "failure","message": "33.33% of diff hit (target 77.77%)"}}',
        ),
    )
    token = uuid.uuid4()
    res = send_reports_result_get_request(
        "commit_sha", "report_code", "encoded_slug", "service", token, None
    )
    output = parse_outstreams_into_log_lines(capsys.readouterr().err)
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()
    assert (
        "info",
        'Finished processing report results --- {"state": "failure", "message": "33.33% of diff hit (target 77.77%)"}',
    ) in output


def test_get_report_results_no_token(mocker, capsys):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.get",
        return_value=mocker.MagicMock(
            status_code=200,
            text='{"state": "completed", "result": {"state": "failure","message": "33.33% of diff hit (target 77.77%)"}}',
        ),
    )
    res = send_reports_result_get_request(
        "commit_sha", "report_code", "encoded_slug", "service", None, None
    )
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


@patch("codecov_cli.services.report.MAX_NUMBER_TRIES", 1)
def test_get_report_results_200_pending(mocker, capsys):
    mocker.patch("codecov_cli.services.report.time.sleep")
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.get",
        return_value=mocker.MagicMock(
            status_code=200, text='{"state": "pending", "result": {}}'
        ),
    )
    token = uuid.uuid4()
    res = send_reports_result_get_request(
        "commit_sha", "report_code", "encoded_slug", "service", token, None
    )
    output = parse_outstreams_into_log_lines(capsys.readouterr().err)
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()
    assert ("info", "Report with the given code is still being processed.") in output


def test_get_report_results_200_error(mocker, capsys):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.get",
        return_value=mocker.MagicMock(
            status_code=200, text='{"state": "error", "result": {}}'
        ),
    )
    token = uuid.uuid4()
    res = send_reports_result_get_request(
        "commit_sha", "report_code", "encoded_slug", "service", token, None
    )
    output = parse_outstreams_into_log_lines(capsys.readouterr().err)
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()
    assert (
        "error",
        'An error occurred while processing the report. Please try again later. --- {"response_status_code": 200, "state": "error", "result": {}}',
    ) in output


def test_get_report_results_200_undefined_state(mocker, capsys):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.get",
        return_value=mocker.MagicMock(
            status_code=200, text='{"state": "undefined_state", "result": {}}'
        ),
    )
    token = uuid.uuid4()
    res = send_reports_result_get_request(
        "commit_sha", "report_code", "encoded_slug", "service", token, None
    )
    output = parse_outstreams_into_log_lines(capsys.readouterr().err)
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()
    assert ("error", "Please try again later.") in output


def test_get_report_results_401(mocker, capsys):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.get",
        return_value=mocker.MagicMock(
            status_code=401, text='{"detail": "Invalid token."}'
        ),
    )
    token = uuid.uuid4()
    res = send_reports_result_get_request(
        "commit_sha", "report_code", "encoded_slug", "service", token, None
    )
    output = parse_outstreams_into_log_lines(capsys.readouterr().err)
    assert res.error == RequestError(
        code="HTTP Error 401",
        description='{"detail": "Invalid token."}',
        params={},
    )
    mocked_response.assert_called_once()
    assert (
        "error",
        'Getting report results failed: {"detail": "Invalid token."}',
    ) in output
