"""
Naming convention engine.

Converts a single developer-provided name (in any casual form) into every
naming variant used across generated code: snake_case, PascalCase,
kebab-case, plural forms, etc.

This is the single source of truth for naming — no generator or template
should re-implement casing/pluralization logic independently.
"""

from __future__ import annotations

import re

import inflect

_inflect_engine = inflect.engine()

# Module/entity names that are acronyms and should render as full
# uppercase in human-readable form, instead of naive Title Case.
_KNOWN_ACRONYMS: set[str] = {
    "hrms",
    "crm",
    "eam",
    "bms",
}

# Words where naive pluralization is wrong or ambiguous and we want a fixed,
# predictable answer regardless of what `inflect` guesses.
_IRREGULAR_PLURALS: dict[str, str] = {
    "status": "statuses",
    "asset": "assets",
    "person": "people",
    "staff": "staff",
    "equipment": "equipment",
    "series": "series",
    "species": "species",
}


def _split_words(raw: str) -> list[str]:
    """
    Split any input form (kebab-case, snake_case, PascalCase, camelCase,
    or plain words) into lowercase word tokens.

    Examples:
        "work-order"                 -> ["work", "order"]
        "InfrastructureMonitoring"   -> ["infrastructure", "monitoring"]
        "field_service_management"  -> ["field", "service", "management"]
    """
    if not raw or not raw.strip():
        raise ValueError("Name cannot be empty")

    # Normalize separators to spaces first.
    normalized = re.sub(r"[-_\s]+", " ", raw.strip())

    # Insert a space before capital letters that start a new word
    # (handles PascalCase / camelCase input).
    normalized = re.sub(r"(?<!^)(?=[A-Z])", " ", normalized)

    words = [w.lower() for w in normalized.split() if w]

    if not words:
        raise ValueError(f"Could not parse any words from name: {raw!r}")

    return words


def to_snake_case(raw: str) -> str:
    """'work-order' -> 'work_order'"""
    return "_".join(_split_words(raw))


def to_kebab_case(raw: str) -> str:
    """'work_order' -> 'work-order'"""
    return "-".join(_split_words(raw))


def to_pascal_case(raw: str) -> str:
    """'work-order' -> 'WorkOrder'"""
    return "".join(word.capitalize() for word in _split_words(raw))


def to_camel_case(raw: str) -> str:
    """'work-order' -> 'workOrder'"""
    words = _split_words(raw)
    if not words:
        return ""
    return words[0] + "".join(w.capitalize() for w in words[1:])


def to_human_readable(raw: str) -> str:
    """'work-order' -> 'Work Order'; 'hrms' -> 'HRMS'"""
    words = _split_words(raw)
    return " ".join(
        word.upper() if word in _KNOWN_ACRONYMS else word.capitalize()
        for word in words
    )


def pluralize_last_word(raw: str) -> str:
    """
    Pluralize only the final word of a (possibly multi-word) snake_case name.

    'work_order' -> 'work_orders'
    'employee'   -> 'employees'
    'company_status' -> 'company_statuses'

    Checks the irregular-plurals table first, falls back to `inflect`.
    """
    words = _split_words(raw)
    last_word = words[-1]

    plural_last = _IRREGULAR_PLURALS.get(last_word)
    if plural_last is None:
        result = _inflect_engine.plural_noun(last_word)
        plural_last = result if result else last_word

    return "_".join([*words[:-1], plural_last])


def to_snake_plural(raw: str) -> str:
    """'work-order' -> 'work_orders'"""
    return pluralize_last_word(to_snake_case(raw))


def to_pascal_plural(raw: str) -> str:
    """'work-order' -> 'WorkOrders'"""
    snake_plural = to_snake_plural(raw)
    return to_pascal_case(snake_plural)


def to_kebab_plural(raw: str) -> str:
    """'work_order' -> 'work-orders'"""
    return to_snake_plural(raw).replace("_", "-")