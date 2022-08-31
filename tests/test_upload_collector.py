from pathlib import Path

from codecov_cli.services.legacy_upload.upload_collector import UploadCollector


def test_fix_kt_files():
    kt_file = Path("tests/data/files_to_fix_examples/sample.kt")

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(kt_file)])

    assert len(fixes) == 1
    fixes_for_kt_file = fixes[0]

    assert fixes_for_kt_file.eof == 30
    assert fixes_for_kt_file.fixed_lines_without_reason == set([1, 3, 7, 9, 12, 14])
    assert fixes_for_kt_file.fixed_lines_with_reason == set(
        [
            (17, "    /*\n"),
            (22, "*/\n"),
        ]
    )


def test_fix_go_files():
    go_file = Path("tests/data/files_to_fix_examples/sample.go")

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(go_file)])

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


def test_fix_php_files():
    php_file = Path("tests/data/files_to_fix_examples/sample.php")

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(php_file)])

    assert len(fixes) == 1
    fixes_for_php_file = fixes[0]

    assert fixes_for_php_file.eof is None
    assert fixes_for_php_file.fixed_lines_without_reason == set([8, 17, 4, 12])
    assert fixes_for_php_file.fixed_lines_with_reason == set([])


def test_fix_for_cpp_swift_vala(tmp_path):
    cpp_file = Path("tests/data/files_to_fix_examples/sample.cpp")

    col = UploadCollector(None, None, None)

    fixes = col._produce_file_fixes_for_network([str(cpp_file)])

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
