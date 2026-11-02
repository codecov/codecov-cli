"""Collect explicit coverage markers from D line comments.

This is deliberately not a D parser. Token/delimited strings are skipped
conservatively by returning no fixes for the file.
"""

import re

_MARKER = re.compile(r"//\s+LCOV_EXCL_(LINE|START|STOP|END)\b")


def d_exclusion_markers(source: str) -> set[tuple[int, str]]:
    markers = set()
    index, line = 0, 1
    quote = None
    raw = False
    block = False
    nested = 0
    while index < len(source):
        char = source[index]
        pair = source[index : index + 2]
        if char == "\n":
            line += 1
        if block:
            if pair == "*/":
                block = False
                index += 2
                continue
        elif nested:
            if pair == "/+":
                nested += 1
                index += 2
                continue
            if pair == "+/":
                nested -= 1
                index += 2
                continue
        elif quote:
            if char == "\\" and not raw:
                # Escapes cannot start comments or close a quoted literal.
                if index + 1 < len(source) and source[index + 1] == "\n":
                    line += 1
                index += 2
                continue
            if char == quote:
                quote = None
        elif pair == "//":
            end = source.find("\n", index)
            if end < 0:
                end = len(source)
            match = _MARKER.match(source[index:end])
            if match:
                # Only send the marker, not explanatory text that might name
                # another marker and confuse legacy block expansion.
                markers.add((line, "// LCOV_EXCL_" + match[1] + "\n"))
            index = end
            continue
        elif pair == "/*":
            block = True
            index += 2
            continue
        elif pair == "/+":
            nested = 1
            index += 2
            continue
        elif pair in ('q"', "q{"):
            # D token/delimited strings require a fuller lexer. Never risk
            # treating their contents as instructions to exclude real code.
            return set()
        elif pair == 'r"':
            quote, raw = '"', True
            index += 2
            continue
        elif char in ('"', "'", "`"):
            quote, raw = char, char == "`"
        index += 1
    return markers
