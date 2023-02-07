import logging

from click.testing import CliRunner

from codecov_cli.services.legacy_upload import (
    LegacyUploadSender,
    UploadCollector,
    do_upload_logic,
)
from codecov_cli.services.legacy_upload.upload_sender import (
    UploadSendingResult,
    UploadSendingResultWarning,
)
from codecov_cli.types import RequestResult


def test_do_upload_logic_happy_path(mocker, make_sure_logger_has_only_1_handler):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.legacy_upload.select_preparation_plugins"
    )
    mock_select_coverage_file_finder = mocker.patch(
        "codecov_cli.services.legacy_upload.select_coverage_file_finder"
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.legacy_upload.select_network_finder"
    )
    mock_generate_upload_data = mocker.patch.object(
        UploadCollector, "generate_upload_data"
    )
    mock_send_upload_data = mocker.patch.object(
        LegacyUploadSender,
        "send_upload_data",
        return_value=UploadSendingResult(
            error=None,
            warnings=[UploadSendingResultWarning(message="somewarningmessage")],
        ),
    )
    cli_config = {}
    versioning_system = mocker.MagicMock()
    ci_adapter = mocker.MagicMock()
    ci_adapter.get_fallback_value.return_value = "service"
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = do_upload_logic(
            cli_config,
            versioning_system,
            ci_adapter,
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_root_folder=None,
            coverage_files_search_root_folder=None,
            coverage_files_search_exclude_folders=None,
            coverage_files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            pull_request_number="pr",
        )
    out_bytes = outstreams[0].getvalue().decode().splitlines()
    assert out_bytes == [
        "info: Upload process had 1 warning",
        "warning: Warning 1: somewarningmessage",
    ]
    assert res == LegacyUploadSender.send_upload_data.return_value
    mock_select_preparation_plugins.assert_called_with(
        cli_config, ["first_plugin", "another", "forth"]
    )
    mock_select_coverage_file_finder.assert_called_with(None, None, None)
    mock_select_network_finder.assert_called_with(versioning_system)
    mock_generate_upload_data.assert_called_with()
    mock_send_upload_data.assert_called_with(
        mock_generate_upload_data.return_value,
        "commit_sha",
        "token",
        None,
        "report_code",
        "name",
        "branch",
        "slug",
        "pr",
        "build_code",
        "build_url",
        "job_code",
        None,
        "service",
    )


def test_do_upload_logic_dry_run(mocker, make_sure_logger_has_only_1_handler):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.legacy_upload.select_preparation_plugins"
    )
    mock_select_coverage_file_finder = mocker.patch(
        "codecov_cli.services.legacy_upload.select_coverage_file_finder"
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.legacy_upload.select_network_finder"
    )
    mock_generate_upload_data = mocker.patch.object(
        UploadCollector, "generate_upload_data"
    )
    mock_send_upload_data = mocker.patch.object(
        LegacyUploadSender,
        "send_upload_data",
    )
    cli_config = {}
    versioning_system = mocker.MagicMock()
    ci_adapter = mocker.MagicMock()
    ci_adapter.get_fallback_value.return_value = "service"
    runner = CliRunner()
    with runner.isolation() as outstreams:
        res = do_upload_logic(
            cli_config,
            versioning_system,
            ci_adapter,
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_root_folder=None,
            coverage_files_search_root_folder=None,
            coverage_files_search_exclude_folders=None,
            coverage_files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            pull_request_number="pr",
            dry_run=True,
        )
    out_bytes = outstreams[0].getvalue().decode().splitlines()
    mock_select_coverage_file_finder.assert_called_with(None, None, None)
    mock_select_network_finder.assert_called_with(versioning_system)
    assert mock_generate_upload_data.call_count == 1
    assert mock_send_upload_data.call_count == 0
    mock_select_preparation_plugins.assert_called_with(
        cli_config, ["first_plugin", "another", "forth"]
    )
    assert out_bytes == [
        "info: dry-run option activated. NOT sending data to Codecov.",
    ]
    assert res == RequestResult(
        error=None,
        warnings=None,
        status_code=200,
        text="Data NOT sent to Codecov because of dry-run option",
    )
