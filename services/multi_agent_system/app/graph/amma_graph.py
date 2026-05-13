from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    cancel_working_memory_node,
    clarification_agent_node,
    command_agent_node,
    confirmation_handler_node,
    confirmation_prepare_node,
    conflict_check_node,
    conflict_resolution_handler_node,
    conflict_resolution_prepare_node,
    final_response_node,
    financial_advisor_agent_node,
    memory_load_node,
    memory_update_node,
    notification_agent_node,
    recommendation_agent_node,
    supervisor_router_node,
    tool_context_node,
    tool_execution_node,
    validation_node,
    vision_extraction_agent_node,
)
from app.graph.state import AgentState


READ_ONLY_ACTIONS = {
    "list_expenses",
    "list_categories",
    "list_loans",
}


def route_after_supervisor_router(state: AgentState) -> str:
    next_node = state.get("next_node", "clarification_agent")

    allowed_routes = {
        "command_agent",
        "confirmation_handler",
        "conflict_resolution_handler",
        "cancel_working_memory",
        "financial_advisor",
        "recommendation_agent",
        "notification_agent",
        "vision_agent",
        "clarification_agent",
        "final_response",
    }

    if next_node not in allowed_routes:
        return "clarification_agent"

    return next_node


def route_after_validation(state: AgentState) -> str:
    validation = state.get("validation") or {}
    extracted_action = state.get("extracted_action") or {}
    action = extracted_action.get("action")

    # If this is only a real missing-field clarification, go to memory.
    # Important: confirmation also uses needs_user_clarification=True,
    # so we must NOT stop here when awaiting_confirmation=True.
    if (
        validation.get("needs_user_clarification")
        and not validation.get("awaiting_confirmation")
    ):
        return "memory_update"

    # Read-only actions do not need conflict check or confirmation.
    if action in READ_ONLY_ACTIONS:
        return "tool_execution"

    # All mutating actions should pass through conflict_check first.
    # This lets us detect duplicates before asking confirmation or executing.
    return "conflict_check"


def route_after_conflict_check(state: AgentState) -> str:
    conflict_check = state.get("conflict_check") or {}
    validation = state.get("validation") or {}
    extracted_action = state.get("extracted_action") or {}

    # If duplicate/conflict exists, ask user what to do first.
    if conflict_check.get("has_conflict"):
        return "conflict_resolution_prepare"

    # If conflict was already resolved with "add anyway" or "update existing",
    # do not ask confirmation again.
    if state.get("skip_confirmation"):
        return "tool_execution"

    # If the action itself requires confirmation, ask confirmation before execution.
    action_requires_confirmation = bool(extracted_action.get("requires_confirmation"))

    if action_requires_confirmation and not validation.get("confirmed"):
        return "confirmation_prepare"

    # Support validation-driven confirmation too.
    if validation.get("awaiting_confirmation") and not validation.get("confirmed"):
        return "confirmation_prepare"

    return "tool_execution"


def route_after_confirmation_handler(state: AgentState) -> str:
    execution_result = state.get("execution_result") or {}

    if execution_result.get("status") in ["failed", "cancelled"]:
        return "memory_update"

    # After user confirms, reload context and pass through validation/conflict_check.
    return "tool_context"


def route_after_conflict_resolution_handler(state: AgentState) -> str:
    execution_result = state.get("execution_result") or {}
    validation = state.get("validation") or {}

    if execution_result.get("status") in ["failed", "cancelled"]:
        return "memory_update"

    if validation.get("needs_user_clarification"):
        return "memory_update"

    # After user chooses add anyway / update existing, reload context before execution.
    return "tool_context"


