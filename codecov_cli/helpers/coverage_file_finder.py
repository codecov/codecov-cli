import os
import typing
from fnmatch import fnmatch
from itertools import chain
from pathlib import Path

from codecov_cli.types import UploadCollectionResultFile

coverage_files_patterns = [
    "*coverage*.*",
    "nosetests.xml",
    "jacoco*.xml",
    "clover.xml",
    "report.xml",
    "*.codecov.*",
    "codecov.*",
    "cobertura.xml",
    "excoveralls.json",
    "luacov.report.out",
    "coverage-final.json",
    "naxsi.info",
    "lcov.info",
    "lcov.dat",
    "*.lcov",
    "*.clover",
    "cover.out",
    "gcov.info",
    "*.gcov",
    "*.lst",
    "test_cov.xml",
]


coverage_files_excluded_patterns = [
    "*.codecov.exe",
    "codecov.exe",
    "__pycache__",
    "node_modules/**/*",
    "vendor",
    ".circleci",
    ".git",
    ".gitignore",
    ".nvmrc",
    ".nyc_output",
    ".tox",
    "*.am",
    "*.bash",
    "*.bat",
    "*.bw",
    "*.cfg",
    "*.class",
    "*.cmake",
    "*.cmake",
    "*.conf",
    "*.coverage",
    "*.cp",
    "*.cpp",
    "*.crt",
    "*.css",
    "*.csv",
    "*.csv",
    "*.data",
    "*.db",
    "*.dox",
    "*.ec",
    "*.ec",
    "*.egg",
    "*.egg-info",
    "*.el",
    "*.env",
    "*.erb",
    "*.exe",
    "*.ftl",
    "*.gif",
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
    "*.map",
    "*.md",
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
    "codecov.SHA256SUM",
    "codecov.SHA256SUM.sig",
    "coverage-summary.json",
    "createdFiles.lst",
    "fullLocaleNames.lst",
    "include.lst",
    "inputFiles.lst",
    "phpunit-code-coverage.xml",
    "phpunit-coverage.xml",
    "remapInstanbul.coverage*.json",
    "scoverage.measurements.*",
    "test-result-*-codecoverage.json",
    "test_*_coverage.txt",
    "testrunner-coverage*",
]


class CoverageFileFinder(object):
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or os.getcwd()

    def find_coverage_files(self) -> typing.List[UploadCollectionResultFile]:
        unfiltered_matched_paths = chain(
            *(self.project_root.rglob(pattern) for pattern in coverage_files_patterns)
        )

        # !This is not accurate since fnmatch doesn't use the same rules for globbing as glob.glob or Path.glob
        # !This will result in some weird pattern matching like this one
        # path = Path("codecov-dev/a/b/hello.json")
        # fnmatch(path, "codecov-*.json") => True

        should_ignore = lambda path: any(
            path.isdir() or fnmatch(path, pattern)
            for pattern in coverage_files_excluded_patterns
        )

        matched_paths = (
            path for path in unfiltered_matched_paths if not should_ignore(path)
        )

        return [UploadCollectionResultFile(path) for path in matched_paths]


def select_coverage_file_finder():
    return CoverageFileFinder()
