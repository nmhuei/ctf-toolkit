"""Automaton Transition Policy Template for Interactive CTF Tasks."""

from __future__ import annotations

import re
from typing import Callable, Any

# Type alias: Action can be bytes, string, or callable(context) -> bytes|str
ActionType = bytes | str | Callable[[dict[str, Any]], bytes | str]

# Transition mapping: state -> list of (regex_pattern, action, next_state)
AUTOMATON_POLICY: dict[str, list[tuple[re.Pattern, ActionType, str]]] = {
    "INIT": [
        (re.compile(r"Choice:\s*"), "1\n", "PROMPT_PARAM"),
        (re.compile(r"Exit\s*"), "0\n", "TERMINATED"),
    ],
    "PROMPT_PARAM": [
        (re.compile(r"Input index:\s*"), lambda ctx: f"{ctx['index']}\n", "WAIT_RESULT"),
    ],
    "WAIT_RESULT": [
        (re.compile(r"Token:\s*([a-zA-Z0-9_]+)"), lambda ctx: None, "SUCCESS"),
    ],
}
