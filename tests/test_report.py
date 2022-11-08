from click.testing import CliRunner

from codecov_cli.services.report import ReportSender, create_report_logic
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning


def test_report_sender_200(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.report.report_sender.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    sender = ReportSender()
    res = sender.send_report_data("commit_sha", "code", "slug")
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_report_sender_403(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.report.report_sender.requests.post",
        return_value=mocker.MagicMock(status_code=403, text="Permission denied"),
    )
    sender = ReportSender()
    res = sender.send_report_data("commit_sha", "code", "slug")
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()


def test_report_command_with_warnings(mocker):
    mock_send_report_data = mocker.patch.object(
        ReportSender,
        "send_report_data",
        return_value=RequestResult(
            error=None,
            warnings=[RequestResultWarning(message="somewarningmessage")],
            status_code=200,
            text="",
        ),
    )
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = create_report_logic(
            commit_sha="commit_sha",
            code="code",
            slug="owner/repo",
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == [
        "info: Report creating process had 1 warning",
        "warning: Warning 1: somewarningmessage",
    ]
    assert res == ReportSender.send_report_data.return_value
    mock_send_report_data.assert_called_with(
        commit_sha="commit_sha",
        code="code",
        slug="owner::::repo",
    )


def test_report_command_with_error(mocker):
    mock_send_report_data = mocker.patch.object(
        ReportSender,
        "send_report_data",
        return_value=RequestResult(
            error=RequestError(
                code="HTTP Error 403",
                description="Permission denied",
                params={},
            ),
            status_code=403,
            text="",
            warnings=[],
        ),
    )
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = create_report_logic(
            commit_sha="commit_sha",
            code="code",
            slug="owner/repo",
        )

    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == ["error: Report creating failed: Permission denied"]
    assert res == ReportSender.send_report_data.return_value
    mock_send_report_data.assert_called_with(
        commit_sha="commit_sha",
        code="code",
        slug="owner::::repo",
    )
