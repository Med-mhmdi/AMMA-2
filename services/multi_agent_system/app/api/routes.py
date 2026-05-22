import base64
import re
import time
import uuid

from fastapi import APIRouter, Header, Response, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.graph.amma_graph import amma_agent_graph
from app.observability.langfuse_client import (
    clear_current_langfuse_trace_id,
    create_langfuse_span,
    create_langfuse_trace,
    finish_langfuse_observation,
    get_langfuse_status,
    set_current_langfuse_trace_id,
    update_langfuse_trace,
)


router = APIRouter(prefix="/agent", tags=["Agent"])


class AgentAnalyzeRequest(BaseModel):
    user_id: int | None = None
    session_id: str | None = None
    message: str | None = None
    image_base64: str | None = None
    image_url: str | None = None


def _limit_payload(value, max_chars: int | None = None):
    """
    Prevent very large payloads from being sent to Langfuse.
    Especially important for images and long LLM responses.
    """

    if value is None:
        return None

    if not settings.LANGFUSE_CAPTURE_INPUT_OUTPUT:
        return "[redacted]"

    max_chars = max_chars or settings.LANGFUSE_MAX_PAYLOAD_CHARS
    text = str(value)

    if len(text) <= max_chars:
        return value

    return text[:max_chars] + f"... [truncated, original_length={len(text)}]"


def _build_langfuse_input(
    user_id: int | None,
    session_id: str | None,
    message: str | None,
    image_base64: str | None,
    image_url: str | None,
) -> dict:
    """
    Build safe Langfuse input.

    Important:
    - Do not send full image_base64 to Langfuse.
    - Only send image presence and size.
    """

    return {
        "user_id": user_id,
        "session_id": session_id,
        "message": _limit_payload(message),
        "image": {
            "has_image_base64": bool(image_base64),
            "image_base64_length": len(image_base64) if image_base64 else 0,
            "image_url": _limit_payload(image_url),
        },
    }


def _build_langfuse_output(response: dict) -> dict:
    """
    Build safe Langfuse output.
    """

    return {
        "status": response.get("status"),
        "result": _limit_payload(response.get("result")),
        "debug_summary": {
            "intent": response.get("debug", {}).get("intent"),
            "next_node": response.get("debug", {}).get("next_node"),
            "has_validation": response.get("debug", {}).get("validation") is not None,
            "has_execution_result": response.get("debug", {}).get("execution_result") is not None,
            "has_errors": bool(response.get("debug", {}).get("errors")),
        },
    }


def build_agent_response(result: dict, langfuse_trace_id: str | None = None) -> dict:
    """
    Build the standard response returned by both:
    - /agent/analyze
    - /agent/analyze/upload
    """

    return {
        "status": "ok",
        "result": result.get("final_response"),
        "debug": {
            "intent": result.get("intent"),
            "next_node": result.get("next_node"),
            "route_reason": result.get("route_reason"),
            "loaded_working_memory": result.get("loaded_working_memory"),
            "extracted_action": result.get("extracted_action"),
            "clarification_result": result.get("clarification_result"),
            "tool_context": result.get("tool_context"),
            "validation": result.get("validation"),
            "execution_result": result.get("execution_result"),
            "memory_event": result.get("memory_event"),
            "financial_advice": result.get("financial_advice"),
            "recommendation_result": result.get("recommendation_result"),
            "notification_decision": result.get("notification_decision"),
            "vision_result": result.get("vision_result"),
            "trace": result.get("trace"),
            "errors": result.get("errors"),
            "langfuse": {
                "enabled": settings.LANGFUSE_ENABLED,
                "trace_id": langfuse_trace_id,
            },
        },
    }


