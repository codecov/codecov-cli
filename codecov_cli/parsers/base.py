from datetime import datetime, timedelta
from typing import List


class ParsingError(Exception):
    ...


class Testcase(object):
    def __init__(self, name: str, status: bool, duration: timedelta):
        self.name = name
        self.status = status
        self.duration = duration

    def __repr__(self):
        return f"{self.name}:{self.status}:{self.duration.total_seconds()}::"


class Testsuite(object):
    def __init__(
        self,
        name: str,
        timestamp: datetime,
        time: timedelta,
        testcases: List[Testcase],
        failures: int,
        errors: int,
        skipped: int,
        total: int,
    ):
        self.testcases = testcases or []
        self.name = name
        self.time = time
        self.timestamp = timestamp
        self.failures = failures
        self.errors = errors
        self.skipped = skipped
        self.total = total

    def to_str(self):
        return (
            ";".join(
                [
                    self.name,
                    str(self.timestamp.timestamp()),
                    str(self.time.total_seconds()),
                    str(self.failures),
                    str(self.errors),
                    str(self.skipped),
                    str(self.total),
                    str(self.testcases),
                ]
            )
            + ";"
        )
