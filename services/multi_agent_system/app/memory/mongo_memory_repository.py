from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient

from app.config import settings


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MongoMemoryRepository:
    """
    Unified working memory repository.

    One active document per user/session:
    - stores unresolved messages
    - stores current partial action
    - stores confirmation state
    - clears after action succeeds or is cancelled
    """

    def __init__(self) -> None:
        self.client = MongoClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.collection = self.db["session_working_memory"]

        self.collection.create_index(
            [("user_id", 1), ("session_id", 1)],
            unique=True,
        )

    def get_working_memory(
        self,
        user_id: int | None,
        session_id: str | None,
    ) -> dict[str, Any] | None:
        if user_id is None or not session_id:
            return None

        document = self.collection.find_one(
            {
                "user_id": user_id,
                "session_id": session_id,
                "status": "active",
            },
            {"_id": 0},
        )

        return document

    def save_working_memory(
        self,
        user_id: int | None,
        session_id: str | None,
        memory: dict[str, Any],
    ) -> dict[str, Any] | None:
        if user_id is None or not session_id:
            return None

        now = _utc_now()

        memory = {
            **memory,
            "user_id": user_id,
            "session_id": session_id,
            "status": "active",
            "updated_at": now,
        }

        if not memory.get("created_at"):
            existing = self.get_working_memory(user_id, session_id)
            memory["created_at"] = existing.get("created_at") if existing else now

        self.collection.update_one(
            {
                "user_id": user_id,
                "session_id": session_id,
            },
            {
                "$set": memory,
            },
            upsert=True,
        )

        return self.get_working_memory(user_id, session_id)

    def append_message(
        self,
        user_id: int | None,
        session_id: str | None,
        role: str,
        content: str,
    ) -> dict[str, Any] | None:
        if user_id is None or not session_id:
            return None

        existing = self.get_working_memory(user_id, session_id) or {
            "user_id": user_id,
            "session_id": session_id,
            "status": "active",
            "messages": [],
            "current_intent": None,
            "current_action": None,
            "awaiting_confirmation": False,
            "confirmation_action": None,
            "last_validation": None,
            "last_question": None,
            "last_result": None,
            "created_at": _utc_now(),
        }

        messages = existing.get("messages", [])

        messages.append(
            {
                "role": role,
                "content": content,
                "created_at": _utc_now(),
            }
        )

        existing["messages"] = messages[-20:]
        existing["updated_at"] = _utc_now()

        return self.save_working_memory(user_id, session_id, existing)

    def clear_working_memory(
        self,
        user_id: int | None,
        session_id: str | None,
    ) -> bool:
        if user_id is None or not session_id:
            return False

        self.collection.delete_one(
            {
                "user_id": user_id,
                "session_id": session_id,
            }
        )

        return True

    # =========================
    # Compatibility helpers
    # Keep these temporarily so old imports do not crash.
    # =========================

    def get_pending_action(
        self,
        user_id: int | None,
        session_id: str | None,
    ) -> dict[str, Any] | None:
        memory = self.get_working_memory(user_id, session_id)

        if not memory:
            return None

        return memory.get("confirmation_action")

    def save_pending_action(
        self,
        user_id: int | None,
        session_id: str | None,
        pending_action: dict[str, Any],
    ) -> None:
        memory = self.get_working_memory(user_id, session_id) or {
            "messages": [],
            "current_intent": "command",
            "current_action": pending_action.get("original_action"),
            "awaiting_confirmation": True,
            "confirmation_action": pending_action,
            "last_validation": None,
            "last_question": None,
            "last_result": None,
            "created_at": _utc_now(),
        }

        memory["awaiting_confirmation"] = True
        memory["confirmation_action"] = pending_action
        memory["current_action"] = pending_action.get("original_action")
        memory["current_intent"] = "command"

        self.save_working_memory(user_id, session_id, memory)

    def clear_pending_action(
        self,
        user_id: int | None,
        session_id: str | None,
    ) -> None:
        self.clear_working_memory(user_id, session_id)


mongo_memory = MongoMemoryRepository()