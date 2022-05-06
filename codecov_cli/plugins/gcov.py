import os
import pathlib
import shutil
import subprocess
import typing
from fnmatch import fnmatch
from itertools import chain


class GcovPlugin(object):
    def __init__(
        self,
        project_root: typing.Optional[pathlib.Path] = None,
        patterns_to_include: typing.List[str] = [],
        patterns_to_ignore: typing.List[str] = [],
        extra_arguments: typing.List[str] = [],
    ):
        self.project_root = project_root or pathlib.Path(os.getcwd())
        self.patterns_to_include = patterns_to_include
        self.patterns_to_ignore = patterns_to_ignore
        self.extra_arguments = extra_arguments

    def run_preparation(self, collector):
        if shutil.which("gcov") is None:
            return None

        matched_paths = self._get_matched_paths()

        s = subprocess.run(
            ["gcov", "-pb", *self.extra_arguments, *matched_paths],
            cwd=self.project_root,
            capture_output=True,
        )

        return s

    def _get_matched_paths(self):
        # This method might need a lot of optimization

        unfiltered_matched_paths = chain(
            *(
                self.project_root.rglob(pattern)
                for pattern in ["*.gcno", *self.patterns_to_include]
            )
        )

        # !This is not accurate since fnmatch doesn't use the same rules for globbing as glob.glob or Path.glob
        # !This will result in some weird pattern matching like this one
        # path = Path("codecov-dev/a/b/hello.json")
        # fnmatch(path, "codecov-*.json") => True

        should_ignore = lambda path: any(
            fnmatch(path, pattern) for pattern in self.patterns_to_ignore
        )

        matched_paths = (
            path for path in unfiltered_matched_paths if not should_ignore(path)
        )

        return matched_paths
