from __future__ import annotations

import re

from app.graph.state import AgentState


def append_trace(state: AgentState, step: str) -> list[str]:
    return [*state.get("trace", []), step]


def _clean_text(message: str | None) -> str:
    return re.sub(r"\s+", " ", (message or "").strip().lower())


def is_confirmation_message(message: str | None) -> bool:
    """
    Returns True only for clear confirmation messages.

    Important:
    We avoid broad substring checks because messages like:
    - "not ok"
    - "no, change amount to 92"
    should not be treated as confirmations.
    """

    text = _clean_text(message)

    if not text:
        return False

    exact_confirmations = {
        "yes",
        "yeah",
        "yep",
        "ok",
        "okay",
        "sure",
        "confirm",
        "confirmed",
        "do it",
        "go ahead",
        "looks good",
        "correct",
        "that's correct",
        "that is correct",
        "yes confirm",
        "yes do it",
        "yes add it",
        "yes create it",
        "add it",
        "create it",
        "save it",
        "oui",
        "saha",
    }

    if text in exact_confirmations:
        return True

    negative_prefixes = (
        "no ",
        "no,",
        "not ",
        "don't ",
        "dont ",
        "do not ",
        "cancel",
        "stop",
    )

    if text.startswith(negative_prefixes):
        return False

    return False


def is_decline_message(message: str | None) -> bool:
    """
    Returns True only for clear cancellation/decline messages.

    Important:
    - "no" means cancel.
    - "no, change amount to 92" means correction, not cancel.
    """

    text = _clean_text(message)

    if not text:
        return False

    exact_declines = {
        "no",
        "nope",
        "cancel",
        "stop",
        "ignore",
        "forget it",
        "nevermind",
        "never mind",
        "do not",
        "don't",
        "dont",
        "do not add",
        "don't add",
        "dont add",
        "do not create",
        "don't create",
        "dont create",
        "لا",
    }

    if text in exact_declines:
        return True

    cancel_phrases = [
        "cancel this",
        "cancel it",
        "stop this",
        "forget this",
        "forget that",
        "do not add it",
        "don't add it",
        "dont add it",
    ]

    return any(phrase == text for phrase in cancel_phrases)


def is_correction_message(message: str | None) -> bool:
    """
    Detects when the user is correcting a pending action.

    Examples:
    - "no, amount is 92"
    - "change it to food"
    - "use 250 instead"
    """

    text = _clean_text(message)

    if not text:
        return False

    correction_markers = [
        "change",
        "instead",
        "actually",
        "correct it",
        "update it",
        "use ",
        "make it",
        "it is",
        "it's",
        "amount is",
        "category is",
        "date is",
        "description is",
        "not ",
        "no,",
        "no ",
    ]

    return any(marker in text for marker in correction_markers)