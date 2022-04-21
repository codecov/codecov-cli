import pytest
import uuid
import responses
import requests

from responses import matchers
from unittest.mock import Mock, MagicMock
from urllib import parse


from codecov_cli.types import UploadCollectionResult
from codecov_cli.entrypoints import UploadSendingResult
from codecov_cli.entrypoints import UploadSender
from codecov_cli import __version__ as codecov_cli_version
from codecov_cli.entrypoints import UploadSender


class TestUploadSender(object):
    @pytest.fixture
    def fake_upload_data(self):
        upload_collection = UploadCollectionResult(["1", "apple.py", "3"], [])
        random_token = uuid.UUID("f359afb9-8a2a-42ab-a448-c3d267ff495b")
        random_sha = "845548c6b95223f12e8317a1820705f64beaf69e"
        return (upload_collection, random_token, random_sha)

    @pytest.fixture
    def mocked_responses(self):
        with responses.RequestsMock() as rsps:
            yield rsps

    @pytest.fixture
    def mocked_post(self, mocked_responses):
        resp = responses.Response(
            responses.POST,
            "https://codecov.io/upload/v4",
            body="https://resulturl.com\nhttps://puturl.com",
            status=200,
        )
        mocked_responses.add(resp)
        yield resp

    @pytest.fixture
    def mocked_put(self, mocked_responses):
        resp = responses.Response(responses.PUT, "https://puturl.com", status=200)
        mocked_responses.add(resp)
        yield resp

    def test_upload_sender_post_called_with_right_parameters(
        self, fake_upload_data, mocked_responses, mocked_post, mocked_put
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        headers = {"X-Upload-Token": random_token.hex}
        params = {
            "package": f"codecov-cli/{codecov_cli_version}",
            "commit": random_sha,
        }

        mocked_post.match = [
            matchers.query_param_matcher(params),
            matchers.header_matcher(headers),
        ]

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}
        )

        assert len(mocked_responses.calls) == 2

        post_req_made = mocked_responses.calls[0].request

        assert post_req_made.url.split("?")[0] == "https://codecov.io/upload/v4"
        assert dict(parse.parse_qsl(parse.urlsplit(post_req_made.url).query)) == params
        assert (
            post_req_made.headers.items() >= headers.items()
        )  # test dict is a subset of the other

    def test_upload_sender_put_called_with_right_parameters(
        self, fake_upload_data, mocked_responses, mocked_post, mocked_put
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}
        )

        assert len(mocked_responses.calls) == 2

        put_req_mad = mocked_responses.calls[1].request
        assert put_req_mad.url == "https://puturl.com/"

    def test_upload_sender_result_success(
        self, fake_upload_data, mocked_responses, mocked_post, mocked_put
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}
        )

        # default status for both put and post is 200

        assert sender.error is None
        assert not sender.warnings

    def test_upload_sender_result_fail_post_400(
        self, fake_upload_data, mocked_responses, mocked_post
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        mocked_post.status = 400

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}
        )

        assert len(mocked_responses.calls) == 1
        assert sender.error is not None
        assert "400" in sender.error.code

        assert sender.warnings is not None

    def test_upload_sender_result_fail_put_400(
        self, fake_upload_data, mocked_responses, mocked_post, mocked_put
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        mocked_put.status = 400

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}
        )

        assert len(mocked_responses.calls) == 2
        assert sender.error is not None
        assert "400" in sender.error.code

        assert sender.warnings is not None

    def test_upload_sender_http_error_with_invalid_sha(
        self, fake_upload_data, mocked_responses, mocked_post
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        random_sha = "invalid"

        mocked_post.body = "Invalid request parameters"
        mocked_post.status = 400

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token, {}
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

        actual_lines = UploadSender()._generate_env_vars_section(env_vars).split(b"\n")
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

        assert UploadSender()._generate_env_vars_section(env_vars) == b""
