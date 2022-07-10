import logging

from codecov_cli.helpers.logging_utils import ClickHandler, ColorFormatter

logger = logging.getLogger("codecovcli")


def pytest_configure():
    ch = ClickHandler()
    ch.setFormatter(ColorFormatter())
    logger.addHandler(ch)
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
