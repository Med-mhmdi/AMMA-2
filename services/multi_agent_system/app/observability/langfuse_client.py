from __future__ import annotations

import contextvars
import logging
from functools import lru_cache
from typing import Any

from app.config import settings


logger = logging.getLogger(__name__)

_current_langfuse_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_langfuse_trace_id",
    default=None,
)


def set_current_langfuse_trace_id(trace_id: str | None) -> None:
    """
    Store the current Langfuse trace id in request-local context.

    This allows other files, such as the LLM provider, to attach LLM generations
    to the same trace created by the API route.
    """
    _current_langfuse_trace_id.set(trace_id)


def get_current_langfuse_trace_id() -> str | None:
    """
    Return the current request trace id.
    """
    return _current_langfuse_trace_id.get()


def clear_current_langfuse_trace_id() -> None:
    """
    Clear the current trace id after request processing.
    """
    _current_langfuse_trace_id.set(None)


@lru_cache(maxsize=1)
def get_langfuse_client():
    """
    Create a cached Langfuse client.

    The app must continue working even if Langfuse is disabled,
    not installed, or wrongly configured.
    """

    if not settings.LANGFUSE_ENABLED:
        return None

    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        logger.warning(
            "Langfuse is enabled but LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY is missing."
        )
        return None

    try:
        from langfuse import Langfuse

        return Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )

    except Exception as exc:
        logger.warning("Failed to initialize Langfuse client: %s", exc)
        return None


def is_langfuse_available() -> bool:
    """
    Return True only when Langfuse is enabled and the client was created.
    """
    return get_langfuse_client() is not None


def get_langfuse_status() -> dict[str, Any]:
    """
    Used by /health and /agent/observability/langfuse.
    """

    client = get_langfuse_client()

    return {
        "enabled": settings.LANGFUSE_ENABLED,
        "available": client is not None,
        "host": settings.LANGFUSE_HOST,
        "environment": settings.LANGFUSE_ENVIRONMENT,
        "release": settings.LANGFUSE_RELEASE,
        "capture_input_output": settings.LANGFUSE_CAPTURE_INPUT_OUTPUT,
        "current_trace_id": get_current_langfuse_trace_id(),
        "has_public_key": bool(settings.LANGFUSE_PUBLIC_KEY),
        "has_secret_key": bool(settings.LANGFUSE_SECRET_KEY),
    }


def _safe_call(obj: Any, method_name: str, **kwargs):
    """
    Safely call a Langfuse SDK method if it exists.

    This makes the project more tolerant to Langfuse SDK version differences.
    """

    if obj is None:
        return None

    method = getattr(obj, method_name, None)

    if not callable(method):
        return None

    try:
        return method(**kwargs)
    except TypeError:
        # Some SDK versions use slightly different argument names.
        filtered_kwargs = {
            key: value
            for key, value in kwargs.items()
            if value is not None
        }

        try:
            return method(**filtered_kwargs)
        except Exception as exc:
            logger.warning("Langfuse method %s failed: %s", method_name, exc)
            return None

    except Exception as exc:
        logger.warning("Langfuse method %s failed: %s", method_name, exc)
        return None


def create_langfuse_trace(
    trace_id: str,
    name: str,
    user_id: str | None = None,
    session_id: str | None = None,
    input_data: Any | None = None,
    metadata: dict[str, Any] | None = None,
):
    """
    Create a Langfuse trace.

    In Langfuse v2/v3 this usually creates a trace object directly.
    If the SDK version does not support direct trace creation, this function
    safely returns None and the app continues normally.
    """

    client = get_langfuse_client()

    if client is None:
        return None

    # Older / common SDK style.
    trace = _safe_call(
        client,
        "trace",
        id=trace_id,
        name=name,
        user_id=user_id,
        session_id=session_id,
        input=input_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]",
        metadata=metadata or {},
        release=settings.LANGFUSE_RELEASE,
    )

    if trace is not None:
        return trace

    # Fallback for newer SDKs that create traces through root spans.
    root_span = _safe_call(
        client,
        "start_span",
        name=name,
        input=input_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]",
        metadata={
            **(metadata or {}),
            "user_id": user_id,
            "session_id": session_id,
            "trace_id": trace_id,
        },
        trace_context={"trace_id": trace_id},
    )

    if root_span is not None:
        try:
            if hasattr(root_span, "update_trace"):
                root_span.update_trace(
                    name=name,
                    user_id=user_id,
                    session_id=session_id,
                    input=input_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]",
                    metadata=metadata or {},
                )
        except Exception as exc:
            logger.warning("Failed to update Langfuse root trace: %s", exc)

    return root_span


