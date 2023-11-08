import json
import logging
import pathlib
from decimal import Decimal
from typing import Any, List

import ijson

from codecov_cli.plugins.types import PreparationPluginReturn

logger = logging.getLogger("codecovcli")


class Encoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)


class CompressPycoverageContextsConfig(dict):
    @property
    def file_to_compress(self) -> pathlib.Path:
        """
        The report file to compress.
        file_to_compress: Union[str, pathlib.Path] [default coverage.json]
        """
        return pathlib.Path(self.get("file_to_compress", "coverage.json"))

    @property
    def delete_uncompressed(self) -> bool:
        """
        Flag indicating to delete the original file after compressing.
        Recommended to avoid uploading the uncompressed file.
        delete_uncompressed: bool [default True]
        """
        return self.get("delete_uncompressed", True)


class CompressPycoverageContexts(object):
    def __init__(self, config: dict = None) -> None:
        if config is None:
            config = {}
        self.config = CompressPycoverageContextsConfig(config)
        self.file_to_compress = self.config.file_to_compress
        self.file_to_write = pathlib.Path(
            str(self.file_to_compress).replace(".json", "") + ".codecov.json"
        )

    def run_preparation(self, collector) -> PreparationPluginReturn:
        if not self.file_to_compress.exists():
            logger.warning(
                f"File to compress {self.file_to_compress} not found. Aborting"
            )
            return PreparationPluginReturn(
                success=False,
                messages=[f"File to compress {self.file_to_compress} not found."],
            )
        if not self.file_to_compress.is_file():
            logger.warning(
                f"File to compress {self.file_to_compress} is not a file. Aborting"
            )
            return PreparationPluginReturn(
                success=False,
                messages=[f"File to compress {self.file_to_compress} is not a file."],
            )
        # Create in and out streams
        fd_in = open(self.file_to_compress, "rb")
        fd_out = open(self.file_to_write, "w")
        # Compress the file
        fd_out.write("{")
        self._copy_meta(fd_in, fd_out)
        files_in_report = ijson.kvitems(fd_in, "files")
        self._compress_files(files_in_report, fd_out)
        fd_out.write("}")
        # Close streams
        fd_in.close()
        fd_out.close()
        logger.info(f"Compressed report written to {self.file_to_write}")
        # Delete original file if needed
        if self.config.delete_uncompressed:
            logger.info(f"Deleting file {self.file_to_compress}")
            self.file_to_compress.unlink()
        return PreparationPluginReturn(success=True, messages=[])

    def _compress_files(self, files_in_report, fd_out) -> None:
        """
        Compress the 'files' entry in the coverage data.
        This is done by creating a labels table [str -> int] mapping labels to an index.
        This index then substitutes the label itself in the contexts
        """
        labels_table = {}
        nxt_idx = 0

        fd_out.write('"files":{')
        for file_name, file_coverage_details in files_in_report:
            self._copy_file_details(file_name, file_coverage_details, fd_out)
            fd_out.write('"contexts": {')
            contexts = file_coverage_details["contexts"]
            for line_number, labels in contexts.items():
                fd_out.write(f'"{line_number}":')
                new_labels = []
                for label in labels:
                    stripped_label = label.split("|")[0]  # removes '|run' from label
                    if stripped_label not in labels_table:
                        labels_table[stripped_label] = nxt_idx
                        nxt_idx += 1
                    new_labels.append(labels_table[stripped_label])
                fd_out.write(json.dumps(new_labels))
                # fd_out.write(self._bitmask_label_indexes(new_labels))
                fd_out.write(",")
            if len(contexts):  # Avoid removing '{' if contexts == {}
                # Because there will be an extra ',' after the last line
                fd_out.seek(fd_out.tell() - 1)
            # One curly brace for the 'contexts', one for the file_name
            fd_out.write("}},")
        # Because there will be an extra ',' after the last file_name
        fd_out.seek(fd_out.tell() - 1)
        fd_out.write("},")
        # Save the inverted index of labels table in the report
        # So when we are processing the result we have int -> label
        fd_out.write(
            f'"labels_table": {json.dumps({ value: key for key, value in labels_table.items() })}'
        )

    def _copy_file_details(self, file_name, file_details, fd_out) -> None:
        fd_out.write(f'"{file_name}":{{')
        fd_out.write(f'"executed_lines": {file_details["executed_lines"]},')
        fd_out.write(f'"summary": {json.dumps(file_details["summary"], cls=Encoder)},')
        fd_out.write(f'"missing_lines": {file_details["missing_lines"]},')
        fd_out.write(f'"excluded_lines": {file_details["excluded_lines"]},')

    def _copy_meta(self, fd_in, fd_out) -> None:
        meta = ijson.kvitems(fd_in, "")
        for key, value in meta:
            if key == "files":
                continue
            fd_out.write(f'"{key}": {json.dumps(value, cls=Encoder)},')
        fd_in.seek(0)
