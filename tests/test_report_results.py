import uuid

from click.testing import CliRunner

from codecov_cli.services.report import (
    get_report_results_logic,
    send_reports_result_request,
)
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning


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
        res = get_report_results_logic(
            commit_sha="commit_sha",
            code="code",
            service="service",
            slug="owner/repo",
            token="token",
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == [
        "info: Report results creating process had 1 warning",
        "warning: Warning 1: somewarningmessage",
    ]
    assert res == mock_send_reports_result_request.return_value
    mock_send_reports_result_request.assert_called_with(
        commit_sha="commit_sha",
        report_code="code",
        service="service",
        encoded_slug="owner::::repo",
        token="token",
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
        res = get_report_results_logic(
            commit_sha="commit_sha",
            code="code",
            service="service",
            slug="owner/repo",
            token="token",
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == ["error: Report results creating failed: Permission denied"]
    assert res == mock_send_reports_result_request.return_value
    mock_send_reports_result_request.assert_called_with(
        commit_sha="commit_sha",
        report_code="code",
        service="service",
        encoded_slug="owner::::repo",
        token="token",
    )


def test_report_results_request_200(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    token = uuid.uuid4()
    res = send_reports_result_request(
        "commit_sha", "report_code", "encoded_slug", "service", token
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
        "commit_sha", "report_code", "encoded_slug", "service", token
    )
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()
