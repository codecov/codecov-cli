import os
import pathlib
import re
import typing
from fnmatch import fnmatch, translate


def search_files(
    folder_to_search: pathlib.Path,
    folders_to_ignore: typing.List[str],
    filename_include_regex: typing.Pattern,
    *,
    filename_exclude_regex: typing.Optional[typing.Pattern],
) -> typing.Generator[pathlib.Path, None, None]:
    yield from ()


def globs_to_regex(patterns: typing.List[str]) -> typing.Pattern:
    """
    Converts a list of glob patterns to a combined ORed regex
    """
    regex_str = ["(" + translate(pattern) + ")" for pattern in patterns]
    return re.compile("|".join(regex_str))
