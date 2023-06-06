from pathlib import Path

from codecov_cli.services.upload.coverage_file_finder import CoverageFileFinder
from codecov_cli.types import UploadCollectionResultFile


class TestCoverageFileFinder(object):
    def test_find_coverage_files_mocked_search_files(self, mocker):
        mocker.patch(
            "codecov_cli.services.upload.coverage_file_finder.search_files",
            return_value=[],
        )
        assert CoverageFileFinder().find_coverage_files() == []

        coverage_files_paths = [
            Path("a/b.txt"),
            Path("c.txt"),
        ]

        mocker.patch(
            "codecov_cli.services.upload.coverage_file_finder.search_files",
            return_value=coverage_files_paths,
        )

        expected = [
            UploadCollectionResultFile(Path("c.txt")),
            UploadCollectionResultFile(Path("a/b.txt")),
        ]

        assert CoverageFileFinder().find_coverage_files() == expected

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
        actual = set(CoverageFileFinder(tmp_path).find_coverage_files())
        assert actual == expected

        extra = tmp_path / "sub" / "nosetests.xml"
        extra.touch()
        actual = set(CoverageFileFinder(tmp_path).find_coverage_files())
        assert actual - expected == {UploadCollectionResultFile(extra)}
