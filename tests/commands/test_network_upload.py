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
    runner = CliRunner()
    mock_network_finder.return_value.find_files.return_value = ["file1.py", "file2.py"]

    result = runner.invoke(
        network_upload,
        [
            "--root-dir",
            ".",
            "--dry-run",
            "--commit-sha",
            "abc123",
            "--token",
            "secret_token",
        ],
    )

    assert result.exit_code == 0
    assert "Found 2 files in the network:" in result.output
    assert "Dry run: No files will be uploaded." in result.output
    assert "file1.py" in result.output
    assert "file2.py" in result.output


def test_network_upload_success(mock_network_finder, mock_upload_sender):
    runner = CliRunner()
    mock_network_finder.return_value.find_files.return_value = ["file1.py", "file2.py"]
    mock_sender = MagicMock()
    mock_sender.send_upload_data.return_value.status_code = 200
    mock_upload_sender.return_value = mock_sender

    result = runner.invoke(
        network_upload,
        [
            "--root-dir",
            ".",
            "--commit-sha",
            "abc123",
            "--token",
            "secret_token",
        ],
    )

    assert result.exit_code == 0
    assert "Found 2 files in the network:" in result.output
    assert "Network files successfully uploaded to Codecov." in result.output

    mock_sender.send_upload_data.assert_called_once()
    args, kwargs = mock_sender.send_upload_data.call_args
    assert isinstance(args[0], UploadCollectionResult)
    assert args[0].network == ["file1.py", "file2.py"]
    assert args[1] == "abc123"
    assert args[2] == "secret_token"
    assert kwargs["upload_file_type"] == "network"


def test_network_upload_failure(mock_network_finder, mock_upload_sender):
    runner = CliRunner()
    mock_network_finder.return_value.find_files.return_value = ["file1.py", "file2.py"]
    mock_sender = MagicMock()
    mock_sender.send_upload_data.return_value.status_code = 400
    mock_upload_sender.return_value = mock_sender

    result = runner.invoke(
        network_upload,
        [
            "--root-dir",
            ".",
            "--commit-sha",
            "abc123",
            "--token",
            "secret_token",
        ],
    )

    assert result.exit_code == 0
    assert "Found 2 files in the network:" in result.output
    assert "Failed to upload network files. Status code: 400" in result.output


def test_network_upload_no_files_found(mock_network_finder):
    runner = CliRunner()
    mock_network_finder.return_value.find_files.return_value = []

    result = runner.invoke(
        network_upload,
        [
            "--root-dir",
            ".",
            "--commit-sha",
            "abc123",
            "--token",
            "secret_token",
        ],
    )

    assert result.exit_code == 0
    assert "No files found in the network." in result.output