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
_exit_requested = False  # In-memory exit flag


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
        # Preserve exit_requested if it was already set
        existing = {}
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing["is_sleeping"] = sleeping
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f)
    except Exception:
        pass


def is_sleeping() -> bool:
    """Check if the agent is currently sleeping (fast in-memory check)."""
    return _is_sleeping


def set_exit_requested(val: bool):
    """Mark that exit has been requested."""
    global _exit_requested
    _exit_requested = val
    try:
        existing = {}
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing["exit_requested"] = val
        existing["is_sleeping"] = True  # Also sleep when exiting
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f)
    except Exception:
        pass


def is_exit_requested() -> bool:
    """Check if exit has been requested."""
    return _exit_requested


def sync_from_disk():
    """Sync in-memory state from state.json (for external changes like GUI)."""
    global _is_sleeping, _exit_requested
    try:
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                _is_sleeping = data.get("is_sleeping", False)
                _exit_requested = data.get("exit_requested", False)
    except Exception:
        pass


def reset_state():
    """Reset all state flags to defaults (called on startup)."""
    global _is_sleeping, _exit_requested
    _is_sleeping = False
    _exit_requested = False
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"is_sleeping": False, "exit_requested": False}, f)
    except Exception:
        pass