def update_langfuse_trace(
    trace: Any,
    output_data: Any | None = None,
    metadata: dict[str, Any] | None = None,
    level: str | None = None,
    status_message: str | None = None,
) -> None:
    """
    Update a Langfuse trace with output and final metadata.
    """

    if trace is None:
        return

    output = output_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]"

    try:
        if hasattr(trace, "update"):
            trace.update(
                output=output,
                metadata=metadata or {},
                level=level,
                status_message=status_message,
            )
            return

        if hasattr(trace, "update_trace"):
            trace.update_trace(
                output=output,
                metadata=metadata or {},
            )
            return

    except Exception as exc:
        logger.warning("Failed to update Langfuse trace: %s", exc)


def create_langfuse_span(
    trace: Any,
    name: str,
    input_data: Any | None = None,
    metadata: dict[str, Any] | None = None,
):
    """
    Create a Langfuse span.

    Used for non-LLM workflow steps such as:
    - langgraph.workflow
    - validation
    - tool_execution
    - memory_save
    """

    client = get_langfuse_client()

    if client is None:
        return None

    input_value = input_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]"

    # If trace object supports child spans.
    if trace is not None:
        span = _safe_call(
            trace,
            "span",
            name=name,
            input=input_value,
            metadata=metadata or {},
        )

        if span is not None:
            return span

        span = _safe_call(
            trace,
            "start_span",
            name=name,
            input=input_value,
            metadata=metadata or {},
        )

        if span is not None:
            return span

    # Fallback: create span directly on client using current trace id.
    trace_id = get_current_langfuse_trace_id()

    return _safe_call(
        client,
        "span",
        trace_id=trace_id,
        name=name,
        input=input_value,
        metadata=metadata or {},
    ) or _safe_call(
        client,
        "start_span",
        name=name,
        input=input_value,
        metadata=metadata or {},
        trace_context={"trace_id": trace_id} if trace_id else None,
    )


def create_langfuse_generation(
    name: str,
    model: str,
    input_data: Any | None = None,
    output_data: Any | None = None,
    metadata: dict[str, Any] | None = None,
    usage: dict[str, Any] | None = None,
    level: str | None = None,
    status_message: str | None = None,
):
    """
    Create a Langfuse generation for an LLM call.

    Use this in llm_provider.py / ollama client after the model returns.
    """

    client = get_langfuse_client()

    if client is None:
        return None

    trace_id = get_current_langfuse_trace_id()

    input_value = input_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]"
    output_value = output_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]"

    generation = _safe_call(
        client,
        "generation",
        trace_id=trace_id,
        name=name,
        model=model,
        input=input_value,
        output=output_value,
        metadata=metadata or {},
        usage=usage,
        level=level,
        status_message=status_message,
    )

    if generation is not None:
        return generation

    generation = _safe_call(
        client,
        "start_generation",
        name=name,
        model=model,
        input=input_value,
        metadata=metadata or {},
        trace_context={"trace_id": trace_id} if trace_id else None,
    )

    if generation is not None:
        finish_langfuse_observation(
            generation,
            output_data=output_value,
            metadata=metadata,
            usage=usage,
            level=level,
            status_message=status_message,
        )

    return generation


def finish_langfuse_observation(
    observation: Any,
    output_data: Any | None = None,
    metadata: dict[str, Any] | None = None,
    usage: dict[str, Any] | None = None,
    level: str | None = None,
    status_message: str | None = None,
) -> None:
    """
    Finish/update a Langfuse span or generation.
    """

    if observation is None:
        return

    output = output_data if settings.LANGFUSE_CAPTURE_INPUT_OUTPUT else "[redacted]"

    try:
        if hasattr(observation, "end"):
            observation.end(
                output=output,
                metadata=metadata or {},
                usage=usage,
                level=level,
                status_message=status_message,
            )
            return

        if hasattr(observation, "update"):
            observation.update(
                output=output,
                metadata=metadata or {},
                usage=usage,
                level=level,
                status_message=status_message,
            )
            return

    except TypeError:
        try:
            if hasattr(observation, "end"):
                observation.end(output=output)
                return

            if hasattr(observation, "update"):
                observation.update(output=output)
                return

        except Exception as exc:
            logger.warning("Failed to finish Langfuse observation: %s", exc)

    except Exception as exc:
        logger.warning("Failed to finish Langfuse observation: %s", exc)


def flush_langfuse() -> None:
    """
    Flush pending Langfuse events before shutdown.
    """

    client = get_langfuse_client()

    if client is None:
        return

    try:
        if hasattr(client, "flush"):
            client.flush()

        if hasattr(client, "shutdown"):
            client.shutdown()

    except Exception as exc:
        logger.warning("Failed to flush Langfuse events: %s", exc)