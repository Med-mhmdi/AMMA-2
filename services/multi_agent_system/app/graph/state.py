from typing import Any, Literal
from typing_extensions import TypedDict


AgentIntent = Literal[
    "command",
    "financial_advice",
    "recommendation",
    "vision_extraction",
    "notification",
    "clarification",
    "unknown",
]


NextNode = Literal[
    "command_agent",
    "confirmation_execution",
    "cancel_working_memory",
    "financial_advisor",
    "recommendation_agent",
    "notification_agent",
    "vision_agent",
    "clarification_agent",
    "final_response",
]


class AgentState(TypedDict, total=False):
    # =========================
    # Request data
    # =========================
    user_id: int | None
    session_id: str | None
    message: str | None
    image_base64: str | None
    image_url: str | None
    auth_header: str | None

    # =========================
    # Unified working memory
    # =========================
    loaded_working_memory: dict[str, Any] | None
    memory_event: dict[str, Any] | None

    # =========================
    # Routing
    # =========================
    intent: AgentIntent | str | None
    next_node: NextNode | str | None
    route_reason: str | None

    # =========================
    # Agent outputs
    # =========================
    extracted_action: dict[str, Any] | None
    clarification_result: dict[str, Any] | None
    financial_advice: dict[str, Any] | None
    recommendation_result: dict[str, Any] | None
    notification_decision: dict[str, Any] | None
    vision_result: dict[str, Any] | None

    # =========================
    # Tool workflow
    # =========================
    tool_context: dict[str, Any] | None
    validation: dict[str, Any] | None
    execution_result: dict[str, Any] | None

    # =========================
    # Final response / debug
    # =========================
    final_response: dict[str, Any] | None
    trace: list[str]
    errors: list[str]