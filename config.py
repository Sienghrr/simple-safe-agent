"""
config.py — Centralised configuration loaded from environment variables.

All sensitive or tuneable values live in .env and are accessed through
this module so no secrets leak into source code.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()  # reads .env in the project root

# ── LLM ───────────────────────────────────────────────────────────────
LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen3:4b")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "ollama")

# ── Database ──────────────────────────────────────────────────────────
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "student_assistant.db")

# ── Agent Safety ──────────────────────────────────────────────────────
MAX_TOOL_CALLS: int = int(os.getenv("MAX_TOOL_CALLS", "10"))
