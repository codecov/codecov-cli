import click

from codecov_cli.helpers.git import GitService

# The set of acceptable upload services from Shelter
_CODECOV_UPLOAD_SERVICES = frozenset(s.value for s in GitService) | {"github-actions"}


def validate_upload_service(
    service: str,
) -> None:
    allowed = ", ".join(sorted(_CODECOV_UPLOAD_SERVICES))
    if not service:
        raise click.ClickException(
            "Upload service is missing (Codecov requires it for upload URLs). "
            f"Pass --git-service with one of: {allowed}"
        )
    if service not in _CODECOV_UPLOAD_SERVICES:
        raise click.ClickException(
            f"Invalid upload service {service!r}. Use one of: {allowed}"
        )