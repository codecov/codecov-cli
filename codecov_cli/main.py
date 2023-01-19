import logging
import pathlib
import typing

import click
import yaml

from codecov_cli.commands.commit import create_commit
from codecov_cli.commands.create_report_result import create_report_results
from codecov_cli.commands.get_report_results import get_report_results
from codecov_cli.commands.report import create_report
from codecov_cli.commands.upload import do_upload
from codecov_cli.helpers.ci_adapters import get_ci_adapter
from codecov_cli.helpers.logging_utils import configure_logger
from codecov_cli.helpers.versioning_systems import get_versioning_system

logger = logging.getLogger("codecovcli")


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
    configure_logger(logger)
    ctx.obj["ci_adapter"] = get_ci_adapter(auto_load_params_from)
    ctx.obj["versioning_system"] = get_versioning_system()
    ctx.obj["codecov_yaml"] = (
        yaml.safe_load(codecov_yml_path.read())
        if codecov_yml_path is not None
        else None
    )


cli.add_command(do_upload)
cli.add_command(create_commit)
cli.add_command(create_report)
cli.add_command(create_report_results)
cli.add_command(get_report_results)


def run():
    cli(obj={})


if __name__ == "__main__":
    run()
