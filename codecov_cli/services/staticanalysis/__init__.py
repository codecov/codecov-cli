import asyncio
import json
import logging
import typing
from functools import partial
from multiprocessing import get_context
from pathlib import Path

import click
import httpx
import requests
import yaml

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
):
    ff = select_file_finder(config)
    files = list(ff.find_files(folder, pattern, folders_to_exclude))
    logger.info(f"Running the analyzer on {len(files)} files")
    mapped_func = partial(analyze_file, config)
    all_data = {}
    file_metadata = []
    with click.progressbar(
        length=len(files),
        label="Analyzing files",
    ) as bar:
        with get_context("fork").Pool(processes=numberprocesses) as pool:
            file_results = pool.imap_unordered(mapped_func, files)
            for x in file_results:
                bar.update(1, x)
                if x is not None:
                    res = x.asdict()["result"]
                    all_data[x.filename] = res
                    file_metadata.append(
                        {"filepath": x.filename, "file_hash": res["hash"]}
                    )
    try:
        json_output = {"commit": commit, "filepaths": file_metadata}
        logger.debug(
            "Sending data for server",
            extra=dict(extra_log_attributes=dict(json_payload=json_output)),
        )
        response = requests.post(
            "https://api.codecov.io/staticanalysis/analyses",
            json=json_output,
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
        failed_upload = []
        with click.progressbar(
            length=len(files_that_need_upload),
            label="Uploading files",
        ) as bar:
            limits = httpx.Limits(max_keepalive_connections=3, max_connections=5)
            async with httpx.AsyncClient(limits=limits) as client:
                all_tasks = []
                for el in files_that_need_upload:
                    all_tasks.append(send_single_upload_put(client, all_data, el))
                    bar.update(1, all_data[el["filepath"]])
                resps = await asyncio.gather(*all_tasks)
            for resp in resps:
                if resp["succeeded"]:
                    uploaded_files.append(resp["filepath"])
                else:
                    failed_upload.append(resp["filepath"])
        if failed_upload:
            logger.warning(f"{len(failed_upload)} files failed to upload")
            logger.debug(
                "Failed files",
                extra=dict(extra_log_attributes=dict(filenames=failed_upload)),
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


async def send_single_upload_put(client, all_data, el):
    retryable_statuses = (429,)
    presigned_put = el["raw_upload_location"]
    number_retries = 5
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
    logger.warning(
        "Unable to send data",
        extra=dict(
            extra_log_attributes=dict(
                response=response.text,
                filepath=el["filepath"],
                url=presigned_put,
                latest_status_code=response.status_code,
            )
        ),
    )
    return {
        "status_code": response.status_code,
        "filepath": el["filepath"],
        "succeeded": False,
    }


def analyze_file(config, filename: FileAnalysisRequest):
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
            "error_class": str(type(e)),
        }
        return FileAnalysisResult(
            filename=str(filename.result_filename), error=error_dict
        )
