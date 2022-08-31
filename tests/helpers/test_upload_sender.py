import json

import pytest

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.services.upload.upload_sender import UploadSender
from codecov_cli.types import UploadCollectionResult, UploadCollectionResultFileFixer
from tests.data import reports_examples


@pytest.fixture
def mocked_coverage_file(mocker):
    fake_result_file = mocker.MagicMock()
    coverage_file_seperated = reports_examples.coverage_file_section_simple.split(
        b"\n", 1
    )
    fake_result_file.get_filename.return_value = coverage_file_seperated[0][
        len(b"# path=") :
    ].strip()
    fake_result_file.get_content.return_value = coverage_file_seperated[1][
        : -len(b"\n<<<<<< EOF\n")
    ]
    return fake_result_file


@pytest.fixture
def mocked_upload_data(mocked_coverage_file):
    network_files = [
        "./codecov.yaml",
        "Makefile",
        "awesome/__init__.py",
        "awesome/code_fib.py",
        "dev.sh",
    ]
    coverage_files = [mocked_coverage_file, mocked_coverage_file]
    path_fixers = [
        UploadCollectionResultFileFixer(
            "SwiftExample/AppDelegate.swift", None, None, None
        ),
        UploadCollectionResultFileFixer("SwiftExample/Hello.swift", None, None, None),
        UploadCollectionResultFileFixer(
            "SwiftExample/ViewController.swift", None, None, None
        ),
    ]
    return UploadCollectionResult(network_files, coverage_files, path_fixers)


