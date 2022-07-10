import os
import typing
from pathlib import Path

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files
from codecov_cli.types import UploadCollectionResultFile

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
    ".gitignore",
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
]


default_folders_to_ignore = [
    "vendor",
    "bower_components",
    ".egg-info*",
    "conftest_*.c.gcov",
    ".env",
    ".envs",
    ".git",
    ".hg",
    ".tox",
    ".venv",
    ".venvs",
    ".virtualenv",
    ".virtualenvs",
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
    ".circleci",
    "jspm_packages",
    ".nyc_output",
]


class CoverageFileFinder(object):
    def __init__(
        self, project_root: Path = None, folders_to_ignore: typing.List[str] = None
    ):
        self.project_root = project_root or Path(os.getcwd())
        self.folders_to_ignore = folders_to_ignore or []

    def find_coverage_files(self) -> typing.List[UploadCollectionResultFile]:
        regex_patterns_to_include = globs_to_regex(coverage_files_patterns)
        regex_patterns_to_exclude = globs_to_regex(coverage_files_excluded_patterns)

        coverage_files_paths = search_files(
            self.project_root,
            default_folders_to_ignore + self.folders_to_ignore,
            filename_include_regex=regex_patterns_to_include,
            filename_exclude_regex=regex_patterns_to_exclude,
        )

        return [UploadCollectionResultFile(path) for path in coverage_files_paths]


def select_coverage_file_finder(
    root_folder_to_search, folders_to_ignore, explicitly_listed_files
):
    return CoverageFileFinder(root_folder_to_search, folders_to_ignore)
