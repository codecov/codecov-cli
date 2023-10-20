import click

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum
from codecov_cli.helpers.git import GitService

_global_options = [
    click.option(
        "-C",
        "--sha",
        "--commit-sha",
        "commit_sha",
        help="Commit SHA (with 40 chars)",
        cls=CodecovOption,
        fallback_field=FallbackFieldEnum.commit_sha,
        required=True,
    ),
    click.option(
        "-Z",
        "--fail-on-error",
        "fail_on_error",
        is_flag=True,
        help="Exit with non-zero code in case of error",
    ),
    click.option(
        "--git-service",
        cls=CodecovOption,
        fallback_field=FallbackFieldEnum.git_service,
        type=click.Choice([service.value for service in GitService]),
    ),
    click.option(
        "-t",
        "--token",
        help="Codecov upload token",
        envvar="CODECOV_TOKEN",
    ),
    click.option(
        "-r",
        "--slug",
        "slug",
        cls=CodecovOption,
        fallback_field=FallbackFieldEnum.slug,
        help="owner/repo slug used instead of the private repo token in Self-hosted",
        envvar="CODECOV_SLUG",
    ),
]


def global_options(func):
    for option in reversed(_global_options):
        func = option(func)
    return func
