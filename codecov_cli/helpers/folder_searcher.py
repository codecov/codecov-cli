import functools
import logging
import os
import pathlib
import re
from typing import Generator, List, Optional, Pattern

from codecov_cli.helpers.glob import translate

logger = logging.getLogger("codecovcli")


def _is_included(
    filename_include_regex: Pattern,
    multipart_include_regex: Optional[Pattern],
    path: pathlib.Path,
):
    return filename_include_regex.match(path.name) and (
        multipart_include_regex is None
        or multipart_include_regex.match(path.resolve().as_posix())
    )


def _is_excluded(
    filename_exclude_regex: Optional[Pattern],
    multipart_exclude_regex: Optional[Pattern],
    path: pathlib.Path,
):
    return (
        filename_exclude_regex is not None and filename_exclude_regex.match(path.name)
    ) or (
        multipart_exclude_regex is not None
        and multipart_exclude_regex.match(path.as_posix())
    )


def search_files(
    folder_to_search: pathlib.Path,
    folders_to_ignore: List[str],
    *,
    filename_include_regex: Pattern,
    filename_exclude_regex: Optional[Pattern] = None,
    multipart_include_regex: Optional[Pattern] = None,
    multipart_exclude_regex: Optional[Pattern] = None,
    search_for_directories: bool = False,
) -> Generator[pathlib.Path, None, None]:
    """ "
    Searches for files or directories in a given folder

    Parameters:
        folder_to_search (pathlib.Path): in which folder you want the search to be
        folders_to_ignore (list of str): what folders inside the folder_to_search to ignore and not search inside
        filename_include_regex (regex): Regex for filenames only, this does not include the full path of the file
        filename_exclude_regex (regex): Regex for filenames only, this does not include the full path of the file
        multipart_include_regex (regex): Regex for full path of the files you want to include
        multipart_exclude_regex (regex): Regex for full path of the files you want to exclude
        search_for_directories (bool)

    """
    this_is_included = functools.partial(
        _is_included, filename_include_regex, multipart_include_regex
    )
    this_is_excluded = functools.partial(
        _is_excluded, filename_exclude_regex, multipart_exclude_regex
    )
    for dirpath, dirnames, filenames in os.walk(folder_to_search):
        dirs_to_remove = set(d for d in dirnames if d in folders_to_ignore)

        if multipart_exclude_regex is not None:
            dirs_to_remove.union(
                directory
                for directory in dirnames
                if multipart_exclude_regex.match(
                    (pathlib.Path(dirpath) / directory).as_posix()
                )
            )

        for directory in dirs_to_remove:
            # Removing to ensure we don't even try to search those
            # This is the documented way of doing this on python docs
            dirnames.remove(directory)

        if search_for_directories:
            for directory in dirnames:
                dir_path = pathlib.Path(dirpath) / directory
                if not this_is_excluded(dir_path) and this_is_included(dir_path):
                    yield dir_path
        else:
            for single_filename in filenames:
                file_path = pathlib.Path(dirpath) / single_filename
                if not this_is_excluded(file_path) and this_is_included(file_path):
                    yield file_path


def globs_to_regex(patterns: List[str]) -> Optional[Pattern]:
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

    regex_patterns = []
    for pattern in patterns:
        regex_pattern = translate(pattern, recursive=True, include_hidden=True)
        logger.debug(f"Translating `{pattern}` into `{regex_pattern}`")
        regex_patterns.append(regex_pattern)
    return re.compile("|".join(regex_patterns))
