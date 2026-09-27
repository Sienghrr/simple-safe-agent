"""
schemas.py — Pydantic models that define the input schema for each tool.

Each schema describes the expected inputs, types, required fields, and
constraints so the LLM knows how to call the tool correctly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


#  Tool input schemas 

class SearchCourseInput(BaseModel):
    """Input schema for the search_course tool."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="A keyword or phrase to search for in the course catalog (e.g. 'machine learning').",
    )


class CheckScheduleInput(BaseModel):
    """Input schema for the check_schedule tool."""

    course_id: int = Field(
        ...,
        gt=0,
        description="The positive integer ID of the course whose schedule you want to check.",
    )


class RegisterCourseInput(BaseModel):
    """Input schema for the register_course tool."""

    course_id: int = Field(
        ...,
        gt=0,
        description="The positive integer ID of the course to register for.",
    )
    student_id: int = Field(
        ...,
        gt=0,
        description="The positive integer ID of the student who is registering.",
    )


#  OpenAI-compatible JSON-schema descriptions for each tool 
# These are passed to the model via the `tools` parameter so it knows
# what tools are available and how to invoke them.

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_course",
            "description": (
                "Search the course catalog by keyword. "
                "Returns a list of matching courses with id, name, and description."
            ),
            "parameters": SearchCourseInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_schedule",
            "description": (
                "Check the weekly schedule (day, time, room) for a specific course."
            ),
            "parameters": CheckScheduleInput.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "register_course",
            "description": (
                "Register a student for a course. "
                "Requires both the course ID and the student ID."
            ),
            "parameters": RegisterCourseInput.model_json_schema(),
        },
    },
]
