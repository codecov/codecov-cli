import os
import pathlib
import subprocess
import shutil
from itertools import chain
from typing import Optional
from fnmatch import fnmatch


class GcovPlugin(object):
    def __init__(
        self,
        project_root: Optional[pathlib.Path] = None,
        patterns_to_include: list[str] = [],
        patterns_to_ignore: list[str] = [],
        extra_arguments: list[str] = [],
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

        should_ignore = lambda path: any(
            fnmatch(path, pattern) for pattern in self.patterns_to_ignore
        )

        matched_paths = (
            path for path in unfiltered_matched_paths if not should_ignore(path)
        )

        return matched_paths
