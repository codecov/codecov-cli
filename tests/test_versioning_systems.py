from unittest.mock import MagicMock

import pytest

from codecov_cli.helpers.versioning_systems import GitVersioningSystem


class TestGitVersioningSystem(object):
    def test_list_relevant_files_throws_exception_if_network_root_cant_be_determined(
        self, mocker
    ):
        mocker.patch.object(GitVersioningSystem, "get_network_root").return_value = None
        vs = GitVersioningSystem()

        with pytest.raises(ValueError) as ex:
            vs.list_relevant_files()

    def test_list_relevant_files_returns_correct_network_files(self, mocker):
        mocked_subprocess = MagicMock()
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.subprocess.run",
            return_value=mocked_subprocess,
        )
        mocked_subprocess.stdout = b"a.txt\nb.txt"

        vs = GitVersioningSystem()

        assert vs.list_relevant_files() == ["a.txt", "b.txt"]
