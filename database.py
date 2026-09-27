"""
database.py — SQLite database initialisation, seeding, and access helpers.

Tables:
  - courses        (id, name, description)
  - schedules      (id, course_id FK, day, time, room, seats_available)
  - registrations  (id, student_id, course_id FK, registered_at)
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from config import DATABASE_PATH



def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database with row-factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables (if they don't exist) and seed sample data."""
    conn = get_connection()
    cur = conn.cursor()

    # ── Create tables ─────────────────────────────────────────────────
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS courses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS schedules (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id       INTEGER NOT NULL UNIQUE,
            day             TEXT    NOT NULL,
            time            TEXT    NOT NULL,
            room            TEXT    NOT NULL,
            seats_available INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (course_id) REFERENCES courses(id)
        );

        CREATE TABLE IF NOT EXISTS registrations (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id    INTEGER NOT NULL,
            course_id     INTEGER NOT NULL,
            registered_at TEXT    NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            UNIQUE(student_id, course_id)
        );
        """
    )

    # ── Seed data (skip if courses already exist) ─────────────────────
    existing = cur.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    if existing == 0:
        courses = [
            (1, "Introduction to Computer Science",
             "Fundamentals of programming and computational thinking."),
            (2, "Machine Learning",
             "Supervised and unsupervised learning, neural networks, and practical applications."),
            (3, "Database Systems",
             "Relational databases, SQL, indexing, and transaction management."),
            (4, "Web Development",
             "HTML, CSS, JavaScript, and modern web frameworks."),
            (5, "Linear Algebra",
             "Vectors, matrices, eigenvalues, and applications in data science."),
        ]
        cur.executemany(
            "INSERT INTO courses (id, name, description) VALUES (?, ?, ?)",
            courses,
        )

        schedules = [
            (1, "Monday",    "09:00-11:00", "A101", 10),
            (2, "Tuesday",   "13:00-15:00", "B202",  3),
            (3, "Wednesday", "10:00-12:00", "C303",  0),
            (4, "Thursday",  "14:00-16:00", "D404", 25),
            (5, "Friday",    "08:00-10:00", "E505",  7),
        ]
        cur.executemany(
            "INSERT INTO schedules (course_id, day, time, room, seats_available) "
            "VALUES (?, ?, ?, ?, ?)",
            schedules,
        )

        conn.commit()
        print("✅ Database seeded with sample data.")
    else:
        print("ℹ️  Database already contains data — skipping seed.")

    conn.close()


# ── Query helpers (used by tools.py) ──────────────────────────────────

def search_courses(query: str) -> list[dict]:
    """Return courses whose name or description matches *query* (case-insensitive)."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, description FROM courses "
        "WHERE LOWER(name) LIKE ? OR LOWER(description) LIKE ?",
        (f"%{query.lower()}%", f"%{query.lower()}%"),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_schedule(course_id: int) -> dict | None:
    """Return schedule details for a course, or None if not found."""
    conn = get_connection()
    row = conn.execute(
        "SELECT s.course_id, c.name AS course_name, "
        "       s.day, s.time, s.room, s.seats_available "
        "FROM schedules s "
        "JOIN courses c ON c.id = s.course_id "
        "WHERE s.course_id = ?",
        (course_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def register_student(course_id: int, student_id: int) -> dict:
    """Attempt to register a student for a course. Returns a result dict."""
    conn = get_connection()
    cur = conn.cursor()

    # Check course exists
    course = cur.execute(
        "SELECT id, name FROM courses WHERE id = ?", (course_id,)
    ).fetchone()
    if course is None:
        conn.close()
        return {"success": False, "error": f"Course with id={course_id} does not exist."}

    # Check seats
    schedule = cur.execute(
        "SELECT seats_available FROM schedules WHERE course_id = ?", (course_id,)
    ).fetchone()
    if schedule is None or schedule["seats_available"] <= 0:
        conn.close()
        return {
            "success": False,
            "error": f"No seats available for '{course['name']}' (course_id={course_id}).",
        }

    # Check duplicate
    dup = cur.execute(
        "SELECT id FROM registrations WHERE student_id = ? AND course_id = ?",
        (student_id, course_id),
    ).fetchone()
    if dup:
        conn.close()
        return {
            "success": False,
            "error": f"Student {student_id} is already registered for '{course['name']}'.",
        }

    # Register
    now = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO registrations (student_id, course_id, registered_at) VALUES (?, ?, ?)",
        (student_id, course_id, now),
    )
    cur.execute(
        "UPDATE schedules SET seats_available = seats_available - 1 WHERE course_id = ?",
        (course_id,),
    )
    conn.commit()

    remaining = cur.execute(
        "SELECT seats_available FROM schedules WHERE course_id = ?", (course_id,)
    ).fetchone()["seats_available"]
    conn.close()

    return {
        "success": True,
        "message": (
            f"Student {student_id} successfully registered for "
            f"'{course['name']}' (course_id={course_id}). "
            f"Seats remaining: {remaining}."
        ),
    }
