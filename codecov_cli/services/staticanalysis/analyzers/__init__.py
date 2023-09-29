from codecov_cli.services.staticanalysis.analyzers.general import BaseAnalyzer
from codecov_cli.services.staticanalysis.analyzers.javascript_es6 import ES6Analyzer
from codecov_cli.services.staticanalysis.analyzers.python import PythonAnalyzer
from codecov_cli.services.staticanalysis.types import FileAnalysisRequest


def get_best_analyzer(
    filename: FileAnalysisRequest, actual_code: bytes
) -> BaseAnalyzer:
    if filename.actual_filepath.suffix == ".py":
        return PythonAnalyzer(filename, actual_code)
    if filename.actual_filepath.suffix == ".js":
        return ES6Analyzer(filename, actual_code)
    return None
