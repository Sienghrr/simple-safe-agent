"""
main.py — Entry point for the Student Assistant agent.

Initialises the database, parses CLI arguments, and kicks off the agent loop.
"""

from __future__ import annotations

import argparse
import sys

from database import init_db
from agent import run_agent


def main() -> None:
    # Ensure tables + seed data exist
    init_db()

    parser = argparse.ArgumentParser(
        description="Student Assistant — an agentic tool-calling demo",
    )
    parser.add_argument(
        "--role",
        choices=["student", "admin"],
        default="student",
        help="The role of the current user (default: student).",
    )
    parser.add_argument(
        "--student-id",
        type=int,
        default=None,
        help="The student's numeric ID (used when role=student).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override the LLM model (default: from .env).",
    )
    parser.add_argument(
        "request",
        nargs="?",
        default=None,
        help="The user request. If omitted, you will be prompted interactively.",
    )

    args = parser.parse_args()

    # Interactive mode if no request was passed on the CLI
    if args.request:
        user_request = args.request
    else:
        print("╭──────────────────────────────────────────╮")
        print("│   🎓  Student Assistant (Agent Demo)     │")
        print("│   Type 'quit' or 'exit' to stop.         │")
        print(f"│   Role: {args.role:<33s}│")
        print("╰──────────────────────────────────────────╯")
        try:
            user_request = input("\n📝 Your request: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            sys.exit(0)

        if user_request.lower() in {"quit", "exit", "q"}:
            print("Bye!")
            sys.exit(0)

        if not user_request:
            print("Empty request — nothing to do.")
            sys.exit(0)

    print(f"\n🚀 Running agent …\n")

    answer = run_agent(
        user_request,
        role=args.role,
        model=args.model,
        student_id=args.student_id,
    )

    print("─" * 50)
    print(f"✅ Final Answer:\n\n{answer}")
    print("─" * 50)


if __name__ == "__main__":
    main()
