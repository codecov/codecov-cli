from datetime import datetime, timedelta

from codecov_cli.parsers.base import Testcase, Testsuite
from codecov_cli.parsers.junit import JUnitXMLParser


def test_parse_junit():
    parser = JUnitXMLParser()
    testsuites = parser.parse(
        bytes(
            """<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest" errors="0" failures="0" skipped="0" tests="1" time="0.016" timestamp="2023-10-20T12:56:19.831266" hostname="test_host_name"><testcase classname="tests.parsers.test_base" name="test_testsuite" time="0.000" /></testsuite></testsuites>""",
            encoding="utf-8",
        )
    )

    result = testsuites[0]

    assert result.name == "pytest"
    assert result.timestamp == datetime.fromisoformat("2023-10-20T12:56:19.831266")
    assert result.time == timedelta(seconds=0.016)
    assert result.testcases[0].name == "tests.parsers.test_base.test_testsuite"
    assert result.testcases[0].status == True
    assert result.testcases[0].duration == timedelta(seconds=0.0)
    assert result.errors == 0
    assert result.failures == 0
    assert result.skipped == 0
    assert result.total == 1
