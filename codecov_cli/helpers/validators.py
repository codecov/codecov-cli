import re

import click


def validate_commit_sha(ctx, param, value):
    if value == "" or value is None:
        raise click.MissingParameter()
    if len(value) < 40:
        raise click.BadParameter("Use the full commit SHA")
    if not re.match(r"[0-9a-f]{40}", value):
        raise click.BadParameter("Commit SHA doesn't match SHA1 regex")
    return value
