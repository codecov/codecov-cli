import logging
import typing
from importlib import import_module

import click

from codecov_cli.plugins.compress_pycoverage_contexts import CompressPycoverageContexts
from codecov_cli.plugins.gcov import GcovPlugin
from codecov_cli.plugins.pycoverage import Pycoverage
from codecov_cli.plugins.xcode import XcodePlugin

logger = logging.getLogger("codecovcli")


class NoopPlugin(object):
    def run_preparation(self, collector):
        pass


def select_preparation_plugins(cli_config: typing.Dict, plugin_names: typing.List[str]):
    plugins = [_get_plugin(cli_config, p) for p in plugin_names]
    logger.debug(
        "Selected preparation plugins",
        extra=dict(
            extra_log_attributes=dict(selected_plugins=list(map(type, plugins)))
        ),
    )
    return plugins


def _load_plugin_from_yaml(plugin_dict: typing.Dict):
    try:
        class_obj = import_module(plugin_dict["path"])
    except ModuleNotFoundError:
        click.secho(
            f"Unable to dynamically load plugin on path {plugin_dict['path']}",
            err=True,
        )
        return NoopPlugin()
    try:
        return class_obj(**plugin_dict["params"])
    except TypeError:
        click.secho(
            f"Unable to instantiate {class_obj} with parameters {plugin_dict['params']}",
            err=True,
        )
        return NoopPlugin()


def _get_plugin(cli_config, plugin_name):
    if plugin_name == "gcov":
        return GcovPlugin()
    if plugin_name == "pycoverage":
        config = cli_config.get("plugins", {}).get("pycoverage", {})
        return Pycoverage(config)
    if plugin_name == "xcode":
        return XcodePlugin()
    if plugin_name == "compress-pycoverage":
        config = cli_config.get("plugins", {}).get("compress-pycoverage", {})
        return CompressPycoverageContexts(config)
    if cli_config and plugin_name in cli_config.get("plugins", {}):
        return _load_plugin_from_yaml(cli_config["plugins"][plugin_name])
    click.secho(f"Unable to find plugin {plugin_name}", fg="magenta", err=True)
    return NoopPlugin()
