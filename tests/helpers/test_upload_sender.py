import uuid

import pytest
import responses
from responses import matchers

from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.services.upload.upload_sender import UploadSender
from codecov_cli.types import UploadCollectionResult

upload_collection = UploadCollectionResult(["1", "apple.py", "3"], [], [])
random_token = uuid.UUID("f359afb9-8a2a-42ab-a448-c3d267ff495b")
random_sha = "845548c6b95223f12e8317a1820705f64beaf69e"
named_upload_data = {
    "report_code": "report_code",
    "env_vars": {},
    "name": "name",
    "branch": "branch",
    "slug": "slug",
    "pull_request_number": "pr",
    "build_code": "build_code",
    "build_url": "build_url",
    "job_code": "job_code",
    "flags": "flags",
    "service": "service",
}
request_data = {
    "ci_url": "build_url",
    "flags": "flags",
    "name": "name",
}


@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mocked_legacy_upload_endpoint(mocked_responses):
    resp = responses.Response(
        responses.POST,
        f"https://codecov.io/upload/{named_upload_data['slug']}/commits/{random_sha}/reports/{named_upload_data['report_code']}/uploads",
        status=200,
        json={"raw_upload_location": "https://puturl.com"},
    )
    mocked_responses.add(resp)
    yield resp


@pytest.fixture
def mocked_storage_server(mocked_responses):
    resp = responses.Response(responses.PUT, "https://puturl.com", status=200)
    mocked_responses.add(resp)
    yield resp


class TestUploadSender(object):
    def test_upload_sender_post_called_with_right_parameters(
        self, mocked_responses, mocked_legacy_upload_endpoint, mocked_storage_server
    ):
        headers = {"Authorization": f"token {random_token.hex}"}

        mocked_legacy_upload_endpoint.match = [
            matchers.urlencoded_params_matcher(request_data),
            matchers.header_matcher(headers),
        ]

        sending_result = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, **named_upload_data
        )
        assert sending_result.error is None
        assert sending_result.warnings == []

        assert len(mocked_responses.calls) == 2

        post_req_made = mocked_responses.calls[0].request
        assert (
            post_req_made.url
            == f"https://codecov.io/upload/{named_upload_data['slug']}/commits/{random_sha}/reports/{named_upload_data['report_code']}/uploads"
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
