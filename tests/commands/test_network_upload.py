import pathlib
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from codecov_cli.commands.network_upload import network_upload
from codecov_cli.types import UploadCollectionResult


@pytest.fixture
def mock_network_finder():
    with patch("codecov_cli.commands.network_upload.NetworkFinder") as mock:
        yield mock


@pytest.fixture
def mock_upload_sender():
    with patch("codecov_cli.commands.network_upload.UploadSender") as mock:
        yield mock


def test_network_upload_dry_run(mock_network_finder):
    mock_network_finder.return_value.find_files.return_value = ["file1.py", "file2.py"]
    runner = CliRunner()
    result = runner.invoke(
        network_upload,
        [
            "--root-dir",
            "/test/path",
            "--network-filter",
            ".*\\.py",
            "--dry-run",
            "--commit-sha",
            "abcdef123456",
            "--token",
            "test-token",
        ],
    )
    assert result.exit_code == 0
    assert "Dry run: No files will be uploaded." in result.output
    assert "file1.py" in result.output
    assert "file2.py" in result.output


def test_network_upload_no_files_found(mock_network_finder):
    mock_network_finder.return_value.find_files.return_value = []
    runner = CliRunner()
    result = runner.invoke(
        network_upload,
        [
            "--root-dir",
            "/test/path",
            "--commit-sha",
            "abcdef123456",
            "--token",
            "test-token",
        ],
    )
    assert result.exit_code == 0
    assert "No files found in the network." in result.output


def test_network_upload_success(mock_network_finder, mock_upload_sender):
    mock_network_finder.return_value.find_files.return_value = ["file1.py", "file2.py"]
    mock_sender = MagicMock()
    mock_sender.send_upload_data.return_value = MagicMock(status_code=200)
    mock_upload_sender.return_value = mock_sender

    runner = CliRunner()
    result = runner.invoke(
        network_upload,
        [
            "--root-dir",
            "/test/path",
            "--commit-sha",
            "abcdef123456",
            "--token",
            "test-token",
        ],
    )
    assert result.exit_code == 0
    assert "Network files successfully uploaded to Codecov." in result.output

    mock_sender.send_upload_data.assert_called_once()
    call_args = mock_sender.send_upload_data.call_args[0]
    assert isinstance(call_args[0], UploadCollectionResult)
    assert call_args[0].network == ["file1.py", "file2.py"]
    assert call_args[1] == "abcdef123456"  # commit_sha
    assert call_args[2] == "test-token"  # token


def test_network_upload_failure(mock_network_finder, mock_upload_sender):
    mock_network_finder.return_value.find_files.return_value = ["file1.py", "file2.py"]
    mock_sender = MagicMock()
    mock_sender.send_upload_data.return_value = MagicMock(status_code=400)
    mock_upload_sender.return_value = mock_sender

    runner = CliRunner()
    result = runner.invoke(
        network_upload,
        [
            "--root-dir", "/test/path",
            "--commit-sha", "abcdef123456",
            "--token", "test-token",
            "--fail-on-error",
        ],
    )
    assert result.exit_code == 1
    assert "Failed to upload network files. Status code: 400" in result.output