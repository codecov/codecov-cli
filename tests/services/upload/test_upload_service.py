import click
import pytest
from click.testing import CliRunner

from codecov_cli.services.upload import (
    LegacyUploadSender,
    UploadCollector,
    UploadSender,
    do_upload_logic,
)
from codecov_cli.services.upload.legacy_upload_sender import (
    UploadSendingResult,
    UploadSendingResultWarning,
)
from codecov_cli.types import RequestResult
from tests.test_helpers import parse_outstreams_into_log_lines


def test_do_upload_logic_happy_path_legacy_uploader(mocker):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.upload.select_preparation_plugins"
    )
    mock_select_file_finder = mocker.patch(
        "codecov_cli.services.upload.select_file_finder"
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.upload.select_network_finder"
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
            upload_file_type="coverage",
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_filter=None,
            network_prefix=None,
            network_root_folder=None,
            files_search_root_folder=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            use_legacy_uploader=True,
            slug="slug",
            pull_request_number="pr",
            git_service="git_service",
            enterprise_url=None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Upload complete"),
        ("info", "Upload process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]

    assert res == LegacyUploadSender.send_upload_data.return_value
    mock_select_preparation_plugins.assert_called_with(
        cli_config, ["first_plugin", "another", "forth"]
    )
    mock_select_file_finder.assert_called_with(None, None, None, False, "coverage")
    mock_select_network_finder.assert_called_with(
        versioning_system,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with("coverage")
    mock_send_upload_data.assert_called_with(
        mock_generate_upload_data.return_value,
        "commit_sha",
        "token",
        None,
        "report_code",
        "coverage",
        "name",
        "branch",
        "slug",
        "pr",
        "build_code",
        "build_url",
        "job_code",
        None,
        "service",
        "git_service",
        None,
    )


def test_do_upload_logic_happy_path(mocker):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.upload.select_preparation_plugins"
    )
    mock_select_file_finder = mocker.patch(
        "codecov_cli.services.upload.select_file_finder"
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.upload.select_network_finder"
    )
    mock_generate_upload_data = mocker.patch.object(
        UploadCollector, "generate_upload_data"
    )
    mock_send_upload_data = mocker.patch.object(
        UploadSender,
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
            upload_file_type="coverage",
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_filter=None,
            network_prefix=None,
            network_root_folder=None,
            files_search_root_folder=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            pull_request_number="pr",
            git_service="git_service",
            enterprise_url=None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Upload complete"),
        ("info", "Upload process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]

    assert res == UploadSender.send_upload_data.return_value
    mock_select_preparation_plugins.assert_called_with(
        cli_config, ["first_plugin", "another", "forth"]
    )
    mock_select_file_finder.assert_called_with(None, None, None, False, "coverage")
    mock_select_network_finder.assert_called_with(
        versioning_system,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with("coverage")
    mock_send_upload_data.assert_called_with(
        mock_generate_upload_data.return_value,
        "commit_sha",
        "token",
        None,
        "report_code",
        "coverage",
        "name",
        "branch",
        "slug",
        "pr",
        "build_code",
        "build_url",
        "job_code",
        None,
        "service",
        "git_service",
        None,
    )


def test_do_upload_logic_dry_run(mocker):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.upload.select_preparation_plugins"
    )
    mock_select_file_finder = mocker.patch(
        "codecov_cli.services.upload.select_file_finder"
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.upload.select_network_finder"
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
            upload_file_type="coverage",
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_filter=None,
            network_prefix=None,
            network_root_folder=None,
            files_search_root_folder=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            pull_request_number="pr",
            dry_run=True,
            git_service="git_service",
            enterprise_url=None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    mock_select_file_finder.assert_called_with(None, None, None, False, "coverage")
    mock_select_network_finder.assert_called_with(
        versioning_system,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    assert mock_generate_upload_data.call_count == 1
    assert mock_send_upload_data.call_count == 0
    mock_select_preparation_plugins.assert_called_with(
        cli_config, ["first_plugin", "another", "forth"]
    )
    assert out_bytes == [
        ("info", "dry-run option activated. NOT sending data to Codecov."),
        ("info", "Process Upload complete"),
    ]
    assert res == RequestResult(
        error=None,
        warnings=None,
        status_code=200,
        text="Data NOT sent to Codecov because of dry-run option",
    )


def test_do_upload_logic_verbose(mocker, use_verbose_option):
    mocker.patch("codecov_cli.services.upload.select_preparation_plugins")
    mocker.patch("codecov_cli.services.upload.select_file_finder")
    mocker.patch("codecov_cli.services.upload.select_network_finder")
    mocker.patch.object(UploadCollector, "generate_upload_data")
    mocker.patch.object(
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
            upload_file_type="coverage",
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_filter=None,
            network_prefix=None,
            network_root_folder=None,
            files_search_root_folder=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            use_legacy_uploader=True,
            pull_request_number="pr",
            dry_run=True,
            git_service="git_service",
            enterprise_url=None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        (
            "debug",
            "Selected uploader to use: <class 'codecov_cli.services.upload.legacy_upload_sender.LegacyUploadSender'>",
        ),
        ("info", "dry-run option activated. NOT sending data to Codecov."),
        ("info", "Process Upload complete"),
        (
            "debug",
            'Upload result --- {"result": "RequestResult(error=None, warnings=None, status_code=200, text=\'Data NOT sent to Codecov because of dry-run option\')"}',
        ),
    ]
    assert res == RequestResult(
        error=None,
        warnings=None,
        status_code=200,
        text="Data NOT sent to Codecov because of dry-run option",
    )


def test_do_upload_no_cov_reports_found(mocker):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.upload.select_preparation_plugins"
    )
    mock_select_file_finder = mocker.patch(
        "codecov_cli.services.upload.select_file_finder",
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.upload.select_network_finder"
    )

    def side_effect(*args, **kwargs):
        raise click.ClickException("error")

    mock_generate_upload_data = mocker.patch(
        "codecov_cli.services.upload.UploadCollector.generate_upload_data",
        side_effect=side_effect,
    )
    mock_upload_completion_call = mocker.patch(
        "codecov_cli.services.upload.upload_completion_logic"
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
            upload_file_type="coverage",
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_filter=None,
            network_prefix=None,
            network_root_folder=None,
            files_search_root_folder=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            pull_request_number="pr",
            git_service="git_service",
            enterprise_url=None,
            handle_no_reports_found=True,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        (
            "info",
            "No coverage reports found. Triggering notificaions without uploading.",
        ),
    ]
    assert res == RequestResult(
        error=None,
        warnings=None,
        status_code=200,
        text="No coverage reports found. Triggering notificaions without uploading.",
    )
    mock_select_preparation_plugins.assert_called_with(
        cli_config, ["first_plugin", "another", "forth"]
    )
    mock_select_file_finder.assert_called_with(None, None, None, False, "coverage")
    mock_select_network_finder.assert_called_with(
        versioning_system,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with("coverage")
    mock_upload_completion_call.assert_called_with(
        commit_sha="commit_sha",
        slug="slug",
        token="token",
        git_service="git_service",
        enterprise_url=None,
        fail_on_error=False,
    )


def test_do_upload_rase_no_cov_reports_found_error(mocker):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.upload.select_preparation_plugins"
    )
    mock_select_file_finder = mocker.patch(
        "codecov_cli.services.upload.select_file_finder",
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.upload.select_network_finder"
    )

    def side_effect(*args, **kwargs):
        raise click.ClickException(
            "No coverage reports found. Please make sure you're generating reports successfully."
        )

    mock_generate_upload_data = mocker.patch(
        "codecov_cli.services.upload.UploadCollector.generate_upload_data",
        side_effect=side_effect,
    )
    cli_config = {}
    versioning_system = mocker.MagicMock()
    ci_adapter = mocker.MagicMock()
    ci_adapter.get_fallback_value.return_value = "service"

    with pytest.raises(click.ClickException) as exp:
        res = do_upload_logic(
            cli_config,
            versioning_system,
            ci_adapter,
            upload_file_type="coverage",
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_filter=None,
            network_prefix=None,
            network_root_folder=None,
            files_search_root_folder=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            pull_request_number="pr",
            git_service="git_service",
            enterprise_url=None,
            handle_no_reports_found=False,
        )
    assert (
        str(exp.value)
        == "No coverage reports found. Please make sure you're generating reports successfully."
    )
    mock_select_preparation_plugins.assert_called_with(
        cli_config, ["first_plugin", "another", "forth"]
    )
    mock_select_file_finder.assert_called_with(None, None, None, False, "coverage")
    mock_select_network_finder.assert_called_with(
        versioning_system,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with("coverage")


def test_do_upload_logic_happy_path_test_results(mocker):
    mock_select_preparation_plugins = mocker.patch(
        "codecov_cli.services.upload.select_preparation_plugins"
    )
    mock_select_file_finder = mocker.patch(
        "codecov_cli.services.upload.select_file_finder"
    )
    mock_select_network_finder = mocker.patch(
        "codecov_cli.services.upload.select_network_finder"
    )
    mock_generate_upload_data = mocker.patch.object(
        UploadCollector, "generate_upload_data"
    )
    mock_send_upload_data = mocker.patch.object(
        UploadSender,
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
            upload_file_type="test_results",
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            name="name",
            network_filter="some_dir",
            network_prefix="hello/",
            network_root_folder="root/",
            files_search_root_folder=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            plugin_names=["first_plugin", "another", "forth"],
            token="token",
            branch="branch",
            slug="slug",
            pull_request_number="pr",
            git_service="git_service",
            enterprise_url=None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Upload complete"),
        ("info", "Upload process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]

    assert res == UploadSender.send_upload_data.return_value
    mock_select_preparation_plugins.assert_not_called
    mock_select_file_finder.assert_called_with(None, None, None, False, "test_results")
    mock_select_network_finder.assert_called_with(
        versioning_system,
        network_filter="some_dir",
        network_prefix="hello/",
        network_root_folder="root/",
    )
    mock_generate_upload_data.assert_called_with("test_results")
    mock_send_upload_data.assert_called_with(
        mock_generate_upload_data.return_value,
        "commit_sha",
        "token",
        None,
        "report_code",
        "test_results",
        "name",
        "branch",
        "slug",
        "pr",
        "build_code",
        "build_url",
        "job_code",
        None,
        "service",
        "git_service",
        None,
    )
