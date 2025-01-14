import os
import time

from opentelemetry import trace
from opentelemetry.propagate import set_global_textmap
from opentelemetry.sdk.trace import TracerProvider
import sentry_sdk
from sentry_sdk.integrations.opentelemetry import SentrySpanProcessor, SentryPropagator


def init_telem(version, url):
    if url:  # dont run on dedicated cloud
        return

    if os.getenv("IS_CI", False):
        return

    sentry_sdk.init(
        dsn="https://0bea75c61745c221a6ef1ac1709b1f4d@o26192.ingest.us.sentry.io/4508615876083713",
        enable_tracing=True,
        release=f"cli@{version}",
        instrumenter="otel",
    )

    provider = TracerProvider()
    provider.add_span_processor(SentrySpanProcessor())
    trace.set_tracer_provider(provider)
    set_global_textmap(SentryPropagator())


def close_telem():
    sentry_sdk.flush()
