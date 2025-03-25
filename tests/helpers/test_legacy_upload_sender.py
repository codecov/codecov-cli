from urllib import parse

import pytest
import responses
from responses import matchers

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.services.upload.legacy_upload_sender import LegacyUploadSender
from codecov_cli.types import UploadCollectionResult
from tests.data import reports_examples

upload_collection = UploadCollectionResult(["1", "apple.py", "3"], [], [])
random_token = "f359afb9-8a2a-42ab-a448-c3d267ff495b"
random_sha = "845548c6b95223f12e8317a1820705f64beaf69e"
named_upload_data = {
    "name": "name",
    "branch": "branch",
    "slug": "slug",
    "pull_request_number": "pr",
    "build_code": "build_code",
    "build_url": "build_url",
    "job_code": "job_code",
    "flags": "flags",
    "ci_service": "ci_service",
    "git_service": "git_service",
}


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mocked_legacy_upload_endpoint(mocked_responses):
    resp = responses.Response(
        responses.POST,
        "https://codecov.io/upload/v4",
        body="https://resulturl.com\nhttps://puturl.com",
        status=200,
    )
    mocked_responses.add(resp)
    yield resp


@pytest.fixture
def mocked_legacy_upload_endpoint_too_many_fails(mocked_responses):
    resp = responses.Response(
        responses.POST,
        "https://codecov.io/upload/v4",
        body="https://resulturl.com\nhttps://puturl.com",
        status=400,
    )
    for _ in range(4):
        mocked_responses.add(resp)


@pytest.fixture
def mocked_storage_server(mocked_responses):
    resp = responses.Response(responses.PUT, "https://puturl.com", status=200)
    mocked_responses.add(resp)
    yield resp


class TestUploadSender(object):
    def test_upload_sender_post_called_with_right_parameters(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        headers = {"X-Upload-Token": random_token}
        params = {
            "package": f"codecov-cli/{codecov_cli_version}",
            "commit": random_sha,
            **named_upload_data,
        }

        # rename query params keys since they are not the same as send_upload_data parameters
        params["build"] = params.pop("build_code")
        params["pr"] = params.pop("pull_request_number")
        params["job"] = params.pop("job_code")
        params["service"] = params.pop("ci_service")
        params.pop("git_service")
        mocked_legacy_upload_endpoint.match = [
            matchers.query_param_matcher(params),
            matchers.header_matcher(headers),
        ]

        sending_result = LegacyUploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}, **named_upload_data
        )
        assert sending_result.error is None
        assert sending_result.warnings == []

        assert len(mocked_responses.calls) == 2

        post_req_made = mocked_responses.calls[0].request
        assert post_req_made.url.split("?")[0] == "https://codecov.io/upload/v4"
        assert dict(parse.parse_qsl(parse.urlsplit(post_req_made.url).query)) == params
        assert (
            post_req_made.headers.items() >= headers.items()
        )  # test dict is a subset of the other

    def test_upload_sender_put_called_with_right_parameters(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        sending_result = LegacyUploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}, **named_upload_data
        )
        assert sending_result.error is None
        assert sending_result.warnings == []

        assert len(mocked_responses.calls) == 2

        put_req_mad = mocked_responses.calls[1].request
        assert put_req_mad.url == "https://puturl.com/"

    def test_upload_sender_result_success(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        sender = LegacyUploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}, **named_upload_data
        )

        # default status for both put and post is 200

        assert sender.error is None
        assert not sender.warnings

    def test_upload_sender_result_fail_post_400(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocker
    ):
        mocked_legacy_upload_endpoint.status = 400
        mocker.patch("codecov_cli.helpers.request.sleep")

        sender = LegacyUploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}, **named_upload_data
        )

        assert len(mocked_responses.calls) == 1
        assert sender.error is not None
        assert "400" in sender.error.code

        assert sender.warnings is not None

    def test_upload_sender_result_fail_put_400(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        mocked_storage_server.status = 400

        sender = LegacyUploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}, **named_upload_data
        )

        assert len(mocked_responses.calls) == 2
        assert sender.error is not None
        assert "400" in sender.error.code

        assert sender.warnings is not None

    def test_upload_sender_http_error_with_invalid_sha(
        self, mocked_responses, mocked_legacy_upload_endpoint
    ):
        random_sha = "invalid"

        mocked_legacy_upload_endpoint.body = "Invalid request parameters"
        mocked_legacy_upload_endpoint.status = 400

        sender = LegacyUploadSender().send_upload_data(
            upload_collection,
            random_sha,
            random_token,
            {},
            **named_upload_data,
        )

        assert sender.error is not None
        assert "HTTP Error 400" in sender.error.code
        assert "Invalid request parameters" in sender.error.description


