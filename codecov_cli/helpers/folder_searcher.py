import os
import pathlib
import re
import typing
from fnmatch import translate


def search_files(
    folder_to_search: pathlib.Path,
    folders_to_ignore: typing.List[str],
    filename_include_regex: typing.Pattern,
    *,
    filename_exclude_regex: typing.Optional[typing.Pattern],
) -> typing.Generator[pathlib.Path, None, None]:
    for (dirpath, dirnames, filenames) in os.walk(folder_to_search):
        dirs_to_remove = set(d for d in dirnames if d in folders_to_ignore)
        for directory in dirs_to_remove:
            # Removing to ensure we don't even try to search those
            # This is the documented way of doing this on python docs
            dirnames.remove(directory)
        for single_filename in filenames:
            if filename_include_regex.match(single_filename) and (
                filename_exclude_regex is None
                or not filename_exclude_regex.match(single_filename)
            ):
                yield pathlib.Path(dirpath) / single_filename


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
