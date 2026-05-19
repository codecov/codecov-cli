import click
from click.testing import CliRunner
from unittest.mock import MagicMock

from codecov_cli.branding import Branding
from codecov_cli.fallbacks import BrandedOption, CodecovOption, FallbackFieldEnum


@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = {}
    ctx.obj["branding"] = [Branding.CODECOV, Branding.PREVENT]


@cli.command()
@click.option("--test", cls=BrandedOption, envvar="TEST")
@click.pass_context
def hello_world(ctx, test):
    click.echo(f"{test}")


def test_branded_option():
    runner = CliRunner()

    result = runner.invoke(cli, ["hello-world"], env={"CODECOV_TEST": "hello_codecov"})
    assert result.output == "hello_codecov\n"

    result = runner.invoke(cli, ["hello-world"], env={"PREVENT_TEST": "hello_prevent"})
    assert result.output == "hello_prevent\n"

    result = runner.invoke(cli, ["hello-world"])
    assert result.output == "None\n"


@click.group()
def codecov_cli_group():
    pass


@codecov_cli_group.command()
@click.option(
    "--name",
    cls=CodecovOption,
    fallback_fields=(
        FallbackFieldEnum.job_name,
        FallbackFieldEnum.build_code,
    ),
)
def with_name_fallback(name):
    click.echo(name or "")


def test_codecov_option_fallback_fields_uses_second_when_first_is_none():
    runner = CliRunner()
    adapter = MagicMock()

    def get_fallback(field):
        return {
            FallbackFieldEnum.job_name: None,
            FallbackFieldEnum.build_code: "build-42",
        }[field]

    adapter.get_fallback_value.side_effect = get_fallback

    result = runner.invoke(
        codecov_cli_group,
        ["with-name-fallback"],
        obj={"ci_adapter": adapter, "versioning_system": None},
    )
    assert result.exit_code == 0
    assert result.output == "build-42\n"


def test_codecov_option_fallback_fields_prefers_first_when_set():
    runner = CliRunner()
    adapter = MagicMock()

    def get_fallback(field):
        return {
            FallbackFieldEnum.job_name: "my-job",
            FallbackFieldEnum.build_code: "build-42",
        }[field]

    adapter.get_fallback_value.side_effect = get_fallback

    result = runner.invoke(
        codecov_cli_group,
        ["with-name-fallback"],
        obj={"ci_adapter": adapter, "versioning_system": None},
    )
    assert result.exit_code == 0
    assert result.output == "my-job\n"