class TestPayloadGeneration(object):
    def test_generate_payload_overall(self, mocked_upload_data):
        actual_report = UploadSender()._generate_payload(mocked_upload_data, None)
        expected_report = {
            "path_fixes": {
                "format": "legacy",
                "value": [
                    "SwiftExample/AppDelegate.swift",
                    "SwiftExample/Hello.swift",
                    "SwiftExample/ViewController.swift",
                ],
            },
            "network_files": [
                "./codecov.yaml",
                "Makefile",
                "awesome/__init__.py",
                "awesome/code_fib.py",
                "dev.sh",
            ],
            "coverage_files": [
                {
                    "filename": "flagtwo.coverage.xml",
                    "format": "base64+compressed",
                    "data": "eJzdVctymzAU3ecrVPYg4hrHkyHOTDfddtM1I8SNUQsSo3vx4+8rngE7pIs6M21ZMNyHzpHOPUD8fCoLdgCLyugn7z4IPfa8u4ulcTmxB5ZaoWXuW0Hw5LliFwP6bQdk8+RBFKpLSVNWBZwUnduwUBoGkGDTxROMz+GQ6hEilyBVApIoK7evTRhuolW42m4jt3rc7zqIgrW3u2Puij/5PvsKGhqajKVnNhwiqM6PLCeq8JHzMWlBZJRDZiQGyjDfn8B8EeggjB5XWXEM9oryOq0RrDSaQFPgDunwUrBUW8GPkPJSIIHlOTWw3Gk78vnhOsgoe+VBU1sJ2EWTzI5/dxTIKVdib6wVpUH+zZofIAm5LBQ05AcOJ9FI7Fdnyo2Oeb+6A+cz9LgS8qfbw5SsT10N+N3BbT2mRemexRHQlOC9AragshCIU5p55XdkL6qAGT5PEqUVJYkb4eVe1g/3w26mXdfcLX8JTqUM+UK5Nd/btbHOckXovOhY69INvXlcwuMLgDFvhbidQNJkkLyo9Fqgh2iQZ9rzD8rTJ2fu5b19/9DQ0WrQiNynBj/Mzi36oplv7eM3ijfzXXeS5p50Y07oaK7MN1X1ou/DDRj+Fe/nRCdsv9OLQ7/o+S9f0DF0LfH4S9z9Ar0cTD8=",
                    "labels": "",
                },
                {
                    "filename": "flagtwo.coverage.xml",
                    "format": "base64+compressed",
                    "data": "eJzdVctymzAU3ecrVPYg4hrHkyHOTDfddtM1I8SNUQsSo3vx4+8rngE7pIs6M21ZMNyHzpHOPUD8fCoLdgCLyugn7z4IPfa8u4ulcTmxB5ZaoWXuW0Hw5LliFwP6bQdk8+RBFKpLSVNWBZwUnduwUBoGkGDTxROMz+GQ6hEilyBVApIoK7evTRhuolW42m4jt3rc7zqIgrW3u2Puij/5PvsKGhqajKVnNhwiqM6PLCeq8JHzMWlBZJRDZiQGyjDfn8B8EeggjB5XWXEM9oryOq0RrDSaQFPgDunwUrBUW8GPkPJSIIHlOTWw3Gk78vnhOsgoe+VBU1sJ2EWTzI5/dxTIKVdib6wVpUH+zZofIAm5LBQ05AcOJ9FI7Fdnyo2Oeb+6A+cz9LgS8qfbw5SsT10N+N3BbT2mRemexRHQlOC9AragshCIU5p55XdkL6qAGT5PEqUVJYkb4eVe1g/3w26mXdfcLX8JTqUM+UK5Nd/btbHOckXovOhY69INvXlcwuMLgDFvhbidQNJkkLyo9Fqgh2iQZ9rzD8rTJ2fu5b19/9DQ0WrQiNynBj/Mzi36oplv7eM3ijfzXXeS5p50Y07oaK7MN1X1ou/DDRj+Fe/nRCdsv9OLQ7/o+S9f0DF0LfH4S9z9Ar0cTD8=",
                    "labels": "",
                },
            ],
            "metadata": {},
        }
        assert actual_report == json.dumps(expected_report).encode()

    def test_generate_empty_payload_overall(self):
        actual_report = UploadSender()._generate_payload(
            UploadCollectionResult([], [], []), None
        )
        expected_report = {
            "path_fixes": {
                "format": "legacy",
                "value": [],
            },
            "network_files": [],
            "coverage_files": [],
            "metadata": {},
        }
        assert actual_report == json.dumps(expected_report).encode()

    def test_formatting_file_coverage_info(self, mocker, mocked_coverage_file):
        format, formatted_content = UploadSender()._get_format_info(
            mocked_coverage_file
        )
        assert format == "base64+compressed"
        assert (
            formatted_content
            == "eJzdVctymzAU3ecrVPYg4hrHkyHOTDfddtM1I8SNUQsSo3vx4+8rngE7pIs6M21ZMNyHzpHOPUD8fCoLdgCLyugn7z4IPfa8u4ulcTmxB5ZaoWXuW0Hw5LliFwP6bQdk8+RBFKpLSVNWBZwUnduwUBoGkGDTxROMz+GQ6hEilyBVApIoK7evTRhuolW42m4jt3rc7zqIgrW3u2Puij/5PvsKGhqajKVnNhwiqM6PLCeq8JHzMWlBZJRDZiQGyjDfn8B8EeggjB5XWXEM9oryOq0RrDSaQFPgDunwUrBUW8GPkPJSIIHlOTWw3Gk78vnhOsgoe+VBU1sJ2EWTzI5/dxTIKVdib6wVpUH+zZofIAm5LBQ05AcOJ9FI7Fdnyo2Oeb+6A+cz9LgS8qfbw5SsT10N+N3BbT2mRemexRHQlOC9AragshCIU5p55XdkL6qAGT5PEqUVJYkb4eVe1g/3w26mXdfcLX8JTqUM+UK5Nd/btbHOckXovOhY69INvXlcwuMLgDFvhbidQNJkkLyo9Fqgh2iQZ9rzD8rTJ2fu5b19/9DQ0WrQiNynBj/Mzi36oplv7eM3ijfzXXeS5p50Y07oaK7MN1X1ou/DDRj+Fe/nRCdsv9OLQ7/o+S9f0DF0LfH4S9z9Ar0cTD8="
        )

    def test_coverage_file_format(self, mocker, mocked_coverage_file):
        mocker.patch(
            "codecov_cli.services.upload.upload_sender.UploadSender._get_format_info",
            return_value=("base64+compressed", "encoded_file_data"),
        )
        json_formatted_coverage_file = UploadSender()._format_coverage_file(
            mocked_coverage_file
        )
        print(json_formatted_coverage_file["data"])
        assert json_formatted_coverage_file == {
            "filename": mocked_coverage_file.get_filename().decode(),
            "format": "base64+compressed",
            "data": "encoded_file_data",
            "labels": "",
        }
