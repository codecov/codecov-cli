import pytest

from codecov_cli.services.upload.d_file_fixes import d_exclusion_markers


@pytest.mark.parametrize(
    "literal",
    [
        '"// LCOV_EXCL_LINE"',
        '"escaped \\" // LCOV_EXCL_LINE"',
        "`// LCOV_EXCL_LINE`",
        'r"// LCOV_EXCL_LINE"',
        '"first\n// LCOV_EXCL_START\nlast"',
        "`first\n// LCOV_EXCL_START\nlast`",
    ],
)
def test_markers_in_strings_are_not_exclusions(literal):
    assert d_exclusion_markers(f"auto text = {literal};\n") == set()


@pytest.mark.parametrize(
    "comment",
    [
        "/*\n// LCOV_EXCL_START\n*/",
        "/+ outer /+ inner +/\n// LCOV_EXCL_START\n+/",
    ],
)
def test_markers_in_block_comments_are_not_exclusions(comment):
    assert d_exclusion_markers(comment) == set()


@pytest.mark.parametrize("ending", ["STOP", "END"])
def test_line_and_block_markers(ending):
    source = (
        'auto text = "// LCOV_EXCL_START"; // LCOV_EXCL_LINE reason\r\n'
        "keep();\r\n"
        "    // LCOV_EXCL_START\r\n"
        "excluded();\r\n"
        f"    // LCOV_EXCL_{ending}"
    )
    assert d_exclusion_markers(source) == {
        (1, "// LCOV_EXCL_LINE\n"),
        (3, "// LCOV_EXCL_START\n"),
        (5, f"// LCOV_EXCL_{ending}\n"),
    }


def test_explanation_cannot_open_a_block():
    assert d_exclusion_markers("return; // LCOV_EXCL_LINE unlike LCOV_EXCL_START") == {
        (1, "// LCOV_EXCL_LINE\n")
    }


@pytest.mark.parametrize(
    "source", ['auto text = q"[text]";', "auto text = q{ int n; };"]
)
def test_token_strings_disable_exclusions_conservatively(source):
    assert d_exclusion_markers("// LCOV_EXCL_START\n" + source) == set()


def test_character_literal_and_invalid_marker():
    assert d_exclusion_markers(
        "auto c = '\\''; // LCOV_EXCL_LINE\n// LCOV_EXCL_LINES\n"
    ) == {(1, "// LCOV_EXCL_LINE\n")}
