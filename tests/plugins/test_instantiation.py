from codecov_cli.plugins import (
    GcovPlugin,
    NoopPlugin,
    XcodePlugin,
    _get_plugin,
    _load_plugin_from_yaml,
    select_preparation_plugins,
)
from codecov_cli.plugins.compress_pycoverage_contexts import CompressPycoverageContexts
from codecov_cli.plugins.pycoverage import Pycoverage, PycoverageConfig


def test_load_plugin_from_yaml(mocker):
    class SamplePlugin(object):
        def __init__(self, banana, other):
            self.something = banana
            self.other = other

    SampleModule = mocker.MagicMock(SamplePlugin=SamplePlugin)

    mocker.patch("codecov_cli.plugins.import_module", return_value=SampleModule)
    res = _load_plugin_from_yaml(
        {
            "module": "a",
            "class": "SamplePlugin",
            "params": {"banana": "super", "other": 1},
        }
    )
    assert isinstance(res, SamplePlugin)
    assert res.something == "super"
    assert res.other == 1


def test_load_plugin_from_yaml_non_existing_class(mocker):
    class SamplePlugin(object):
        def __init__(self, banana, other):
            self.something = banana
            self.other = other

    SampleModule = mocker.MagicMock(SamplePlugin=SamplePlugin)
    del SampleModule.NonExistingClass

    mocker.patch("codecov_cli.plugins.import_module", return_value=SampleModule)

    res = _load_plugin_from_yaml(
        {
            "module": "a",
            "class": "NonExistingClass",
            "params": {"banana": "super", "other": 1},
        }
    )
    assert isinstance(res, NoopPlugin)


def test_load_plugin_from_yaml_non_existing_module(mocker):
    res = _load_plugin_from_yaml(
        {
            "module": "nonexisting.module",
            "class": "nonexisting.class",
            "params": {"banana": "super", "other": 1},
        }
    )
    assert isinstance(res, NoopPlugin)


def test_load_plugin_from_yaml_bad_parameters(mocker):
    class SamplePlugin(object):
        def __init__(self, banana):
            pass

    SampleModule = mocker.MagicMock(SamplePlugin=SamplePlugin)

    mocker.patch("codecov_cli.plugins.import_module", return_value=SampleModule)
    res = _load_plugin_from_yaml(
        {
            "module": "a",
            "class": "SamplePlugin",
            "params": {"banana": "super", "other": 1},
        }
    )
    assert isinstance(res, NoopPlugin)


def test_load_plugin_from_yaml_missing_params(mocker):
    class SamplePlugin(object):
        def __init__(self):
            pass

    SampleModule = mocker.MagicMock(SamplePlugin=SamplePlugin)

    mocker.patch("codecov_cli.plugins.import_module", return_value=SampleModule)
    res = _load_plugin_from_yaml({"module": "a", "class": "SamplePlugin"})
    assert isinstance(res, SamplePlugin)


def test_load_plugin_from_yaml_empty_params(mocker):
    class SamplePlugin(object):
        def __init__(self):
            pass

    SampleModule = mocker.MagicMock(SamplePlugin=SamplePlugin)

    mocker.patch("codecov_cli.plugins.import_module", return_value=SampleModule)
    res = _load_plugin_from_yaml({"module": "a", "class": "SamplePlugin", "params": {}})
    assert isinstance(res, SamplePlugin)


def test_get_plugin_gcov():
    res = _get_plugin({}, "gcov", {})
    assert isinstance(res, GcovPlugin)

    res = _get_plugin(
        {},
        "gcov",
        {
            "gcov_executable": "lcov",
        },
    )
    assert isinstance(res, GcovPlugin)


def test_get_plugin_xcode():
    res = _get_plugin({}, "xcode", {})
    assert isinstance(res, XcodePlugin)


def test_get_plugin_noop():
    res = _get_plugin({}, "noop", {})
    assert isinstance(res, NoopPlugin)


def test_get_plugin_pycoverage():
    res = _get_plugin({}, "pycoverage", {})
    assert isinstance(res, Pycoverage)
    assert res.config == PycoverageConfig()
    assert res.config.report_type == "xml"

    pycoverage_config = {"project_root": "project/root", "report_type": "json"}
    res = _get_plugin({"plugins": {"pycoverage": pycoverage_config}}, "pycoverage", {})
    assert isinstance(res, Pycoverage)
    assert res.config == PycoverageConfig(pycoverage_config)
    assert res.config.report_type == "json"


def test_get_plugin_compress_pycoverage():
    res = _get_plugin({}, "compress-pycoverage", {})
    assert isinstance(res, CompressPycoverageContexts)

    res = _get_plugin(
        {"plugins": {"compress-pycoverage": {"file_to_compress": "something.json"}}},
        "compress-pycoverage",
        {},
    )
    assert isinstance(res, CompressPycoverageContexts)
    assert str(res.file_to_compress) == "something.json"


def test_select_preparation_plugins(mocker):
    class SamplePlugin(object):
        def __init__(self, banana=None):
            pass

    SampleModule = mocker.MagicMock(SamplePlugin=SamplePlugin)

    class SecondSamplePlugin(object):
        def __init__(self, banana=None):
            pass

    SecondSampleModule = mocker.MagicMock(SecondSamplePlugin=SecondSamplePlugin)

    mocker.patch(
        "codecov_cli.plugins.import_module",
        side_effect=[ModuleNotFoundError, SampleModule, SecondSampleModule],
    )

    res = select_preparation_plugins(
        {
            "plugins": {
                "otherthing": {
                    "module": "a",
                    "class": "SamplePlugin",
                    "params": {"banana": "apple", "pineapple": 2},
                },
                "second": {
                    "module": "c",
                    "class": "SecondSamplePlugin",
                    "params": {"banana": "apple"},
                },
                "something": {"module": "e", "class": "f"},
            }
        },
        ["gcov", "something", "otherthing", "second", "lalalala"],
        {},
    )
    assert len(res) == 5
    assert isinstance(res[0], GcovPlugin)
    assert isinstance(res[1], NoopPlugin)
    assert isinstance(res[2], NoopPlugin)
    assert isinstance(res[3], SecondSamplePlugin)
    assert isinstance(res[4], NoopPlugin)
