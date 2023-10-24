from dataclasses import dataclass
from datetime import datetime, timedelta
from json import JSONEncoder
from typing import Any, List


class ParsingError(Exception):
    ...


class ParserJSONEncoder(JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, (TestRunGroup, TestRun)):
            return o.__dict__
        elif isinstance(o, timedelta):
            return o.total_seconds()
        elif isinstance(o, datetime):
            return o.isoformat()
        else:
            raise ParsingError("Error encoding object to JSON")


@dataclass
class TestRun(object):
    name: str
    status: bool
    duration: timedelta


@dataclass
class TestRunGroup(object):
    name: str
    timestamp: datetime
    time: timedelta
    testruns: List[TestRun]
    failures: int
    errors: int
    skipped: int
    total: int


class Parser:
    def parse(self, file_content) -> List[TestRunGroup]:
        raise NotImplementedError()
