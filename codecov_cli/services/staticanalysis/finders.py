import subprocess
from pathlib import Path

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files
from codecov_cli.services.staticanalysis.types import FileAnalysisRequest


class FileFinder(object):
    def find_files(self, root_folder, pattern, exclude_folders):
        regex_patterns_to_include = globs_to_regex(
            [
                pattern,
            ]
        )
        exclude_folders = list(map(str, exclude_folders))
        files_paths = search_files(
            folder_to_search=root_folder,
            folders_to_ignore=exclude_folders,
            filename_include_regex=regex_patterns_to_include,
        )

        return [
            FileAnalysisRequest(
                actual_filepath=p, result_filename=str(p.relative_to(root_folder))
            )
            for p in files_paths
        ]


class GitFileFinder(object):
    def find_files(self, folder_name, pattern, exclude_folders):
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
