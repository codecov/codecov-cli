import os
import pathlib
import shutil
import subprocess
import typing
from fnmatch import fnmatch
from itertools import chain

import click

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files


class GcovPlugin(object):
    def __init__(
        self,
        project_root: typing.Optional[pathlib.Path] = None,
        patterns_to_include: typing.Optional[typing.List[str]] = None,
        patterns_to_ignore: typing.Optional[typing.List[str]] = None,
        folders_to_ignore: typing.Optional[typing.List[str]] = None,
        extra_arguments: typing.Optional[typing.List[str]] = None,
    ):
        self.project_root = project_root or pathlib.Path(os.getcwd())
        self.patterns_to_include = patterns_to_include or []
        self.patterns_to_ignore = patterns_to_ignore or []
        self.folders_to_ignore = folders_to_ignore or []
        self.extra_arguments = extra_arguments or []

    def run_preparation(self, collector):
        click.echo("Running gcov plugin...")

        if shutil.which("gcov") is None:
            click.echo("gcov is not installed or can't be found.")
            click.echo("aborting gcov plugin...")
            return

        filename_include_regex = globs_to_regex(["*.gcno", *self.patterns_to_include])
        filename_exclude_regex = globs_to_regex(self.patterns_to_ignore)

        matched_paths = [
            str(path)
            for path in search_files(
                self.project_root,
                self.folders_to_ignore,
                filename_include_regex,
                filename_exclude_regex=filename_exclude_regex,
            )
        ]

        if not matched_paths:
            click.echo("No gcov data found.")
            click.echo("aborting gcov plugin...")
            return

        click.echo("Running gcov on the following list of files:")
        for path in matched_paths:
            click.echo(path)

        s = subprocess.run(
            ["gcov", "-pb", *self.extra_arguments, *matched_paths],
            cwd=self.project_root,
            capture_output=True,
        )

        click.echo("aborting gcov plugin...")
        return s