def invoke_agent(
    user_id: int | None,
    session_id: str | None,
    message: str | None,
    authorization: str | None,
    image_base64: str | None = None,
    image_url: str | None = None,
) -> dict:
    """
    Invoke the compiled AMMA LangGraph agent.
    Used by both JSON and Swagger file-upload endpoints.

    Langfuse behavior:
    - Creates one trace per user request.
    - Adds one span around the complete LangGraph execution.
    - Stores trace_id in context so the LLM provider can attach generations to the same trace.
    """

    started_at = time.perf_counter()
    langfuse_trace_id = str(uuid.uuid4())

    langfuse_input = _build_langfuse_input(
        user_id=user_id,
        session_id=session_id,
        message=message,
        image_base64=image_base64,
        image_url=image_url,
    )

    trace = create_langfuse_trace(
        trace_id=langfuse_trace_id,
        name="AMMA Multi-Agent Request",
        user_id=str(user_id) if user_id is not None else None,
        session_id=session_id,
        input_data=langfuse_input,
        metadata={
            "service": "agent_service",
            "endpoint": "/agent/analyze",
            "environment": settings.LANGFUSE_ENVIRONMENT,
            "release": settings.LANGFUSE_RELEASE,
            "has_image": bool(image_base64 or image_url),
            "model": settings.OLLAMA_MODEL,
            "vision_model": settings.OLLAMA_VISION_MODEL,
        },
    )

    set_current_langfuse_trace_id(langfuse_trace_id)

    graph_span = create_langfuse_span(
        trace=trace,
        name="langgraph.workflow",
        input_data={
            "session_id": session_id,
            "has_message": bool(message),
            "has_image": bool(image_base64 or image_url),
        },
        metadata={
            "workflow": "amma_agent_graph",
        },
    )

    try:
        initial_state = {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
            "image_base64": image_base64,
            "image_url": image_url,
            "auth_header": authorization,
            "trace": [],
            "errors": [],
            "langfuse_trace_id": langfuse_trace_id,
        }

        result = amma_agent_graph.invoke(initial_state)
        response = build_agent_response(result, langfuse_trace_id=langfuse_trace_id)

        total_latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

        finish_langfuse_observation(
            graph_span,
            output_data={
                "intent": result.get("intent"),
                "next_node": result.get("next_node"),
                "validation": result.get("validation"),
                "execution_result": _limit_payload(result.get("execution_result")),
                "errors": result.get("errors"),
                "total_latency_ms": total_latency_ms,
            },
            metadata={
                "status": "success",
                "total_latency_ms": total_latency_ms,
            },
        )

        update_langfuse_trace(
            trace=trace,
            output_data=_build_langfuse_output(response),
            metadata={
                "status": "success",
                "intent": result.get("intent"),
                "next_node": result.get("next_node"),
                "total_latency_ms": total_latency_ms,
            },
        )

        return response

    except Exception as exc:
        total_latency_ms = round((time.perf_counter() - started_at) * 1000, 2)

        finish_langfuse_observation(
            graph_span,
            output_data={
                "error": str(exc),
                "total_latency_ms": total_latency_ms,
            },
            metadata={
                "status": "error",
                "error_type": exc.__class__.__name__,
                "total_latency_ms": total_latency_ms,
            },
            level="ERROR",
            status_message=str(exc),
        )

        update_langfuse_trace(
            trace=trace,
            output_data={
                "status": "error",
                "error": str(exc),
            },
            metadata={
                "status": "error",
                "error_type": exc.__class__.__name__,
                "total_latency_ms": total_latency_ms,
            },
        )

        raise

    finally:
        clear_current_langfuse_trace_id()


def _replace_node_definition(
    mermaid: str,
    node_id: str,
    label: str,
    shape: str = "rect",
) -> str:
    """
    Replace only the node definition line generated by LangGraph.
    It does not touch edges, so the graph stays automatic.
    """

    safe_label = label.replace('"', "'")

    if shape == "start_end":
        new_node = f'{node_id}(["{safe_label}"])'
    elif shape == "decision":
        new_node = f'{node_id}{{"{safe_label}"}}'
    else:
        new_node = f'{node_id}["{safe_label}"]'

    pattern = (
        rf'(?m)^(\s*){re.escape(node_id)}'
        rf'(\([^\n]*?\)|\[[^\n]*?\]|\{{[^\n]*?\}})'
        rf'(:::[A-Za-z0-9_-]+)?;?\s*$'
    )

    return re.sub(
        pattern,
        rf'\1{new_node};',
        mermaid,
    )


