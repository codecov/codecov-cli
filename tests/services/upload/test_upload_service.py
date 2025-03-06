import click
import pytest
from click.testing import CliRunner

from codecov_cli.helpers.upload_type import ReportType
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
            report_type=ReportType.COVERAGE,
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            gcov_args=None,
            gcov_executable=None,
            gcov_ignore=None,
            gcov_include=None,
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
            swift_project="App",
            pull_request_number="pr",
            git_service="git_service",
            enterprise_url=None,
            args=None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Upload complete"),
        ("info", "Upload process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]

    assert res == LegacyUploadSender.send_upload_data.return_value
    mock_select_preparation_plugins.assert_called_with(
        cli_config,
        ["first_plugin", "another", "forth"],
        {
            "folders_to_ignore": None,
            "gcov_args": None,
            "gcov_executable": None,
            "gcov_ignore": None,
            "gcov_include": None,
            "project_root": None,
            "swift_project": "App",
        },
    )
    mock_select_file_finder.assert_called_with(
        None, None, None, False, ReportType.COVERAGE
    )
    mock_select_network_finder.assert_called_with(
        versioning_system,
        recurse_submodules=False,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with(ReportType.COVERAGE)
    mock_send_upload_data.assert_called_with(
        upload_data=mock_generate_upload_data.return_value,
        commit_sha="commit_sha",
        token="token",
        env_vars=None,
        report_code="report_code",
        report_type=ReportType.COVERAGE,
        name="name",
        branch="branch",
        slug="slug",
        pull_request_number="pr",
        build_code="build_code",
        build_url="build_url",
        job_code="job_code",
        flags=None,
        ci_service="service",
        git_service="git_service",
        enterprise_url=None,
        parent_sha=None,
        upload_coverage=False,
        args=None,
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
            report_type=ReportType.COVERAGE,
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            gcov_args=None,
            gcov_executable=None,
            gcov_ignore=None,
            gcov_include=None,
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
            swift_project="App",
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
        cli_config,
        ["first_plugin", "another", "forth"],
        {
            "folders_to_ignore": None,
            "gcov_args": None,
            "gcov_executable": None,
            "gcov_ignore": None,
            "gcov_include": None,
            "project_root": None,
            "swift_project": "App",
        },
    )
    mock_select_file_finder.assert_called_with(
        None, None, None, False, ReportType.COVERAGE
    )
    mock_select_network_finder.assert_called_with(
        versioning_system,
        recurse_submodules=False,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with(ReportType.COVERAGE)
    mock_send_upload_data.assert_called_with(
        upload_data=mock_generate_upload_data.return_value,
        commit_sha="commit_sha",
        token="token",
        env_vars=None,
        report_code="report_code",
        report_type=ReportType.COVERAGE,
        name="name",
        branch="branch",
        slug="slug",
        pull_request_number="pr",
        build_code="build_code",
        build_url="build_url",
        job_code="job_code",
        flags=None,
        ci_service="service",
        git_service="git_service",
        enterprise_url=None,
        parent_sha=None,
        upload_coverage=False,
        args=None,
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
            report_type=ReportType.COVERAGE,
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            gcov_args=None,
            gcov_executable=None,
            gcov_ignore=None,
            gcov_include=None,
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
            swift_project="App",
            pull_request_number="pr",
            dry_run=True,
            git_service="git_service",
            enterprise_url=None,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    mock_select_file_finder.assert_called_with(
        None, None, None, False, ReportType.COVERAGE
    )
    mock_select_network_finder.assert_called_with(
        versioning_system,
        recurse_submodules=False,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    assert mock_generate_upload_data.call_count == 1
    assert mock_send_upload_data.call_count == 0
    mock_select_preparation_plugins.assert_called_with(
        cli_config,
        ["first_plugin", "another", "forth"],
        {
            "folders_to_ignore": None,
            "gcov_args": None,
            "gcov_executable": None,
            "gcov_ignore": None,
            "gcov_include": None,
            "project_root": None,
            "swift_project": "App",
        },
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
            branch="branch",
            build_code="build_code",
            build_url="build_url",
            commit_sha="commit_sha",
            dry_run=True,
            enterprise_url=None,
            env_vars=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            files_search_root_folder=None,
            flags=None,
            gcov_args=None,
            gcov_executable=None,
            gcov_ignore=None,
            gcov_include=None,
            git_service="git_service",
            job_code="job_code",
            name="name",
            network_filter=None,
            network_prefix=None,
            network_root_folder=None,
            plugin_names=["first_plugin", "another", "forth"],
            pull_request_number="pr",
            report_code="report_code",
            slug="slug",
            swift_project="App",
            token="token",
            report_type=ReportType.COVERAGE,
            use_legacy_uploader=True,
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
            report_type=ReportType.COVERAGE,
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            gcov_args=None,
            gcov_executable=None,
            gcov_ignore=None,
            gcov_include=None,
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
            swift_project="App",
            pull_request_number="pr",
            git_service="git_service",
            enterprise_url=None,
            handle_no_reports_found=True,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        (
            "info",
            "No coverage reports found. Triggering notifications without uploading.",
        ),
    ]
    assert res == RequestResult(
        error=None,
        warnings=None,
        status_code=200,
        text="No coverage reports found. Triggering notifications without uploading.",
    )
    mock_select_preparation_plugins.assert_called_with(
        cli_config,
        ["first_plugin", "another", "forth"],
        {
            "folders_to_ignore": None,
            "gcov_args": None,
            "gcov_executable": None,
            "gcov_ignore": None,
            "gcov_include": None,
            "project_root": None,
            "swift_project": "App",
        },
    )
    mock_select_file_finder.assert_called_with(
        None, None, None, False, ReportType.COVERAGE
    )
    mock_select_network_finder.assert_called_with(
        versioning_system,
        recurse_submodules=False,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with(ReportType.COVERAGE)
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
        _ = do_upload_logic(
            cli_config,
            versioning_system,
            ci_adapter,
            report_type=ReportType.COVERAGE,
            commit_sha="commit_sha",
            report_code="report_code",
            build_code="build_code",
            build_url="build_url",
            job_code="job_code",
            env_vars=None,
            flags=None,
            gcov_args=None,
            gcov_executable=None,
            gcov_ignore=None,
            gcov_include=None,
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
            swift_project="App",
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
        cli_config,
        ["first_plugin", "another", "forth"],
        {
            "folders_to_ignore": None,
            "gcov_args": None,
            "gcov_executable": None,
            "gcov_ignore": None,
            "gcov_include": None,
            "project_root": None,
            "swift_project": "App",
        },
    )
    mock_select_file_finder.assert_called_with(
        None, None, None, False, ReportType.COVERAGE
    )
    mock_select_network_finder.assert_called_with(
        versioning_system,
        recurse_submodules=False,
        network_filter=None,
        network_prefix=None,
        network_root_folder=None,
    )
    mock_generate_upload_data.assert_called_with(ReportType.COVERAGE)


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
            args={"args": "fake_args"},
            branch="branch",
            build_code="build_code",
            build_url="build_url",
            commit_sha="commit_sha",
            enterprise_url=None,
            env_vars=None,
            files_search_exclude_folders=None,
            files_search_explicitly_listed_files=None,
            files_search_root_folder=None,
            flags=None,
            gcov_args=None,
            gcov_executable=None,
            gcov_ignore=None,
            gcov_include=None,
            git_service="git_service",
            job_code="job_code",
            name="name",
            network_filter="some_dir",
            network_prefix="hello/",
            network_root_folder="root/",
            plugin_names=["first_plugin", "another", "forth"],
            pull_request_number="pr",
            report_code="report_code",
            slug="slug",
            swift_project="App",
            token="token",
            report_type=ReportType.TEST_RESULTS,
        )
    out_bytes = parse_outstreams_into_log_lines(outstreams[0].getvalue())
    assert out_bytes == [
        ("info", "Process Upload complete"),
        ("info", "Upload process had 1 warning"),
        ("warning", "Warning 1: somewarningmessage"),
    ]

    assert res == UploadSender.send_upload_data.return_value
    mock_select_preparation_plugins.assert_not_called
    mock_select_file_finder.assert_called_with(
        None, None, None, False, ReportType.TEST_RESULTS
    )
    mock_select_network_finder.assert_called_with(
        versioning_system,
        recurse_submodules=False,
        network_filter="some_dir",
        network_prefix="hello/",
        network_root_folder="root/",
    )
    mock_generate_upload_data.assert_called_with(ReportType.TEST_RESULTS)
    mock_send_upload_data.assert_called_with(
        upload_data=mock_generate_upload_data.return_value,
        commit_sha="commit_sha",
        token="token",
        env_vars=None,
        report_code="report_code",
        report_type=ReportType.TEST_RESULTS,
        name="name",
        branch="branch",
        slug="slug",
        pull_request_number="pr",
        build_code="build_code",
        build_url="build_url",
        job_code="job_code",
        flags=None,
        ci_service="service",
        git_service="git_service",
        enterprise_url=None,
        parent_sha=None,
        upload_coverage=False,
        args={"args": "fake_args"},
    )
