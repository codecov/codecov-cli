import click

from codecov_cli.services.patch_coverage import PatchCoverageService


@click.command()
def patch_coverage():
    patch_coverage_service = PatchCoverageService()
    patch_coverage_service.run_patch_coverage_command()
