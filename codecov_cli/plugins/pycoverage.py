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


class PycoverageConfig(dict):
    @property
    def project_root(self) -> typing.Optional[pathlib.Path]:
        """
        The project root to search for coverage files.
        project_root: pathlib.Path [default os.getcwd()]
        """
        return self.get("project_root", pathlib.Path(os.getcwd()))

    @property
    def report_type(self) -> str:
        """
        Report type to generate.
        Overrided if include_contexts == True
        report_type: str [values xml|json; default xml]
        """
        return self.get("report_type", "xml")

    @property
    def path_to_coverage_file(self) -> str:
        """
        The coverage dir with .coverage file
        If set, will not look search for coverage files
        """
        return self.get("path_to_coverage_file", None)

    @property
    def include_contexts(self) -> bool:
        """
        Includes test context in JSON report. Flag.
        (test contexts are the test labels used in ATS)
        include_contexts: bool [default True]
        """
        return self.get("include_contexts", True)


class Pycoverage(object):
    def __init__(self, config: dict):
        self.config = PycoverageConfig(config)

    def run_preparation(self, collector) -> PreparationPluginReturn:

        if shutil.which("coverage") is None:
            logger.warning("coverage.py is not installed or can't be found.")
            return

        path_to_coverage_data = self._get_path_to_coverage()
        if path_to_coverage_data is None:
            logger.warning("No coverage data found to transform")
            return
        coverage_dir = pathlib.Path(path_to_coverage_data).parent
        if self.config.report_type == "xml":
            return self._generate_XML_report(coverage_dir)
        if self.config.report_type == "json":
            return self._generate_JSON_report(coverage_dir)
        return PreparationPluginReturn(
            success=False, messages=[f"report type {self.config.report_type} unknown"]
        )

    def _get_path_to_coverage(self) -> pathlib.Path:
        if self.config.path_to_coverage_file:
            path = pathlib.Path(self.config.path_to_coverage_file)
            if path.exists():
                return pathlib.Path(self.config.path_to_coverage_file)
            logger.warning(
                f"Dir {self.config.path_to_coverage_file} doesn't exist or doesn't have .coverage file. Falling back to search"
            )
        return next(
            search_files(
                self.config.project_root,
                [],
                filename_include_regex=coverage_files_regex,
                filename_exclude_regex=None,
            ),
            None,
        )

    def _generate_XML_report(self, dir: pathlib.Path) -> PreparationPluginReturn:
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
        return PreparationPluginReturn(success=True, messages=[])

    def _generate_JSON_report(self, dir: pathlib.Path):
        if (dir / ".coverage").exists():
            logger.info(
                f"Generating JSON report in {dir}",
                extra=dict(
                    extra_log_attributes=dict(
                        include_contexts=self.config.include_contexts
                    )
                ),
            )
            command = ["coverage", "json"]
            if self.config.include_contexts:
                command.append("--show-contexts")
            completed_process = subprocess.run(command, cwd=dir, capture_output=True)

            output = completed_process.stdout.decode().strip()
            logger.info(output)
            return PreparationPluginReturn(success=True, messages=[])
        logger.warning(f".coverage file not found at {dir}. Parsing failed")
        return PreparationPluginReturn(
            success=False, messages=[f".coverage file not found at {dir}."]
        )
