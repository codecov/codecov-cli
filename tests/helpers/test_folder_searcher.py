import re

import pytest

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files


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

    assert sorted(
        search_files(
            tmp_path, [], filename_include_regex=search_for, filename_exclude_regex=None
        )
    ) == sorted(
        [
            tmp_path / "banana.txt",
            tmp_path / "banana.py",
            tmp_path / "path/to/banana.py",
            tmp_path / "path/to/banana.c",
        ]
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
        "path/folder with space/banana.py",
        "apple.py",
        "banana.py",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()

    assert sorted(
        search_files(
            tmp_path,
            ["to"],
            filename_include_regex=search_for,
            filename_exclude_regex=None,
        )
    ) == sorted(
        [
            tmp_path / "banana.txt",
            tmp_path / "banana.py",
            tmp_path / "from/some/banana.py",
            tmp_path / "another/some/banana.py",
            tmp_path / "path/folder with space/banana.py",
        ]
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

    assert sorted(
        search_files(
            tmp_path, [], filename_include_regex=search_for, filename_exclude_regex=None
        )
    ) == sorted(
        [
            tmp_path / "banana.txt",
            tmp_path / "banana.py",
            tmp_path / "apple.py",
            tmp_path / "path/to/banana.py",
            tmp_path / "path/to/banana.c",
        ]
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

    assert sorted(
        search_files(
            tmp_path,
            [],
            filename_include_regex=search_for,
            filename_exclude_regex=re.compile(r".*\.py"),
        )
    ) == sorted([tmp_path / "banana.txt", tmp_path / "path/to/banana.c"])


def test_search_files_with_multipart_excluded_regex_with_filename(tmp_path):
    multipart_exclude_regex = re.compile(r".*\/classycle\/report\.xml")
    search_for = re.compile(r"report\.xml")
    filepaths = [
        "report.txt",
        "report.xml",
        "path/to/report.xml",
        "path/to/classycle/report.xml",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()

    assert sorted(
        search_files(
            tmp_path,
            [],
            filename_include_regex=search_for,
            filename_exclude_regex=None,
            multipart_exclude_regex=multipart_exclude_regex,
        )
    ) == sorted([tmp_path / "report.xml", tmp_path / "path/to/report.xml"])


def test_search_files_with_multipart_excluded_regex_with_foldername(tmp_path):
    multipart_exclude_regex = re.compile(r".*js\/generated\/coverage")
    search_for = re.compile(r"report\.xml")
    filepaths = [
        "report.txt",
        "report.xml",
        "js/generated/coverage/report.xml",
        "js/generated/report.xml",
        "path/to/js/generated/coverage/report.xml",
        "path/to/report.xml",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()

    assert sorted(
        search_files(
            tmp_path,
            [],
            filename_include_regex=search_for,
            filename_exclude_regex=None,
            multipart_exclude_regex=multipart_exclude_regex,
        )
    ) == sorted(
        [
            tmp_path / "report.xml",
            tmp_path / "path/to/report.xml",
            tmp_path / "js/generated/report.xml",
        ]
    )


@pytest.mark.parametrize(
    "patterns,should_match,shouldnt_match",
    [
        (
            ["*coverage*.*"],
            [
                "coverage.",
                "abc-coverage.xyz",
                "coverage.abc",
                "coverage-abc.xyz",
                "abc-coverage.",
                "ccoverage.abc",
                "ijk-coverage.abc.xyz",
            ],
            ["hoverage.", "xyz-coverage-abc"],
        ),
        (
            ["*.codecov.*", "codecov.*"],
            [
                ".codecov.",
                "codecov.",
                "abc.codecov.xyz",
                "abc.codecov.",
                "codecov.abc",
            ],
            ["codecov"],
        ),
        (
            ["?.coverage", "??.coverage", "abc"],
            ["a.coverage", "ab.coverage", "abc"],
            [".coverage", "abc.coverage", "abcz"],
        ),
        (
            ["[a-f]coverage", "[h-w]coverage"],
            ["acoverage", "ccoverage", "hcoverage", "ncoverage", "wcoverage"],
            ["gcoverage", "zcoverage", "coverage"],
        ),
        (["[!c-f]coverage"], ["acoverage"], ["coverage", "ccoverage"]),
        (
            ["lcov.info", "cover.out", "gcov.info", "jacoco*.xml", "luacov.report.out"],
            [
                "lcov.info",
                "cover.out",
                "gcov.info",
                "jacoco.xml",
                "jacocoabc.xml",
                "luacov.report.out",
            ],
            [],
        ),
    ],
)
def test_globs_to_regex_matches_expected_files(patterns, should_match, shouldnt_match):
    regex = globs_to_regex(patterns)

    # assert all(regex.match(file_name) for file_name in should_match)
    # assert all(not regex.match(file_name) for file_name in shouldnt_match)

    for file_name in should_match:
        assert regex.match(file_name)

    for file_name in shouldnt_match:
        assert not regex.match(file_name)


def test_globs_to_regex_returns_none_if_patterns_empty():
    regex = globs_to_regex([])

    assert regex is None


def test_search_directories(tmp_path):
    filename_include_regex = globs_to_regex(["*.app"])
    filepaths = [
        "banana.app/path/of/directory.txt",
        "path/to/apple.app/path/of/directories",
        "path/to/banana.app/folder/test.txt",
        "apple.py",
        "banana.py",
    ]
    for f in filepaths:
        relevant_filepath = tmp_path / f
        relevant_filepath.parent.mkdir(parents=True, exist_ok=True)
        relevant_filepath.touch()

    assert sorted(
        search_files(
            tmp_path,
            [],
            filename_include_regex=filename_include_regex,
            filename_exclude_regex=None,
            search_for_directories=True,
        )
    ) == sorted(
        [
            tmp_path / "banana.app",
            tmp_path / "path/to/banana.app",
            tmp_path / "path/to/apple.app",
        ]
    )
