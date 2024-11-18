from codecov_cli import main


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
        "process-test-results",
        "send-notifications",
        "static-analysis",
        "upload-coverage",
        "upload-process",
    ]
