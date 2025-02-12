from enum import Enum


class ReportType(Enum):
    COVERAGE = "coverage"
    TEST_RESULTS = "test_results"


def report_type_from_str(report_type_str: str) -> ReportType:
    if report_type_str == "coverage":
        return ReportType.COVERAGE
    elif report_type_str == "test_results":
        return ReportType.TEST_RESULTS
    else:
        raise ValueError(f"Invalid upload type: {report_type_str}")
