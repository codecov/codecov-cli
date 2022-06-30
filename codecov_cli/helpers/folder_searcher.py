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
    multipart_include_regex: typing.Optional[typing.Pattern] = None,
    multipart_exclude_regex: typing.Optional[typing.Pattern] = None,
) -> typing.Generator[pathlib.Path, None, None]:
    for (dirpath, dirnames, filenames) in os.walk(folder_to_search):
        dirs_to_remove = set(d for d in dirnames if d in folders_to_ignore)

        if multipart_exclude_regex is not None:
            dirs_to_remove.union(
                dir
                for dir in dirnames
                if multipart_exclude_regex.search(str(pathlib.Path(dirpath) / dir))
            )

        for directory in dirs_to_remove:
            # Removing to ensure we don't even try to search those
            # This is the documented way of doing this on python docs
            dirnames.remove(directory)

        is_excluded = lambda file_path: (
            filename_exclude_regex is not None
            and filename_exclude_regex.match(file_path.name)
        ) or (
            multipart_exclude_regex is not None
            and multipart_exclude_regex.search(str(file_path))
        )

        is_included = lambda file_path: (
            filename_include_regex.match(file_path.name)
            or (
                multipart_include_regex is not None
                and multipart_include_regex.search(str(file_path))
            )
        )
        for single_filename in filenames:
            file_path = pathlib.Path(dirpath) / single_filename
            if not is_excluded(file_path) and is_included(file_path):
                yield file_path


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
