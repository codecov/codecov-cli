import json
import logging
from pathlib import PosixPath

import click

from codecov_cli import __version__

logger = logging.getLogger("codecovcli")


def get_cli_args(ctx: click.Context):
    args = ctx.obj["cli_args"]
    args["command"] = str(ctx.command.name)
    args["version"] = f"cli-{__version__}"
    args.update(ctx.params)
    if "token" in args:
        del args["token"]

    filtered_args = {}
    for k in args.keys():
        try:
            if type(args[k]) == PosixPath:
                filtered_args[k] = str(args[k])
            else:
                json.dumps(args[k])
                filtered_args[k] = args[k]
        except Exception as e:
            continue

    return filtered_args
