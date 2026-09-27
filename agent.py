"""
agent.py — The agent loop: sends messages to the LLM, detects tool
           calls, dispatches them through the harness, and loops until
           a final answer is produced or the budget is exhausted.

Uses Ollama via its OpenAI-compatible API endpoint.
"""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, MAX_TOOL_CALLS
from harness import check_iteration_budget, execute_tool_call
from schemas import TOOL_SCHEMAS


# ── System prompt ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a helpful Student Assistant. You help students and admins
with university course information.

You have access to the following tools:
  • search_course  – search the course catalog by keyword.
  • check_schedule – look up the schedule (day, time, room, seats) for a course.
  • register_course – register a student for a course (admin only).

Guidelines:
  - Always search for courses before checking schedules.
  - When registering, confirm the course has available seats first.
  - If a tool returns an error, relay it clearly to the user.
  - When you have enough information, provide a concise final answer.
  - Do not use tools unnecessarily — only call a tool when it helps answer the request.
"""


def run_agent(
    user_message: str,
    *,
    role: str = "student",
    model: str | None = None,
    student_id: int | None = None,
) -> str:
    """
    Execute the full agent loop for a single user request.

    Parameters
    ----------
    user_message : str
        The natural-language request from the user.
    role : str
        The caller's role — used by the harness for permission checks.
    model : str | None
        Override the LLM model (defaults to LLM_MODEL from .env).
    student_id : int | None
        If the caller is a student, their ID (injected into context).

    Returns
    -------
    str
        The agent's final textual answer.
    """

    model = model or LLM_MODEL

    # Ollama exposes an OpenAI-compatible API
    client = OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
    )

    # Build the initial message list
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                f"Current user role: {role}."
                + (f" Student ID: {student_id}." if student_id else "")
            ),
        },
        {"role": "user", "content": user_message},
    ]

    tool_call_count = 0

    print(f"  ⚙️ Model: {model}  |  Base URL: {LLM_BASE_URL}")
    print(f"  🔒 Role: {role}  |  Max tool calls: {MAX_TOOL_CALLS}\n")

    # ── Agent loop ────────────────────────────────────────────────────
    while True:
        # Budget check
        budget_error = check_iteration_budget(tool_call_count)
        if budget_error:
            return f"[Agent stopped] {budget_error}"

        # Call the LLM
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message

        # Append the assistant's message to the conversation
        messages.append(assistant_message.model_dump(exclude_none=True))

        # If no tool calls → the model is done; return its text answer
        if not assistant_message.tool_calls:
            return assistant_message.content or "[Agent produced no output]"

        # Process every tool call in this turn
        for tc in assistant_message.tool_calls:
            tool_call_count += 1

            budget_error = check_iteration_budget(tool_call_count)
            if budget_error:
                return f"[Agent stopped] {budget_error}"

            tool_name = tc.function.name
            raw_args = tc.function.arguments

            print(f"  🔧  Tool call #{tool_call_count}: {tool_name}({raw_args})")

            # Dispatch through the harness (permission + validation + execution)
            result = execute_tool_call(tool_name, raw_args, role=role)
            result_str = json.dumps(result, ensure_ascii=False)

            print(f"  📦  Result: {result_str}\n")

            # Feed the result back into the conversation
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_str,
                }
            )
