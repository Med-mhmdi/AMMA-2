from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    cancel_working_memory_node,
    clarification_agent_node,
    command_agent_node,
    confirmation_execution_node,
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


def route_after_supervisor_router(state: AgentState) -> str:
    next_node = state.get("next_node", "clarification_agent")

    allowed_routes = {
        "command_agent",
        "confirmation_execution",
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
    validation = state.get("validation", {})

    if validation.get("needs_user_clarification"):
        return "memory_update"

    return "tool_execution"


def build_amma_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("memory_load", memory_load_node)
    graph.add_node("supervisor_router", supervisor_router_node)

    graph.add_node("command_agent", command_agent_node)
    graph.add_node("clarification_agent", clarification_agent_node)
    graph.add_node("vision_agent", vision_extraction_agent_node)
    graph.add_node("financial_advisor", financial_advisor_agent_node)
    graph.add_node("recommendation_agent", recommendation_agent_node)
    graph.add_node("notification_agent", notification_agent_node)

    graph.add_node("tool_context", tool_context_node)
    graph.add_node("validation", validation_node)
    graph.add_node("tool_execution", tool_execution_node)

    graph.add_node("confirmation_execution", confirmation_execution_node)
    graph.add_node("cancel_working_memory", cancel_working_memory_node)

    graph.add_node("memory_update", memory_update_node)
    graph.add_node("final_response", final_response_node)

    graph.add_edge(START, "memory_load")
    graph.add_edge("memory_load", "supervisor_router")

    graph.add_conditional_edges(
        "supervisor_router",
        route_after_supervisor_router,
        {
            "command_agent": "command_agent",
            "confirmation_execution": "confirmation_execution",
            "cancel_working_memory": "cancel_working_memory",
            "financial_advisor": "financial_advisor",
            "recommendation_agent": "recommendation_agent",
            "notification_agent": "notification_agent",
            "vision_agent": "vision_agent",
            "clarification_agent": "clarification_agent",
            "final_response": "final_response",
        },
    )

    graph.add_edge("command_agent", "tool_context")
    graph.add_edge("tool_context", "validation")

    graph.add_conditional_edges(
        "validation",
        route_after_validation,
        {
            "tool_execution": "tool_execution",
            "memory_update": "memory_update",
        },
    )

    graph.add_edge("tool_execution", "memory_update")

    graph.add_edge("vision_agent", "validation")

    graph.add_edge("financial_advisor", "recommendation_agent")
    graph.add_edge("recommendation_agent", "notification_agent")
    graph.add_edge("notification_agent", "memory_update")

    graph.add_edge("clarification_agent", "memory_update")
    graph.add_edge("confirmation_execution", "memory_update")
    graph.add_edge("cancel_working_memory", "memory_update")

    graph.add_edge("memory_update", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile()


amma_agent_graph = build_amma_agent_graph()