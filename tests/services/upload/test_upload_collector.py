from pathlib import Path
from unittest.mock import patch

from codecov_cli.helpers.versioning_systems import (
    GitVersioningSystem,
    NoVersioningSystem,
)
from codecov_cli.services.upload.file_finder import FileFinder
from codecov_cli.services.upload.network_finder import NetworkFinder
from codecov_cli.services.upload.upload_collector import UploadCollector
from codecov_cli.types import UploadCollectionResultFile


def test_fix_kt_files():
    kt_file = Path("tests/data/files_to_fix_examples/sample.kt")

    col = UploadCollector(None, None, None, None)

    fixes = col._produce_file_fixes([kt_file])

    assert len(fixes) == 1
    fixes_for_kt_file = fixes[0]

    assert fixes_for_kt_file.eof == 33
    assert fixes_for_kt_file.fixed_lines_without_reason == set([1, 3, 7, 9, 12, 14, 18])
    assert fixes_for_kt_file.fixed_lines_with_reason == set(
        [
            (20, "    /*\n"),
            (25, "*/\n"),
        ]
    )


def test_fix_go_files():
    go_file = Path("tests/data/files_to_fix_examples/sample.go")

    col = UploadCollector(None, None, None, None)

    fixes = col._produce_file_fixes([go_file])

    assert len(fixes) == 1
    fixes_for_go_file = fixes[0]

    assert fixes_for_go_file.eof is None
    assert fixes_for_go_file.fixed_lines_without_reason == set(
        [1, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 26]
    )
    assert fixes_for_go_file.fixed_lines_with_reason == set(
        [
            (21, "/*\n"),
            (24, "	/*\n"),
            (25, "	*/\n"),
            (23, "*/\n"),
        ]
    )


@patch("codecov_cli.services.upload.upload_collector.open")
def test_fix_bad_encoding_files(mock_open):
    mock_open.side_effect = UnicodeDecodeError("", bytes(), 0, 0, "")
    go_file = Path("tests/data/files_to_fix_examples/bad_encoding.go")

    col = UploadCollector(None, None, None, None)

    fixes = col._produce_file_fixes([go_file])
    assert len(fixes) == 1
    fixes_for_go_file = fixes[0]
    assert fixes_for_go_file.eof is None
    assert fixes_for_go_file.fixed_lines_without_reason == set([])
    assert fixes_for_go_file.fixed_lines_with_reason == set([])


def test_fix_php_files():
    php_file = Path("tests/data/files_to_fix_examples/sample.php")

    col = UploadCollector(None, None, None, None)

    fixes = col._produce_file_fixes([php_file])

    assert len(fixes) == 1
    fixes_for_php_file = fixes[0]

    assert fixes_for_php_file.eof is None
    assert fixes_for_php_file.fixed_lines_without_reason == set([8, 17, 4, 12])
    assert fixes_for_php_file.fixed_lines_with_reason == set([])


def test_can_read_unicode_file():
    col = UploadCollector(None, None, None, None, True)

    php_file = Path("tests/data/Контроллеры/Пользователь/ГлавныйКонтроллер.php")
    _fixes = col._produce_file_fixes([php_file])
    # we just want to assert that this is not throwing an error related to file encoding,
    # see <https://github.com/codecov/codecov-action/issues/1539>


def test_fix_for_cpp_swift_vala(tmp_path):
    cpp_file = Path("tests/data/files_to_fix_examples/sample.cpp")

    col = UploadCollector(None, None, None, None)

    fixes = col._produce_file_fixes([cpp_file])

    assert len(fixes) == 1
    fixes_for_cpp_file = fixes[0]

    assert fixes_for_cpp_file.eof is None
    assert fixes_for_cpp_file.fixed_lines_without_reason == set([1, 2, 3, 4, 9, 10, 11])
    assert fixes_for_cpp_file.fixed_lines_with_reason == set(
        [
            (8, "// LCOV_EXCL_END\n"),
            (13, "// LCOV_EXCL_STOP\n"),
            (5, "// LCOV_EXCL_BEGIN\n"),
            (7, "// LCOV_EXCL_START\n"),
        ]
    )


def test_fix_when_disabled_fixes(tmp_path):
    cpp_file = Path("tests/data/files_to_fix_examples/sample.cpp")

    col = UploadCollector(None, None, None, None, True)

    fixes = col._produce_file_fixes([cpp_file])

    assert len(fixes) == 0
    assert fixes == []


def test_generate_upload_data(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "subsub").mkdir()
    (tmp_path / "node_modules").mkdir()

    should_find = [
        "abc-coverage.cov",
        "coverage-abc.abc",
        "sub/coverage-abc.abc",
        "sub/subsub/coverage-abc.abc",
        "coverage.abc",
        "jacocoxyz.xml",
        "sub/jacocoxyz.xml",
        "codecov.abc",
        "sub/subsub/codecov.abc",
        "xyz.codecov.abc",
        "sub/xyz.codecov.abc",
        "sub/subsub/xyz.codecov.abc",
        "cover.out",
        "abc.gcov",
        "sub/abc.gcov",
        "sub/subsub/abc.gcov",
    ]

    should_ignore = [
        "abc.codecov.exe",
        "sub/abc.codecov.exe",
        "codecov.exe",
        "__pycache__",
        "sub/subsub/__pycache__",
        ".gitignore",
        "a.sql",
        "a.csv",
        ".abc-coveragerc",
        ".coverage-xyz",
        "sub/scoverage.measurements.xyz",
        "sub/test_abcd_coverage.txt",
        "test-result-ff-codecoverage.json",
        "node_modules/abc-coverage.cov",
    ]

    for filename in should_find:
        (tmp_path / filename).touch()

    for filename in should_ignore:
        (tmp_path / filename).touch()

    file_finder = FileFinder(tmp_path)

    network_finder = NetworkFinder(GitVersioningSystem(), False, None, None, None)

    collector = UploadCollector([], network_finder, file_finder, None)

    res = collector.generate_upload_data()

    expected = {UploadCollectionResultFile(tmp_path / file) for file in should_find}

    for file in expected:
        assert file in res.files


@patch("codecov_cli.services.upload.upload_collector.logger")
def test_generate_upload_data_with_none_network(mock_logger, tmp_path):
    (tmp_path / "coverage.xml").touch()

    file_finder = FileFinder(tmp_path)
    network_finder = NetworkFinder(NoVersioningSystem(), False, None, None, None)

    collector = UploadCollector([], network_finder, file_finder, {})

    res = collector.generate_upload_data()

    mock_logger.debug.assert_any_call("Collecting relevant files")

    mock_logger.info.assert_any_call("Found 1 coverage files to report")
    mock_logger.info.assert_any_call("> {}".format(tmp_path / "coverage.xml"))

    assert len(res.network) > 1
    assert len(res.files) == 1
    assert len(res.file_fixes) > 1


def test_generate_network_with_no_versioning_system(tmp_path):
    versioning_system = NoVersioningSystem()
    found_files = versioning_system.list_relevant_files()
    assert len(found_files) > 1

    found_files = versioning_system.list_relevant_files(tmp_path)
    assert len(found_files) == 0

    (tmp_path / "coverage.xml").touch()
    found_files = versioning_system.list_relevant_files(tmp_path)
    assert len(found_files) == 1
