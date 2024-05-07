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

test_results_files_patterns = [
    "*junit.xml",
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

test_results_files_excluded_patterns = (
    coverage_files_patterns + coverage_files_excluded_patterns
)


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


class FileFinder(object):
    def __init__(
        self,
        search_root: Path = None,
        folders_to_ignore: typing.List[str] = None,
        explicitly_listed_files: typing.List[Path] = None,
        disable_search: bool = False,
        report_type: str = "coverage",
    ):
        self.search_root = search_root or Path(os.getcwd())
        self.folders_to_ignore = folders_to_ignore or []
        self.explicitly_listed_files = explicitly_listed_files or None
        self.disable_search = disable_search
        self.report_type = report_type

    def find_files(self) -> typing.List[UploadCollectionResultFile]:
        if self.report_type == "coverage":
            files_excluded_patterns = coverage_files_excluded_patterns
            files_patterns = coverage_files_patterns
        elif self.report_type == "test_results":
            files_excluded_patterns = test_results_files_excluded_patterns
            files_patterns = test_results_files_patterns
        regex_patterns_to_exclude = globs_to_regex(files_excluded_patterns)
        files_paths = []
        user_files_paths = []
        if self.explicitly_listed_files:
            user_files_paths = self.get_user_specified_files(regex_patterns_to_exclude)
        if not self.disable_search:
            regex_patterns_to_include = globs_to_regex(files_patterns)
            files_paths = search_files(
                self.search_root,
                default_folders_to_ignore + self.folders_to_ignore,
                filename_include_regex=regex_patterns_to_include,
                filename_exclude_regex=regex_patterns_to_exclude,
            )
        result_files = [
            UploadCollectionResultFile(path) for path in files_paths if files_paths
        ]
        user_result_files = [
            UploadCollectionResultFile(path)
            for path in user_files_paths
            if user_files_paths
        ]

        return list(set(result_files + user_result_files))

    def get_user_specified_files(self, regex_patterns_to_exclude):
        user_filenames_to_include = []
        files_excluded_but_user_includes = []
        for file in self.explicitly_listed_files:
            user_filenames_to_include.append(file.name)
            if regex_patterns_to_exclude.match(file.name):
                files_excluded_but_user_includes.append(str(file))
        if files_excluded_but_user_includes:
            logger.warning(
                "Some files being explicitly added are found in the list of excluded files for upload. We are still going to search for the explicitly added files.",
                extra=dict(
                    extra_log_attributes=dict(files=files_excluded_but_user_includes)
                ),
            )
        regex_patterns_to_include = globs_to_regex(user_filenames_to_include)
        multipart_include_regex = globs_to_regex(
            [str(path.resolve()) for path in self.explicitly_listed_files]
        )
        user_files_paths = list(
            search_files(
                self.search_root,
                self.folders_to_ignore,
                filename_include_regex=regex_patterns_to_include,
                multipart_include_regex=multipart_include_regex,
            )
        )
        not_found_files = []
        user_files_paths_resolved = [path.resolve() for path in user_files_paths]
        for filepath in self.explicitly_listed_files:
            if filepath.resolve() not in user_files_paths_resolved:
                ## The file given might be linked or in a parent dir, check to see if it exists
                if filepath.exists():
                    user_files_paths.append(filepath)
                else:
                    not_found_files.append(filepath)

        if not_found_files:
            logger.warning(
                "Some files were not found",
                extra=dict(extra_log_attributes=dict(not_found_files=not_found_files)),
            )

        return user_files_paths


def select_file_finder(
    root_folder_to_search,
    folders_to_ignore,
    explicitly_listed_files,
    disable_search,
    report_type="coverage",
):
    return FileFinder(
        root_folder_to_search,
        folders_to_ignore,
        explicitly_listed_files,
        disable_search,
        report_type,
    )
