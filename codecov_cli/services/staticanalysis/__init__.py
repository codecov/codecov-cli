import asyncio
import json
import logging
import typing
from functools import partial
from multiprocessing import Pool
from pathlib import Path

import click
import httpx
import requests

from codecov_cli.helpers import request
from codecov_cli.helpers.config import CODECOV_API_URL
from codecov_cli.services.staticanalysis.analyzers import get_best_analyzer
from codecov_cli.services.staticanalysis.exceptions import AnalysisError
from codecov_cli.services.staticanalysis.finders import select_file_finder
from codecov_cli.services.staticanalysis.types import (
    FileAnalysisRequest,
    FileAnalysisResult,
)

logger = logging.getLogger("codecovcli")


async def run_analysis_entrypoint(
    config: typing.Optional[typing.Dict],
    folder: Path,
    numberprocesses: typing.Optional[int],
    pattern,
    commit: str,
    token: str,
    should_force: bool,
    folders_to_exclude: typing.List[Path],
    enterprise_url: typing.Optional[str],
):
    ff = select_file_finder(config)
    files = list(ff.find_files(folder, pattern, folders_to_exclude))
    processing_results = await process_files(files, numberprocesses, config)
    # Let users know if there were processing errors
    # This is here and not in the funcition so we can add an option to ignore those (possibly)
    # Also makes the function easier to test
    processing_errors = processing_results["processing_errors"]
    log_processing_errors(processing_errors)
    # Upload results metadata to codecov to get list of files that we need to upload
    file_metadata = processing_results["file_metadata"]
    all_data = processing_results["all_data"]
    try:
        json_output = {"commit": commit, "filepaths": file_metadata}
        logger.info(
            "Sending files fingerprints to Codecov",
            extra=dict(
                extra_log_attributes=dict(
                    files_effectively_analyzed=len(json_output["filepaths"])
                )
            ),
        )
        logger.debug(
            "Data sent to Codecov",
            extra=dict(extra_log_attributes=dict(json_payload=json_output)),
        )
        upload_url = enterprise_url or CODECOV_API_URL
        response = request.post(
            f"{upload_url}/staticanalysis/analyses",
            data=json_output,
            headers={"Authorization": f"Repotoken {token}"},
        )
        response_json = response.json()
        if response.status_code >= 500:
            raise click.ClickException("Sorry. Codecov is having problems")
        if response.status_code >= 400:
            raise click.ClickException(
                f"There is some problem with the submitted information.\n{response_json.get('detail')}"
            )
    except requests.RequestException:
        raise click.ClickException(click.style("Unable to reach Codecov", fg="red"))
    logger.info(
        "Received response from server",
        extra=dict(
            extra_log_attributes=dict(time_taken=response.elapsed.total_seconds())
        ),
    )
    logger.debug(
        "Response",
        extra=dict(
            extra_log_attributes=dict(
                response_json=response_json,
            )
        ),
    )

    valid_files_len = len(
        [el for el in response_json["filepaths"] if el["state"].lower() == "valid"]
    )
    created_files_len = len(
        [el for el in response_json["filepaths"] if el["state"].lower() == "created"]
    )
    logger.info(
        f"{valid_files_len} files VALID; {created_files_len} files CREATED",
    )

    files_that_need_upload = [
        el
        for el in response_json["filepaths"]
        if (el["state"].lower() == "created" or should_force)
    ]

    if files_that_need_upload:
        uploaded_files = []
        failed_uploads = []
        with click.progressbar(
            length=len(files_that_need_upload),
            label=f"Upload info to storage",
        ) as bar:
            # It's better to have less files competing over CPU time when uploading
            # Especially if we might have large files
            limits = httpx.Limits(max_connections=20)
            # Because there might be too many files to upload we will ignore most timeouts
            timeout = httpx.Timeout(read=None, pool=None, connect=None, write=10.0)
            async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
                all_tasks = []
                for el in files_that_need_upload:
                    all_tasks.append(send_single_upload_put(client, all_data, el))
                try:
                    for task in asyncio.as_completed(all_tasks):
                        resp = await task
                        bar.update(1, el["filepath"])
                        if resp["succeeded"]:
                            uploaded_files.append(resp["filepath"])
                        else:
                            failed_uploads.append(resp["filepath"])
                except asyncio.CancelledError:
                    message = (
                        "Unknown error cancelled the upload tasks.\n"
                        + f"Uploaded {len(uploaded_files)}/{len(files_that_need_upload)} files successfully."
                    )
                    raise click.ClickException(message)
        if failed_uploads:
            logger.warning(f"{len(failed_uploads)} files failed to upload")
            logger.debug(
                "Failed files",
                extra=dict(extra_log_attributes=dict(filenames=failed_uploads)),
            )
        logger.info(
            f"Uploaded {len(uploaded_files)} files",
        )
        logger.debug(
            "Uploaded files",
            extra=dict(extra_log_attributes=dict(filenames=uploaded_files)),
        )
    else:
        logger.info("All files are already uploaded!")
    try:
        response = send_finish_signal(response_json, upload_url, token)
    except requests.RequestException:
        raise click.ClickException(click.style("Unable to reach Codecov", fg="red"))
    logger.info(
        "Received response with status code %s from server",
        response.status_code,
        extra=dict(
            extra_log_attributes=dict(time_taken=response.elapsed.total_seconds())
        ),
    )
    log_processing_errors(processing_errors)


