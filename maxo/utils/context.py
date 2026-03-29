# utils/context.py — Context Awareness & Learning System for Maxo
# Tracks active window, learns usage patterns, provides smart suggestions

import ctypes
import ctypes.wintypes
import datetime
import os
import json
import psutil

# ══════════════════════════════════════════
# 🧠 CONTEXT AWARENESS — Detect active app
# ══════════════════════════════════════════

def get_active_window():
    """Get the currently focused window's process name and title."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        
        # Get window title
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        
        # Get process name via PID
        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            proc = psutil.Process(pid.value)
            process_name = proc.name().replace(".exe", "")
        except:
            process_name = "unknown"
        
        return process_name, title
    except:
        return "unknown", ""


def get_context_string():
    """Get a human-readable context string for the AI."""
    process_name, title = get_active_window()
    
    # Map process names to friendly names
    APP_NAMES = {
        "Code": "VS Code (code editor)",
        "chrome": "Google Chrome (browser)",
        "msedge": "Microsoft Edge (browser)",
        "firefox": "Firefox (browser)",
        "explorer": "File Explorer",
        "WINWORD": "Microsoft Word",
        "EXCEL": "Microsoft Excel",
        "POWERPNT": "Microsoft PowerPoint",
        "notepad": "Notepad",
        "WindowsTerminal": "Windows Terminal",
        "cmd": "Command Prompt",
        "powershell": "PowerShell",
        "Spotify": "Spotify (music)",
        "Discord": "Discord",
        "Telegram": "Telegram",
        "WhatsApp": "WhatsApp",
        "python": "Python",
        "pythonw": "Maxo (self)",
    }
    
    friendly = APP_NAMES.get(process_name, process_name)
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    
    # Time of day context
    hour = now.hour
    if hour < 6:
        period = "late night"
    elif hour < 12:
        period = "morning"
    elif hour < 17:
        period = "afternoon"
    elif hour < 21:
        period = "evening"
    else:
        period = "night"
    
    context = f"[CONTEXT] Time: {time_str} ({period}). "
    context += f"Active app: {friendly}"
    if title and process_name != "pythonw":
        # Truncate long titles
        short_title = title[:80] + "..." if len(title) > 80 else title
        context += f" — \"{short_title}\""
    context += "."
    
    return context


# ══════════════════════════════════════════
# 📊 LEARNING PREFERENCES — Track patterns
# ══════════════════════════════════════════

USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json")


def log_usage(command):
    """Log a command usage with timestamp for pattern learning."""
    try:
        now = datetime.datetime.now()
        entry = {
            "command": command,
            "hour": now.hour,
            "day": now.strftime("%A"),
            "timestamp": now.isoformat(),
        }
        
        # Load memory
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                mem = json.load(f)
        else:
            mem = {}
        
        # Append to usage log (keep last 200)
        mem.setdefault("usage_log", [])
        mem["usage_log"].append(entry)
        if len(mem["usage_log"]) > 200:
            mem["usage_log"] = mem["usage_log"][-200:]
        
        # Update frequency counter
        mem.setdefault("command_frequency", {})
        mem["command_frequency"][command] = mem["command_frequency"].get(command, 0) + 1
        
        # Track time-based patterns
        time_key = f"{now.hour}:{command}"
        mem.setdefault("time_patterns", {})
        mem["time_patterns"][time_key] = mem["time_patterns"].get(time_key, 0) + 1
        
        # Save
        mem["owner"] = "Abhiyank"
        mem["owner_protected"] = True
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
    except:
        pass  # Non-critical


def get_suggestion():
    """Get a smart suggestion based on time of day and past usage."""
    try:
        if not os.path.exists(USAGE_FILE):
            return None
        
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            mem = json.load(f)
        
        time_patterns = mem.get("time_patterns", {})
        current_hour = datetime.datetime.now().hour
        
        # Find commands frequently used at this hour
        relevant = {}
        for key, count in time_patterns.items():
            hour_str, cmd = key.split(":", 1)
            if int(hour_str) == current_hour and count >= 3:  # At least 3 times at this hour
                relevant[cmd] = count
        
        if not relevant:
            return None
        
        # Return the most frequent one
        top_cmd = max(relevant, key=relevant.get)
        return f"Based on your usual routine, would you like me to {top_cmd.replace('_', ' ')}?"
    except:
        return None


def get_usage_stats():
    """Get usage statistics."""
    try:
        if not os.path.exists(USAGE_FILE):
            return "No usage data yet."
        
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            mem = json.load(f)
        
        freq = mem.get("command_frequency", {})
        if not freq:
            return "No usage data yet."
        
        sorted_cmds = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        lines = [f"  {cmd}: {count}x" for cmd, count in sorted_cmds]
        return "Your most used commands:\n" + "\n".join(lines)
    except:
        return "Couldn't read usage data."
