import json
import pathlib
from io import BytesIO
from unittest.mock import call

import pytest

from codecov_cli.plugins.compress_pycoverage_contexts import CompressPycoverageContexts
from codecov_cli.plugins.types import PreparationPluginReturn

sample = {
    "meta": {
        "version": "6.5.0",
        "timestamp": "2023-05-15T18:35:30.641570",
        "branch_coverage": False,
        "show_contexts": True,
    },
    "totals": {
        "covered_lines": 416,
        "num_statements": 437,
        "percent_covered": 95.19450800915332,
        "percent_covered_display": "95",
        "missing_lines": 21,
        "excluded_lines": 0,
    },
    "files": {
        "awesome.py": {
            "executed_lines": [1, 2, 3, 5],
            "summary": {
                "covered_lines": 4,
                "num_statements": 5,
                "percent_covered": 80.0,
                "percent_covered_display": "80",
                "missing_lines": 1,
                "excluded_lines": 0,
            },
            "missing_lines": [4],
            "excluded_lines": [],
            "contexts": {
                "1": [""],
                "2": ["label_1|run", "label_2|run"],
                "3": ["label_2|run", "label_3|run"],
                "5": ["label_5|run"],
            },
        },
        "__init__.py": {
            "executed_lines": [],
            "summary": {
                "covered_lines": 0,
                "num_statements": 4,
                "percent_covered": 0.0,
                "percent_covered_display": "0",
                "missing_lines": 4,
                "excluded_lines": 0,
            },
            "missing_lines": [1, 3, 4, 5],
            "excluded_lines": [],
            "contexts": {},
        },
    },
}


class TestCompressPycoverageContexts_CompressionFunctions(object):
    def test_copy_meta(self, mocker):
        fd_in_mock = BytesIO(bytearray(json.dumps(sample), encoding="utf-8"))
        fd_out_mock = mocker.MagicMock()
        plugin = CompressPycoverageContexts()
        plugin._copy_meta(fd_in_mock, fd_out_mock)
        fd_out_mock.write.assert_has_calls(
            [
                call(
                    '"meta": {"version": "6.5.0", "timestamp": "2023-05-15T18:35:30.641570", "branch_coverage": false, "show_contexts": true},'
                ),
                call(
                    '"totals": {"covered_lines": 416, "num_statements": 437, "percent_covered": "95.19450800915332", "percent_covered_display": "95", "missing_lines": 21, "excluded_lines": 0},'
                ),
            ],
            any_order=True,
        )

    def test_copy_file_details(self, mocker):
        fd_out_mock = mocker.MagicMock()
        file_name = "awesome.py"
        file_details = sample["files"][file_name]
        plugin = CompressPycoverageContexts()
        plugin._copy_file_details(file_name, file_details, fd_out_mock)
        fd_out_mock.write.assert_has_calls(
            [
                call('"awesome.py":{'),
                call('"executed_lines": [1, 2, 3, 5],'),
                call(
                    '"summary": {"covered_lines": 4, "num_statements": 5, "percent_covered": 80.0, "percent_covered_display": "80", "missing_lines": 1, "excluded_lines": 0},'
                ),
                call('"missing_lines": [4],'),
                call('"excluded_lines": [],'),
            ]
        )

    def test_compress_files(self, mocker):
        out_stream = ""

        def write_side_effect(msg):
            nonlocal out_stream
            out_stream += str(msg)

        def seek_site_effect(offset):
            nonlocal out_stream
            out_stream = out_stream[:offset]

        fd_out_mock = mocker.MagicMock()
        fd_out_mock.write.side_effect = write_side_effect
        fd_out_mock.tell.side_effect = lambda: len(out_stream)
        fd_out_mock.seek.side_effect = seek_site_effect

        files_in_report = [
            ("awesome.py", sample["files"]["awesome.py"]),
            ("__init__.py", sample["files"]["__init__.py"]),
        ]

        expected_output = {
            "files": {
                "awesome.py": {
                    "executed_lines": [1, 2, 3, 5],
                    "summary": {
                        "covered_lines": 4,
                        "num_statements": 5,
                        "percent_covered": 80.0,
                        "percent_covered_display": "80",
                        "missing_lines": 1,
                        "excluded_lines": 0,
                    },
                    "missing_lines": [4],
                    "excluded_lines": [],
                    "contexts": {
                        "1": [0],
                        "2": [1, 2],
                        "3": [2, 3],
                        "5": [4],
                    },
                },
                "__init__.py": {
                    "executed_lines": [],
                    "summary": {
                        "covered_lines": 0,
                        "num_statements": 4,
                        "percent_covered": 0.0,
                        "percent_covered_display": "0",
                        "missing_lines": 4,
                        "excluded_lines": 0,
                    },
                    "missing_lines": [1, 3, 4, 5],
                    "excluded_lines": [],
                    "contexts": {},
                },
            },
            "labels_table": {
                "0": "",
                "1": "label_1",
                "2": "label_2",
                "3": "label_3",
                "4": "label_5",
            },
        }
        plugin = CompressPycoverageContexts()
        plugin._compress_files(files_in_report, fd_out_mock)
        print(out_stream)
        assert json.loads("{" + out_stream + "}") == expected_output


