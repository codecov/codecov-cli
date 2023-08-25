import click

from codecov_cli.services.patch_coverage import PatchCoverageService


@click.option(
    "--staged",
    help="See the patch coverage for the staged changes",
    is_flag=True,
    default=False,
)
@click.option(
    "--diff-base",
    "diff_base",
    help="The base point to compare against. It can be a commit sha, tag or branch name.",
)
@click.command()
def patch_coverage(staged, diff_base):
    """Displays the patch coverage and list of uncovered lines for current changes.
    (requires git and an XML coverage report with updated data)
    """
    patch_coverage_service = PatchCoverageService()
    patch_coverage_service.run_patch_coverage_command(staged, diff_base)
