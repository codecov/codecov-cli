from datetime import datetime, timedelta

from codecov_cli.parsers.base import Test, Testrun


def test_testsuite():
    now = datetime.now()
    ts = Testrun(
        "test_name",
        now,
        timedelta(seconds=1),
        [Test("testcase_name", True, timedelta(seconds=1))],
        errors=0,
        failures=0,
        skipped=0,
        total=1,
    )

    assert (
        ts.to_str()
        == f"test_name;{now.timestamp()};1.0;0;0;0;1;[testcase_name:True:1.0::];"
    )
