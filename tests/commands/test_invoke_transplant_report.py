from click.testing import CliRunner

from unittest import mock
from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.main import cli
from tests.factory import FakeProvider


def test_invoke_transplant_report(mocker):
    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: "sha to copy to"})
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)

    mocked_response = mocker.patch(
        "codecov_cli.helpers.request.requests.post",
        return_value=mocker.MagicMock(status_code=200, text="all good"),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["transplant-report", "--slug", "foo/bar", "--from-sha", "sha to copy from"],
        obj={},
    )
    assert result.exit_code == 0

    mocked_response.assert_called_with(
        "https://ingest.codecov.io/upload/github/foo::::bar/commits/transplant",
        headers=mock.ANY,
        params=mock.ANY,
        json={
            "cli_args": mock.ANY,
            "from_sha": "sha to copy from",
            "to_sha": "sha to copy to",
        },
    )