class TestCompressPycoverageContexts(object):
    def test_default_options(self):
        plugin = CompressPycoverageContexts()
        assert plugin.config.file_to_compress == pathlib.Path("coverage.json")
        assert plugin.config.delete_uncompressed
        assert plugin.file_to_compress == pathlib.Path("coverage.json")
        assert plugin.file_to_write == pathlib.Path("coverage.codecov.json")

    def test_change_options(self):
        config = {
            "file_to_compress": "label.coverage.json",
            "delete_uncompressed": False,
        }
        plugin = CompressPycoverageContexts(config)
        assert plugin.config.file_to_compress == pathlib.Path("label.coverage.json")
        assert not plugin.config.delete_uncompressed
        assert plugin.file_to_compress == pathlib.Path("label.coverage.json")
        assert plugin.file_to_write == pathlib.Path("label.coverage.codecov.json")

    def test_run_preparation_fail_fast_no_file(self):
        plugin = CompressPycoverageContexts()
        res = plugin.run_preparation(None)
        assert res == PreparationPluginReturn(
            success=False,
            messages=["File to compress coverage.json not found."],
        )

    def test_run_preparation_fail_fast_path_not_file(self, tmp_path):
        config = {"file_to_compress": tmp_path}
        plugin = CompressPycoverageContexts(config)
        res = plugin.run_preparation(None)
        assert res == PreparationPluginReturn(
            success=False,
            messages=[f"File to compress {tmp_path} is not a file."],
        )

    def test_run_preparation_mocked(self, tmp_path, mocker):
        (tmp_path / "coverage.json").touch()
        mock_fd_in = mocker.MagicMock()
        mock_fd_out = mocker.MagicMock()
        mock_smart_open = mocker.patch(
            "codecov_cli.plugins.compress_pycoverage_contexts.open",
            side_effect=[mock_fd_in, mock_fd_out],
        )
        mock_ijson = mocker.patch(
            "codecov_cli.plugins.compress_pycoverage_contexts.ijson"
        )
        mock_ijson.kvitems.return_value = "files_in_report"
        mock_copy_meta = mocker.patch.object(CompressPycoverageContexts, "_copy_meta")
        mock_compress_files = mocker.patch.object(
            CompressPycoverageContexts, "_compress_files"
        )

        config = {"file_to_compress": (tmp_path / "coverage.json")}
        plugin = CompressPycoverageContexts(config)
        res = plugin.run_preparation(None)
        assert res == PreparationPluginReturn(success=True, messages=[])
        mock_smart_open.assert_has_calls(
            [
                call((tmp_path / "coverage.json"), "rb"),
                call((tmp_path / "coverage.codecov.json"), "w"),
            ]
        )
        mock_copy_meta.assert_called_with(mock_fd_in, mock_fd_out)
        mock_ijson.kvitems.assert_called_with(mock_fd_in, "files")
        mock_compress_files.assert_called_with("files_in_report", mock_fd_out)
        mock_fd_in.close.assert_called()
        mock_fd_out.close.assert_called()
        mock_fd_out.write.assert_has_calls([call("{"), call("}")])
        assert not (tmp_path / "coverage.json").exists()

    def test_run_preparation_sample(self, tmp_path):
        file_to_compress = tmp_path / "coverage.json"
        file_to_compress.write_text(json.dumps(sample))
        config = {"file_to_compress": file_to_compress}
        plugin = CompressPycoverageContexts(config)
        res = plugin.run_preparation(None)
        assert res == PreparationPluginReturn(success=True, messages=[])
        assert not file_to_compress.exists()
        expected_file = tmp_path / "coverage.codecov.json"
        assert expected_file.exists()
        result = json.loads(expected_file.read_text())
        print(result)
        assert result == {
            "meta": {
                "version": "6.5.0",
                "timestamp": "2023-05-15T18:35:30.641570",
                "branch_coverage": False,
                "show_contexts": True,
            },
            "totals": {
                "covered_lines": 416,
                "num_statements": 437,
                "percent_covered": "95.19450800915332",
                "percent_covered_display": "95",
                "missing_lines": 21,
                "excluded_lines": 0,
            },
            "files": {
                "awesome.py": {
                    "executed_lines": [1, 2, 3, 5],
                    "summary": {
                        "covered_lines": 4,
                        "num_statements": 5,
                        "percent_covered": "80.0",
                        "percent_covered_display": "80",
                        "missing_lines": 1,
                        "excluded_lines": 0,
                    },
                    "missing_lines": [4],
                    "excluded_lines": [],
                    "contexts": {
                        "1": [0],
                        "2": [1, 2],
                        "3": [2, 3],
                        "5": [4],
                    },
                },
                "__init__.py": {
                    "executed_lines": [],
                    "summary": {
                        "covered_lines": 0,
                        "num_statements": 4,
                        "percent_covered": "0.0",
                        "percent_covered_display": "0",
                        "missing_lines": 4,
                        "excluded_lines": 0,
                    },
                    "missing_lines": [1, 3, 4, 5],
                    "excluded_lines": [],
                    "contexts": {},
                },
            },
            "labels_table": {
                "0": "",
                "1": "label_1",
                "2": "label_2",
                "3": "label_3",
                "4": "label_5",
            },
        }