def improve_mermaid_graph(raw_mermaid: str) -> str:
    """
    Improve the Mermaid graph automatically generated by LangGraph.

    This keeps the real LangGraph nodes and edges.
    It only improves:
    - visual style
    - readable labels
    - node descriptions
    - curve style
    - spacing
    - node categories
    """

    if not raw_mermaid:
        return ""

    mermaid = raw_mermaid.strip()

    # Remove HTML paragraph tags generated by LangGraph.
    mermaid = mermaid.replace("<p>", "")
    mermaid = mermaid.replace("</p>", "")

    # Remove old Mermaid frontmatter if present.
    mermaid = re.sub(
        r"---\s*config:\s*flowchart:\s*curve:\s*linear\s*---",
        "",
        mermaid,
        flags=re.DOTALL,
    ).strip()

    mermaid = mermaid.replace("graph TD;", "flowchart TD")
    mermaid = mermaid.replace("graph TD", "flowchart TD")

    # Mermaid config must be at the very top.
    mermaid = (
        "---\n"
        "config:\n"
        "  flowchart:\n"
        "    curve: basis\n"
        "    nodeSpacing: 45\n"
        "    rankSpacing: 70\n"
        "---\n"
        + mermaid
    )

    # Remove LangGraph default styles.
    cleaned_lines = []

    for line in mermaid.splitlines():
        stripped = line.strip()

        if stripped.startswith("classDef default"):
            continue

        if stripped.startswith("classDef first"):
            continue

        if stripped.startswith("classDef last"):
            continue

        cleaned_lines.append(line)

    mermaid = "\n".join(cleaned_lines)

    node_labels = {
        "__start__": {
            "label": "Start",
            "shape": "start_end",
        },
        "__end__": {
            "label": "End",
            "shape": "start_end",
        },
        "memory_load": {
            "label": "Memory Load<br/>Load session state and working memory",
            "shape": "rect",
        },
        "supervisor_router": {
            "label": "Supervisor Router<br/>Select the correct processing path",
            "shape": "decision",
        },
        "command_agent": {
            "label": "Command Agent<br/>Convert user text into a financial action",
            "shape": "rect",
        },
        "tool_context": {
            "label": "Tool Context<br/>Prepare backend input and auth context",
            "shape": "rect",
        },
        "validation": {
            "label": "Validation<br/>Check required fields and business rules",
            "shape": "rect",
        },
        "conflict_check": {
            "label": "Conflict Check<br/>Detect duplicate or risky actions",
            "shape": "decision",
        },
        "tool_execution": {
            "label": "Tool Execution<br/>Call Expense, Category, Loan, or Analytics APIs",
            "shape": "rect",
        },
        "confirmation_prepare": {
            "label": "Confirmation Prepare<br/>Ask before executing risky actions",
            "shape": "rect",
        },
        "confirmation_handler": {
            "label": "Confirmation Handler<br/>Handle yes/no user decision",
            "shape": "rect",
        },
        "conflict_resolution_prepare": {
            "label": "Conflict Resolution Prepare<br/>Prepare options for duplicates/conflicts",
            "shape": "rect",
        },
        "conflict_resolution_handler": {
            "label": "Conflict Resolution Handler<br/>Apply the selected conflict decision",
            "shape": "rect",
        },
        "clarification_agent": {
            "label": "Clarification Agent<br/>Ask for missing information",
            "shape": "rect",
        },
        "cancel_working_memory": {
            "label": "Cancel Working Memory<br/>Clear unfinished pending action",
            "shape": "rect",
        },
        "financial_advisor": {
            "label": "Financial Advisor<br/>Explain spending and financial behavior",
            "shape": "rect",
        },
        "recommendation_agent": {
            "label": "Recommendation Agent<br/>Generate saving and budget advice",
            "shape": "rect",
        },
        "notification_agent": {
            "label": "Notification Agent<br/>Prepare alerts, reminders, and warnings",
            "shape": "rect",
        },
        "vision_agent": {
            "label": "Vision Agent<br/>Extract financial data from image or receipt",
            "shape": "rect",
        },
        "memory_update": {
            "label": "Memory Update<br/>Save result, pending state, and trace",
            "shape": "rect",
        },
        "final_response": {
            "label": "Final Response<br/>Return message to AMMA Chat",
            "shape": "rect",
        },
    }

    for node_id, data in node_labels.items():
        mermaid = _replace_node_definition(
            mermaid=mermaid,
            node_id=node_id,
            label=data["label"],
            shape=data["shape"],
        )

    style_block = """

%% =====================================================
%% Visual Styles
%% =====================================================

classDef default fill:#f8f9fa,stroke:#495057,stroke-width:1.5px,color:#111827;
classDef startEnd fill:#ede9fe,stroke:#6d28d9,stroke-width:2.5px,color:#1e1b4b;
classDef router fill:#ffe3e3,stroke:#c92a2a,stroke-width:2.5px,color:#3b0000;
classDef solid fill:#d8f3dc,stroke:#2d6a4f,stroke-width:2.5px,color:#081c15;
classDef partial fill:#fff3bf,stroke:#e67700,stroke-width:2.5px,color:#3d2b00;
classDef planned fill:#e7f5ff,stroke:#1c7ed6,stroke-width:2.5px,color:#0b2545;
classDef memory fill:#f3f0ff,stroke:#7048e8,stroke-width:2.5px,color:#1b103f;
classDef execution fill:#d0ebff,stroke:#1864ab,stroke-width:2.5px,color:#06172e;
classDef response fill:#e6fcf5,stroke:#087f5b,stroke-width:2.5px,color:#003c2f;

class __start__,__end__ startEnd;

class supervisor_router,conflict_check router;

class command_agent,vision_agent,tool_context,validation,confirmation_prepare,confirmation_handler,conflict_resolution_prepare,conflict_resolution_handler solid;

class tool_execution execution;

class memory_load,memory_update memory;

class clarification_agent,cancel_working_memory partial;

class financial_advisor,recommendation_agent,notification_agent planned;

class final_response response;
"""

    if "%% Visual Styles" not in mermaid:
        mermaid = mermaid.rstrip() + style_block

    # Legend comments must be at the bottom, not before Mermaid config.
    legend_comment = """

%% =====================================================
%% Legend
%% Purple: Start / End
%% Violet: Memory
%% Red: Routing / Decision
%% Green: Solid implemented command pipeline
%% Yellow: Partial support
%% Blue: Planned or future AI agents
%% Cyan: Backend execution
%% =====================================================
"""

    if "%% Legend" not in mermaid:
        mermaid = mermaid.rstrip() + legend_comment

    return mermaid.strip()


