import os
import pathlib
import shutil
import subprocess
import typing
from glob import iglob

import click

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files


class Pycoverage(object):
    def __init__(self, project_root: typing.Optional[pathlib.Path] = None):
        self.project_root = project_root or pathlib.Path(os.getcwd())

    def run_preparation(self, collector):
        click.echo("Running coverage.py plugin...")

        if shutil.which("coverage") is None:
            click.echo("coverage.py is not installed or can't be found.")
            click.echo("aborting coverage.py plugin...")
            return

        patterns_regex = globs_to_regex([".coverage", ".coverage.*"])
        path_to_coverage_data = next(
            search_files(
                self.project_root, [], patterns_regex, filename_exclude_regex=None
            ),
            None,
        )

        if path_to_coverage_data is None:
            click.echo("No coverage data found.")
            click.echo("aborting coverage.py plugin...")
            return

        coverage_data_directory = pathlib.Path(path_to_coverage_data).parent
        self._generate_XML_report(coverage_data_directory)

        click.echo("aborting coverage.py plugin...")

    def _generate_XML_report(self, dir):
        """Generates up-to-date XML report in the given directory"""

        # the following if conditions avoid creating dummy .coverage file

        if next(iglob(os.path.join(dir, ".coverage.*")), None) is not None:
            click.echo(f"Running coverage combine -a in {dir}")
            subprocess.run(["coverage", "combine", "-a"], cwd=dir)

        if os.path.exists(os.path.join(dir, ".coverage")):
            click.echo(f"Generating coverage.xml report in {dir}")
            completed_process = subprocess.run(
                ["coverage", "xml", "-i"], cwd=dir, capture_output=True
            )

            output = completed_process.stdout.decode().strip()
            click.echo(output)
