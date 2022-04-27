import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum


@click.command()
@click.option(
    "--commit-sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
)
@click.option(
    "--code", help="The code of the report. If unsure, leave default", default="default"
)
@click.pass_context
def create_report(ctx, commit_sha: str, code: str):
    for x in range(10):
        click.echo(f"Hello {commit_sha}!")
