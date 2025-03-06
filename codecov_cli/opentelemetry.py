import os
import time

import sentry_sdk

from codecov_cli import __version__


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
    )


def close_telem():
    sentry_sdk.flush()
