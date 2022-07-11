import logging
import os
import pathlib
import shutil
import subprocess
import typing
from glob import iglob

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files
from codecov_cli.plugins.types import PreparationPluginReturn

coverage_files_regex = globs_to_regex([".coverage", ".coverage.*"])
logger = logging.getLogger("codecovcli")


class Pycoverage(object):
    def __init__(self, project_root: typing.Optional[pathlib.Path] = None):
        self.project_root = project_root or pathlib.Path(os.getcwd())

    def run_preparation(self, collector) -> PreparationPluginReturn:
        logger.debug("Running coverage.py plugin...")

        if shutil.which("coverage") is None:
            logger.warning("coverage.py is not installed or can't be found.")
            return

        path_to_coverage_data = next(
            search_files(
                self.project_root,
                [],
                filename_include_regex=coverage_files_regex,
                filename_exclude_regex=None,
            ),
            None,
        )

        if path_to_coverage_data is None:
            logger.warning("No coverage data found to transform")
            return

        coverage_data_directory = pathlib.Path(path_to_coverage_data).parent
        self._generate_XML_report(coverage_data_directory)

        return PreparationPluginReturn(success=True, messages=[])

    def _generate_XML_report(self, dir: pathlib.Path):
        """Generates up-to-date XML report in the given directory"""

        # the following if conditions avoid creating dummy .coverage file

        if next(iglob(str(dir / ".coverage.*")), None) is not None:
            logger.info(f"Running coverage combine -a in {dir}")
            subprocess.run(["coverage", "combine", "-a"], cwd=dir)

        if (dir / ".coverage").exists():
            logger.info(f"Generating coverage.xml report in {dir}")
            completed_process = subprocess.run(
                ["coverage", "xml", "-i"], cwd=dir, capture_output=True
            )

            output = completed_process.stdout.decode().strip()
            logger.info(output)
