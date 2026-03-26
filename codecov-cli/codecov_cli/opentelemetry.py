import os
import random

import sentry_sdk

from codecov_cli import __version__

_SAMPLED_MESSAGES = [
    "Token required",
]
_SAMPLE_RATE = 100
_SKIP_TAG_KEYS = {"branch", "flags", "commit_sha", "env_vars"}


def _before_send(event, hint):
    messages = []
    if "message" in event and event.get("message") is not None:
        messages.append(event.get("message"))
    if "logentry" in event and "message" in event.get("logentry", {}) and event.get("logentry", {}).get("message") is not None:
        messages.append(event.get("logentry", {}).get("message"))
    if "exception" in event and event.get("exception") is not None:
        for exc in event.get("exception", {}).get("values", []):
            if "value" in exc:
                messages.append(exc.get("value"))

    matched = False
    for message in messages:
        for pattern in _SAMPLED_MESSAGES:
            if pattern in message:
                matched = True
                break

    if matched and random.randint(1, _SAMPLE_RATE) != 1:
        return None
    return event


def init_telem(ctx):
    if ctx["disable_telem"]:
        return
    if ctx["enterprise_url"]:  # dont run on dedicated cloud
        return
    if os.getenv("CODECOV_ENV", "production") == "test":
        return

    sentry_sdk.init(
        dsn="https://0bea75c61745c221a6ef1ac1709b1f4d@o26192.ingest.us.sentry.io/4508615876083713",
        enable_tracing=True,
        environment=os.getenv("CODECOV_ENV", "production"),
        release=f"cli@{__version__}",
        before_send=_before_send,
    )


def set_cli_tags(args: dict, ctx):
    """Set Sentry tags from resolved CLI arguments."""
    for key, value in args.items():
        if key in _SKIP_TAG_KEYS:
            continue
        if value is None or value in ([], (), {}):
            continue
        if isinstance(value, (list, tuple)):
            value = ",".join(str(v) for v in value)
        elif isinstance(value, dict):
            value = ",".join(
                f"{k}={v}" for k, v in value.items() if v is not None
            )
        sentry_sdk.set_tag(f"cli.{key}", str(value)[:200])

    token = ctx.params.get("token") if hasattr(ctx, "params") else None
    sentry_sdk.set_tag("cli.token_provided", str(bool(token)).lower())

    ci_adapter = (
        ctx.obj.get("ci_adapter") if hasattr(ctx, "obj") and ctx.obj else None
    )
    if ci_adapter is not None:
        try:
            sentry_sdk.set_tag("cli.ci_adapter", ci_adapter.get_service_name())
        except Exception:
            pass


def close_telem():
    sentry_sdk.flush()
