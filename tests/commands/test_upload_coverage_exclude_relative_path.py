"""Make sure upload-coverage passes relative --exclude folders through to the upload logic.

The ``upload-coverage`` command goes through
``codecov_cli.services.upload_coverage.upload_coverage_logic``. That module
imports its own copy of ``do_upload_logic`` with
``from codecov_cli.services.upload import do_upload_logic``, so a test has to
patch it *there*. Patching ``codecov_cli.services.upload.do_upload_logic`` or
``codecov_cli.commands.upload.do_upload_logic`` does nothing for this command:
the real upload runs and ``mock.call_args`` stays ``None`` (Sentry issue CLI-J4).
"""

import pathlib
import traceback

from click.testing import CliRunner
from pytest import MonkeyPatch
from pytest_mock import MockerFixture

from codecov_cli.main import cli
from codecov_cli.services import upload_coverage


def test_upload_coverage_exclude_relative_path(
    mocker: MockerFixture,
    monkeypatch: MonkeyPatch,
    tmp_path: pathlib.Path,
) -> None:
    for f in (
        "js/generated/coverage.xml",
        "other/dist/build/coverage.xml",
        "coverage.xml",
    ):
        p = tmp_path / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("<coverage></coverage>")
    monkeypatch.chdir(tmp_path)

    # Patch the name that upload_coverage_logic actually calls.
    mocked_logic = mocker.patch.object(upload_coverage, "do_upload_logic")

    result = CliRunner().invoke(
        cli,
        [
            "upload-coverage",
            "--commit-sha=deadbeef",
            "--slug=owner/repo",
            "--git-service=github",
            "--token=sentinel-token",
            "--exclude",
            "js/generated",
            "--dry-run",
        ],
        obj={},
    )
    if result.exception is not None:
        traceback.print_exception(
            type(result.exception),
            result.exception,
            result.exception.__traceback__,
        )

    assert mocked_logic.called, (
        "do_upload_logic was not called; the patch target probably does not match "
        f"the import upload-coverage uses. CLI output:\n{result.output}"
    )
    kwargs = mocked_logic.call_args.kwargs
    assert kwargs["upload_coverage"] is True
    assert pathlib.Path("js/generated") in [
        pathlib.Path(e) for e in kwargs["files_search_exclude_folders"]
    ]
    assert kwargs["files_search_root_folder"] is not None
