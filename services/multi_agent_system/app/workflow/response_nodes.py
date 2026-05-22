from app.graph.state import AgentState
from app.workflow.common import append_trace


def final_response_node(state: AgentState) -> AgentState:
    validation = state.get("validation") or {}
    execution_result = state.get("execution_result")
    clarification_result = state.get("clarification_result")
    vision_result = state.get("vision_result") or {}
    intent = state.get("intent")

    if execution_result:
        response = {
            "type": "command_result",
            "message": execution_result.get("message", "Done."),
            "action": state.get("extracted_action"),
            "execution": execution_result,
            "trace": state.get("trace", []),
        }

    elif validation.get("awaiting_conflict_resolution"):
        response = {
            "type": "conflict_resolution",
            "message": validation.get("question"),
            "intent": intent,
            "pending_memory": state.get("memory_event"),
            "conflict_action": validation.get("conflict_action"),
            "existing_record": validation.get("existing_record"),
            "options": validation.get(
                "conflict_options",
                ["add_anyway", "update_existing", "cancel"],
            ),
            "trace": state.get("trace", []),
        }

    elif validation.get("awaiting_confirmation"):
        response = {
            "type": "confirmation",
            "message": validation.get("question"),
            "intent": intent,
            "pending_memory": state.get("memory_event"),
            "confirmation_action": validation.get("confirmation_action"),
            "action": state.get("extracted_action"),
            "vision_result": vision_result if vision_result else None,
            "trace": state.get("trace", []),
        }

    # Important:
    # If Vision Agent extracted partial data, use its friendly question instead
    # of the generic validation question.
    elif (
        vision_result.get("needs_user_clarification")
        and vision_result.get("question")
    ):
        response = {
            "type": "clarification",
            "message": vision_result.get("question"),
            "intent": intent,
            "action": state.get("extracted_action"),
            "vision_result": vision_result,
            "pending_memory": state.get("memory_event"),
            "matches": validation.get("matches"),
            "trace": state.get("trace", []),
        }

    elif validation.get("needs_user_clarification"):
        response = {
            "type": "clarification",
            "message": validation.get("question"),
            "intent": intent,
            "action": state.get("extracted_action"),
            "pending_memory": state.get("memory_event"),
            "matches": validation.get("matches"),
            "trace": state.get("trace", []),
        }

    elif clarification_result:
        response = {
            "type": "clarification",
            "message": clarification_result.get("message"),
            "intent": intent,
            "pending_memory": state.get("memory_event"),
            "trace": state.get("trace", []),
        }

    elif intent == "financial_advice":
        response = {
            "type": "financial_advice",
            "message": state.get("financial_advice", {}).get("summary"),
            "financial_advice": state.get("financial_advice"),
            "recommendations": state.get("recommendation_result", {}).get(
                "recommendations",
                state.get("financial_advice", {}).get("recommendations", []),
            ),
            "recommendation_result": state.get("recommendation_result"),
            "notification": state.get("notification_decision"),
            "trace": state.get("trace", []),
        }

    elif intent == "recommendation":
        response = {
            "type": "recommendation",
            "recommendations": state.get("recommendation_result", {}).get(
                "recommendations",
                [],
            ),
            "recommendation_result": state.get("recommendation_result"),
            "notification": state.get("notification_decision"),
            "trace": state.get("trace", []),
        }

    elif intent == "notification":
        response = {
            "type": "notification",
            "notification": state.get("notification_decision"),
            "trace": state.get("trace", []),
        }

    else:
        response = {
            "type": "clarification",
            "message": (
                "I could not understand the request clearly. "
                "Please tell me what you want to add, update, delete, check, or analyze."
            ),
            "intent": intent,
            "trace": state.get("trace", []),
        }

    return {
        "final_response": response,
        "trace": append_trace(state, "FinalResponseNode"),
    }