import logging
import os
from typing import Optional

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


_LOGGER = logging.getLogger("amma.observability")
_INSTRUMENTED_APPS: set[int] = set()
_TRACER_PROVIDERS: set[str] = set()


def setup_observability(app: FastAPI, service_name: str, expose_metrics: bool = True) -> None:
    """
    Real observability setup for AMMA FastAPI services.

    What this gives you:
    - /metrics endpoint in Prometheus text format.
    - FastAPI request metrics such as http_requests_total and latency histograms.
    - OpenTelemetry traces exported to Jaeger OTLP endpoint.

    Environment variables:
    - OTEL_EXPORTER_OTLP_ENDPOINT, default: http://jaeger:4317
    - OTEL_TRACES_ENABLED, default: true
    """
    app_id = id(app)
    if app_id in _INSTRUMENTED_APPS:
        return
    _INSTRUMENTED_APPS.add(app_id)

    if expose_metrics:
        try:
            Instrumentator(
                should_group_status_codes=True,
                should_ignore_untemplated=True,
                should_respect_env_var=False,
                excluded_handlers=["/metrics"],
            ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)
        except Exception as exc:  # do not break app startup because of metrics
            _LOGGER.warning("Prometheus instrumentation failed for %s: %s", service_name, exc)

    traces_enabled = os.getenv("OTEL_TRACES_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
    if not traces_enabled:
        return

    try:
        # Global tracer provider can be set once per process. Each AMMA service runs in its own container,
        # so this is safe. The guard only protects against reload/double import in dev mode.
        if service_name not in _TRACER_PROVIDERS:
            resource = Resource.create({
                "service.name": service_name,
                "service.namespace": "amma",
                "deployment.environment": os.getenv("APP_ENV", "local"),
            })

            provider = TracerProvider(resource=resource)
            endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
            exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            _TRACER_PROVIDERS.add(service_name)

        FastAPIInstrumentor.instrument_app(app)
    except Exception as exc:  # do not break app startup because of tracing
        _LOGGER.warning("OpenTelemetry instrumentation failed for %s: %s", service_name, exc)
