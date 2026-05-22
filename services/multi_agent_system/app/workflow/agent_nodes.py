from app.agents.clarification_agent import generate_clarification
from app.agents.command_agent import extract_command
from app.agents.financial_advisor_agent import generate_financial_advice
from app.agents.notification_agent import decide_notification
from app.agents.recommendation_agent import generate_recommendations
from app.agents.supervisor_router_agent import route_next_node
from app.agents.vision_agent import extract_from_image
from app.graph.state import AgentState
from app.workflow.common import (
    append_trace,
    is_confirmation_message,
    is_correction_message,
    is_decline_message,
)


def supervisor_router_node(state: AgentState) -> AgentState:
    message = state.get("message")
    has_image = bool(state.get("image_base64") or state.get("image_url"))
    working_memory = state.get("loaded_working_memory") or {}

    # ============================================================
    # Deterministic memory-based routing
    # ============================================================
    # These branches are safety-sensitive, so they should not depend
    # only on the LLM router.

    # 1. Conflict resolution has the highest priority.
    # Example:
    # Assistant: "Possible duplicate. add anyway / update existing / cancel?"
    # User: "add anyway"
    if working_memory.get("awaiting_conflict_resolution"):
        return {
            "intent": "command",
            "next_node": "conflict_resolution_handler",
            "route_reason": "System is awaiting conflict resolution from the user.",
            "trace": append_trace(state, "SupervisorRouterAgent"),
        }

    # 2. Confirmation comes after conflict resolution.
    # If the user confirms, go to confirmation_handler.
    # If the user cancels, clear memory.
    # If the user corrects details, go back to command_agent.
    if working_memory.get("awaiting_confirmation"):
        if is_decline_message(message):
            return {
                "intent": "command",
                "next_node": "cancel_working_memory",
                "route_reason": "User cancelled the pending confirmation.",
                "trace": append_trace(state, "SupervisorRouterAgent"),
            }

        if is_confirmation_message(message):
            return {
                "intent": "command",
                "next_node": "confirmation_handler",
                "route_reason": "User confirmed the pending action.",
                "trace": append_trace(state, "SupervisorRouterAgent"),
            }

        if is_correction_message(message):
            return {
                "intent": "command",
                "next_node": "command_agent",
                "route_reason": "User corrected the pending action.",
                "trace": append_trace(state, "SupervisorRouterAgent"),
            }

        # If unclear while confirmation is pending, let command_agent try
        # to combine the message with working memory.
        return {
            "intent": "command",
            "next_node": "command_agent",
            "route_reason": "System is awaiting confirmation, but the user did not clearly confirm or cancel.",
            "trace": append_trace(state, "SupervisorRouterAgent"),
        }

    # ============================================================
    # Normal LLM/router-based routing
    # ============================================================

    result = route_next_node(
        message=message,
        has_image=has_image,
        working_memory=working_memory,
    )

    return {
        "intent": result.get("intent", "unknown"),
        "next_node": result.get("next_node", "clarification_agent"),
        "route_reason": result.get("reason", "No route reason provided."),
        "trace": append_trace(state, "SupervisorRouterAgent"),
    }


def command_agent_node(state: AgentState) -> AgentState:
    message = state.get("message") or ""
    working_memory = state.get("loaded_working_memory")

    result = extract_command(
        message=message,
        working_memory=working_memory,
    )

    return {
        "extracted_action": result,
        "trace": append_trace(state, "CommandAgent"),
    }


def clarification_agent_node(state: AgentState) -> AgentState:
    result = generate_clarification(
        message=state.get("message") or "",
        working_memory=state.get("loaded_working_memory"),
    )

    return {
        "clarification_result": result,
        "validation": {
            "is_valid": False,
            "needs_user_clarification": True,
            "question": result.get("message"),
        },
        "trace": append_trace(state, "ClarificationAgent"),
    }


def vision_extraction_agent_node(state: AgentState) -> AgentState:
    result = extract_from_image(
        image_base64=state.get("image_base64"),
        image_url=state.get("image_url"),
        message=state.get("message"),
    )

    extracted_action = result.get("extracted_action")

    return {
        "vision_result": result,
        "extracted_action": extracted_action,
        "trace": append_trace(state, "VisionAgent"),
    }


def financial_advisor_agent_node(state: AgentState) -> AgentState:
    result = generate_financial_advice(state.get("message") or "")

    return {
        "financial_advice": result,
        "trace": append_trace(state, "FinancialAdvisorAgent"),
    }


def recommendation_agent_node(state: AgentState) -> AgentState:
    result = generate_recommendations(
        message=state.get("message") or "",
        financial_advice=state.get("financial_advice", {}),
    )

    return {
        "recommendation_result": result,
        "trace": append_trace(state, "RecommendationAgent"),
    }


def notification_agent_node(state: AgentState) -> AgentState:
    result = decide_notification(
        message=state.get("message") or "",
        financial_advice=state.get("financial_advice", {}),
        recommendation=state.get("recommendation_result", {}),
    )

    return {
        "notification_decision": result,
        "trace": append_trace(state, "NotificationAgent"),
    }