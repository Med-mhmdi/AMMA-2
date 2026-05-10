from typing import Any

from app.graph.state import AgentState
from app.memory.mongo_memory_repository import mongo_memory
from app.workflow.common import append_trace


def _base_memory(state: AgentState) -> dict[str, Any]:
    return state.get("loaded_working_memory") or {
        "messages": [],
        "current_intent": None,
        "current_action": None,
        "awaiting_confirmation": False,
        "confirmation_action": None,
        "last_validation": None,
        "last_question": None,
        "last_result": None,
    }


def _append_message(memory: dict[str, Any], role: str, content: str | None) -> dict[str, Any]:
    if not content:
        return memory

    messages = memory.get("messages", [])

    messages.append(
        {
            "role": role,
            "content": content,
        }
    )

    memory["messages"] = messages[-20:]
    return memory


def _get_assistant_message(state: AgentState) -> str | None:
    validation = state.get("validation") or {}
    execution = state.get("execution_result") or {}
    clarification = state.get("clarification_result") or {}

    if execution.get("message"):
        return execution.get("message")

    if validation.get("question"):
        return validation.get("question")

    if clarification.get("message"):
        return clarification.get("message")

    return None


def memory_update_node(state: AgentState) -> AgentState:
    """
    Unified memory update rules:

    Save working memory when:
    - request is unclear
    - validation needs clarification
    - validation asks for confirmation

    Clear working memory when:
    - execution succeeds
    - execution is cancelled
    """

    user_id = state.get("user_id")
    session_id = state.get("session_id")
    user_message = state.get("message") or ""

    validation = state.get("validation") or {}
    execution = state.get("execution_result") or {}
    extracted_action = state.get("extracted_action")
    clarification = state.get("clarification_result")

    try:
        if execution.get("status") in ["executed", "cancelled"]:
            mongo_memory.clear_working_memory(user_id, session_id)

            return {
                "memory_event": {
                    "status": "working_memory_cleared",
                    "user_id": user_id,
                    "session_id": session_id,
                    "reason": execution.get("status"),
                },
                "trace": append_trace(state, "MemoryUpdateNode"),
            }

        memory = _base_memory(state)

        assistant_message = _get_assistant_message(state)

        memory = _append_message(memory, "user", user_message)
        memory = _append_message(memory, "assistant", assistant_message)

        memory["current_intent"] = state.get("intent")
        memory["last_validation"] = validation
        memory["last_question"] = validation.get("question") or clarification.get("message") if clarification else validation.get("question")
        memory["last_result"] = execution if execution else None

        if extracted_action:
            memory["current_action"] = extracted_action

        if validation.get("awaiting_confirmation"):
            memory["awaiting_confirmation"] = True
            memory["confirmation_action"] = validation.get("confirmation_action")
        else:
            memory["awaiting_confirmation"] = False
            memory["confirmation_action"] = None

        saved_memory = mongo_memory.save_working_memory(
            user_id=user_id,
            session_id=session_id,
            memory=memory,
        )

        return {
            "memory_event": {
                "status": "working_memory_saved",
                "user_id": user_id,
                "session_id": session_id,
                "working_memory": saved_memory,
            },
            "loaded_working_memory": saved_memory,
            "trace": append_trace(state, "MemoryUpdateNode"),
        }

    except Exception as exc:
        return {
            "memory_event": {
                "status": "working_memory_update_failed",
                "error": str(exc),
            },
            "errors": [*state.get("errors", []), f"Memory update failed: {exc}"],
            "trace": append_trace(state, "MemoryUpdateNode"),
        }