import pytest

from codecov_cli.upload_collector import UploadCollector
from tests.data import files_to_fix_examples


def test_fix_kt_files(tmp_path):
    kt_file = tmp_path / "abc.kt"
    kt_file.write_text(files_to_fix_examples.kt_file)

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(kt_file)])

    assert len(fixes) == 1
    fixes_for_kt_file = fixes[0]

    lines = files_to_fix_examples.kt_file.splitlines(keepends=True)

    assert fixes_for_kt_file.eof == 30
    assert fixes_for_kt_file.fixed_lines_without_reason == set([1, 3, 7, 9, 12, 14])
    assert fixes_for_kt_file.fixed_lines_with_reason == set(
        [
            (22, lines[21]),
            (17, lines[16]),
        ]
    )


def test_fix_go_files(tmp_path):
    go_file = tmp_path / "abc.go"
    go_file.write_text(files_to_fix_examples.go_file)

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(go_file)])

    assert len(fixes) == 1
    fixes_for_go_file = fixes[0]

    lines = files_to_fix_examples.go_file.splitlines(keepends=True)

    assert fixes_for_go_file.eof is None
    assert fixes_for_go_file.fixed_lines_without_reason == set(
        [1, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 26]
    )
    assert fixes_for_go_file.fixed_lines_with_reason == set(
        [
            (21, lines[20]),
            (25, lines[24]),
            (24, lines[23]),
            (23, lines[22]),
        ]
    )


def test_fix_php_files(tmp_path):
    php_file = tmp_path / "abc.php"
    php_file.write_text(files_to_fix_examples.php_file)

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(php_file)])

    assert len(fixes) == 1
    fixes_for_php_file = fixes[0]

    lines = files_to_fix_examples.php_file.splitlines(keepends=True)

    assert fixes_for_php_file.eof is None
    assert fixes_for_php_file.fixed_lines_without_reason == set([8, 17, 4, 12])
    assert fixes_for_php_file.fixed_lines_with_reason == set([])


def test_fix_for_cpp_swift_vala(tmp_path):
    cpp_file = tmp_path / "abc.cpp"
    cpp_file.write_text(files_to_fix_examples.cpp_file)

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(cpp_file)])

    assert len(fixes) == 1
    fixes_for_cpp_file = fixes[0]

    lines = files_to_fix_examples.cpp_file.splitlines(keepends=True)

    assert fixes_for_cpp_file.eof is None
    assert fixes_for_cpp_file.fixed_lines_without_reason == set([1, 2, 3, 4, 9, 10, 11])
    assert fixes_for_cpp_file.fixed_lines_with_reason == set(
        [
            (8, lines[7]),
            (13, lines[12]),
            (5, lines[4]),
            (7, lines[6]),
        ]
    )
