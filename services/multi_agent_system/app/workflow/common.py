from app.graph.state import AgentState


def append_trace(state: AgentState, step: str) -> list[str]:
    return [*state.get("trace", []), step]


def is_confirmation_message(message: str | None) -> bool:
    text = (message or "").lower().strip()

    yes_words = [
        "yes",
        "yeah",
        "yep",
        "ok",
        "okay",
        "sure",
        "confirm",
        "do it",
        "create it",
        "add it",
        "yes add it",
        "yes create it",
        "oui",
        "saha",
        "saha add it",
        "saha create it",
    ]

    return any(word == text or word in text for word in yes_words)


def is_decline_message(message: str | None) -> bool:
    text = (message or "").lower().strip()

    no_words = [
        "no",
        "nope",
        "cancel",
        "don't",
        "do not",
        "stop",
        "ignore",
        "لا",
    ]

    return any(word == text or word in text for word in no_words)