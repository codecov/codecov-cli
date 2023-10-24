import json
from datetime import datetime, timedelta

from codecov_cli.parsers.base import ParserJSONEncoder, TestRun, TestRunGroup


def test_parserjsonencoder():
    now = datetime.now()
    ts = TestRunGroup(
        "test_name",
        now,
        timedelta(seconds=1),
        [TestRun("testcase_name", True, timedelta(seconds=1))],
        errors=0,
        failures=0,
        skipped=0,
        total=1,
    )

    print(json.dumps(ts, cls=ParserJSONEncoder))

    assert (
        json.dumps(ts, cls=ParserJSONEncoder)
        == '{"name": "test_name", "timestamp": "%s", "time": 1.0, "testruns": [{"name": "testcase_name", "status": true, "duration": 1.0}], "failures": 0, "errors": 0, "skipped": 0, "total": 1}'
        % now.isoformat()
    )
