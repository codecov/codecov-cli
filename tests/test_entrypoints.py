import pytest
import uuid

from unittest.mock import Mock, MagicMock


from codecov_cli.types import UploadCollectionResult
from codecov_cli.entrypoints import UploadSendingResult
from codecov_cli.entrypoints import UploadSender
from codecov_cli import __version__ as codecov_cli_version


class TestUploadSender(object):
    class MockHTTPResponse:
        status_code = -1
        text = ""

    @pytest.fixture
    def fake_upload_data(self):
        upload_collection = UploadCollectionResult(["1", "apple.py", "3"], [])
        random_token = uuid.UUID("f359afb9-8a2a-42ab-a448-c3d267ff495b")
        random_sha = "845548c6b95223f12e8317a1820705f64beaf69e"
        return (upload_collection, random_token, random_sha)

    @pytest.fixture
    def mocked_post(self, mocker):
        return mocker.patch(
            "codecov_cli.entrypoints.requests.post", return_value=self.MockHTTPResponse
        )

    def test_upload_sender_post_called_with_right_parameters(
        self, fake_upload_data, mocked_post
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        headers = {"X-Upload-Token": random_token.hex}
        params = {
            "package": f"codecov-cli/{codecov_cli_version}",
            "commit": random_sha,
        }

        self.MockHTTPResponse.status_code = 200
        self.MockHTTPResponse.text = "aa\nbb"

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token
        )

        mocked_post.assert_called_with(
            "https://codecov.io/upload/v4", headers=headers, params=params
        )

    def test_upload_sender_result_success(self, fake_upload_data, mocked_post):
        (upload_collection, random_token, random_sha) = fake_upload_data

        self.MockHTTPResponse.status_code = 200
        self.MockHTTPResponse.text = "aa\nbb"

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token
        )

        assert sender.error is None
        assert not sender.warnings

    def test_upload_sender_result_fail(self, fake_upload_data, mocked_post):
        (upload_collection, random_token, random_sha) = fake_upload_data

        self.MockHTTPResponse.status_code = 400
        self.MockHTTPResponse.text = ""

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token
        )

        assert sender.error is not None
        assert str(self.MockHTTPResponse.status_code) in sender.error.code

        assert sender.warnings is not None

    def test_upload_sender_http_error_with_invalid_sha(
        self, fake_upload_data, mocked_post
    ):
        (upload_collection, random_token, random_sha) = fake_upload_data

        random_sha = "invalid"

        self.MockHTTPResponse.status_code = 400
        self.MockHTTPResponse.text = "Invalid request parameters"

        sender = UploadSender().send_upload_data(
            upload_collection, random_sha, random_token
        )

        assert sender.error is not None
        assert "HTTP Error 400" in sender.error.code
        assert self.MockHTTPResponse.text in sender.error.description
