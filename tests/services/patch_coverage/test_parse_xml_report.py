from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from codecov_cli.services.patch_coverage.parse_coverage_report import (
    ET,
    ParseXMLReport,
    ReportAndTree,
)
from codecov_cli.services.patch_coverage.types import DiffFile


class TestParseXMLReport(object):
    example_report = """
    <coverage version="6.4.1" timestamp="1692806806894" lines-valid="5910" lines-covered="5687" line-rate="0.9623" branches-covered="0" branches-valid="0" branch-rate="0" complexity="0">
    <packages>
        <package name="." line-rate="0" branch-rate="0" complexity="0">
        <classes>
            <class name="setup.py" filename="setup.py" complexity="0" line-rate="0.5" branch-rate="0">
                <methods/>
                <lines>
                    <line number="1" hits="0"/>
                    <line number="2" hits="1"/>
                    <line number="4" hits="1"/>
                    <line number="6" hits="1"/>
                    <line number="8" hits="1"/>
                    <line number="9" hits="0"/>
                    <line number="11" hits="1"/>
                    <line number="12" hits="0"/>
                    <line number="14" hits="0"/>
                    <line number="15" hits="0"/>
                </lines>
            </class>
            <class name="awesome.py" filename="awesome.py" complexity="0" line-rate="1" branch-rate="0">
                <methods/>
                <lines>
                    <line number="1" hits="1"/>
                    <line number="2" hits="1"/>
                    <line number="4" hits="1"/>
                    <line number="6" hits="1"/>
                    <line number="8" hits="1"/>
                    <line number="9" hits="1"/>
                    <line number="11" hits="1"/>
                    <line number="12" hits="1"/>
                    <line number="14" hits="1"/>
                    <line number="15" hits="1"/>
                </lines>
            </class>
			</classes>
        </package>
    </packages>
    </coverage>
    """

    example_report_alternate = """
    <coverage version="6.4.1" timestamp="1692806806894" lines-valid="5910" lines-covered="5687" line-rate="0.9623" branches-covered="0" branches-valid="0" branch-rate="0" complexity="0">
    <packages>
        <package name="." line-rate="0" branch-rate="0" complexity="0">
        <classes>
            <class name="setup.py" filename="setup.py" complexity="0" line-rate="0.2" branch-rate="0">
                <methods/>
                <lines>
                    <line number="1" hits="1"/>
                    <line number="2" hits="0"/>
                    <line number="4" hits="0"/>
                    <line number="6" hits="0"/>
                    <line number="8" hits="0"/>
                    <line number="9" hits="0"/>
                    <line number="11" hits="0"/>
                    <line number="12" hits="0"/>
                    <line number="14" hits="0"/>
                    <line number="15" hits="1"/>
                </lines>
            </class>
            <class name="awesome.py" filename="awesome.py" complexity="0" line-rate="0" branch-rate="0">
                <methods/>
                <lines>
                    <line number="1" hits="0"/>
                    <line number="2" hits="0"/>
                    <line number="4" hits="0"/>
                    <line number="6" hits="0"/>
                    <line number="8" hits="0"/>
                    <line number="9" hits="0"/>
                    <line number="11" hits="0"/>
                    <line number="12" hits="0"/>
                    <line number="14" hits="0"/>
                    <line number="15" hits="0"/>
                </lines>
            </class>
			</classes>
        </package>
    </packages>
    </coverage>
    """

    @pytest.mark.parametrize(
        "path,expected",
        [
            (Path(".coverage"), False),
            (Path("coverage.xml"), True),
            (Path("coverage.json"), False),
            (Path("package/module/coverage.xml"), True),
        ],
    )
    def test_is_report_suported(self, path, expected):
        parse_report = ParseXMLReport()
        assert parse_report._is_report_supported(path) == expected

    @patch("codecov_cli.services.patch_coverage.parse_coverage_report.search_files")
    def test_load_reports(self, mock_search_files, mocker):
        mock_root = MagicMock(name="root")
        mock_tree = MagicMock(name="tree", getroot=MagicMock(return_value=mock_root))
        mock_et_parse = mocker.patch.object(ET, "parse", return_value=mock_tree)
        mock__build_file_map = mocker.patch.object(ParseXMLReport, "_build_file_map")
        mock_search_files.return_value = [
            Path(".coverage"),
            Path("coverage.xml"),
            Path("coverage.json"),
            Path("package/module/coverage.xml"),
        ]
        parse_report = ParseXMLReport()
        reports = parse_report.load_reports()
        assert len(reports) == 2
        mock_et_parse.assert_has_calls(
            [call(Path("coverage.xml")), call(Path("package/module/coverage.xml"))]
        )
        assert mock_et_parse.call_count == 2
        assert mock__build_file_map.call_count == 2
        mock__build_file_map.assert_called_with(mock_root)
        # Running again uses the cached version
        reports = parse_report.load_reports()
        assert len(reports) == 2
        assert mock_et_parse.call_count == 2
        assert mock__build_file_map.call_count == 2

    def test_build_file_map(self):
        root = ET.fromstring(self.example_report)
        parse_report = ParseXMLReport()
        file_map = parse_report._build_file_map(root)
        assert len(file_map.keys()) == 2
        assert list(file_map.keys()) == ["setup.py", "awesome.py"]

    def test_get_covered_lines_in_patch_for_diff_file(self):
        root = ET.fromstring(self.example_report)
        parse_report = ParseXMLReport()
        file_map = parse_report._build_file_map(root)
        parse_report.reports = [ReportAndTree(Path("coverage.xml"), root, file_map)]
        root = ET.fromstring(self.example_report_alternate)
        file_map = parse_report._build_file_map(root)
        parse_report.reports.append(
            ReportAndTree(Path("alternate/coverage.xml"), root, file_map)
        )
        # awesome.py
        file_to_test = DiffFile()
        file_to_test.path = Path("awesome.py")
        lines_info = parse_report.get_covered_lines_in_patch_for_diff_file(file_to_test)
        assert lines_info == {
            1: True,
            2: True,
            4: True,
            6: True,
            8: True,
            9: True,
            11: True,
            12: True,
            14: True,
            15: True,
        }
        # setup.py
        file_to_test.path = Path("setup.py")
        lines_info = parse_report.get_covered_lines_in_patch_for_diff_file(file_to_test)
        assert lines_info == {
            1: True,
            2: True,
            4: True,
            6: True,
            8: True,
            9: False,
            11: True,
            12: False,
            14: False,
            15: True,
        }
        # File that doesn't exist
        file_to_test.path = Path("missing.py")
        lines_info = parse_report.get_covered_lines_in_patch_for_diff_file(file_to_test)
        assert lines_info == {}