class TestPayloadGeneration(object):
    def test_generate_env_vars_section(self):
        terminator = b"<<<<<< ENV"

        expected_without_terminator = b"""var1=value1
        var2=value2
        abc=valbc
        """

        env_vars = {"var1": "value1", "var2": "value2", "var3": None, "abc": "valbc"}

        actual_lines = (
            LegacyUploadSender()._generate_env_vars_section(env_vars).split(b"\n")
        )
        assert terminator in actual_lines

        # lines might not be in the same order since env_vars is a dict. lines' order doesn't matter, only last (non-empty) line must be terminator

        expected_lines_without_terminator = {
            line.strip() for line in expected_without_terminator.split(b"\n")
        }
        actual_lines_without_terminator = {
            line for line in actual_lines if line != terminator
        }

        assert expected_lines_without_terminator == actual_lines_without_terminator

        assert (
            actual_lines[-2] == terminator
        )  # assuming that there will alawys be a new line after terminator

    def test_generate_env_vars_section_empty_result(self):
        env_vars = {"var1": None}
        assert LegacyUploadSender()._generate_env_vars_section(env_vars) == b""

    def test_generate_network_section(self):
        network_files = [
            "./codecov.yaml",
            "Makefile",
            "awesome/__init__.py",
            "awesome/code_fib.py",
            "dev.sh",
            "tests/__init__.py",
            "tests/test_number_two.py",
            "tests/test_sample.py",
            "unit.coverage.xml",
        ]

        expected_network_section = b"""./codecov.yaml
                                    Makefile
                                    awesome/__init__.py
                                    awesome/code_fib.py
                                    dev.sh
                                    tests/__init__.py
                                    tests/test_number_two.py
                                    tests/test_sample.py
                                    unit.coverage.xml
                                    <<<<<< network
                                    """

        upload_data = UploadCollectionResult(network_files, [], [])

        actual_network_section = LegacyUploadSender()._generate_network_section(
            upload_data
        )

        assert [line.strip() for line in expected_network_section.split(b"\n")] == [
            line for line in actual_network_section.split(b"\n")
        ]

    def test_generate_network_section_empty_result(self):
        assert (
            LegacyUploadSender()._generate_network_section(
                UploadCollectionResult([], [], [])
            )
            == b""
        )

    def test_format_coverage_file(self, mocker):
        fake_result_file = mocker.MagicMock()
        mocker.patch(
            "codecov_cli.services.upload.upload_sender.UploadCollectionResultFile",
            return_value=fake_result_file,
        )

        coverage_file_seperated = reports_examples.coverage_file_section_simple.split(
            b"\n", 1
        )

        fake_result_file.get_filename.return_value = (
            coverage_file_seperated[0][len(b"# path=") :].strip().decode()
        )
        fake_result_file.get_content.return_value = coverage_file_seperated[1][
            : -len(b"\n<<<<<< EOF\n")
        ]
        actual_coverage_file_section = LegacyUploadSender()._format_coverage_file(
            fake_result_file
        )

        assert (
            actual_coverage_file_section
            == reports_examples.coverage_file_section_simple
        )

    def test_generate_coverage_files_section(self, mocker):
        mocker.patch(
            "codecov_cli.services.upload.LegacyUploadSender._format_coverage_file",
            side_effect=lambda file_bytes: file_bytes,
        )

        coverage_files = [
            reports_examples.coverage_file_section_simple,
            reports_examples.coverage_file_section_simple,
            reports_examples.coverage_file_section_small,
            reports_examples.coverage_file_section_simple,
        ]

        actual_section = LegacyUploadSender()._generate_coverage_files_section(
            UploadCollectionResult([], coverage_files, [])
        )

        expected_section = b"".join(coverage_files)

        assert actual_section == expected_section

    def test_generate_payload_overall(self, mocker):
        mocker.patch(
            "codecov_cli.services.upload.LegacyUploadSender._generate_env_vars_section",
            return_value=reports_examples.env_section,
        )
        mocker.patch(
            "codecov_cli.services.upload.LegacyUploadSender._generate_network_section",
            return_value=reports_examples.network_section,
        )
        mocker.patch(
            "codecov_cli.services.upload.LegacyUploadSender._generate_coverage_files_section",
            return_value=reports_examples.coverage_file_section_simple,
        )

        actual_report = LegacyUploadSender()._generate_payload(None, None)

        assert actual_report == reports_examples.env_network_coverage_sections
