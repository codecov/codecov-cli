from unittest.mock import MagicMock

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.versioning_systems import GitVersioningSystem


class TestGitVersioningSystem(object):
    @pytest.mark.parametrize(
        "commit_sha,expected", [("", None), (b" random_sha  ", "random_sha")]
    )
    def test_commit_sha(self, mocker, commit_sha, expected):
        mocked_subprocess = MagicMock()
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.subprocess.run",
            return_value=mocked_subprocess,
        )

        mocked_subprocess.stdout = commit_sha

        assert (
            GitVersioningSystem().get_fallback_value(FallbackFieldEnum.commit_sha)
            == expected
        )

    @pytest.mark.parametrize(
        "branch,expected",
        [
            ("", None),
            (b" master  ", "master"),
            (b"feature", "feature"),
            (b"HEAD", None),
        ],
    )
    def test_branch(self, mocker, branch, expected):
        mocked_subprocess = MagicMock()
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.subprocess.run",
            return_value=mocked_subprocess,
        )

        mocked_subprocess.stdout = branch

        assert (
            GitVersioningSystem().get_fallback_value(FallbackFieldEnum.branch)
            == expected
        )

    @pytest.mark.parametrize(
        "remote_list,remote_url,expected",
        [
            (b"", b"git@github.com:codecov/codecov-cli.git", None),
            (b"origin", b"", None),
            (
                b"origin",
                b"git@github.com:codecov/codecov-cli.git",
                "codecov/codecov-cli",
            ),
            (
                b"upstream\norigin\notherrepo",
                b"git@github.com:codecov/codecov-cli.git",
                "codecov/codecov-cli",
            ),
            (
                b"upstream\notherrepo",
                b"git@github.com:codecov/codecov-cli.git",
                "codecov/codecov-cli",
            ),
        ],
    )
    def test_slug_(self, mocker, remote_list, remote_url, expected):
        def side_effect(*args, **kwargs):
            m = MagicMock()
            if args[0][1] == "remote":
                m.stdout = remote_list
            if args[0][1] == "ls-remote":
                m.stdout = remote_url

            return m

        mocker.patch(
            "codecov_cli.helpers.versioning_systems.subprocess.run",
            side_effect=side_effect,
        )

        assert (
            GitVersioningSystem().get_fallback_value(FallbackFieldEnum.slug) == expected
        )
