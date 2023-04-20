import logging

from codecov_cli.runners.dan_runner import DoAnythingNowRunner
from codecov_cli.runners.python_standard_runner import PythonStandardRunner
from codecov_cli.runners.types import LabelAnalysisRunnerInterface

logger = logging.getLogger("codecovcli")


class UnableToFindRunner(Exception):
    pass


def _load_runner_from_yaml() -> LabelAnalysisRunnerInterface:
    raise NotImplementedError()


def get_runner(cli_config, runner_name) -> LabelAnalysisRunnerInterface:
    if runner_name == "python":
        config_params = cli_config.get("runners", {}).get("python", {})
        return PythonStandardRunner(config_params)
    elif runner_name == "dan":
        config_params = cli_config.get("runners", {}).get("dan", {})
        return DoAnythingNowRunner(config_params)
    logger.debug(
        f"Trying to load runner {runner_name}",
        extra=dict(
            extra_log_attributes=dict(
                available_runners=cli_config.get("runners", {}).keys()
            )
        ),
    )
    if cli_config and runner_name in cli_config.get("runners", {}):
        return _load_runner_from_yaml(cli_config["runners"][runner_name])
    raise UnableToFindRunner(f"Can't find runner {runner_name}")
