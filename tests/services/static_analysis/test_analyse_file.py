import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from codecov_cli.services.staticanalysis import analyze_file
from codecov_cli.services.staticanalysis.types import FileAnalysisRequest

here = Path(__file__)
here_parent = here.parent


@pytest.mark.parametrize(
    "input_filename,output_filename",
    [
        ("samples/inputs/sample_001.py", "samples/outputs/sample_001.json"),
        ("samples/inputs/sample_002.py", "samples/outputs/sample_002.json"),
        ("samples/inputs/sample_003.js", "samples/outputs/sample_003.json"),
        ("samples/inputs/sample_004.js", "samples/outputs/sample_004.json"),
        ("samples/inputs/sample_005.py", "samples/outputs/sample_005.json"),
    ],
)
@pytest.mark.skipif(
    sys.platform == "win32", reason="windows is producing different `code_hash` values"
)
def test_sample_analysis(input_filename, output_filename):
    config = {}
    res = analyze_file(
        config, FileAnalysisRequest(input_filename, Path(input_filename))
    )
    with open(output_filename, "r") as file:
        expected_result = json.load(file)
    json_res = json.dumps(res.asdict())
    res_dict = json.loads(json_res)
    assert sorted(res_dict["result"].keys()) == sorted(expected_result["result"].keys())
    res_dict["result"]["functions"] = sorted(
        res_dict["result"]["functions"], key=lambda x: x["start_line"]
    )
    expected_result["result"]["functions"] = sorted(
        expected_result["result"]["functions"], key=lambda x: x["start_line"]
    )
    assert res_dict["result"]["functions"] == expected_result["result"]["functions"]
    assert res_dict["result"].get("statements") == expected_result["result"].get(
        "statements"
    )
    assert res_dict["result"] == expected_result["result"]
    assert res_dict == expected_result


@patch("builtins.open")
@patch("codecov_cli.services.staticanalysis.get_best_analyzer", return_value=None)
def test_analyse_file_no_analyzer(mock_get_analyzer, mock_open):
    fake_contents = MagicMock(name="fake_file_contents")
    file_name = MagicMock(actual_filepath="filepath")
    mock_open.return_value.__enter__.return_value.read.return_value = fake_contents
    config = {}
    res = analyze_file(config, file_name)
    assert res is None
    mock_open.assert_called_with("filepath", "rb")
    mock_get_analyzer.assert_called_with(file_name, fake_contents)
