import subprocess
from pathlib import Path

from codecov_cli.services.staticanalysis.types import FileAnalysisRequest


class FileFinder(object):
    def find_files(self, folder_name, pattern):
        return [
            FileAnalysisRequest(
                actual_filepath=p, result_filename=str(p.relative_to(folder_name))
            )
            for p in folder_name.rglob(pattern)
            if not p.is_dir()
        ]


class GitFileFinder(object):
    def find_files(self, folder_name, pattern):
        res = subprocess.run(
            ["git", "-C", str(folder_name), "ls-files"], capture_output=True
        )
        return [
            FileAnalysisRequest(
                actual_filepath=f"{Path(folder_name) / x}", result_filename=x
            )
            for x in res.stdout.decode().split()
        ]

    def find_configuration_file(self, folder_name):
        return None


def select_file_finder(config):
    return FileFinder()
