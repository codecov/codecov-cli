import os
from pathlib import PosixPath

import click

from codecov_cli import __version__
from codecov_cli.helpers.args import get_cli_args


def test_get_cli_args():
    ctx = click.Context(click.Command("do-upload"))
    ctx.obj = {}
    ctx.obj["cli_args"] = {
        "verbose": True,
    }
    ctx.params = {
        "branch": "fake_branch",
        "token": "fakeTOKEN",
    }

    expected = {
        "branch": "fake_branch",
        "command": "do-upload",
        "verbose": True,
        "version": f"cli-{__version__}",
    }

    assert get_cli_args(ctx) == expected


def test_get_cli_args_with_posix():
    ctx = click.Context(click.Command("do-upload"))
    ctx.obj = {}
    ctx.obj["cli_args"] = {
        "verbose": True,
    }
    ctx.params = {
        "branch": "fake_branch",
        "path": PosixPath(os.getcwd()),
        "token": "fakeTOKEN",
    }

    expected = {
        "branch": "fake_branch",
        "command": "do-upload",
        "path": str(PosixPath(os.getcwd())),
        "verbose": True,
        "version": f"cli-{__version__}",
    }

    assert get_cli_args(ctx) == expected
