"""Tests ensuring that an env-provided token can be found."""

from pathlib import Path
from textwrap import dedent as _dedent_text_block

from click.testing import CliRunner
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from codecov_cli.commands import upload
from codecov_cli.main import cli


def test_no_cli_token_config_fallback(
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that a config-stored token is used with no CLI argument."""
    # NOTE: The pytest's `caplog` fixture is not used in this test as it
    # NOTE: doesn't play well with Click's testing CLI runner, and does
    # NOTE: not capture any log entries for mysterious reasons.
    #
    # Refs:
    # * https://github.com/pallets/click/issues/2573#issuecomment-1649773563
    # * https://github.com/pallets/click/issues/1763#issuecomment-767687608
    (tmp_path / ".codecov.yml").write_text(
        _dedent_text_block(
            """
            ---

            codecov:
              token: sentinel-value

            ...
            """
        )
    )
    monkeypatch.chdir(tmp_path)

    mocker.patch.object(upload, "do_upload_logic")
    do_upload_cmd_spy = mocker.spy(upload, "do_upload_logic")

    CliRunner().invoke(cli, ["do-upload", "--commit-sha=deadbeef"], obj={})

    assert do_upload_cmd_spy.call_args[-1]["token"] == "sentinel-value"
