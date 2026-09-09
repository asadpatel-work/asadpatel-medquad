"""OpenTelemetry Distributed Tracing and Cloud Trace Exporter."""

from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider | None = None
_in_memory_exporter: InMemorySpanExporter | None = None


def setup_telemetry() -> TracerProvider:
    """Initializes OpenTelemetry TracerProvider with Cloud Trace or In-Memory exporters."""
    global _tracer_provider, _in_memory_exporter
    settings = get_settings()

    resource = Resource.create(
        {
            SERVICE_NAME: settings.app_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.environment,
            "gcp.project_id": settings.gcp_project_id,
        }
    )

    provider = TracerProvider(resource=resource)
    _in_memory_exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(_in_memory_exporter))

    if settings.export_to_cloud_trace:
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

            cloud_exporter = CloudTraceSpanExporter(project_id=settings.gcp_project_id)
            provider.add_span_processor(BatchSpanProcessor(cloud_exporter))
            logger.info(
                "Configured Google Cloud Trace SpanExporter for project '%s'.",
                settings.gcp_project_id,
            )
        except Exception as e:
            logger.warning(
                "CloudTraceSpanExporter unavailable (%s). Using fallback telemetry.", str(e)
            )
    else:
        if settings.environment == "development":
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _tracer_provider = provider
    return provider


def get_tracer(name: str = "medquad_clinical_assistant") -> trace.Tracer:
    """Returns an OpenTelemetry Tracer instance."""
    if _tracer_provider is None:
        setup_telemetry()
    return trace.get_tracer(name)


def get_in_memory_spans() -> list[Any]:
    """Returns captured spans from in-memory exporter (for testing and verification)."""
    if _in_memory_exporter:
        return _in_memory_exporter.get_finished_spans()
    return []


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Generator[trace.Span, None, None]:
    """Context manager for creating a standardized OpenTelemetry child span."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for k, v in attributes.items():
                if v is not None:
                    span.set_attribute(k, str(v) if not isinstance(v, (int, float, bool)) else v)
        yield span
