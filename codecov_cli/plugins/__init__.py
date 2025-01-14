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


def select_preparation_plugins(
    cli_config: typing.Dict, plugin_names: typing.List[str], plugin_config: typing.Dict
):
    plugins = [_get_plugin(cli_config, p, plugin_config) for p in plugin_names]
    logger.debug(
        "Selected preparation plugins",
        extra=dict(
            extra_log_attributes=dict(
                selected_plugins=list(map(type, plugins)),
                cli_config=cli_config,
            )
        ),
    )
    return plugins


def _load_plugin_from_yaml(plugin_dict: typing.Dict):
    try:
        module_obj = import_module(plugin_dict["module"])
        class_obj = getattr(module_obj, plugin_dict["class"])
    except ModuleNotFoundError:
        click.secho(
            f"Unable to dynamically load module {plugin_dict['module']}",
            err=True,
        )
        return NoopPlugin()
    except AttributeError:
        click.secho(
            f"Unable to dynamically load class {plugin_dict['class']} from module {plugin_dict['module']}",
            err=True,
        )
        return NoopPlugin()
    try:
        params = plugin_dict.get("params", None)
        if params:
            return class_obj(**plugin_dict["params"])
        else:
            return class_obj()

    except TypeError:
        click.secho(
            f"Unable to instantiate {class_obj} with provided parameters {plugin_dict.get('params', '')}",
            err=True,
        )
        return NoopPlugin()


def _get_plugin(cli_config, plugin_name, plugin_config):
    if plugin_name == "noop":
        return NoopPlugin()
    if plugin_name == "gcov":
        return GcovPlugin(
            plugin_config.get("project_root", None),
            plugin_config.get("folders_to_ignore", None),
            plugin_config.get("gcov_executable", "gcov"),
            plugin_config.get("gcov_include", None),
            plugin_config.get("gcov_ignore", None),
            plugin_config.get("gcov_args", None),
        )
    if plugin_name == "pycoverage":
        config = cli_config.get("plugins", {}).get("pycoverage", {})
        return Pycoverage(config)
    if plugin_name == "xcode":
        return XcodePlugin(
            plugin_config.get("swift_project", None),
        )
    if plugin_name == "compress-pycoverage":
        config = cli_config.get("plugins", {}).get("compress-pycoverage", {})
        return CompressPycoverageContexts(config)
    if cli_config and plugin_name in cli_config.get("plugins", {}):
        return _load_plugin_from_yaml(cli_config["plugins"][plugin_name])
    click.secho(f"Unable to find plugin {plugin_name}", fg="magenta", err=True)
    return NoopPlugin()
