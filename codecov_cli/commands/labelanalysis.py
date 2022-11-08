import json
import subprocess
import time

import click
import requests

from codecov_cli.fallbacks import CodecovOption, FallbackFieldEnum


@click.command()
@click.option("--token", required=True)
@click.option(
    "--head-sha",
    "head_commit_sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    fallback_field=FallbackFieldEnum.commit_sha,
    required=True,
)
@click.option(
    "--base-sha",
    "base_commit_sha",
    help="Commit SHA (with 40 chars)",
    cls=CodecovOption,
    required=True,
)
def label_analysis(token, head_commit_sha, base_commit_sha):
    url = "https://api.codecov.io/labels/labels-analysis"
    token_header = f"Repotoken {token}"
    requested_labels = _retrieve_requested_labels()
    payload = {
        "base_commit": base_commit_sha,
        "head_commit": head_commit_sha,
        "requested_labels": requested_labels,
    }
    try:
        response = requests.post(
            url, json=payload, headers={"Authorization": token_header}
        )
        if response.status_code >= 500:
            raise click.ClickException("Sorry. Codecov is having problems")
        if response.status_code >= 400:
            click.echo(response.json())
            raise click.ClickException(
                "There is some problem with the submitted information"
            )
    except requests.RequestException:
        raise click.ClickException(click.style("Unable to reach Codecov", fg="red"))
    eid = response.json()["external_id"]
    has_result = False
    time.sleep(2)
    while not has_result:
        resp_data = requests.get(
            f"https://api.codecov.io/labels/labels-analysis/{eid}",
            headers={"Authorization": token_header},
        )
        if resp_data.json()["state"].lower() == "finished":
            click.echo(resp_data.json()["result"])
            return
        if resp_data.json()["state"].lower() == "error":
            click.echo("ERROR")
            return
        click.echo("Leaving time for result to arrive")
        time.sleep(5)


def _retrieve_requested_labels():
    # This is a temporary way of doing this while we decide how we are going to
    # receive the input from the user
    # It's probably going to be a json in the end
    return [
        x
        for x in subprocess.run(
            ["python", "-m", "pytest", "-q", "--collect-only"], capture_output=True
        )
        .stdout.decode()
        .split()
        if "::" in x
    ]
