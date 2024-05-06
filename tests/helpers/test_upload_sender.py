import json
import os
import re
from pathlib import Path

import pytest
import responses
from responses import matchers

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.helpers.encoder import encode_slug
from codecov_cli.services.upload.upload_sender import UploadSender
from codecov_cli.types import UploadCollectionResult, UploadCollectionResultFileFixer
from tests.data import reports_examples

upload_collection = UploadCollectionResult(["1", "apple.py", "3"], [], [])
random_token = "f359afb9-8a2a-42ab-a448-c3d267ff495b"
random_sha = "845548c6b95223f12e8317a1820705f64beaf69e"
named_upload_data = {
    "upload_file_type": "coverage",
    "report_code": "report_code",
    "env_vars": {},
    "name": "name",
    "branch": "branch",
    "slug": "org/repo",
    "pull_request_number": "pr",
    "build_code": "build_code",
    "build_url": "build_url",
    "job_code": "job_code",
    "flags": "flags",
    "ci_service": "ci_service",
    "git_service": "github",
}
test_results_named_upload_data = {
    "upload_file_type": "test_results",
    "report_code": "report_code",
    "env_vars": {},
    "name": "name",
    "branch": "branch",
    "slug": "org/repo",
    "pull_request_number": "pr",
    "build_code": "build_code",
    "build_url": "build_url",
    "job_code": "job_code",
    "flags": "flags",
    "ci_service": "ci_service",
    "git_service": "github",
}
request_data = {
    "ci_url": "build_url",
    "env": {},
    "flags": "flags",
    "job_code": "job_code",
    "name": "name",
    "version": codecov_cli_version,
    "ci_service": "ci_service",
}


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mocked_legacy_upload_endpoint(mocked_responses):
    encoded_slug = encode_slug(named_upload_data["slug"])
    resp = responses.Response(
        responses.POST,
        f"https://api.codecov.io/upload/github/{encoded_slug}/commits/{random_sha}/reports/{named_upload_data['report_code']}/uploads",
        status=200,
        json={
            "raw_upload_location": "https://puturl.com",
            "url": "https://app.codecov.io/commit-url",
        },
    )
    mocked_responses.add(resp)
    yield resp


@pytest.fixture
def mocked_test_results_endpoint(mocked_responses):
    resp = responses.Response(
        responses.POST,
        f"https://api.codecov.io/upload/test_results/v1",
        status=200,
        json={
            "raw_upload_location": "https://puturl.com",
        },
    )
    mocked_responses.add(resp)
    yield resp


@pytest.fixture
def mocked_storage_server(mocked_responses):
    resp = responses.Response(responses.PUT, "https://puturl.com", status=200)
    mocked_responses.add(resp)
    yield resp


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


def get_fake_upload_collection_result(mocked_coverage_file):
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
            path=Path("SwiftExample/AppDelegate.swift"),
            fixed_lines_without_reason=set([1, 2, 3, 4, 9, 10, 11]),
            fixed_lines_with_reason=set(
                [
                    (8, "// LCOV_EXCL_END\n"),
                    (13, "// LCOV_EXCL_STOP\n"),
                    (5, "// LCOV_EXCL_BEGIN\n"),
                    (7, "// LCOV_EXCL_START\n"),
                ]
            ),
            eof=15,
        ),
        UploadCollectionResultFileFixer(
            path=Path("SwiftExample/Hello.swift"),
            fixed_lines_without_reason=set([1, 3, 7, 9, 12, 14]),
            fixed_lines_with_reason=set(
                [
                    (17, "    /*\n"),
                    (22, "*/\n"),
                ]
            ),
            eof=30,
        ),
        UploadCollectionResultFileFixer(
            path=Path("SwiftExample/ViewController.swift"),
            fixed_lines_without_reason=set(
                [1, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 26]
            ),
            fixed_lines_with_reason=set([]),
            eof=None,
        ),
    ]
    return UploadCollectionResult(network_files, coverage_files, path_fixers)


