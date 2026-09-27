"""
harness.py — Permission control, input validation, iteration limits,
             and safety checks.

This module sits between the agent loop and the actual tool functions.
Every tool call proposed by the LLM passes through `execute_tool_call`
which enforces:
  1. Role-based permission (RBAC)
  2. Input validation via Pydantic schemas
  3. A per-run iteration / tool-call budget
  4. Graceful error handling
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from config import MAX_TOOL_CALLS
from schemas import (
    CheckScheduleInput,
    RegisterCourseInput,
    SearchCourseInput,
)
from tools import check_schedule, register_course, search_course


#RBAC
PERMISSIONS: dict[str, set[str]] = {
    "search_course":   {"student", "admin"},
    "check_schedule":  {"student", "admin"},
    "register_course": {"admin"},
}


# Internal registry: tool name → (schema class, implementation) 

_TOOL_REGISTRY: dict[str, tuple[type, callable]] = {
    "search_course":   (SearchCourseInput,   search_course),
    "check_schedule":  (CheckScheduleInput,  check_schedule),
    "register_course": (RegisterCourseInput, register_course),
}


# Public helpers 

def check_iteration_budget(current_count: int) -> str | None:
    """Return an error message if the tool-call budget is exhausted, else None."""
    if current_count >= MAX_TOOL_CALLS:
        return (
            f"Tool-call limit reached ({MAX_TOOL_CALLS}). "
            "Stopping the agent loop to prevent runaway execution."
        )
    return None


def execute_tool_call(
    tool_name: str,
    raw_arguments: str | dict,
    role: str,
) -> dict[str, Any]:
    """
    Validate permissions → validate input → execute tool → return result.

    Returns a dict that is always safe to serialise back into the
    conversation as a tool-result message.
    """

    # 1. Check the tool exists
    if tool_name not in _TOOL_REGISTRY:
        return {"error": f"Unknown tool '{tool_name}'."}

    # 2. Permission check
    allowed_roles = PERMISSIONS.get(tool_name, set())
    if role not in allowed_roles:
        return {
            "error": (
                f"Permission denied: role '{role}' is not allowed to call "
                f"'{tool_name}'. Allowed roles: {sorted(allowed_roles)}."
            )
        }

    schema_cls, impl_fn = _TOOL_REGISTRY[tool_name]

    # 3. Parse raw arguments (LLM may send a JSON string or a dict)
    if isinstance(raw_arguments, str):
        try:
            args_dict = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            return {"error": f"Invalid JSON arguments: {exc}"}
    else:
        args_dict = raw_arguments

    # 4. Validate with Pydantic
    try:
        validated = schema_cls(**args_dict)
    except ValidationError as exc:
        return {"error": f"Input validation failed: {exc}"}

    # 5. Execute the tool
    try:
        result = impl_fn(**validated.model_dump())
    except Exception as exc:  # noqa: BLE001
        return {"error": f"Tool execution error: {exc}"}

    return result
