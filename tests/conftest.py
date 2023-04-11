import logging

import pytest

from codecov_cli.helpers.ci_adapters.base import CIAdapterBase
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


class FakeProvider(CIAdapterBase):
    def detect(self) -> bool:
        return True

    def _get_branch(self):
        return "BUILD_BRANCH"

    def _get_build_code(self):
        return "BUILD_CODE"

    def _get_build_url(self):
        return "BUILD_URL"

    def _get_commit_sha(self):
        return "COMMIT_SHA"

    def _get_slug(self):
        return "REPO_SLUG"

    def _get_service(self):
        return "FAKE_PROVIDER"

    def _get_pull_request_number(self):
        return "PR_NUMBER"

    def _get_job_code(self):
        return "JOB_CODE"

    def get_service_name(self):
        return "FAKE_PROVIDER"


@pytest.fixture
def fake_ci_provider():
    return FakeProvider()
