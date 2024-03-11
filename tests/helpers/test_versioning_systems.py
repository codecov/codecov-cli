from unittest.mock import MagicMock

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.versioning_systems import GitVersioningSystem


class TestGitVersioningSystem(object):
    @pytest.mark.parametrize(
        "runs_output,expected",
        [
            # No output for parents nor commit
            ([b"", b""], None),
            # No output for parents, commit has SHA
            ([b"", b" random_sha"], "random_sha"),
            # Commit is NOT a merge-commit
            ([b" parent_sha", b" random_sha  "], "random_sha"),
            # Commit IS a merge-commit
            ([b" parent_sha0\nparent_sha1", b" random_sha"], "parent_sha1"),
        ],
    )
    def test_commit_sha(self, mocker, runs_output, expected):
        mocked_subprocess = [
            MagicMock(**{"stdout": runs_output[0]}),
            MagicMock(**{"stdout": runs_output[1]}),
        ]
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.subprocess.run",
            side_effect=mocked_subprocess,
        )

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
    def test_slug(self, mocker, remote_list, remote_url, expected):
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

    def test_list_relevant_files_returns_correct_network_files(self, mocker, tmp_path):
        mocked_subprocess = MagicMock()
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.subprocess.run",
            return_value=mocked_subprocess,
        )
        # git ls-files diplays a single \n as \\\\n
        mocked_subprocess.stdout = b'a.txt\nb.txt\n"a\\\\nb.txt"\nc.txt\nd.txt\n.circleci/config.yml\nLICENSE\napp/advanced calculations/advanced_calculator.js\n'

        vs = GitVersioningSystem()

        assert vs.list_relevant_files(tmp_path) == [
            "a.txt",
            "b.txt",
            "a\\nb.txt",
            "c.txt",
            "d.txt",
            ".circleci/config.yml",
            "LICENSE",
            "app/advanced calculations/advanced_calculator.js",
        ]

    def test_list_relevant_files_fails_if_no_root_is_found(self, mocker):
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.GitVersioningSystem.get_network_root",
            return_value=None,
        )

        vs = GitVersioningSystem()
        with pytest.raises(ValueError) as ex:
            vs.list_relevant_files()
