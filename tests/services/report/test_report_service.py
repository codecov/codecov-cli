import os
import uuid

from click.testing import CliRunner

from codecov_cli.services.report import create_report_logic, send_create_report_request
from codecov_cli.types import RequestError, RequestResult, RequestResultWarning
from tests.test_helpers import parse_outstreams_into_log_lines


def test_send_create_report_request_200(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.report.requests.post",
        return_value=mocker.MagicMock(status_code=200),
    )
    res = send_create_report_request(
        "commit_sha",
        "code",
        "github",
        uuid.uuid4(),
        "owner::::repo",
        "enterprise_url",
    )
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_once()


def test_send_create_report_request_200_tokenless(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.report.send_post_request",
        return_value=RequestResult(
            status_code=200,
            error=None,
            warnings=[],
            text="mocked response",
        ),
    )

    os.environ["TOKENLESS"] = "user:branch"
    res = send_create_report_request(
        "commit_sha",
        "code",
        "github",
        None,
        "owner::::repo",
        "enterprise_url",
    )
    assert res.error is None
    assert res.warnings == []
    mocked_response.assert_called_with(
        url=f"enterprise_url/upload/github/owner::::repo/commits/commit_sha/reports",
        headers={
            "X-Tokenless": "user:branch",
        },
        data={"code": "code"},
    )


def test_send_create_report_request_403(mocker):
    mocked_response = mocker.patch(
        "codecov_cli.services.report.requests.post",
        return_value=mocker.MagicMock(status_code=403, text="Permission denied"),
    )
    res = send_create_report_request(
        "commit_sha", "code", "github", uuid.uuid4(), "owner::::repo", None
    )
    assert res.error == RequestError(
        code="HTTP Error 403",
        description="Permission denied",
        params={},
    )
    mocked_response.assert_called_once()


def test_create_report_command_with_warnings(mocker):
    mocked_send_request = mocker.patch(
        "codecov_cli.services.report.send_create_report_request",
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
            service="github",
            token="token",
            enterprise_url=None,
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Report creating complete"),
        ("info", "Report creating process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]
    assert res == RequestResult(
        error=None,
        warnings=[RequestResultWarning(message="somewarningmessage")],
        status_code=200,
        text="",
    )
    mocked_send_request.assert_called_with(
        "commit_sha", "code", "github", "token", "owner::::repo", None
    )


def test_create_report_command_with_error(mocker):
    mock_send_report_data = mocker.patch(
        "codecov_cli.services.report.send_create_report_request",
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
            service="github",
            token="token",
            enterprise_url="enterprise_url",
        )

    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Report creating complete"),
        ("error", "Report creating failed: Permission denied"),
    ]
    assert res == RequestResult(
        error=RequestError(
            code="HTTP Error 403",
            description="Permission denied",
            params={},
        ),
        status_code=403,
        text="",
        warnings=[],
    )
    mock_send_report_data.assert_called_with(
        "commit_sha", "code", "github", "token", "owner::::repo", "enterprise_url"
    )
