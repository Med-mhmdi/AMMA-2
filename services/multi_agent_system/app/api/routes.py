from fastapi import APIRouter, Header, Response
from pydantic import BaseModel

from app.config import settings
from app.graph.amma_graph import amma_agent_graph


router = APIRouter(prefix="/agent", tags=["Agent"])


class AgentAnalyzeRequest(BaseModel):
    user_id: int | None = None
    session_id: str | None = None
    message: str | None = None
    image_base64: str | None = None
    image_url: str | None = None


@router.post("/analyze")
def analyze(
    request: AgentAnalyzeRequest,
    authorization: str | None = Header(default=None),
):
    initial_state = {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "message": request.message,
        "image_base64": request.image_base64,
        "image_url": request.image_url,
        "auth_header": authorization,
        "trace": [],
        "errors": [],
    }

    result = amma_agent_graph.invoke(initial_state)

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
        },
    }


@router.get("/graph/mermaid")
def graph_mermaid():
    mermaid = amma_agent_graph.get_graph().draw_mermaid()

    return {
        "status": "ok",
        "format": "mermaid",
        "mermaid": mermaid,
    }


@router.get("/graph/mermaid/raw")
def graph_mermaid_raw():
    mermaid = amma_agent_graph.get_graph().draw_mermaid()

    return Response(
        content=mermaid,
        media_type="text/plain",
    )


@router.get("/llm/config")
def llm_config():
    return {
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
    }


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "multi_agent_system",
        "mode": "langgraph",
    }