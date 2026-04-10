"""Text matching utilities for conversation input."""

from __future__ import annotations


GREETING_WORDS = {"hello", "hi", "hey", "yo", "start", "begin", "menu", "order", "hungry"}


def is_greeting(text: str) -> bool:
    """Check if user text is a greeting / conversation starter."""
    normalized = text.strip().lower()
    # Exact match
    if normalized in GREETING_WORDS:
        return True
    # Contains a greeting word
    words = set(normalized.split())
    return bool(words & GREETING_WORDS)


def fuzzy_match(text: str, options: list[str]) -> str | None:
    """
    Match user text against a list of options.
    Returns the matched option string, or None.

    Priority: exact match > contains match > partial word match.
    """
    normalized = text.strip().lower()
    if not normalized:
        return None

    # 1. Exact match
    for opt in options:
        if normalized == opt.lower():
            return opt

    # 2. User text contains option or option contains user text
    for opt in options:
        opt_lower = opt.lower()
        if opt_lower in normalized or normalized in opt_lower:
            return opt

    return None
