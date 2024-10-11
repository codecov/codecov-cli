import logging
import pathlib
import typing

import click

from codecov_cli.services.upload.network_finder import NetworkFinder
from codecov_cli.services.upload.upload_sender import UploadSender
from codecov_cli.helpers.options import global_options
from codecov_cli.types import CommandContext, UploadCollectionResult
from codecov_cli.helpers.request import log_warnings_and_errors_if_any

logger = logging.getLogger("codecovcli")

@click.command()
@click.option(
    "--root-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=pathlib.Path),
    default=pathlib.Path.cwd(),
    help="Root directory for searching files (default: current working directory)",
)
@click.option(
    "--network-filter",
    help="Regex to filter files (e.g., '.*\\.py')",
)
@click.option(
    "--network-prefix",
    help="Prefix to prepend to file paths",
)
@click.option(
    "--include-git-files",
    is_flag=True,
    default=False,
    help="Include files tracked by git",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Perform a dry run without actually uploading files",
)
@click.option(
    "--commit-sha",
    required=True,
    help="Commit SHA to associate with the upload",
)
@click.option(
    "--token",
    required=True,
    help="Codecov token for authentication",
)
@global_options
@click.pass_context
def network_upload(
    ctx: CommandContext,
    root_dir: pathlib.Path,
    network_filter: typing.Optional[str],
    network_prefix: typing.Optional[str],
    include_git_files: bool,
    dry_run: bool,
    commit_sha: str,
    slug: typing.Optional[str],
    token: typing.Optional[str],
    git_service: typing.Optional[str],
    fail_on_error: bool,
):
    """
    Find and list files in the project network, then upload them to Codecov.
    """
    network_finder = NetworkFinder(
        versioning_system=ctx.obj["versioning_system"],
        network_root_folder=root_dir,
        network_filter=network_filter,
        network_prefix=network_prefix,
    )

    files = network_finder.find_files(include_git_files)

    if not files:
        logger.warning("No files found in the network.")
        return

    logger.info(f"Found {len(files)} files in the network:")
    

    if dry_run:
        logger.info("Dry run: No files will be uploaded.")
        for file in files:
            click.echo(file)
        return

    logger.info("Preparing to upload files...")

    # Prepare the upload data
    upload_data = UploadCollectionResult(
        network=files,
        files=[],  # We're not uploading coverage files in this command
        file_fixes=[],
    )

    # Create an UploadSender instance
    sender = UploadSender()

    # Send the upload data
    sending_result = sender.send_upload_data(
        upload_data,
        commit_sha,
        token,
        env_vars={},
        report_code=None,
        upload_file_type="network",
        name=None,
        branch=None,
        slug=slug,
        pull_request_number=None,
        build_code=None,
        build_url=None,
        job_code=None,
        flags=[],
        ci_service=None,
        git_service=git_service,
        enterprise_url=ctx.obj.get("enterprise_url"),
    )

    # Log any warnings or errors
    log_warnings_and_errors_if_any(sending_result, "Network Upload", fail_on_error=False)

    if sending_result.status_code == 200:
        logger.info("Network files successfully uploaded to Codecov.")
    else:
        logger.error(f"Failed to upload network files. Status code: {sending_result.status_code}")
        if fail_on_error:
            exit(1) 
