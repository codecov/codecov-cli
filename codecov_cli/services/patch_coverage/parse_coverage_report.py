import logging
import re
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from codecov_cli.helpers.folder_searcher import search_files
from codecov_cli.services.patch_coverage.types import DiffFile, ReportAndTree

logger = logging.getLogger("codecovcli")

# TODO: This should not be tied to XML, but a generic report parser
class ParseXMLReport(object):
    def _is_report_supported(self, report_path: Path) -> bool:
        return "coverage.xml" in report_path.parts

    def _build_file_map(self, root: ET.Element) -> Dict[str, ET.Element]:
        queue = deque([root])
        file_map: Dict[str, ET.Element] = {}
        while queue:
            curr = queue.popleft()
            if curr.tag == "class" and "filename" in curr.attrib:
                file_map[curr.attrib["filename"]] = curr
            else:
                for child in curr:
                    queue.append(child)
        return file_map

    def __init__(self) -> None:
        self.reports: List[ReportAndTree] = None

    def load_reports(self) -> List[ReportAndTree]:
        if self.reports is not None:
            return self.reports
        self.reports = []
        reports = search_files(
            ".",
            [],
            filename_include_regex=re.compile("coverage.xml"),
            search_for_directories=False,
        )
        for report in reports:
            if self._is_report_supported(report):
                tree = ET.parse(report)
                file_map = self._build_file_map(tree.getroot())
                stat = report.stat()
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                self.reports.append(
                    ReportAndTree(report, tree, file_map, last_modified)
                )
        return self.reports

    def possibly_warn_if_old_reports(
        self, report: ReportAndTree, diff_file: DiffFile
    ) -> bool:
        if report.last_modified < diff_file.last_modified:
            logger.warning(
                "Coverage report is older than files in diff. Please generate a new one.",
                extra=dict(
                    extra_log_attributes=dict(
                        path_with_recent_changes=diff_file.path,
                        time_of_last_report=report.last_modified,
                        time_of_path_changes=diff_file.last_modified,
                    )
                ),
            )
            return True
        return False

    def get_covered_lines_in_patch_for_diff_file(
        self, diff_file: DiffFile
    ) -> Dict[int, bool]:
        lines_info = defaultdict(bool)
        for report in self.reports:
            file_map = report.file_map
            if str(diff_file.path) in file_map:
                self.possibly_warn_if_old_reports(report, diff_file)
                file_root = file_map[str(diff_file.path)]
                lines = file_root.find("lines")
                for line in lines:
                    idx = int(line.attrib["number"])
                    lines_info[idx] = lines_info[idx] or (line.attrib["hits"] == "1")
            else:
                logger.error(f"Can't find file {diff_file.path} in XML report")
        return lines_info
