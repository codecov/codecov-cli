from unittest.mock import patch

from click.testing import CliRunner

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.main import cli
from codecov_cli.types import RequestError, RequestResult
from tests.factory import FakeProvider, FakeVersioningSystem


def test_upload_coverage_missing_commit_sha(mocker):
    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: None})
    fake_versioning_system = FakeVersioningSystem({FallbackFieldEnum.commit_sha: None})
    mocker.patch(
        "codecov_cli.main.get_versioning_system", return_value=fake_versioning_system
    )
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["upload-coverage"], obj={})
        assert result.exit_code != 0


def test_upload_coverage_raise_Z_option(mocker, use_verbose_option):
    error = RequestError(
        code=401, params={"some": "params"}, description="Unauthorized"
    )
    command_result = RequestResult(
        error=error, warnings=[], status_code=401, text="Unauthorized"
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch(
            "codecov_cli.services.commit.send_commit_data"
        ) as mocked_create_commit:
            mocked_create_commit.return_value = command_result
            result = runner.invoke(
                cli,
                [
                    "upload-coverage",
                    "--fail-on-error",
                    "-C",
                    "command-sha",
                    "--slug",
                    "owner/repo",
                    "--report-type",
                    "test_results",
                ],
                obj={},
            )

    assert result.exit_code != 0
    assert "Commit creating failed: Unauthorized" in result.output
    assert str(result) == "<Result SystemExit(1)>"


def test_upload_coverage_options(mocker):
    runner = CliRunner()
    fake_ci_provider = FakeProvider({FallbackFieldEnum.commit_sha: None})
    mocker.patch("codecov_cli.main.get_ci_adapter", return_value=fake_ci_provider)
    with runner.isolated_filesystem():
        runner = CliRunner()
        result = runner.invoke(cli, ["upload-coverage", "-h"], obj={})
        assert result.exit_code == 0
        print(result.output)

        assert result.output.split("\n")[1:] == [
            "Usage: cli upload-coverage [OPTIONS]",
            "",
            "Options:",
            "  -C, --sha, --commit-sha TEXT    Commit SHA (with 40 chars)  [required]",
            "  -Z, --fail-on-error             Exit with non-zero code in case of error",
            "  --git-service [github|gitlab|bitbucket|github_enterprise|gitlab_enterprise|bitbucket_server]",
            "  -t, --token TEXT                Codecov upload token",
            "  -r, --slug TEXT                 owner/repo slug used instead of the private",
            "                                  repo token in Self-hosted",
            "  --code, --report-code TEXT      The code of the report. If unsure, leave",
            "                                  default",
            "  --network-root-folder PATH      Root folder from which to consider paths on",
            "                                  the network section  [default: (Current",
            "                                  working directory)]",
            "  -s, --dir, --coverage-files-search-root-folder, --files-search-root-folder PATH",
            "                                  Folder where to search for coverage files",
            "                                  [default: (Current Working Directory)]",
            "  --exclude, --coverage-files-search-exclude-folder, --files-search-exclude-folder PATH",
            "                                  Folders to exclude from search",
            "  -f, --file, --coverage-files-search-direct-file, --files-search-direct-file PATH",
            "                                  Explicit files to upload. These will be added",
            "                                  to the coverage files found for upload. If you",
            "                                  wish to only upload the specified files,",
            "                                  please consider using --disable-search to",
            "                                  disable uploading other files.",
            "  --recurse-submodules            Whether to enumerate files inside of",
            "                                  submodules for path-fixing purposes. Off by",
            "                                  default.",
            "  --disable-search                Disable search for coverage files. This is",
            "                                  helpful when specifying what files you want to",
            "                                  upload with the --file option.",
            "  --disable-file-fixes            Disable file fixes to ignore common lines from",
            "                                  coverage (e.g. blank lines or empty brackets)",
            "  -b, --build, --build-code TEXT  Specify the build number manually",
            "  --build-url TEXT                The URL of the build where this is running",
            "  --job-code TEXT",
            "  -n, --name TEXT                 Custom defined name of the upload. Visible in",
            "                                  Codecov UI",
            "  -B, --branch TEXT               Branch to which this commit belongs to",
            "  -P, --pr, --pull-request-number TEXT",
            "                                  Specify the pull request number manually. Used",
            "                                  to override pre-existing CI environment",
            "                                  variables",
            "  -e, --env, --env-var TEXT       Specify environment variables to be included",
            "                                  with this build.",
            "  -F, --flag TEXT                 Flag the upload to group coverage metrics.",
            "                                  Multiple flags allowed.",
            "  --plugin TEXT",
            "  -d, --dry-run                   Don't upload files to Codecov",
            "  --legacy, --use-legacy-uploader",
            "                                  Use the legacy upload endpoint",
            "  --handle-no-reports-found       Raise no exceptions when no coverage reports",
            "                                  found.",
            "  --report-type [coverage|test_results]",
            "                                  The type of the file to upload, coverage by",
            "                                  default. Possible values are: testing,",
            "                                  coverage.",
            "  --network-filter TEXT           Specify a filter on the files listed in the",
            "                                  network section of the Codecov report. This",
            "                                  will only add files whose path begin with the",
            "                                  specified filter. Useful for upload-specific",
            "                                  path fixing",
            "  --network-prefix TEXT           Specify a prefix on files listed in the",
            "                                  network section of the Codecov report. Useful",
            "                                  to help resolve path fixing",
            "  --gcov-args TEXT                Extra arguments to pass to gcov",
            "  --gcov-ignore TEXT              Paths to ignore during gcov gathering",
            "  --gcov-include TEXT             Paths to include during gcov gathering",
            "  --gcov-executable TEXT          gcov executable to run. Defaults to 'gcov'",
            "  --swift-project TEXT            Specify the swift project",
            "  --parent-sha TEXT               SHA (with 40 chars) of what should be the",
            "                                  parent of this commit",
            "  -h, --help                      Show this message and exit.",
            "",
        ]
