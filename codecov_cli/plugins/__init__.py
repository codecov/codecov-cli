from codecov_cli.plugins.gcov import GcovPlugin
from codecov_cli.plugins.pycoverage import Pycoverage


class NoopPlugin(object):
    def run_preparation(self, collector):
        pass


def select_preparation_plugins(plugin_names):
    return [_get_plugin(p) for p in plugin_names]


def _get_plugin(plugin_name):
    if plugin_name == "gcov":
        return GcovPlugin()
    elif plugin_name == "pycoverage":
        return Pycoverage()
    return NoopPlugin()
