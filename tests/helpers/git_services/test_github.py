import json

import pytest
import requests
from requests import Response

from codecov_cli.helpers import git
from codecov_cli.helpers.git_services.github import Github


def test_get_pull_request(mocker):
    def mock_request(*args, headers={}, **kwargs):
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
        res = {
            "url": "https://api.github.com/repos/codecov/codecov-cli/pulls/1",
            "head": {
                "sha": "123",
                "label": "codecov-cli:branch",
                "ref": "branch",
                "repo": {"full_name": "user_forked_repo/codecov-cli"},
            },
            "base": {
                "sha": "123",
                "label": "codecov-cli:main",
                "ref": "main",
                "repo": {"full_name": "codecov/codecov-cli"},
            },
        }
        response = Response()
        response.status_code = 200
        response._content = json.dumps(res).encode("utf-8")
        return response

    mocker.patch.object(
        requests,
        "get",
        side_effect=mock_request,
    )
    slug = "codecov/codecov-cli"
    response = Github().get_pull_request(slug, 1)
    assert response == {
        "url": "https://api.github.com/repos/codecov/codecov-cli/pulls/1",
        "head": {
            "sha": "123",
            "label": "codecov-cli:branch",
            "ref": "branch",
            "slug": "user_forked_repo/codecov-cli",
        },
        "base": {
            "sha": "123",
            "label": "codecov-cli:main",
            "ref": "main",
            "slug": "codecov/codecov-cli",
        },
    }


def test_get_pull_request_404(mocker):
    def mock_request(*args, headers={}, **kwargs):
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
        res = {}
        response = Response()
        response.status_code = 404
        response._content = json.dumps(res).encode("utf-8")
        return response

    mocker.patch.object(
        requests,
        "get",
        side_effect=mock_request,
    )
    slug = "codecov/codecov-cli"
    response = Github().get_pull_request(slug, 1)
    assert response is None
