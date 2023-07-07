from codecov_cli import __version__, main


def test_version():
    assert __version__ == "0.1.0"


def test_existing_commands():
    assert sorted(main.cli.commands.keys()) == [
        "create-commit",
        "create-report",
        "create-report-results",
        "do-upload",
        "empty-upload",
        "get-report-results",
        "label-analysis",
        "pr-base-picking",
        "static-analysis",
        "upload-process",
    ]
