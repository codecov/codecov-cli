import logging

from codecov_cli.services.upload.finders.result_file_finder import ResultFileFinder

logger = logging.getLogger("codecovcli")

testing_result_patterns = ["**junit.xml"]


class TestingResultFileFinder(ResultFileFinder):
    file_patterns = testing_result_patterns


def select_testing_result_file_finder(*args, **kwargs):
    return TestingResultFileFinder(*args, **kwargs)
