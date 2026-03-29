# utils/memory.py — Maxo Persistent Memory System
# Owner: Abhiyank (protected, cannot be changed by voice commands)

import json
import os
import datetime

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json")

# Protected fields that ONLY the owner can change
PROTECTED_FIELDS = ["owner", "owner_protected", "created_at"]

DEFAULT_MEMORY = {
    "owner": "Abhiyank",
    "owner_protected": True,
    "created_at": datetime.datetime.now().isoformat(),
    "facts": {
        "owner_name": "Abhiyank",
        "assistant_name": "Maxo",
        "assistant_creator": "Abhiyank",
    },
    "notes": [],
    "reminders": [],
    "preferences": {},
    "important": [],
}


def _load_memory():
    """Load memory from disk."""
    if not os.path.exists(MEMORY_FILE):
        _save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure owner is always Abhiyank (tamper protection)
        data["owner"] = "Abhiyank"
        data["owner_protected"] = True
        return data
    except Exception:
        return DEFAULT_MEMORY.copy()


def _save_memory(data):
    """Save memory to disk."""
    # Always enforce owner protection before saving
    data["owner"] = "Abhiyank"
    data["owner_protected"] = True
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Memory save error: {e}")


def save_fact(key, value):
    """Save a key-value fact to memory."""
    # Block attempts to change owner
    if key.lower() in ["owner", "owner_name", "owner_protected", "created_at"]:
        return "Sorry Sir, owner information is protected and cannot be changed."
    mem = _load_memory()
    mem["facts"][key] = value
    mem["facts"]["last_updated"] = datetime.datetime.now().isoformat()
    _save_memory(mem)
    return f"Remembered: {key} = {value}"


def recall_fact(key):
    """Recall a specific fact from memory."""
    mem = _load_memory()
    val = mem["facts"].get(key)
    if val:
        return f"{key}: {val}"
    return f"I don't have anything stored for '{key}', Sir."


def recall_all():
    """Recall all stored facts."""
    mem = _load_memory()
    facts = mem.get("facts", {})
    if not facts:
        return "Memory is empty, Sir."
    lines = [f"  • {k}: {v}" for k, v in facts.items() if k != "last_updated"]
    return "Here's what I remember:\n" + "\n".join(lines)


def save_note(text):
    """Save a quick note."""
    mem = _load_memory()
    note = {
        "text": text,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    mem["notes"].append(note)
    _save_memory(mem)
    return f"Note saved: {text}"


def get_notes():
    """Get all saved notes."""
    mem = _load_memory()
    notes = mem.get("notes", [])
    if not notes:
        return "No notes saved yet, Sir."
    lines = [f"  [{n['timestamp']}] {n['text']}" for n in notes[-10:]]  # Last 10
    return "Your notes:\n" + "\n".join(lines)


def save_reminder(text):
    """Save a reminder."""
    mem = _load_memory()
    reminder = {
        "text": text,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "done": False,
    }
    mem["reminders"].append(reminder)
    _save_memory(mem)
    return f"Reminder set: {text}"


def get_reminders():
    """Get all active reminders."""
    mem = _load_memory()
    reminders = [r for r in mem.get("reminders", []) if not r.get("done")]
    if not reminders:
        return "No active reminders, Sir."
    lines = [f"  • {r['text']} (set {r['timestamp']})" for r in reminders]
    return "Your reminders:\n" + "\n".join(lines)


def save_important(text):
    """Save something important (highlighted in memory)."""
    mem = _load_memory()
    entry = {
        "text": text,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    mem["important"].append(entry)
    _save_memory(mem)
    return f"Marked as important: {text}"


def get_important():
    """Get all important items."""
    mem = _load_memory()
    items = mem.get("important", [])
    if not items:
        return "Nothing marked as important yet, Sir."
    lines = [f"  ⭐ {i['text']} ({i['timestamp']})" for i in items]
    return "Important items:\n" + "\n".join(lines)


def save_preference(key, value):
    """Save a user preference."""
    mem = _load_memory()
    mem.setdefault("preferences", {})[key] = value
    _save_memory(mem)
    return f"Preference saved: {key} = {value}"


def get_owner():
    """Get owner info — always Abhiyank, cannot be changed."""
    return "The owner is Abhiyank. This is protected and cannot be changed."


def clear_notes():
    """Clear all notes."""
    mem = _load_memory()
    mem["notes"] = []
    _save_memory(mem)
    return "All notes cleared, Sir."


def clear_reminders():
    """Clear all reminders."""
    mem = _load_memory()
    mem["reminders"] = []
    _save_memory(mem)
    return "All reminders cleared, Sir."
