import logging
import pathlib

import yaml

logger = logging.getLogger("codecovcli")


def load_cli_config(codecov_yml_path: pathlib.Path):
    if codecov_yml_path.exists() and codecov_yml_path.is_file():
        logger.debug(f"Loading config from {codecov_yml_path}")
        with open(codecov_yml_path, "r") as file_stream:
            return yaml.safe_load(file_stream.read())
    logger.warning(
        f"File {codecov_yml_path} not found, or is not a file. Ignoring config."
    )
    return None
