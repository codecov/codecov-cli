import os
import shutil
import subprocess
from glob import iglob
import pathlib
import typing

class Pycoverage(object):
    def __init__(self, project_root: typing.Optional[pathlib.Path] = None):
        self.project_root = project_root or pathlib.Path(os.getcwd())

    def run_preparation(self, collector):
        print("Running coverage.py plugin...")

        if shutil.which("coverage") is None:
            print("coverage.py is not installed or can't be found.")
            print("aborting coverage.py plugin...")
            return

        # This might need optimization
        path_to_coverage_data = next(
            iglob(os.path.join(self.project_root, "**/.coverage"), recursive=True), None
        ) or next(
            iglob(os.path.join(self.project_root, "**/.coverage.*"), recursive=True),
            None,
        )


        if path_to_coverage_data is None:
            print("No coverage data found.")
            print("aborting coverage.py plugin...")
            return

        coverage_data_directory = pathlib.Path(path_to_coverage_data).parent
        self._generate_XML_report(coverage_data_directory)

        print("aborting coverage.py plugin...")

    def _generate_XML_report(self, dir):
        """Generates up-to-date XML report in the given directory"""

        # the following if conditions avoid creating dummy .coverage file

        if next(iglob(os.path.join(dir, ".coverage.*")), None) is not None:
            print(f"Running coverage combine -a in {dir}")
            subprocess.run(["coverage", "combine", "-a"], cwd=dir)

        if os.path.exists(os.path.join(dir, ".coverage")):
            print(f"Generating coverage.xml report in {dir}")
            completed_process = subprocess.run(
                ["coverage", "xml", "-i"], cwd=dir, capture_output=True
            )

            output = completed_process.stdout.decode().strip()
            print(output)
