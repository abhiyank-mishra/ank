# agent_state.py — Shared state between agent and tools
# This module allows tools to communicate with the agent session
# without circular imports.

import json
import os
from pathlib import Path

STATE_FILE = Path(__file__).parent / "state.json"

# ── In-memory state (fast, no disk I/O) ──
_session = None        # Reference to the active AgentSession
_is_sleeping = False   # In-memory sleep flag


def set_session(session):
    """Store the active AgentSession reference so tools can access it."""
    global _session
    _session = session


def get_session():
    """Get the active AgentSession (or None if not set)."""
    return _session


def set_sleeping(sleeping: bool):
    """Update sleep state in both memory and disk."""
    global _is_sleeping
    _is_sleeping = sleeping
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"is_sleeping": sleeping}, f)
    except Exception:
        pass


def is_sleeping() -> bool:
    """Check if the agent is currently sleeping (fast in-memory check)."""
    return _is_sleeping


def sync_from_disk():
    """Sync in-memory state from state.json (for external changes like GUI)."""
    global _is_sleeping
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                _is_sleeping = json.load(f).get("is_sleeping", False)
    except Exception:
        pass
