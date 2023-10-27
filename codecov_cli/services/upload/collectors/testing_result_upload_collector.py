import base64
import json
import zlib

from codecov_cli.services.upload.finders.testing_result_file_finder import (
    TestingResultFileFinder,
)
from codecov_cli.types import UploadCollectionResultFile


class TestingResultUploadCollector:
    def __init__(self, file_finder: TestingResultFileFinder) -> None:
        self.file_finder = file_finder

    def generate_payload_data(self) -> bytes:
        testing_result_files = self.file_finder.find_files()

        return json.dumps(
            {
                "testing_result_files": [
                    self._format_file(file) for file in testing_result_files
                ]
            }
        ).encode()

    def _format_file(self, file: UploadCollectionResultFile):
        format_info, formatted_content = self._get_format_info(file)
        return {
            "filename": file.get_filename().decode(),
            "format": format_info,
            "data": formatted_content,
            "labels": "",
        }

    def _get_format_info(self, file: UploadCollectionResultFile):
        format_info = "base64+compressed"
        formatted_content = (
            base64.b64encode(zlib.compress((file.get_content())))
        ).decode()
        return format_info, formatted_content
