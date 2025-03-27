import logging
import os
import pathlib
import re
import shutil
import subprocess
import typing
from fnmatch import translate

import sentry_sdk

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files
from codecov_cli.plugins.types import PreparationPluginReturn

logger = logging.getLogger("codecovcli")


class XcodePlugin(object):
    def __init__(
        self,
        app_name: typing.Optional[str] = None,
        derived_data_folder: typing.Optional[pathlib.Path] = None,
    ):
        self.derived_data_folder = (
            derived_data_folder
            or pathlib.Path("~/Library/Developer/Xcode/DerivedData").expanduser()
        )

        # this is to speed up processing and to build reports for the project being tested,
        # if empty the plugin will build reports for every xcode project it finds
        self.app_name = app_name or ""

    def run_preparation(self, collector) -> PreparationPluginReturn:
        with sentry_sdk.start_span(name="xcode"):
            logger.debug("Running xcode plugin...")

            if shutil.which("xcrun") is None:
                logger.warning("xcrun is not installed or can't be found.")
                return

            logger.debug(f"DerivedData folder: {self.derived_data_folder}")

            filename_include_regex = globs_to_regex(["*.profdata"])

            matched_paths = list(
                search_files(
                    folder_to_search=self.derived_data_folder,
                    folders_to_ignore=[],
                    filename_include_regex=filename_include_regex,
                )
            )

            if not matched_paths:
                logger.warning("No swift data found.")
                return

            logger.info(
                "Running swift coverage on the following list of files:",
                extra=dict(
                    extra_log_attributes=dict(
                        matched_paths=[p.as_posix() for p in matched_paths]
                    )
                ),
            )

            for path in matched_paths:
                self.swiftcov(path, self.app_name)

            return PreparationPluginReturn(success=True, messages="")

    def swiftcov(self, path: pathlib.Path, app_name: str) -> None:
        directory = os.path.dirname(path)
        build_dir = pathlib.Path(re.sub("(Build).*", "Build", directory))

        for type in ["app", "framework", "xctest"]:
            filename_include_regex = re.compile(translate(f"*.{type}"))
            matched_dir_paths = search_files(
                folder_to_search=build_dir,
                folders_to_ignore=[],
                filename_include_regex=filename_include_regex,
                search_for_directories=True,
            )

            for dir_path in matched_dir_paths:
                # proj name without extension
                proj = dir_path.stem
                if app_name == "" or (app_name.lower() in proj.lower()):
                    logger.info(f"+ Building reports for {proj} {type}")
                    proj_path = dir_path / proj
                    dest = (
                        proj_path
                        if proj_path.is_file()
                        else dir_path / "Contents/MacOS/{proj}"
                    )
                    output_file_name = f"{proj}.{type}.coverage.txt".replace(" ", "")
                    self.run_llvm_cov(output_file_name, path, dest)

    def run_llvm_cov(
        self, output_file_name: str, path: pathlib.Path, dest: pathlib.Path
    ) -> None:
        with open(output_file_name, "w") as output_file:
            s = subprocess.run(
                [
                    "xcrun",
                    "llvm-cov",
                    "show",
                    "-instr-profile",
                    str(path),
                    str(dest),
                ],
                stdout=output_file,
            )
            # 0 = success
            if s.returncode != 0:
                logger.warning(f"llvm-cov failed to produce results for {dest}")
            else:
                logger.info(f"Generated {output_file_name} file successfully")
