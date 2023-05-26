import logging
import typing
from importlib import import_module

import click

from codecov_cli.runners.dan_runner import DoAnythingNowRunner
from codecov_cli.runners.python_standard_runner import PythonStandardRunner
from codecov_cli.runners.types import LabelAnalysisRunnerInterface

logger = logging.getLogger("codecovcli")


class UnableToFindRunner(Exception):
    pass


def _load_runner_from_yaml(plugin_dict: typing.Dict) -> LabelAnalysisRunnerInterface:
    try:
        module_obj = import_module(plugin_dict["module"])
        class_obj = getattr(module_obj, plugin_dict["class"])
    except ModuleNotFoundError:
        click.secho(
            f"Unable to dynamically load module {plugin_dict['module']}",
            err=True,
        )
        raise
    except AttributeError:
        click.secho(
            f"Unable to dynamically load class {plugin_dict['class']} from module {plugin_dict['module']}",
            err=True,
        )
        raise
    try:
        return class_obj(**plugin_dict["params"])
    except TypeError:
        click.secho(
            f"Unable to instantiate {class_obj} with parameters {plugin_dict['params']}",
            err=True,
        )
        raise


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
