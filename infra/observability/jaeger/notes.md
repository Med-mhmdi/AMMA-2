# Jaeger / Tracing Notes

Jaeger is included in Docker Compose as `jaegertracing/all-in-one`.

Open UI:

```text
http://localhost:16686
```

Current use in AMMA:

- Ready as tracing backend.
- Agent observability is currently stronger through Langfuse/LangSmith.
- Production improvement: add OpenTelemetry instrumentation to FastAPI services and export traces to Jaeger over OTLP ports 4317/4318.
