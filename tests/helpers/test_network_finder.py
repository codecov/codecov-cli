from unittest.mock import MagicMock

import pytest

from codecov_cli.services.upload.network_finder import NetworkFinder


def test_find_files(mocker, tmp_path):
    filenames = ["a.txt", "b.txt"]
    filtered_filenames = []

    mocked_vs = MagicMock()
    mocked_vs.list_relevant_files.return_value = filenames

    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter=None,
            network_prefix=None,
            network_root_folder=tmp_path,
        ).find_files()
        == filenames
    )
    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter="hello",
            network_prefix="bello",
            network_root_folder=tmp_path,
        ).find_files(False)
        == filtered_filenames
    )
    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter="hello",
            network_prefix="bello",
            network_root_folder=tmp_path,
        ).find_files(True)
        == filenames
    )
    mocked_vs.list_relevant_files.assert_called_with(tmp_path)


def test_find_files_with_filter(mocker, tmp_path):
    filenames = ["hello/a.txt", "hello/c.txt", "bello/b.txt"]
    filtered_filenames = ["hello/a.txt", "hello/c.txt"]

    mocked_vs = MagicMock()
    mocked_vs.list_relevant_files.return_value = filenames

    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter="hello",
            network_prefix=None,
            network_root_folder=tmp_path,
        ).find_files()
        == filtered_filenames
    )
    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter="hello",
            network_prefix="bello",
            network_root_folder=tmp_path,
        ).find_files(True)
        == filenames
    )
    mocked_vs.list_relevant_files.assert_called_with(tmp_path)


def test_find_files_with_prefix(mocker, tmp_path):
    filenames = ["hello/a.txt", "hello/c.txt", "bello/b.txt"]
    filtered_filenames = ["hellohello/a.txt", "hellohello/c.txt", "hellobello/b.txt"]

    mocked_vs = MagicMock()
    mocked_vs.list_relevant_files.return_value = filenames

    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter=None,
            network_prefix="hello",
            network_root_folder=tmp_path,
        ).find_files()
        == filtered_filenames
    )
    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter="hello",
            network_prefix="bello",
            network_root_folder=tmp_path,
        ).find_files(True)
        == filenames
    )
    mocked_vs.list_relevant_files.assert_called_with(tmp_path)


def test_find_files_with_filter_and_prefix(mocker, tmp_path):
    filenames = ["hello/a.txt", "hello/c.txt", "bello/b.txt"]
    filtered_filenames = ["bellohello/a.txt", "bellohello/c.txt"]

    mocked_vs = MagicMock()
    mocked_vs.list_relevant_files.return_value = filenames

    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter="hello",
            network_prefix="bello",
            network_root_folder=tmp_path,
        ).find_files()
        == filtered_filenames
    )
    assert (
        NetworkFinder(
            versioning_system=mocked_vs,
            network_filter="hello",
            network_prefix="bello",
            network_root_folder=tmp_path,
        ).find_files(True)
        == filenames
    )
    mocked_vs.list_relevant_files.assert_called_with(tmp_path)
