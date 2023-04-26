import logging
import pathlib
import typing

import click

from codecov_cli.commands.base_picking import pr_base_picking
from codecov_cli.commands.commit import create_commit
from codecov_cli.commands.create_report_result import create_report_results
from codecov_cli.commands.get_report_results import get_report_results
from codecov_cli.commands.labelanalysis import label_analysis
from codecov_cli.commands.report import create_report
from codecov_cli.commands.staticanalysis import static_analysis
from codecov_cli.commands.upload import do_upload
from codecov_cli.helpers.ci_adapters import get_ci_adapter, get_ci_providers_list
from codecov_cli.helpers.config import load_cli_config
from codecov_cli.helpers.logging_utils import configure_logger
from codecov_cli.helpers.versioning_systems import get_versioning_system

logger = logging.getLogger("codecovcli")


@click.group()
@click.option(
    "--auto-load-params-from",
    type=click.Choice(
        [provider.get_service_name() for provider in get_ci_providers_list()],
        case_sensitive=False,
    ),
)
@click.option(
    "--codecov-yml-path",
    type=click.Path(path_type=pathlib.Path),
)
@click.option("--enterprise-url")
@click.option("-v", "--verbose", "verbose", help="Use verbose logging", is_flag=True)
@click.pass_context
@click.version_option()
def cli(
    ctx: click.Context,
    auto_load_params_from: typing.Optional[str],
    codecov_yml_path: pathlib.Path,
    enterprise_url: str,
    verbose: bool = False,
):
    configure_logger(logger, log_level=(logging.DEBUG if verbose else logging.INFO))
    ctx.obj["ci_adapter"] = get_ci_adapter(auto_load_params_from)
    ctx.obj["versioning_system"] = get_versioning_system()
    ctx.obj["codecov_yaml"] = (
        load_cli_config(codecov_yml_path) if codecov_yml_path else None
    )
    if ctx.obj["codecov_yaml"] is None:
        logger.debug("No codecov_yaml found")


cli.add_command(do_upload)
cli.add_command(create_commit)
cli.add_command(create_report)
cli.add_command(create_report_results)
cli.add_command(get_report_results)
cli.add_command(pr_base_picking)
cli.add_command(label_analysis)
cli.add_command(static_analysis)


def run():
    cli(obj={})


if __name__ == "__main__":
    run()
