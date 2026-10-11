"""OpenTelemetry setup hooks."""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider


def setup_tracing(service_name: str = "org-brain") -> None:
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)


def get_tracer(name: str = "org_brain"):
    return trace.get_tracer(name)
