import click

from codecov_cli.services.patch_coverage import PatchCoverageService


@click.option(
    "--staged",
    help="See the patch coverage for the staged changes",
    is_flag=True,
    default=False,
)
@click.command()
def patch_coverage(staged):
    patch_coverage_service = PatchCoverageService()
    patch_coverage_service.run_patch_coverage_command(staged)
