import re

from codecov_cli.helpers.folder_searcher import search_files


def test_search_files(tmp_path):
    search_for = re.compile("banana.*")
    filepaths = [
        "banana.txt",
        "path/to/banana.c",
        "path/to/banana.py",
        "apple.py",
        "banana.py",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()
    expected_results = sorted(
        [
            tmp_path / "banana.txt",
            tmp_path / "banana.py",
            tmp_path / "path/to/banana.py",
            tmp_path / "path/to/banana.c",
        ]
    )
    assert expected_results == sorted(
        search_files(tmp_path, [], search_for, filename_exclude_regex=None)
    )


def test_search_files_with_folder_exclusion(tmp_path):
    search_for = re.compile("banana.*")
    filepaths = [
        "banana.txt",
        "path/to/banana.c",
        "path/to/banana.py",
        "another/to/banana.py",
        "another/some/banana.py",
        "from/some/banana.py",
        "to/some/banana.py",
        "apple.py",
        "banana.py",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()
    expected_results = sorted(
        [
            tmp_path / "banana.txt",
            tmp_path / "banana.py",
            tmp_path / "from/some/banana.py",
            tmp_path / "another/some/banana.py",
        ]
    )
    assert expected_results == sorted(
        search_files(tmp_path, ["to"], search_for, filename_exclude_regex=None)
    )


def test_search_files_combined_regex(tmp_path):
    search_for = re.compile(r"(banana.*)|(apple\..*)")
    filepaths = [
        "banana.txt",
        "path/to/banana.c",
        "path/to/banana.py",
        "apple.py",
        "banana.py",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()
    expected_results = sorted(
        [
            tmp_path / "banana.txt",
            tmp_path / "banana.py",
            tmp_path / "apple.py",
            tmp_path / "path/to/banana.py",
            tmp_path / "path/to/banana.c",
        ]
    )
    assert expected_results == sorted(
        search_files(tmp_path, [], search_for, filename_exclude_regex=None)
    )


def test_search_files_with_exclude_regex(tmp_path):
    search_for = re.compile("banana.*")
    filepaths = [
        "banana.txt",
        "path/to/banana.c",
        "path/to/banana.py",
        "apple.py",
        "banana.py",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()
    expected_results = sorted([tmp_path / "banana.txt", tmp_path / "path/to/banana.c"])
    assert expected_results == sorted(
        search_files(
            tmp_path, [], search_for, filename_exclude_regex=re.compile(r".*\.py")
        )
    )
