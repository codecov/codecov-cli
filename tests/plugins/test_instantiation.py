from codecov_cli.plugins import (
    GcovPlugin,
    NoopPlugin,
    XcodePlugin,
    _get_plugin,
    _load_plugin_from_yaml,
    select_preparation_plugins,
)


def test_load_plugin_from_yaml(mocker):
    class SamplePlugin(object):
        def __init__(self, banana, other):
            self.something = banana
            self.other = other

    mocker.patch("codecov_cli.plugins.import_module", return_value=SamplePlugin)
    res = _load_plugin_from_yaml(
        {"path": "a", "params": {"banana": "super", "other": 1}}
    )
    assert isinstance(res, SamplePlugin)
    assert res.something == "super"
    assert res.other == 1


def test_load_plugin_from_yaml_non_existing_class(mocker):
    res = _load_plugin_from_yaml(
        {"path": "nonexisting.path", "params": {"banana": "super", "other": 1}}
    )
    assert isinstance(res, NoopPlugin)


def test_load_plugin_from_yaml_bad_parameters(mocker):
    class SamplePlugin(object):
        def __init__(self, banana):
            pass

    mocker.patch("codecov_cli.plugins.import_module", return_value=SamplePlugin)
    res = _load_plugin_from_yaml(
        {"path": "a", "params": {"banana": "super", "other": 1}}
    )
    assert isinstance(res, NoopPlugin)


def test_get_plugin_gcov():
    res = _get_plugin({}, "gcov")
    assert isinstance(res, GcovPlugin)


def test_get_plugin_xcode():
    res = _get_plugin({}, "xcode")
    assert isinstance(res, XcodePlugin)


def test_select_preparation_plugins(mocker):
    class SamplePlugin(object):
        def __init__(self, banana=None):
            pass

    class SecondSamplePlugin(object):
        def __init__(self, banana=None):
            pass

    mocker.patch(
        "codecov_cli.plugins.import_module",
        side_effect=[ModuleNotFoundError, SamplePlugin, SecondSamplePlugin],
    )
    res = select_preparation_plugins(
        {
            "plugins": {
                "otherthing": {
                    "path": "a",
                    "params": {"banana": "apple", "pineapple": 2},
                },
                "second": {"path": "b", "params": {"banana": "apple"}},
                "something": {"path": "c"},
            }
        },
        ["gcov", "something", "otherthing", "second", "lalalala"],
    )
    assert len(res) == 5
    assert isinstance(res[0], GcovPlugin)
    assert isinstance(res[1], NoopPlugin)
    assert isinstance(res[2], NoopPlugin)
    assert isinstance(res[3], SecondSamplePlugin)
    assert isinstance(res[4], NoopPlugin)