def get_clean_mermaid_graph() -> str:
    """
    Generate the graph automatically from LangGraph,
    then clean it for display.
    """

    raw_mermaid = amma_agent_graph.get_graph().draw_mermaid()
    return improve_mermaid_graph(raw_mermaid)


@router.post("/analyze")
def analyze(
    request: AgentAnalyzeRequest,
    authorization: str | None = Header(default=None),
):
    return invoke_agent(
        user_id=request.user_id,
        session_id=request.session_id,
        message=request.message,
        image_base64=request.image_base64,
        image_url=request.image_url,
        authorization=authorization,
    )


@router.post("/analyze/upload")
async def analyze_upload(
    user_id: int | None = Form(default=None),
    session_id: str | None = Form(default=None),
    message: str | None = Form(default="Analyze this receipt image"),
    image: UploadFile = File(...),
    authorization: str | None = Header(default=None),
):
    """
    Swagger-friendly endpoint.

    This endpoint accepts a real uploaded image file using multipart/form-data.
    Swagger will show a Choose File button.
    """

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image file.",
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    return invoke_agent(
        user_id=user_id,
        session_id=session_id,
        message=message,
        image_base64=image_base64,
        image_url=None,
        authorization=authorization,
    )


@router.get("/graph/mermaid")
def graph_mermaid():
    mermaid = get_clean_mermaid_graph()

    return {
        "status": "ok",
        "format": "mermaid",
        "mermaid": mermaid,
    }


@router.get("/graph/mermaid/raw")
def graph_mermaid_raw():
    mermaid = get_clean_mermaid_graph()

    return Response(
        content=mermaid,
        media_type="text/plain",
    )


@router.get("/llm/config")
def llm_config():
    return {
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "ollama_vision_model": settings.OLLAMA_VISION_MODEL,
    }


@router.get("/observability/langfuse")
def langfuse_observability():
    return {
        "status": "ok",
        "langfuse": get_langfuse_status(),
    }


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "multi_agent_system",
        "mode": "langgraph",
        "observability": {
            "langfuse": get_langfuse_status(),
        },
    }