from codecov_cli.services.staticanalysis.analyzers.ecmascriptsix import ES6Analyzer
from codecov_cli.services.staticanalysis.analyzers.general import GeneralAnalyzer
from codecov_cli.services.staticanalysis.analyzers.python import PythonAnalyzer


def get_best_analyzer(filename, actual_code):
    if filename.actual_filepath.suffix == ".py":
        return PythonAnalyzer(filename, actual_code)
    if filename.actual_filepath.suffix == ".js":
        return ES6Analyzer(filename, actual_code)
    return None
