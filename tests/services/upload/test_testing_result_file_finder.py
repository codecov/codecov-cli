import tempfile
import unittest
from pathlib import Path

from codecov_cli.services.upload.finders.testing_result_file_finder import (
    TestingResultFileFinder,
)
from codecov_cli.types import UploadCollectionResultFile


class TestTestingResultFileFinder(object):
    def test_find_files_mocked_search_files(self, mocker):
        mocker.patch(
            "codecov_cli.services.upload.finders.result_file_finder.search_files",
            return_value=[],
        )
        assert TestingResultFileFinder().find_files() == []

        coverage_files_paths = [
            Path("a/junit.xml"),
        ]

        mocker.patch(
            "codecov_cli.services.upload.finders.result_file_finder.search_files",
            return_value=coverage_files_paths,
        )

        expected = [
            UploadCollectionResultFile(Path("a/junit.xml")),
        ]

        expected_paths = sorted([file.get_filename() for file in expected])

        actual_paths = sorted(
            [file.get_filename() for file in TestingResultFileFinder().find_files()]
        )

        assert expected_paths == actual_paths

    def test_find_files(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "subsub").mkdir()
        (tmp_path / "node_modules").mkdir()

        should_find = ["junit.xml", "sub/subsub/junit.xml"]

        should_ignore = [
            "abc.codecov.exe",
            "sub/abc.codecov.exe",
            "codecov.exe",
            "__pycache__",
            "sub/subsub/__pycache__",
            ".gitignore",
            "a.sql",
            "a.csv",
            ".abc-coveragerc",
            ".coverage-xyz",
            "sub/scoverage.measurements.xyz",
            "sub/test_abcd_coverage.txt",
            "test-result-ff-codecoverage.json",
            "node_modules/abc-coverage.cov",
            "node_modules/junit.xml",
        ]

        for filename in should_find:
            (tmp_path / filename).touch()

        for filename in should_ignore:
            (tmp_path / filename).touch()

        expected = {
            UploadCollectionResultFile((tmp_path / file)) for file in should_find
        }
        actual = set(TestingResultFileFinder(tmp_path).find_files())
        assert actual == expected

        extra = tmp_path / "sub" / "junit.xml"
        extra.touch()
        actual = set(TestingResultFileFinder(tmp_path).find_files())
        assert actual - expected == {UploadCollectionResultFile(extra)}


class TestTestingResultFileFinderUserInput(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()  # Create a temporary directory
        self.project_root = Path(self.temp_dir.name)
        self.folders_to_ignore = []
        self.explicitly_listed_files = [
            self.project_root / "subdirectory" / "junit.xml",
        ]
        self.disable_search = False
        self.testing_result_file_finder = TestingResultFileFinder(
            self.project_root,
            self.folders_to_ignore,
            self.explicitly_listed_files,
            self.disable_search,
        )

    def tearDown(self):
        self.temp_dir.cleanup()  # Clean up the temporary directory

    def test_find_files_with_existing_files(self):
        # Create some sample coverage files
        coverage_files = [
            self.project_root / "subdirectory" / "junit.xml",
            self.project_root / "other_file.txt",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        result = sorted(
            [
                file.get_filename()
                for file in self.testing_result_file_finder.find_files()
            ]
        )
        expected = [
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/junit.xml")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        self.assertEqual(result, expected_paths)

    def test_find_files_with_no_files(self):
        result = self.testing_result_file_finder.find_files()
        self.assertEqual(result, [])

    def test_find_files_with_disabled_search(self):
        # Create some sample coverage files
        print("project root", self.project_root)
        coverage_files = [
            self.project_root / "subdirectory" / "junit.xml",
            self.project_root / "junit.xml",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        # Disable search
        self.testing_result_file_finder.disable_search = True

        result = sorted(
            [
                file.get_filename()
                for file in self.testing_result_file_finder.find_files()
            ]
        )

        expected = [
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/junit.xml")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])

        self.assertEqual(result, expected_paths)

    def test_find_files_with_user_specified_files(self):
        # Create some sample coverage files
        coverage_files = [
            self.project_root / "subdirectory" / "junit.xml",
            self.project_root / "extra.xml",
            self.project_root / "junit.xml",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        self.testing_result_file_finder.explicitly_listed_files.append(
            self.project_root / "extra.xml"
        )

        result = sorted(
            [
                file.get_filename()
                for file in self.testing_result_file_finder.find_files()
            ]
        )

        expected = [
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/junit.xml")
            ),
            UploadCollectionResultFile(Path(f"{self.project_root}/junit.xml")),
            UploadCollectionResultFile(Path(f"{self.project_root}/extra.xml")),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        self.assertEqual(result, expected_paths)

    def test_find_files_with_user_specified_files_not_found(self):
        # Create some sample coverage files
        coverage_files = [
            self.project_root / "junit.xml",
            self.project_root / "subdirectory" / "junit.xml",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        # Add a non-existent file to explicitly_listed_files
        self.testing_result_file_finder.explicitly_listed_files.append(
            self.project_root / "non_existent.xml"
        )

        result = sorted(
            [
                file.get_filename()
                for file in self.testing_result_file_finder.find_files()
            ]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{self.project_root}/junit.xml")),
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/junit.xml")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        self.assertEqual(result, expected_paths)
