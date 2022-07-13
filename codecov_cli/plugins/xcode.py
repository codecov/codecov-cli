import logging
import pathlib
import subprocess
import typing

from codecov_cli.helpers.folder_searcher import globs_to_regex, search_files
from codecov_cli.plugins.types import PreparationPluginReturn

logger = logging.getLogger("codecovcli")


class GcovPlugin(object):
    def __init__(
        self,
        derived_data_folder: typing.Optional[pathlib.Path] = None,
        xp: typing.Optional[pathlib.Path] = None,
    ):
        self.derived_data_folder = derived_data_folder or pathlib.Path(
            "$HOME/Library/Developer/Xcode/DerivedData"
        )
        self.xp = xp or ""

    def run_preparation(self, collector) -> PreparationPluginReturn:
        logger.debug("Running xcode plugin...")

        filename_include_regex = globs_to_regex(["*.profdata"])

        matched_paths = [
            str(path)
            for path in search_files(
                folder_to_search=self.derived_data_folder,
                folders_to_ignore=[],
                filename_include_regex=filename_include_regex,
            )
        ]

        if not matched_paths:
            logger.warning("No swift data found.")
            return

        logger.warning("Running swift coverage on the following list of files:")
        for path in matched_paths:
            logger.warning(path)

        s = subprocess.run(
            ["swiftcov", self.xp, *matched_paths],
            cwd=self.derived_data_folder,
            capture_output=True,
        )
        return PreparationPluginReturn(success=True, messages=[s.stdout])
