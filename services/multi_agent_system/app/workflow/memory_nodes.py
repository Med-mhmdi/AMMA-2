from app.graph.state import AgentState
from app.memory.mongo_memory_repository import mongo_memory
from app.workflow.common import append_trace


def memory_load_node(state: AgentState) -> AgentState:
    """
    Loads unified working memory from MongoDB.
    """

    user_id = state.get("user_id")
    session_id = state.get("session_id")

    try:
        working_memory = mongo_memory.get_working_memory(
            user_id=user_id,
            session_id=session_id,
        )
    except Exception as exc:
        return {
            "loaded_working_memory": None,
            "errors": [*state.get("errors", []), f"Memory load failed: {exc}"],
            "trace": append_trace(state, "MemoryLoadNode"),
        }

    return {
        "loaded_working_memory": working_memory,
        "trace": append_trace(state, "MemoryLoadNode"),
    }