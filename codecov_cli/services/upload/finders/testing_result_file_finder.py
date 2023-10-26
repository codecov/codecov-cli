import logging

from codecov_cli.helpers.file_finder import BaseFileFinder

logger = logging.getLogger("codecovcli")

testing_result_patterns = ["**junit.xml"]


class TestingResultFileFinder(BaseFileFinder):
    file_patterns = testing_result_patterns


def select_testing_result_file_finder(*args, **kwargs):
    return TestingResultFileFinder(*args, **kwargs)
