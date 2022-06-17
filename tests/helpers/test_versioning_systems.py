from unittest.mock import MagicMock

import pytest

from codecov_cli.helpers.versioning_systems import GitVersioningSystem


class TestGitVersioningSystem(object):
    def test_list_relevant_files_returns_correct_network_files(self, mocker, tmp_path):
        mocked_subprocess = MagicMock()
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.subprocess.run",
            return_value=mocked_subprocess,
        )

        # git ls-files diplays a single \n as \\\\n
        mocked_subprocess.stdout = b'a.txt\nb.txt\n"a\\\\nb.txt"\nc.txt\nd.txt'

        vs = GitVersioningSystem()

        assert vs.list_relevant_files(tmp_path) == [
            "a.txt",
            "b.txt",
            "a\\nb.txt",
            "c.txt",
            "d.txt",
        ]

    def test_list_relevant_files_fails_if_no_root_is_found(self, mocker):
        mocker.patch(
            "codecov_cli.helpers.versioning_systems.GitVersioningSystem.get_network_root",
            return_value=None,
        )

        vs = GitVersioningSystem()
        with pytest.raises(ValueError) as ex:
            vs.list_relevant_files()
