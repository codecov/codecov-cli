import logging
import pathlib
import typing

import yaml

from codecov_cli.helpers.versioning_systems import get_versioning_system

logger = logging.getLogger("codecovcli")

CODECOV_API_URL = "https://api.codecov.io"
LEGACY_CODECOV_API_URL = "https://codecov.io"

# Relative to the project root
CODECOV_YAML_RECOGNIZED_DIRECTORIES = [
    "",
    ".github/",
    "dev/",
]

CODECOV_YAML_RECOGNIZED_FILENAMES = [
    "codecov.yml",
    "codecov.yaml",
    ".codecov.yml",
    ".codecov.yaml",
]


def _find_codecov_yamls():
    vcs = get_versioning_system()
    vcs_root = vcs.get_network_root() if vcs else None
    project_root = vcs_root if vcs_root else pathlib.Path.cwd()

    yamls = []
    for directory in CODECOV_YAML_RECOGNIZED_DIRECTORIES:
        dir_candidate = project_root / directory
        if not dir_candidate.exists() or not dir_candidate.is_dir():
            continue

        for filename in CODECOV_YAML_RECOGNIZED_FILENAMES:
            file_candidate = dir_candidate / filename
            if file_candidate.exists() and file_candidate.is_file():
                yamls.append(file_candidate)

    return yamls


def load_cli_config(codecov_yml_path: typing.Optional[pathlib.Path]):
    if not codecov_yml_path:
        yamls = _find_codecov_yamls()
        codecov_yml_path = yamls[0] if yamls else None

    if not codecov_yml_path:
        logger.warning("No config file could be found. Ignoring config.")
        return None

    if not codecov_yml_path.exists() or not codecov_yml_path.is_file():
        logger.warning(
            f"Config file {codecov_yml_path} not found, or is not a file. Ignoring config."
        )
        return None

    logger.debug(f"Loading config from {codecov_yml_path}")
    with open(codecov_yml_path, "r") as file_stream:
        return yaml.safe_load(file_stream.read())
