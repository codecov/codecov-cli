import logging
from pathlib import Path

from codecov_cli.helpers.file_finder import BaseFileFinder

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


class CoverageFileFinder(BaseFileFinder):
    file_patterns = coverage_files_patterns


def select_coverage_file_finder(*args, **kwargs):
    return CoverageFileFinder(*args, **kwargs)
