"""
tools.py — Actual tool implementations / business logic.

Each function delegates to database.py for persistent SQLite storage.
"""

from __future__ import annotations

from database import get_schedule, register_student, search_courses


#  Tool implementations 

def search_course(query: str) -> list[dict]:
    """Search the course catalog by keyword (case-insensitive)."""
    results = search_courses(query)
    if not results:
        return [{"message": f"No courses found matching '{query}'."}]
    return results


def check_schedule(course_id: int) -> dict:
    """Return the schedule details for a given course ID."""
    schedule = get_schedule(course_id)
    if schedule is None:
        return {"error": f"No schedule found for course_id={course_id}."}
    return schedule


def register_course(course_id: int, student_id: int) -> dict:
    """Register a student for a course, checking availability first."""
    return register_student(course_id, student_id)