def log_processing_errors(processing_errors: typing.Dict[str, str]) -> None:
    if len(processing_errors) > 0:
        logger.error(
            f"{len(processing_errors)} files have processing errors and have been IGNORED."
        )
        for file, error in processing_errors.items():
            logger.error(f"-> {file}: ERROR {error}")


async def process_files(
    files_to_analyze: typing.List[FileAnalysisRequest],
    numberprocesses: int,
    config: typing.Optional[typing.Dict],
):
    logger.info(f"Running the analyzer on {len(files_to_analyze)} files")
    mapped_func = partial(analyze_file, config)
    all_data = {}
    file_metadata = []
    errors = {}
    with click.progressbar(
        length=len(files_to_analyze),
        label="Analyzing files",
    ) as bar:
        # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
        # from the link above, we want to use the default start methods
        with Pool(processes=numberprocesses) as pool:
            file_results = pool.imap_unordered(mapped_func, files_to_analyze)
            for result in file_results:
                bar.update(1, result)
                if result is not None:
                    if result.result:
                        all_data[result.filename] = result.result
                        file_metadata.append(
                            {
                                "filepath": result.filename,
                                "file_hash": result.result["hash"],
                            }
                        )
                    elif result.error:
                        errors[result.filename] = result.error
    logger.info("All files have been processed")
    return dict(
        all_data=all_data, file_metadata=file_metadata, processing_errors=errors
    )


async def send_single_upload_put(client, all_data, el) -> typing.Dict:
    retryable_statuses = (429,)
    presigned_put = el["raw_upload_location"]
    number_retries = 5
    try:
        for current_retry in range(number_retries):
            response = await client.put(
                presigned_put, data=json.dumps(all_data[el["filepath"]])
            )
            if response.status_code < 300:
                return {
                    "status_code": response.status_code,
                    "filepath": el["filepath"],
                    "succeeded": True,
                }
            if response.status_code in retryable_statuses:
                await asyncio.sleep(2**current_retry)
        status_code = response.status_code
        message_to_warn = response.text
        exception = None
    except httpx.HTTPError as exp:
        status_code = None
        exception = type(exp)
        message_to_warn = str(exp)
    logger.warning(
        "Unable to send single_upload_put",
        extra=dict(
            extra_log_attributes=dict(
                message=message_to_warn,
                exception=exception,
                filepath=el["filepath"],
                latest_status_code=status_code,
            )
        ),
    )
    return {
        "status_code": status_code,
        "exception": exception,
        "filepath": el["filepath"],
        "succeeded": False,
    }


def send_finish_signal(response_json, upload_url: str, token: str):
    external_id = response_json["external_id"]
    logger.debug(
        "Sending finish signal to let API know to schedule static analysis task",
        extra=dict(extra_log_attributes=dict(external_id=external_id)),
    )
    response = request.post(
        f"{upload_url}/staticanalysis/analyses/{external_id}/finish",
        headers={"Authorization": f"Repotoken {token}"},
    )
    if response.status_code >= 500:
        raise click.ClickException("Sorry. Codecov is having problems")
    if response.status_code >= 400:
        raise click.ClickException(
            f"There is some problem with the submitted information.\n{response_json.get('detail')}"
        )
    return response


def analyze_file(
    config, filename: FileAnalysisRequest
) -> typing.Optional[FileAnalysisResult]:
    try:
        with open(filename.actual_filepath, "rb") as file:
            actual_code = file.read()
        analyzer = get_best_analyzer(filename, actual_code)
        if analyzer is None:
            return None
        output = analyzer.process()
        if output is None:
            return None
        return FileAnalysisResult(filename=filename.result_filename, result=output)
    except AnalysisError as e:
        error_dict = {
            "filename": str(filename.result_filename),
            "error": str(e),
        }
        return FileAnalysisResult(
            filename=str(filename.result_filename), error=error_dict
        )
