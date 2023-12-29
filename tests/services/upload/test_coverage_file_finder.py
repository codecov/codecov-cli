import tempfile
import unittest
from pathlib import Path

from codecov_cli.services.upload.file_finder import FileFinder
from codecov_cli.types import UploadCollectionResultFile


class TestCoverageFileFinder(object):
    def test_find_coverage_files_mocked_search_files(self, mocker):
        mocker.patch(
            "codecov_cli.services.upload.file_finder.search_files",
            return_value=[],
        )
        assert FileFinder().find_files() == []

        coverage_files_paths = [
            Path("a/b.txt"),
            Path("c.txt"),
        ]

        mocker.patch(
            "codecov_cli.services.upload.file_finder.search_files",
            return_value=coverage_files_paths,
        )

        expected = [
            UploadCollectionResultFile(Path("c.txt")),
            UploadCollectionResultFile(Path("a/b.txt")),
        ]

        expected_paths = sorted([file.get_filename() for file in expected])

        actual_paths = sorted(
            [file.get_filename() for file in FileFinder().find_files()]
        )

        assert expected_paths == actual_paths

    def test_find_coverage_files(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "subsub").mkdir()
        (tmp_path / "node_modules").mkdir()

        should_find = [
            "abc-coverage.cov",
            "coverage-abc.abc",
            "sub/coverage-abc.abc",
            "sub/subsub/coverage-abc.abc",
            "coverage.abc",
            "jacocoxyz.xml",
            "sub/jacocoxyz.xml",
            "codecov.abc",
            "sub/subsub/codecov.abc",
            "xyz.codecov.abc",
            "sub/xyz.codecov.abc",
            "sub/subsub/xyz.codecov.abc",
            "cover.out",
            "abc.gcov",
            "sub/abc.gcov",
            "sub/subsub/abc.gcov",
        ]

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
        ]

        for filename in should_find:
            (tmp_path / filename).touch()

        for filename in should_ignore:
            (tmp_path / filename).touch()

        expected = {
            UploadCollectionResultFile((tmp_path / file)) for file in should_find
        }
        actual = set(FileFinder(tmp_path).find_files())
        assert actual == expected

        extra = tmp_path / "sub" / "nosetests.xml"
        extra.touch()
        actual = set(FileFinder(tmp_path).find_files())
        assert actual - expected == {UploadCollectionResultFile(extra)}


class TestCoverageFileFinderUserInput(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()  # Create a temporary directory
        self.project_root = Path(self.temp_dir.name)
        self.folders_to_ignore = []
        self.explicitly_listed_files = [
            self.project_root / "test_file.abc",
            self.project_root / "subdirectory" / "another_file.abc",
        ]
        self.disable_search = False
        self.coverage_file_finder = FileFinder(
            self.project_root,
            self.folders_to_ignore,
            self.explicitly_listed_files,
            self.disable_search,
        )

    def tearDown(self):
        self.temp_dir.cleanup()  # Clean up the temporary directory

    def test_find_coverage_files_with_existing_files(self):
        # Create some sample coverage files
        coverage_files = [
            self.project_root / "coverage.xml",
            self.project_root / "subdirectory" / "test_coverage.xml",
            self.project_root / "other_file.txt",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        result = sorted(
            [file.get_filename() for file in self.coverage_file_finder.find_files()]
        )
        expected = [
            UploadCollectionResultFile(Path(f"{self.project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/test_coverage.xml")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        self.assertEqual(result, expected_paths)

    def test_find_coverage_files_with_no_files(self):
        result = self.coverage_file_finder.find_files()
        self.assertEqual(result, [])

    def test_find_coverage_files_with_disabled_search(self):
        # Create some sample coverage files
        print("project root", self.project_root)
        coverage_files = [
            self.project_root / "test_file.abc",
            self.project_root / "subdirectory" / "another_file.abc",
            self.project_root / "subdirectory" / "test_coverage.xml",
            self.project_root / "other_file.txt",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        # Disable search
        self.coverage_file_finder.disable_search = True

        result = sorted(
            [file.get_filename() for file in self.coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{self.project_root}/test_file.abc")),
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/another_file.abc")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])

        self.assertEqual(result, expected_paths)

    def test_find_coverage_files_with_user_specified_files(self):
        # Create some sample coverage files
        coverage_files = [
            self.project_root / "coverage.xml",
            self.project_root / "subdirectory" / "test_coverage.xml",
            self.project_root / "test_file.abc",
            self.project_root / "subdirectory" / "another_file.abc",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        result = sorted(
            [file.get_filename() for file in self.coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{self.project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/test_coverage.xml")
            ),
            UploadCollectionResultFile(Path(f"{self.project_root}/test_file.abc")),
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/another_file.abc")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        self.assertEqual(result, expected_paths)

    def test_find_coverage_files_with_user_specified_files_not_found(self):
        # Create some sample coverage files
        coverage_files = [
            self.project_root / "coverage.xml",
            self.project_root / "subdirectory" / "test_coverage.xml",
        ]
        (self.project_root / "subdirectory").mkdir()
        for file in coverage_files:
            file.touch()

        # Add a non-existent file to explicitly_listed_files
        self.coverage_file_finder.explicitly_listed_files.append(
            self.project_root / "non_existent.xml"
        )

        result = sorted(
            [file.get_filename() for file in self.coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{self.project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{self.project_root}/subdirectory/test_coverage.xml")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        self.assertEqual(result, expected_paths)
