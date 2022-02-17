import pathlib
import typing

import click
import yaml

from codecov_cli.commands.commit import create_commit
from codecov_cli.commands.report import create_report
from codecov_cli.commands.upload import do_upload
from codecov_cli.fallbackers import get_provider_specific_fallbacker
from codecov_cli.helpers.explorers import get_file_explorer


@click.group()
@click.option(
    "--auto-load-params-from",
    type=click.Choice(["circleci", "githubactions"], case_sensitive=False),
)
@click.option(
    "--codecov-yml-path",
    type=click.Path(path_type=pathlib.Path),
)
@click.option("--enterprise-url")
@click.pass_context
def cli(
    ctx: click.Context,
    auto_load_params_from: typing.Optional[str],
    codecov_yml_path: pathlib.Path,
    enterprise_url: str,
):
    ctx.obj["fallbacker"] = get_provider_specific_fallbacker(auto_load_params_from)
    ctx.obj["file_explorer"] = get_file_explorer()
    ctx.obj["codecov_yml"] = (
        yaml.safe_load(codecov_yml_path.read())
        if codecov_yml_path is not None
        else None
    )


cli.add_command(do_upload)
cli.add_command(create_commit)
cli.add_command(create_report)


def run():
    cli(obj={})
