import logging

import pytest

from codecov_cli.helpers.logging_utils import ClickHandler, ColorFormatter

logger = logging.getLogger("codecovcli")


def pytest_configure():
    ch = ClickHandler()
    ch.setFormatter(ColorFormatter())
    logger.addHandler(ch)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)


@pytest.fixture
def make_sure_logger_has_only_1_handler():
    if len(logger.handlers) > 1:
        handler_to_keep = logger.handlers[0]
        logger.handlers = [handler_to_keep]
