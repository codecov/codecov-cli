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


def test_no_token_anywhere(
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that a missing token produces `NOTOKEN` in logs."""
    # NOTE: The pytest's `caplog` fixture is not used in this test as it
    # NOTE: doesn't play well with Click's testing CLI runner, and does
    # NOTE: not capture any log entries for mysterious reasons.
    #
    # Refs:
    # * https://github.com/pallets/click/issues/2573#issuecomment-1649773563
    # * https://github.com/pallets/click/issues/1763#issuecomment-767687608
    monkeypatch.chdir(tmp_path)

    mocker.patch.object(upload, "do_upload_logic")
    do_upload_cmd_spy = mocker.spy(upload, "do_upload_logic")
    debug_log_spy = mocker.spy(upload.logger, "debug")

    cov_upload_cmd_output = (
        CliRunner()
        .invoke(
            cli,
            [
                "-v",  # <- NOTE: this is the only way to turn on debug logger
                "do-upload",
                "--commit-sha=deadbeef",
            ],
            obj={},
        )
        .output
    )

    assert (
        debug_log_spy.call_args[1]["extra"]["extra_log_attributes"]["token"]
        == "NOTOKEN"
    )
    assert '"token": "NOTOKEN"' in cov_upload_cmd_output
    assert do_upload_cmd_spy.call_args[-1]["token"] is None


def test_cli_token_masked_in_logs(
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Test that a present token is masked in logs."""
    # NOTE: The pytest's `caplog` fixture is not used in this test as it
    # NOTE: doesn't play well with Click's testing CLI runner, and does
    # NOTE: not capture any log entries for mysterious reasons.
    #
    # Refs:
    # * https://github.com/pallets/click/issues/2573#issuecomment-1649773563
    # * https://github.com/pallets/click/issues/1763#issuecomment-767687608
    monkeypatch.chdir(tmp_path)

    mocker.patch.object(upload, "do_upload_logic")
    do_upload_cmd_spy = mocker.spy(upload, "do_upload_logic")
    debug_log_spy = mocker.spy(upload.logger, "debug")

    cov_upload_cmd_output = (
        CliRunner()
        .invoke(
            cli,
            [
                "-v",  # <- NOTE: this is the only way to turn on debug logger
                "do-upload",
                "--commit-sha=deadbeef",
                "--token=sentinel-value",
            ],
            obj={},
        )
        .output
    )

    assert (
        debug_log_spy.call_args[1]["extra"]["extra_log_attributes"]["token"]
        == "s" + "*" * 18
    )
    assert f'"token": "s{"*" * 18}"' in cov_upload_cmd_output
    assert do_upload_cmd_spy.call_args[-1]["token"] == "sentinel-value"