class TestUploadSender(object):
    def test_upload_sender_post_called_with_right_parameters(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        headers = {"Authorization": f"token {random_token}"}

        mocked_legacy_upload_endpoint.match = [
            matchers.json_params_matcher(request_data),
            matchers.header_matcher(headers),
        ]

        sending_result = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, **named_upload_data
        )
        assert sending_result.error is None
        assert sending_result.warnings == []

        assert len(mocked_responses.calls) == 2

        post_req_made = mocked_responses.calls[0].request
        encoded_slug = encode_slug(named_upload_data["slug"])
        response = json.loads(mocked_responses.calls[0].response.text)
        assert response.get("url") == "https://app.codecov.io/commit-url"
        assert (
            post_req_made.url
            == f"https://api.codecov.io/upload/github/{encoded_slug}/commits/{random_sha}/reports/{named_upload_data['report_code']}/uploads"
        )
        assert (
            post_req_made.headers.items() >= headers.items()
        )  # test dict is a subset of the other

    def test_upload_sender_post_called_with_right_parameters_test_results(
        self, mocked_responses, mocked_test_results_endpoint, mocked_storage_server
    ):
        headers = {"Authorization": f"token {random_token}"}

        mocked_legacy_upload_endpoint.match = [
            matchers.json_params_matcher(request_data),
            matchers.header_matcher(headers),
        ]

        sending_result = UploadSender().send_upload_data(
            upload_collection,
            random_sha,
            random_token,
            **test_results_named_upload_data,
        )
        assert sending_result.error is None
        assert sending_result.warnings == []

        assert len(mocked_responses.calls) == 2

        post_req_made = mocked_responses.calls[0].request
        response = json.loads(mocked_responses.calls[0].response.text)
        assert response.get("raw_upload_location") == "https://puturl.com"
        assert post_req_made.url == "https://api.codecov.io/upload/test_results/v1"
        assert (
            post_req_made.headers.items() >= headers.items()
        )  # test dict is a subset of the other

        put_req_made = mocked_responses.calls[1].request
        assert put_req_made.url == "https://puturl.com/"
        assert "test_results_files" in put_req_made.body.decode("utf-8")

    def test_upload_sender_post_called_with_right_parameters_tokenless(
        self,
        mocked_responses,
        mocked_legacy_upload_endpoint,
        mocked_storage_server,
        mocker,
    ):
        headers = {"X-Tokenless": "user:branch"}
        mocked_legacy_upload_endpoint.match = [
            matchers.json_params_matcher(request_data),
            matchers.header_matcher(headers),
        ]

        os.environ["TOKENLESS"] = "user:branch"
        sending_result = UploadSender().send_upload_data(
            upload_collection, random_sha, None, **named_upload_data
        )
        assert sending_result.error is None
        assert sending_result.warnings == []

        assert len(mocked_responses.calls) == 2

        post_req_made = mocked_responses.calls[0].request
        encoded_slug = encode_slug(named_upload_data["slug"])
        response = json.loads(mocked_responses.calls[0].response.text)
        assert response.get("url") == "https://app.codecov.io/commit-url"
        assert (
            post_req_made.url
            == f"https://api.codecov.io/upload/github/{encoded_slug}/commits/{random_sha}/reports/{named_upload_data['report_code']}/uploads"
        )
        assert (
            post_req_made.headers.items() >= headers.items()
        )  # test dict is a subset of the other

    def test_upload_sender_put_called_with_right_parameters(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        sending_result = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, **named_upload_data
        )
        assert sending_result.error is None
        assert sending_result.warnings == []

        assert len(mocked_responses.calls) == 2

        put_req_mad = mocked_responses.calls[1].request
        assert put_req_mad.url == "https://puturl.com/"

    def test_upload_sender_result_success(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, **named_upload_data
        )

        # default status for both put and post is 200

        assert sender.error is None
        assert not sender.warnings

    def test_upload_sender_result_fail_post_400(
        self, mocked_responses, mocked_legacy_upload_endpoint
    ):
        mocked_legacy_upload_endpoint.status = 400

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, **named_upload_data
        )

        assert len(mocked_responses.calls) == 1
        assert sender.error is not None
        assert "400" in sender.error.code

        assert sender.warnings is not None

    def test_upload_sender_result_fail_post_502(
        self, mocker, mocked_responses, mocked_legacy_upload_endpoint, capsys
    ):
        mocker.patch("codecov_cli.helpers.request.sleep")
        mocked_legacy_upload_endpoint.status = 502

        with pytest.raises(Exception, match="Request failed after too many retries"):
            _ = UploadSender().send_upload_data(
                upload_collection, random_sha, random_token, **named_upload_data
            )

        matcher = re.compile(
            r"(warning.*((Response status code was 502)|(Request failed\. Retrying)).*(\n)?){6}"
        )

        assert matcher.match(capsys.readouterr().err) is not None

    def test_upload_sender_result_fail_put_400(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        mocked_storage_server.status = 400

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, **named_upload_data
        )

        assert len(mocked_responses.calls) == 2
        assert sender.error is not None
        assert "400" in sender.error.code

        assert sender.warnings is not None

    def test_upload_sender_http_error_with_invalid_sha(
        self, mocked_responses, mocked_legacy_upload_endpoint
    ):
        mocked_legacy_upload_endpoint.body = "Invalid request parameters"
        mocked_legacy_upload_endpoint.status = 400

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, **named_upload_data
        )

        assert sender.error is not None
        assert "HTTP Error 400" in sender.error.code
        assert "Invalid request parameters" in sender.error.description


class TestPayloadGeneration(object):
    def test_generate_payload_overall(self, mocked_coverage_file):
        actual_report = UploadSender()._generate_payload(
            get_fake_upload_collection_result(mocked_coverage_file), None
        )
        expected_report = {
            "report_fixes": {
                "format": "legacy",
                "value": {
                    "SwiftExample/AppDelegate.swift": {
                        "eof": 15,
                        "lines": [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13],
                    },
                    "SwiftExample/Hello.swift": {
                        "eof": 30,
                        "lines": [1, 17, 3, 22, 7, 9, 12, 14],
                    },
                    "SwiftExample/ViewController.swift": {
                        "eof": None,
                        "lines": [
                            1,
                            4,
                            5,
                            6,
                            7,
                            9,
                            10,
                            11,
                            12,
                            13,
                            14,
                            15,
                            16,
                            17,
                            18,
                            19,
                            20,
                            22,
                            26,
                        ],
                    },
                },
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
            "report_fixes": {
                "format": "legacy",
                "value": {},
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
        json_formatted_coverage_file = UploadSender()._format_file(mocked_coverage_file)
        print(json_formatted_coverage_file["data"])
        assert json_formatted_coverage_file == {
            "filename": mocked_coverage_file.get_filename().decode(),
            "format": "base64+compressed",
            "data": "encoded_file_data",
            "labels": "",
        }
