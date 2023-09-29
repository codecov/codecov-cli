from pathlib import Path
from unittest.mock import MagicMock

import click
import pytest
import requests
import responses
from responses import matchers

from codecov_cli.services.staticanalysis import process_files, run_analysis_entrypoint
from codecov_cli.services.staticanalysis.types import (
    FileAnalysisRequest,
    FileAnalysisResult,
)


class TestStaticAnalysisService:
    @pytest.mark.asyncio
    async def test_process_files_with_error(self, mocker):
        files_found = list(
            map(
                lambda filename: FileAnalysisRequest(str(filename), Path(filename)),
                [
                    "correct_file.py",
                    "error_file.py",
                ],
            )
        )
        mock_get_context = mocker.patch(
            "codecov_cli.services.staticanalysis.get_context"
        )

        def side_effect(config, filename: FileAnalysisRequest):
            if filename.result_filename == "correct_file.py":
                return FileAnalysisResult(
                    filename=filename.result_filename, result={"hash": "abc123"}
                )
            if filename.result_filename == "error_file.py":
                return FileAnalysisResult(
                    filename=filename.result_filename, error="some error @ line 12"
                )
            # Should not get here, so fail test
            assert False

        mock_analyze_function = mocker.patch(
            "codecov_cli.services.staticanalysis.analyze_file"
        )
        mock_analyze_function.side_effect = side_effect

        def imap_side_effect(mapped_func, files):
            results = []
            for file in files:
                results.append(mapped_func(file))
            return results

        mock_get_context.return_value.Pool.return_value.__enter__.return_value.imap_unordered.side_effect = (
            imap_side_effect
        )

        results = await process_files(files_found, 1, {})
        mock_get_context.return_value.Pool.return_value.__enter__.return_value.imap_unordered.assert_called()
        assert mock_analyze_function.call_count == 2
        assert results == dict(
            all_data={"correct_file.py": {"hash": "abc123"}},
            file_metadata=[{"file_hash": "abc123", "filepath": "correct_file.py"}],
            processing_errors={"error_file.py": "some error @ line 12"},
        )

    @pytest.mark.asyncio
    async def test_static_analysis_service(self, mocker):
        mock_file_finder = mocker.patch(
            "codecov_cli.services.staticanalysis.select_file_finder"
        )
        mock_send_upload_put = mocker.patch(
            "codecov_cli.services.staticanalysis.send_single_upload_put"
        )

        # Doing it this way to support Python 3.7
        async def side_effect(*args, **kwargs):
            return MagicMock()

        mock_send_upload_put.side_effect = side_effect

        files_found = map(
            lambda filename: FileAnalysisRequest(str(filename), Path(filename)),
            [
                "samples/inputs/sample_001.py",
                "samples/inputs/sample_002.py",
            ],
        )
        mock_file_finder.return_value.find_files = MagicMock(return_value=files_found)
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses",
                json={
                    "external_id": "externalid",
                    "filepaths": [
                        {
                            "state": "created",
                            "filepath": "samples/inputs/sample_001.py",
                            "raw_upload_location": "http://storage-url",
                        },
                        {
                            "state": "valid",
                            "filepath": "samples/inputs/sample_002.py",
                            "raw_upload_location": "http://storage-url",
                        },
                    ],
                },
                status=200,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses/externalid/finish",
                status=204,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )

            await run_analysis_entrypoint(
                config={},
                folder=".",
                numberprocesses=1,
                pattern="*.py",
                token="STATIC_TOKEN",
                commit="COMMIT",
                should_force=False,
                folders_to_exclude=[],
                enterprise_url=None,
            )
        mock_file_finder.assert_called_with({})
        mock_file_finder.return_value.find_files.assert_called()
        assert mock_send_upload_put.call_count == 1
        args, _ = mock_send_upload_put.call_args
        assert args[2] == {
            "state": "created",
            "filepath": "samples/inputs/sample_001.py",
            "raw_upload_location": "http://storage-url",
        }

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "finish_endpoint_response,expected",
        [
            (500, "Codecov is having problems"),
            (400, "some problem with the submitted information"),
        ],
    )
    async def test_static_analysis_service_finish_fails_status_code(
        self, mocker, finish_endpoint_response, expected
    ):
        mock_file_finder = mocker.patch(
            "codecov_cli.services.staticanalysis.select_file_finder"
        )
        mock_send_upload_put = mocker.patch(
            "codecov_cli.services.staticanalysis.send_single_upload_put"
        )

        # Doing it this way to support Python 3.7
        async def side_effect(*args, **kwargs):
            return MagicMock()

        mock_send_upload_put.side_effect = side_effect

        files_found = map(
            lambda filename: FileAnalysisRequest(str(filename), Path(filename)),
            [
                "samples/inputs/sample_001.py",
                "samples/inputs/sample_002.py",
            ],
        )
        mock_file_finder.return_value.find_files = MagicMock(return_value=files_found)
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses",
                json={
                    "external_id": "externalid",
                    "filepaths": [
                        {
                            "state": "created",
                            "filepath": "samples/inputs/sample_001.py",
                            "raw_upload_location": "http://storage-url",
                        },
                        {
                            "state": "valid",
                            "filepath": "samples/inputs/sample_002.py",
                            "raw_upload_location": "http://storage-url",
                        },
                    ],
                },
                status=200,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses/externalid/finish",
                status=finish_endpoint_response,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            with pytest.raises(click.ClickException, match=expected):
                await run_analysis_entrypoint(
                    config={},
                    folder=".",
                    numberprocesses=1,
                    pattern="*.py",
                    token="STATIC_TOKEN",
                    commit="COMMIT",
                    should_force=False,
                    folders_to_exclude=[],
                    enterprise_url=None,
                )
        mock_file_finder.assert_called_with({})
        mock_file_finder.return_value.find_files.assert_called()
        assert mock_send_upload_put.call_count == 1
        args, _ = mock_send_upload_put.call_args
        assert args[2] == {
            "state": "created",
            "filepath": "samples/inputs/sample_001.py",
            "raw_upload_location": "http://storage-url",
        }

    @pytest.mark.asyncio
    async def test_static_analysis_service_finish_fails_request_exception(self, mocker):
        mock_file_finder = mocker.patch(
            "codecov_cli.services.staticanalysis.select_file_finder"
        )
        mock_send_upload_put = mocker.patch(
            "codecov_cli.services.staticanalysis.send_single_upload_put"
        )

        # Doing it this way to support Python 3.7
        async def side_effect(*args, **kwargs):
            return MagicMock()

        mock_send_upload_put.side_effect = side_effect

        files_found = map(
            lambda filename: FileAnalysisRequest(str(filename), Path(filename)),
            [
                "samples/inputs/sample_001.py",
                "samples/inputs/sample_002.py",
            ],
        )
        mock_file_finder.return_value.find_files = MagicMock(return_value=files_found)
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses",
                json={
                    "external_id": "externalid",
                    "filepaths": [
                        {
                            "state": "created",
                            "filepath": "samples/inputs/sample_001.py",
                            "raw_upload_location": "http://storage-url",
                        },
                        {
                            "state": "valid",
                            "filepath": "samples/inputs/sample_002.py",
                            "raw_upload_location": "http://storage-url",
                        },
                    ],
                },
                status=200,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses/externalid/finish",
                body=requests.RequestException(),
            )
            with pytest.raises(click.ClickException, match="Unable to reach Codecov"):
                await run_analysis_entrypoint(
                    config={},
                    folder=".",
                    numberprocesses=1,
                    pattern="*.py",
                    token="STATIC_TOKEN",
                    commit="COMMIT",
                    should_force=False,
                    folders_to_exclude=[],
                    enterprise_url=None,
                )
        mock_file_finder.assert_called_with({})
        mock_file_finder.return_value.find_files.assert_called()
        assert mock_send_upload_put.call_count == 1
        args, _ = mock_send_upload_put.call_args
        assert args[2] == {
            "state": "created",
            "filepath": "samples/inputs/sample_001.py",
            "raw_upload_location": "http://storage-url",
        }

    @pytest.mark.asyncio
    async def test_static_analysis_service_should_force_option(self, mocker):
        mock_file_finder = mocker.patch(
            "codecov_cli.services.staticanalysis.select_file_finder"
        )
        mock_send_upload_put = mocker.patch(
            "codecov_cli.services.staticanalysis.send_single_upload_put"
        )

        # Doing it this way to support Python 3.7
        async def side_effect(*args, **kwargs):
            return MagicMock()

        mock_send_upload_put.side_effect = side_effect

        files_found = map(
            lambda filename: FileAnalysisRequest(str(filename), Path(filename)),
            [
                "samples/inputs/sample_001.py",
                "samples/inputs/sample_002.py",
            ],
        )
        mock_file_finder.return_value.find_files = MagicMock(return_value=files_found)
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses",
                json={
                    "external_id": "externalid",
                    "filepaths": [
                        {
                            "state": "created",
                            "filepath": "samples/inputs/sample_001.py",
                            "raw_upload_location": "http://storage-url",
                        },
                        {
                            "state": "valid",
                            "filepath": "samples/inputs/sample_002.py",
                            "raw_upload_location": "http://storage-url",
                        },
                    ],
                },
                status=200,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses/externalid/finish",
                status=204,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            await run_analysis_entrypoint(
                config={},
                folder=".",
                numberprocesses=1,
                pattern="*.py",
                token="STATIC_TOKEN",
                commit="COMMIT",
                should_force=True,
                folders_to_exclude=[],
                enterprise_url=None,
            )
        mock_file_finder.assert_called_with({})
        mock_file_finder.return_value.find_files.assert_called()
        assert mock_send_upload_put.call_count == 2

    @pytest.mark.asyncio
    async def test_static_analysis_service_no_upload(self, mocker):
        mock_file_finder = mocker.patch(
            "codecov_cli.services.staticanalysis.select_file_finder"
        )
        mock_send_upload_put = mocker.patch(
            "codecov_cli.services.staticanalysis.send_single_upload_put"
        )

        # Doing it this way to support Python 3.7
        async def side_effect(*args, **kwargs):
            return MagicMock()

        mock_send_upload_put.side_effect = side_effect

        files_found = map(
            lambda filename: FileAnalysisRequest(str(filename), Path(filename)),
            [
                "samples/inputs/sample_001.py",
                "samples/inputs/sample_002.py",
            ],
        )
        mock_file_finder.return_value.find_files = MagicMock(return_value=files_found)
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses",
                json={
                    "external_id": "externalid",
                    "filepaths": [
                        {
                            "state": "valid",
                            "filepath": "samples/inputs/sample_001.py",
                            "raw_upload_location": "http://storage-url",
                        },
                        {
                            "state": "valid",
                            "filepath": "samples/inputs/sample_002.py",
                            "raw_upload_location": "http://storage-url",
                        },
                    ],
                },
                status=200,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )
            rsps.add(
                responses.POST,
                "https://api.codecov.io/staticanalysis/analyses/externalid/finish",
                status=204,
                match=[
                    matchers.header_matcher({"Authorization": "Repotoken STATIC_TOKEN"})
                ],
            )

            await run_analysis_entrypoint(
                config={},
                folder=".",
                numberprocesses=1,
                pattern="*.py",
                token="STATIC_TOKEN",
                commit="COMMIT",
                should_force=False,
                folders_to_exclude=[],
                enterprise_url=None,
            )
        mock_file_finder.assert_called_with({})
        mock_file_finder.return_value.find_files.assert_called()
        assert mock_send_upload_put.call_count == 0
