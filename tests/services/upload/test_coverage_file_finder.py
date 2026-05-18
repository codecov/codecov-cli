import tempfile
from pathlib import Path

import pytest

from codecov_cli.helpers.upload_type import ReportType
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

    def test_find_coverage_files_test_results(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "subsub").mkdir()
        (tmp_path / "node_modules").mkdir()

        should_find = ["junit.xml", "abc.junit.xml", "sub/junit.xml"]

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

        for filename in should_find:
            (tmp_path / filename).touch()

        for filename in should_ignore:
            (tmp_path / filename).touch()

        expected = {
            UploadCollectionResultFile((tmp_path / file)) for file in should_find
        }
        actual = set(
            FileFinder(tmp_path, report_type=ReportType.TEST_RESULTS).find_files()
        )
        assert actual == expected

        extra = tmp_path / "sub" / "nosetests.junit.xml"
        extra.touch()
        actual = set(
            FileFinder(tmp_path, report_type=ReportType.TEST_RESULTS).find_files()
        )
        assert actual - expected == {UploadCollectionResultFile(extra)}


@pytest.fixture()
def coverage_file_finder_fixture():
    temp_dir = tempfile.TemporaryDirectory()  # Create a temporary directory
    project_root = Path(temp_dir.name)
    folders_to_ignore = []
    explicitly_listed_files = [
        project_root / "test_file.abc",
        project_root / "subdirectory" / "another_file.abc",
    ]
    disable_search = False
    coverage_file_finder = FileFinder(
        project_root,
        folders_to_ignore,
        explicitly_listed_files,
        disable_search,
    )
    yield project_root, coverage_file_finder
    temp_dir.cleanup()


