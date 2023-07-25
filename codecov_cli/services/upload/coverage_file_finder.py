import logging
import os
import typing
from pathlib import Path

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files
from codecov_cli.types import UploadCollectionResultFile

logger = logging.getLogger("codecovcli")

coverage_files_patterns = [
    "*.clover",
    "*.codecov.*",
    "*.gcov",
    "*.lcov",
    "*.lst",
    "*coverage*.*",
    "*Jacoco*.xml",
    "clover.xml",
    "cobertura.xml",
    "codecov-result.json",
    "codecov.*",
    "cover.out",
    "coverage-final.json",
    "excoveralls.json",
    "gcov.info",
    "jacoco*.xml",
    "lcov.dat",
    "pylcov.dat",
    "lcov.info",
    "luacov.report.out",
    "naxsi.info",
    "nosetests.xml",
    "report.xml",
    "test_cov.xml",
]


coverage_files_excluded_patterns = [
    "*.am",
    "*.bash",
    "*.bat",
    "*.bw",
    "*.cfg",
    "*.class",
    "*.cmake",
    "*.conf",
    "*.coverage",
    "*.cp",
    "*.cpp",
    "*.crt",
    "*.css",
    "*.csv",
    "*.data",
    "*.db",
    "*.dox",
    "*.ec",
    "*.egg",
    "*.el",
    "*.env",
    "*.erb",
    "*.exe",
    "*.ftl",
    "*.gif",
    ".git*",
    "*.gradle",
    "*.gz",
    "*.h",
    "*.html",
    "*.in",
    "*.jade",
    "*.jar*",
    "*.jpeg",
    "*.jpg",
    "*.js",
    "*.less",
    "*.log",
    "*.m4",
    "*.mak*",
    "*.md",
    ".nvmrc",
    "*.o",
    "*.p12",
    "*.pem",
    "*.png",
    "*.pom*",
    "*.profdata",
    "*.proto",
    "*.ps1",
    "*.pth",
    "*.py",
    "*.pyc",
    "*.pyo",
    "*.rb",
    "*.rsp",
    "*.rst",
    "*.ru",
    "*.sbt",
    "*.scss",
    "*.serialized",
    "*.sh",
    "*.snapshot",
    "*.sql",
    "*.svg",
    "*.tar.tz",
    "*.template",
    "*.ts",
    "*.whl",
    "*.xcconfig",
    "*.xcoverage.*",
    "*/classycle/report.xml",
    "*codecov.yml",
    "*~",
    ".*coveragerc",
    ".coverage*",
    "coverage-summary.json",
    "codecov.SHA256SUM",
    "codecov.SHA256SUM.sig",
    "createdFiles.lst",
    "fullLocaleNames.lst",
    "include.lst",
    "inputFiles.lst",
    "phpunit-code-coverage.xml",
    "phpunit-coverage.xml",
    "remapInstanbul.coverage*.json",
    "scoverage.measurements.*",
    "test_*_coverage.txt",
    "test-result-*-codecoverage.json",
    "testrunner-coverage*",
    "*.*js",
    "*.map",
    "*.egg-info",
    ".ds_store",
    "*.zip",
]


default_folders_to_ignore = [
    "vendor",
    "bower_components",
    ".circleci",
    "conftest_*.c.gcov",
    ".egg-info*",
    ".env",
    ".envs",
    ".git",
    ".go",
    ".hg",
    ".map",
    ".marker",
    ".tox",
    ".venv",
    ".venvs",
    ".virtualenv",
    ".virtualenvs",
    ".yarn",
    ".yarn-cache",
    "__pycache__",
    "env",
    "envs",
    "htmlcov",
    "js/generated/coverage",
    "node_modules",
    "venv",
    "venvs",
    "virtualenv",
    "virtualenvs",
    "jspm_packages",
    ".nyc_output",
]


class CoverageFileFinder(object):
    def __init__(
        self,
        project_root: Path = None,
        folders_to_ignore: typing.List[str] = None,
        explicitly_listed_files: typing.List[Path] = None,
        disable_search: bool = False,
    ):
        self.project_root = project_root or Path(os.getcwd())
        self.folders_to_ignore = folders_to_ignore or []
        self.explicitly_listed_files = explicitly_listed_files or None
        self.disable_search = disable_search

    def find_coverage_files(self) -> typing.List[UploadCollectionResultFile]:
        regex_patterns_to_exclude = globs_to_regex(coverage_files_excluded_patterns)
        coverage_files_paths = []
        user_coverage_files_paths = []
        if self.explicitly_listed_files:
            user_coverage_files_paths = self.get_user_specified_coverage_files(
                regex_patterns_to_exclude
            )
        if not self.disable_search:
            regex_patterns_to_include = globs_to_regex(coverage_files_patterns)
            coverage_files_paths = search_files(
                self.project_root,
                default_folders_to_ignore + self.folders_to_ignore,
                filename_include_regex=regex_patterns_to_include,
                filename_exclude_regex=regex_patterns_to_exclude,
            )
        result_files = [
            UploadCollectionResultFile(path)
            for path in coverage_files_paths
            if coverage_files_paths
        ]
        user_result_files = [
            UploadCollectionResultFile(path)
            for path in user_coverage_files_paths
            if user_coverage_files_paths
        ]

        return list(set(result_files + user_result_files))

    def get_user_specified_coverage_files(self, regex_patterns_to_exclude):
        user_filenames_to_include = []
        files_excluded_but_user_includes = []
        for file in self.explicitly_listed_files:
            user_filenames_to_include.append(file.name)
            if regex_patterns_to_exclude.match(file.name):
                files_excluded_but_user_includes.append(str(file))
        if files_excluded_but_user_includes:
            logger.warning(
                "Some files being explicitly added are found in the list of excluded files for upload.",
                extra=dict(
                    extra_log_attributes=dict(files=files_excluded_but_user_includes)
                ),
            )
        regex_patterns_to_include = globs_to_regex(user_filenames_to_include)
        multipart_include_regex = globs_to_regex(
            [str(path.resolve()) for path in self.explicitly_listed_files]
        )
        user_coverage_files_paths = list(
            search_files(
                self.project_root,
                default_folders_to_ignore + self.folders_to_ignore,
                filename_include_regex=regex_patterns_to_include,
                filename_exclude_regex=regex_patterns_to_exclude,
                multipart_include_regex=multipart_include_regex,
            )
        )
        not_found_files = []
        for filepath in self.explicitly_listed_files:
            if filepath.resolve() not in user_coverage_files_paths:
                not_found_files.append(filepath)

        if not_found_files:
            logger.warning(
                "Some files were not found",
                extra=dict(extra_log_attributes=dict(not_found_files=not_found_files)),
            )

        return user_coverage_files_paths


def select_coverage_file_finder(
    root_folder_to_search, folders_to_ignore, explicitly_listed_files, disable_search
):
    return CoverageFileFinder(
        root_folder_to_search,
        folders_to_ignore,
        explicitly_listed_files,
        disable_search,
    )