def build_amma_agent_graph():
    graph = StateGraph(AgentState)

    # =========================
    # Core routing
    # =========================
    graph.add_node("memory_load", memory_load_node)
    graph.add_node("supervisor_router", supervisor_router_node)

    # =========================
    # Agent nodes
    # =========================
    graph.add_node("command_agent", command_agent_node)
    graph.add_node("clarification_agent", clarification_agent_node)
    graph.add_node("vision_agent", vision_extraction_agent_node)
    graph.add_node("financial_advisor", financial_advisor_agent_node)
    graph.add_node("recommendation_agent", recommendation_agent_node)
    graph.add_node("notification_agent", notification_agent_node)

    # =========================
    # Tool flow
    # =========================
    graph.add_node("tool_context", tool_context_node)
    graph.add_node("validation", validation_node)
    graph.add_node("conflict_check", conflict_check_node)
    graph.add_node("conflict_resolution_prepare", conflict_resolution_prepare_node)
    graph.add_node("tool_execution", tool_execution_node)

    # =========================
    # Confirmation / conflict / cancel
    # =========================
    graph.add_node("confirmation_prepare", confirmation_prepare_node)
    graph.add_node("confirmation_handler", confirmation_handler_node)
    graph.add_node("conflict_resolution_handler", conflict_resolution_handler_node)
    graph.add_node("cancel_working_memory", cancel_working_memory_node)

    # =========================
    # Memory / response
    # =========================
    graph.add_node("memory_update", memory_update_node)
    graph.add_node("final_response", final_response_node)

    # =========================
    # Entry
    # =========================
    graph.add_edge(START, "memory_load")
    graph.add_edge("memory_load", "supervisor_router")

    # =========================
    # Main router
    # =========================
    graph.add_conditional_edges(
        "supervisor_router",
        route_after_supervisor_router,
        {
            "command_agent": "command_agent",
            "confirmation_handler": "confirmation_handler",
            "conflict_resolution_handler": "conflict_resolution_handler",
            "cancel_working_memory": "cancel_working_memory",
            "financial_advisor": "financial_advisor",
            "recommendation_agent": "recommendation_agent",
            "notification_agent": "notification_agent",
            "vision_agent": "vision_agent",
            "clarification_agent": "clarification_agent",
            "final_response": "final_response",
        },
    )

    # =========================
    # Command flow
    # =========================
    graph.add_edge("command_agent", "tool_context")
    graph.add_edge("tool_context", "validation")

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "tool_execution": "tool_execution",
            "conflict_check": "conflict_check",
            "memory_update": "memory_update",
        },
    )

    graph.add_conditional_edges(
        "conflict_check",
        route_after_conflict_check,
        {
            "tool_execution": "tool_execution",
            "confirmation_prepare": "confirmation_prepare",
            "conflict_resolution_prepare": "conflict_resolution_prepare",
        },
    )

    graph.add_edge("tool_execution", "memory_update")
    graph.add_edge("confirmation_prepare", "memory_update")
    graph.add_edge("conflict_resolution_prepare", "memory_update")

    # =========================
    # Confirmation / conflict answer flow
    # =========================
    graph.add_conditional_edges(
        "confirmation_handler",
        route_after_confirmation_handler,
        {
            "tool_context": "tool_context",
            "memory_update": "memory_update",
        },
    )

    graph.add_conditional_edges(
        "conflict_resolution_handler",
        route_after_conflict_resolution_handler,
        {
            "tool_context": "tool_context",
            "memory_update": "memory_update",
        },
    )

    # =========================
    # Vision flow
    # =========================
    graph.add_edge("vision_agent", "validation")

    # =========================
    # Advice / recommendation / notification flow
    # =========================
    graph.add_edge("financial_advisor", "recommendation_agent")
    graph.add_edge("recommendation_agent", "notification_agent")
    graph.add_edge("notification_agent", "memory_update")

    # =========================
    # Clarification / cancel flow
    # =========================
    graph.add_edge("clarification_agent", "memory_update")
    graph.add_edge("cancel_working_memory", "memory_update")

    # =========================
    # Final
    # =========================
    graph.add_edge("memory_update", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile()


amma_agent_graph = build_amma_agent_graph()