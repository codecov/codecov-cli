from unittest.mock import MagicMock

import pytest

from codecov_cli.helpers.network_finder import NetworkFinder


def test_find_files(mocker, tmp_path):

    expected_filenames = ["a.txt", "b.txt"]

    mocked_vs = MagicMock()
    mocked_vs.list_relevant_files.return_value = expected_filenames

    assert NetworkFinder(mocked_vs).find_files(tmp_path) == expected_filenames
    mocked_vs.list_relevant_files.assert_called_with(tmp_path)
