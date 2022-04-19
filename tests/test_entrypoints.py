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

    @pytest.fixture()
    def mocked_post(self, mocked_responses):
        resp = responses.Response(
            responses.POST,
            "https://codecov.io/upload/v4",
            body="aa\nbb",
            status=200,
        )
        mocked_responses.add(resp)
        yield resp

    def test_upload_sender_post_called_with_right_parameters(
        self, fake_upload_data, mocked_responses, mocked_post
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
            upload_collection, random_sha, random_token
        )

        assert len(mocked_responses.calls) == 1

        req_made = mocked_responses.calls[0].request

        assert req_made.url.split("?")[0] == "https://codecov.io/upload/v4"
        assert dict(parse.parse_qsl(parse.urlsplit(req_made.url).query)) == params
        assert (
            req_made.headers.items() >= headers.items()
        )  # test dict is a subset of the other

    def test_upload_sender_result_success(
        self, fake_upload_data, mocked_responses, mocked_post
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token
        )

        assert sender.error is None
        assert not sender.warnings

    def test_upload_sender_result_fail(
        self, fake_upload_data, mocked_responses, mocked_post
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        mocked_post.status = 400

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token
        )

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
            upload_collection, random_sha, random_token
        )

        assert sender.error is not None
        assert "HTTP Error 400" in sender.error.code
        assert "Invalid request parameters" in sender.error.description



class TestPayloadGeneration(object):
    def test_generate_env_vars_section(self):
        expected = (b"""var1=value1
        var2=value2
        abc=valbc
        <<<<<< ENV
        """
        )
        
        env_vars = {
            "var1": "value1",
            "var2": "value2",
            "var3": None,
            "abc": "valbc"
        }
        
        expected_lines = set(line.strip() for line in expected.split(b'\n'))
        actual_lines = set(UploadSender()._generate_env_vars_section(env_vars).split(b'\n'))
        
        
        assert actual_lines == expected_lines
        
    def test_generate_env_vars_section_empty_result(self):
        env_vars = {
            "var1": None
        }
        
        assert UploadSender()._generate_env_vars_section(env_vars) == b""

