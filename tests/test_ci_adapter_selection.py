import os
from enum import Enum

import pytest

from codecov_cli.fallbacks import FallbackFieldEnum
from codecov_cli.helpers.ci_adapters import (
    AppveyorCIAdapter,
    CircleCICIAdapter,
    GithubActionsCIAdapter,
    GitlabCIAdapter,
    LocalAdapter,
    get_ci_adapter,
)


class TestCISelector(object):
    def test_returns_none_if_name_is_invalid(self):
        assert get_ci_adapter("random ci adapter name") is None

    def test_returns_circleCI(self):
        assert isinstance(get_ci_adapter("circleci"), CircleCICIAdapter)

    def test_returns_githubactions(self):
        assert isinstance(get_ci_adapter("githubactions"), GithubActionsCIAdapter)

    def test_returns_gitlabCI(self):
        assert isinstance(get_ci_adapter("gitlabCI"), GitlabCIAdapter)

    def test_returns_appveyor(self):
        assert isinstance(get_ci_adapter("appveyor"), AppveyorCIAdapter)

    def test_returns_local(self):
        assert isinstance(get_ci_adapter("local"), LocalAdapter)
