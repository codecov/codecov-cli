import pathlib
from dataclasses import dataclass
from typing import Optional


@dataclass
class FileAnalysisRequest(object):
    result_filename: str
    actual_filepath: pathlib.Path


@dataclass
class FileAnalysisResult(object):
    filename: str
    result: Optional[dict] = None
    error: Optional[dict] = None

    def asdict(self):
        return {"result": self.result, "error": self.error}
