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


def globs_to_regex(patterns: typing.List[str]) -> typing.Optional[typing.Pattern]:
    """
    Converts a list of glob patterns to a combined ORed regex
    
    Parameters:
        patterns (List[str]): a list of globs, possibly empty

    Returns:
        (Pattern): a combined ORed regex, or None if patterns is an empty list
    """
    # if patterns is an empty list, avoid returning re.compile("") since it matches everything
    if not patterns:
        return None
    
    regex_str = ["(" + translate(pattern) + ")" for pattern in patterns]
    return re.compile("|".join(regex_str))
