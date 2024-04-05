from unittest.mock import MagicMock

import pytest

from codecov_cli.services.upload.network_finder import NetworkFinder


def test_find_files(mocker, tmp_path):

    expected_filenames = ["a.txt", "b.txt"]

    mocked_vs = MagicMock()
    mocked_vs.list_relevant_files.return_value = expected_filenames

    assert NetworkFinder(versioning_system=mocked_vs, network_filter=None, network_prefix=None, network_root_folder=tmp_path).find_files() == expected_filenames
    mocked_vs.list_relevant_files.assert_called_with(tmp_path)
