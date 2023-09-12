import logging
import pathlib

import yaml

logger = logging.getLogger("codecovcli")

CODECOV_API_URL = "https://api.codecov.io"
LEGACY_CODECOV_API_URL = "https://codecov.io"


def load_cli_config(codecov_yml_path: pathlib.Path):
    if codecov_yml_path.exists() and codecov_yml_path.is_file():
        logger.debug(f"Loading config from {codecov_yml_path}")
        with open(codecov_yml_path, "r") as file_stream:
            return yaml.safe_load(file_stream.read())
    logger.warning(
        f"Config file {codecov_yml_path} not found, or is not a file. Ignoring config."
    )
    return None
