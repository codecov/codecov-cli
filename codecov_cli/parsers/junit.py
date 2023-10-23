import logging
from datetime import datetime, timedelta
from typing import List

from lxml import etree

from codecov_cli.parsers.base import Parser, ParsingError, Test, Testrun

logger = logging.getLogger("codecovcli")


class JUnitXMLParser(Parser):
    def __init__(self):
        self._parser = etree.XMLParser(recover=True, resolve_entities=False)

    def parse(self, file_content) -> List[Testrun]:
        processed = self._parse_xml(file_content)
        if processed is None or len(processed) == 0:
            raise ParsingError("Error parsing XML file")

        testsuites = [
            self._create_testsuite(testsuite_xml)
            for testsuite_xml in processed.iter("testsuite")
        ]

        return testsuites

    def _create_testcase(self, testcase_xml: etree.Element):
        return Test(
            f"{testcase_xml.get('classname')}.{testcase_xml.get('name')}",
            len(testcase_xml) == 0,
            timedelta(seconds=float(testcase_xml.get("time"))),
        )

    def _create_testsuite(self, testsuite_xml: etree.Element):
        return Testrun(
            testsuite_xml.get("name"),
            datetime.fromisoformat(testsuite_xml.get("timestamp")),
            timedelta(seconds=float(testsuite_xml.get("time"))),
            [
                self._create_testcase(testcase_xml)
                for testcase_xml in testsuite_xml.iter("testcase")
            ],
            int(testsuite_xml.get("failures")),
            int(testsuite_xml.get("errors")),
            int(testsuite_xml.get("skipped")),
            int(testsuite_xml.get("tests")),
        )

    def _parse_xml(self, file_content):
        return etree.fromstring(file_content, parser=self._parser)
