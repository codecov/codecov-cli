import logging

import pytest

from codecov_cli.helpers.logging_utils import ClickHandler, ColorFormatter

logger = logging.getLogger("codecovcli")


def pytest_configure():
    # This if exists to avoid an issue where extra handlers would be added by tests that use runner.invoke()
    # Which would cause subsequent tests to failed due to repeated log lines
    if not logger.hasHandlers():
        ch = ClickHandler()
        ch.setFormatter(ColorFormatter())
        logger.addHandler(ch)
    logger.propagate = False
    logger.setLevel(logging.INFO)


@pytest.fixture
def use_verbose_option():
    # Before the test we set logging to DEBUG
    prev_level = logger.level
    logger.setLevel(logging.DEBUG)
    # Let the test run
    yield
    # After the test set logging back to INFO
    logger.setLevel(prev_level)