class TestCoverageFileFinderUserInput:
    def test_find_coverage_files_with_existing_files(
        self, coverage_file_finder_fixture
    ):
        # Create some sample coverage coverage_file_finder_fixture
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture
        coverage_files = [
            project_root / "coverage.xml",
            project_root / "subdirectory" / "test_coverage.xml",
            project_root / "other_file.txt",
            project_root / ".tox" / "another_file.abc",
        ]
        (project_root / "subdirectory").mkdir()
        (project_root / ".tox").mkdir()
        for file in coverage_files:
            file.touch()

        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )
        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/test_coverage.xml")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        assert result == expected_paths

    def test_find_coverage_files_with_directory_named_as_file(
        self, coverage_file_finder_fixture
    ):
        # Create some sample coverage coverage_file_finder_fixture
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture
        coverage_files = [
            project_root / "coverage.xml" / "coverage.xml",
        ]
        (project_root / "coverage.xml").mkdir()
        for file in coverage_files:
            file.touch()

        coverage_file_finder.explicitly_listed_files = [Path("coverage.xml/coverage.xml")]
        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )
        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/coverage.xml/coverage.xml")),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        assert result == expected_paths

        coverage_file_finder.explicitly_listed_files = [Path("coverage.xml")]
        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )
        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/coverage.xml/coverage.xml")),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        assert result == expected_paths

        coverage_file_finder.explicitly_listed_files = [Path("coverage.xml")]
        coverage_file_finder.disable_search = True
        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )
        expected = []
        expected_paths = sorted([file.get_filename() for file in expected])
        assert result == expected_paths

    def test_find_coverage_files_with_file_in_parent(
        self, coverage_file_finder_fixture
    ):
        # Create some sample coverage coverage_file_finder_fixture
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture
        coverage_files = [
            project_root.parent / "coverage.xml",
        ]
        for file in coverage_files:
            file.touch()

        coverage_file_finder.explicitly_listed_files = [
            project_root.parent / "coverage.xml"
        ]

        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )
        expected = [
            UploadCollectionResultFile(Path(f"{project_root.parent}/coverage.xml"))
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        assert result == expected_paths

    def test_find_coverage_files_with_no_files(self, coverage_file_finder_fixture):
        (
            _,
            coverage_file_finder,
        ) = coverage_file_finder_fixture
        result = coverage_file_finder.find_files()
        assert result == []

    def test_find_coverage_files_with_disabled_search(
        self, coverage_file_finder_fixture
    ):
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture
        # Create some sample coverage coverage_file_finder_fixture
        print("project root", project_root)
        coverage_files = [
            project_root / "test_file.abc",
            project_root / "subdirectory" / "another_file.abc",
            project_root / "subdirectory" / "test_coverage.xml",
            project_root / "other_file.txt",
            project_root / ".tox" / "another_file.abc",
        ]
        (project_root / "subdirectory").mkdir()
        (project_root / ".tox").mkdir()
        for file in coverage_files:
            file.touch()

        # Disable search
        coverage_file_finder.disable_search = True

        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/test_file.abc")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/another_file.abc")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])

        assert result == expected_paths

    def test_find_coverage_files_with_user_specified_files(
        self, coverage_file_finder_fixture
    ):
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture

        # Create some sample coverage coverage_file_finder_fixture
        coverage_files = [
            project_root / "coverage.xml",
            project_root / "subdirectory" / "test_coverage.xml",
            project_root / "test_file.abc",
            project_root / "subdirectory" / "another_file.abc",
            project_root / ".tox" / "another_file.abc",
        ]
        (project_root / "subdirectory").mkdir()
        (project_root / ".tox").mkdir()
        for file in coverage_files:
            file.touch()

        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/test_coverage.xml")
            ),
            UploadCollectionResultFile(Path(f"{project_root}/test_file.abc")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/another_file.abc")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        assert result == expected_paths

    def test_find_coverage_files_with_user_specified_files_not_found(
        self, coverage_file_finder_fixture
    ):
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture

        # Create some sample coverage coverage_file_finder_fixture
        coverage_files = [
            project_root / "coverage.xml",
            project_root / "subdirectory" / "test_coverage.xml",
            project_root / ".tox" / "another_file.abc",
        ]
        (project_root / "subdirectory").mkdir()
        (project_root / ".tox").mkdir()
        for file in coverage_files:
            file.touch()

        # Add a non-existent file to explicitly_listed_files
        coverage_file_finder.explicitly_listed_files.append(
            project_root / "non_existent.xml"
        )

        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/test_coverage.xml")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])
        assert result == expected_paths

    def test_find_coverage_files_with_user_specified_files_in_default_ignored_folder(
        self, coverage_file_finder_fixture
    ):
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture

        # Create some sample coverage files
        coverage_files = [
            project_root / "coverage.xml",
            project_root / "subdirectory" / "test_coverage.xml",
            project_root / "test_file.abc",
            project_root / "subdirectory" / "another_file.abc",
            project_root / ".tox" / "another_file.abc",
        ]
        (project_root / "subdirectory").mkdir()
        (project_root / ".tox").mkdir()
        for file in coverage_files:
            file.touch()

        coverage_file_finder.explicitly_listed_files = [
            project_root / ".tox" / "another_file.abc",
        ]
        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/test_coverage.xml")
            ),
            UploadCollectionResultFile(Path(f"{project_root}/.tox/another_file.abc")),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])

        assert result == expected_paths

    def test_find_coverage_files_with_user_specified_files_in_excluded(
        self, capsys, coverage_file_finder_fixture
    ):
        (
            project_root,
            coverage_file_finder,
        ) = coverage_file_finder_fixture

        # Create some sample coverage coverage_file_finder_fixture
        coverage_files = [
            project_root / "coverage.xml",
            project_root / "subdirectory" / "test_coverage.xml",
            project_root / "test_file.abc",
            project_root / "subdirectory" / "another_file.abc",
            project_root / "subdirectory" / "another_file.bash",
            project_root / ".tox" / "another_file.abc",
        ]
        (project_root / "subdirectory").mkdir()
        (project_root / ".tox").mkdir()
        for file in coverage_files:
            file.touch()

        coverage_file_finder.explicitly_listed_files.append(
            project_root / "subdirectory" / "another_file.bash"
        )
        result = sorted(
            [file.get_filename() for file in coverage_file_finder.find_files()]
        )

        expected = [
            UploadCollectionResultFile(Path(f"{project_root}/coverage.xml")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/test_coverage.xml")
            ),
            UploadCollectionResultFile(Path(f"{project_root}/test_file.abc")),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/another_file.abc")
            ),
            UploadCollectionResultFile(
                Path(f"{project_root}/subdirectory/another_file.bash")
            ),
        ]
        expected_paths = sorted([file.get_filename() for file in expected])

        assert result == expected_paths

        assert (
            "Some files being explicitly added are found in the list of excluded files for upload. We are still going to search for the explicitly added files."
            in capsys.readouterr().err
        )
