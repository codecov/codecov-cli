from codecov_cli.opentelemetry import _before_send


def _exc_event(frames, value="boom"):
    return {
        "exception": {
            "values": [
                {
                    "type": "Error",
                    "value": value,
                    "stacktrace": {"frames": frames},
                }
            ]
        }
    }


def test_before_send_keeps_cli_exceptions():
    event = _exc_event(
        [
            {"module": "__main__", "filename": "<string>"},
            {"module": "codecov_cli.services.upload", "filename": "upload.py"},
        ]
    )
    assert _before_send(event, {}) is event


def test_before_send_keeps_cli_exceptions_by_path():
    event = _exc_event(
        [{"abs_path": "/site-packages/codecov_cli/main.py", "filename": "main.py"}]
    )
    assert _before_send(event, {}) is event


def test_before_send_drops_host_script_exceptions():
    event = _exc_event(
        [{"module": "__main__", "filename": "<string>", "abs_path": "<string>"}],
        value="No module named 'prevent_cli.fallbacks'",
    )
    assert _before_send(event, {}) is None


def test_before_send_keeps_messages():
    event = {"message": "something happened"}
    assert _before_send(event, {}) is event
