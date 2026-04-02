# utils/context.py — Context Awareness & Auto-Learning System for Jessica
# Tracks active window, learns usage patterns, auto-observes user behavior
# Automatically saves important user info to memory.json
# Owner: Abhiyank

import ctypes
import ctypes.wintypes
import datetime
import os
import json
import psutil
import re

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "memory.json")

# ══════════════════════════════════════════
# 🧠 CONTEXT AWARENESS — Detect active app
# ══════════════════════════════════════════

def get_active_window():
    """Get the currently focused window's process name and title."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
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
    APP_NAMES = {
        "Code": "VS Code (code editor)", "chrome": "Google Chrome (browser)",
        "msedge": "Microsoft Edge (browser)", "firefox": "Firefox (browser)",
        "explorer": "File Explorer", "WINWORD": "Microsoft Word",
        "EXCEL": "Microsoft Excel", "POWERPNT": "Microsoft PowerPoint",
        "notepad": "Notepad", "WindowsTerminal": "Windows Terminal",
        "cmd": "Command Prompt", "powershell": "PowerShell",
        "Spotify": "Spotify (music)", "Discord": "Discord",
        "Telegram": "Telegram", "WhatsApp": "WhatsApp",
        "python": "Python", "pythonw": "Jessica (self)",
    }
    friendly = APP_NAMES.get(process_name, process_name)
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    hour = now.hour
    if hour < 6:    period = "late night"
    elif hour < 12: period = "morning"
    elif hour < 17: period = "afternoon"
    elif hour < 21: period = "evening"
    else:           period = "night"
    context = f"[CONTEXT] Time: {time_str} ({period}). "
    context += f"Active app: {friendly}"
    if title and process_name != "pythonw":
        short_title = title[:80] + "..." if len(title) > 80 else title
        context += f' — "{short_title}"'
    context += "."
    return context


# ══════════════════════════════════════════
# 📊 USAGE TRACKING — Track command patterns
# ══════════════════════════════════════════

def log_usage(command):
    """Log a command usage with timestamp for pattern learning."""
    try:
        now = datetime.datetime.now()
        entry = {
            "command": command, "hour": now.hour,
            "day": now.strftime("%A"), "timestamp": now.isoformat(),
        }
        mem = _load_mem()
        mem.setdefault("usage_log", []).append(entry)
        if len(mem["usage_log"]) > 200:
            mem["usage_log"] = mem["usage_log"][-200:]
        mem.setdefault("command_frequency", {})
        mem["command_frequency"][command] = mem["command_frequency"].get(command, 0) + 1
        time_key = f"{now.hour}:{command}"
        mem.setdefault("time_patterns", {})
        mem["time_patterns"][time_key] = mem["time_patterns"].get(time_key, 0) + 1
        _save_mem(mem)
    except:
        pass


def get_suggestion():
    """Get a smart suggestion based on time of day and past usage."""
    try:
        mem = _load_mem()
        time_patterns = mem.get("time_patterns", {})
        current_hour = datetime.datetime.now().hour
        relevant = {}
        for key, count in time_patterns.items():
            hour_str, cmd = key.split(":", 1)
            if int(hour_str) == current_hour and count >= 3:
                relevant[cmd] = count
        if not relevant:
            return None
        top_cmd = max(relevant, key=relevant.get)
        return f"Based on your usual routine, would you like me to {top_cmd.replace('_', ' ')}?"
    except:
        return None


def get_usage_stats():
    """Get usage statistics."""
    try:
        mem = _load_mem()
        freq = mem.get("command_frequency", {})
        if not freq:
            return "No usage data yet."
        sorted_cmds = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
        lines = [f"  {cmd}: {count}x" for cmd, count in sorted_cmds]
        return "Your most used commands:\n" + "\n".join(lines)
    except:
        return "Couldn't read usage data."


# ══════════════════════════════════════════
# 🧬 AUTO-LEARNING — Jessica silently learns about User
# ══════════════════════════════════════════
# This system observes EVERY user speech and extracts:
#  - Personal info (name, age, birthday, location, phone)
#  - Relationships (friends, family, gf/bf names)
#  - Preferences (likes, dislikes, favorites)
#  - Work/study info
#  - Habits & routines
#  - Emotional state
#  - Topics of interest
#  - Important things user wants remembered
# Like a real personal assistant who never forgets.

# ─── Pattern groups for extraction ───

_PERSONAL_PATTERNS = [
    # Name — capture 1 word, or 2 words only if second is also a name (uppercase start)
    (r"(?:my|mera|mere|meri)\s+(?:name|naam)\s+(?:is|hai|h)\s+([a-zA-Z]+)(?:\s+(?:and|or|i|aur|hai|h|main|me|hoon|hu)\b|[.,!]|\s|$)", "user_name"),
    (r"(?:call me|mujhe bolo|bolo mujhe)\s+([a-zA-Z]+)(?:\s|[.,!]|$)", "nickname"),
    # Age
    (r"(?:my|mera|meri)\s+(?:age|umar|umr)\s+(?:is|hai|h)\s+(\d+)", "age"),
    (r"(?:i am|main|me|i'm)\s+(\d{1,2})\s+(?:years?\s*old|saal\s*ka|saal\s*ki|ka\s*hu|ki\s*hu)", "age"),
    # Birthday
    (r"(?:my|mera|mere)\s+(?:birthday|bday|janamdin|janam\s*din)\s+(?:is|hai|h|on)\s+(.+?)(?:\.|,|!|$)", "birthday"),
    # Location
    (r"(?:i\s+live\s+in|i'm\s+from|i\s+am\s+from)\s+([A-Za-z]+(?:\s[A-Za-z]+){0,2})", "location"),
    (r"(?:mera\s+ghar|my\s+home)\s+(?:is\s+in|hai|h)\s+([A-Za-z]+(?:\s[A-Za-z]+){0,2})", "location"),
    # Phone/Email
    (r"(?:my|mera|mere)\s+(?:number|phone|mobile|no)\s+(?:is|hai|h)\s+(\+?\d[\d\s\-]{7,14})", "phone"),
    (r"(?:my|mera)\s+(?:email|mail|gmail)\s+(?:is|hai|h)\s+([\w.+-]+@[\w.-]+)", "email"),
    # Education
    (r"(?:i\s+study|main\s+padhta|main\s+padhti|i\s+am\s+studying|me\s+padhta)\s+(?:in\s+)?(.+?)(?:\.|,|!|$)", "studying"),
    (r"(?:my\s+(?:college|school|university|uni))\s+(?:is|hai|h|ka\s+naam)\s+(.+?)(?:\.|,|!|$)", "school"),
    (r"(?:i\s+am\s+(?:in|a)\s+)(?:class|std|standard|semester|sem)\s+(.+?)(?:\.|,|!|$)", "class"),
    # Work
    (r"(?:i\s+am\s+a|main\s+ek|me\s+ek)\s+(student|developer|engineer|teacher|designer|doctor|coder|programmer|freelancer|artist|gamer|youtuber|creator|streamer)", "occupation"),
    (r"(?:i\s+work\s+at|i\s+work\s+for)\s+(.+?)(?:\.|,|!|$)", "workplace"),
]

_RELATIONSHIP_PATTERNS = [
    # Family & Friends — capture clean name only
    (r"(?:my|mera|mere|meri)\s+(friend|dost|best\s*friend|bhai|brother|sister|behan|didi|bhaiya|mom|maa|mother|dad|papa|father|girlfriend|gf|bf|boyfriend|wife|husband|crush|partner|uncle|chacha|aunt|mausi)\s+(?:ka\s+naam|ka\s+name|is|name\s+is)\s+([A-Za-z]+)(?:\s|[.,!]|$)", "relationship"),
    (r"([A-Z][a-z]+)\s+(?:is\s+my|mera|meri)\s+(friend|dost|best\s*friend|brother|bhai|sister|behan|mom|dad|girlfriend|gf|bf|boyfriend)", "relationship_reverse"),
]

_PREFERENCE_PATTERNS = [
    # Likes
    (r"(?:i\s+like|mujhe\s+pasand|i\s+love|mujhe\s+accha|mujhe\s+acha|mujhe\s+pasan)\s+(.+?)(?:\.|,|!|$)", "likes"),
    (r"(?:i\s+enjoy|i\s+prefer|mujhe\s+maja)\s+(.+?)(?:\.|,|!|$)", "likes"),
    # Dislikes
    (r"(?:i\s+hate|i\s+don'?t\s+like|mujhe\s+nahi\s+pasand|mujhe\s+pasand\s+nahi|i\s+dislike)\s+(.+?)(?:\.|,|!|$)", "dislikes"),
    # Favorites
    (r"(?:my\s+favorite|my\s+fav|mera\s+favorite|meri\s+favorite|mera\s+fav)\s+(\w+)\s+(?:is|hai|h)\s+(.+?)(?:\.|,|!|$)", "favorite"),
    (r"(?:i\s+love|best)\s+(\w+)\s+(?:is|hai|h)\s+(.+?)(?:\.|,|!|$)", "favorite"),
]

_REMEMBER_PATTERNS = [
    # Explicit memory requests
    (r"(?:remember\s+that|yaad\s+rakh|yaad\s+rakhna|note\s+kr|note\s+karo)\s+(.+?)(?:\.|!|$)", "explicit_remember"),
    (r"(?:don'?t\s+forget|bhulna\s+mat|bhulna\s+nhi|mat\s+bhulna)\s+(.+?)(?:\.|!|$)", "explicit_remember"),
    (r"(?:important\s+(?:baat|thing|cheez))\s+(?:hai|is|h)\s+(?:ki|that)\s+(.+?)(?:\.|!|$)", "explicit_remember"),
    # Passwords & PINs (sensitive — still saved but marked)
    (r"(?:password|pin|code|passcode)\s+(?:is|hai|h)\s+(.+?)(?:\.|,|!|$)", "sensitive"),
    (r"(?:my|mera)\s+(?:password|pin|code|passcode)\s+(?:is|hai|h|for)\s+(.+?)(?:\.|,|!|$)", "sensitive"),
]

_HABIT_PATTERNS = [
    # Daily routines
    (r"(?:i\s+(?:usually|always|normally)|main\s+(?:hamesha|roz))\s+(.+?)(?:\.|,|!|$)", "habit"),
    (r"(?:every\s+(?:day|morning|night|evening)|har\s+(?:din|subah|raat|shaam))\s+(?:i|main|me)\s+(.+?)(?:\.|,|!|$)", "routine"),
    # Sleep patterns
    (r"(?:i\s+(?:sleep|wake\s+up|uthta|sota)|main\s+(?:sota|uthta))\s+(?:at|ko)\s+(.+?)(?:\.|,|!|$)", "sleep_schedule"),
]

_INTEREST_PATTERNS = [
    # Topics & hobbies
    (r"(?:i\s+am\s+interested\s+in|mujhe\s+interest\s+hai|i\s+am\s+into)\s+(.+?)(?:\.|,|!|$)", "interests"),
    (r"(?:my\s+hobby|mera\s+hobby|mera\s+shauk)\s+(?:is|hai|h)\s+(.+?)(?:\.|,|!|$)", "hobby"),
    (r"(?:i\s+am\s+learning|main\s+seekh\s+raha|me\s+seekh\s+raha)\s+(.+?)(?:\.|,|!|$)", "learning"),
    (r"(?:i\s+am\s+working\s+on|main\s+kaam\s+kr\s+raha|me\s+kaam\s+kr\s+raha)\s+(.+?)(?:\.|,|!|$)", "working_on"),
]

# Emotional state detection keywords (for mood tracking)
_MOOD_KEYWORDS = {
    "happy": ["happy", "khush", "mast", "badhiya", "great", "awesome", "amazing", "wonderful"],
    "sad": ["sad", "dukhi", "upset", "down", "depressed", "low", "bura", "kharab"],
    "angry": ["angry", "gussa", "irritated", "frustrated", "annoyed", "pagal"],
    "tired": ["tired", "thaka", "thak", "exhausted", "sleepy", "neend"],
    "excited": ["excited", "pumped", "hyped", "jaldi", "can't wait"],
    "bored": ["bored", "bore", "boring", "kuch nahi"],
    "stressed": ["stressed", "tension", "pressure", "worried", "pareshan", "preshan"],
}


def auto_learn_from_speech(text: str) -> list:
    """
    Analyze user speech and auto-extract important information.
    Runs silently on every transcription. Returns list of learned items.
    """
    if not text or len(text.strip()) < 4:
        return []

    learned_items = []
    text_lower = text.lower().strip()

    # ─── Extract personal info ───
    for pattern, category in _PERSONAL_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            value = match.groups()[-1].strip().rstrip(".,!?")
            if 2 <= len(value) <= 100:
                learned_items.append({"key": category, "value": value, "category": "personal"})

    # ─── Extract relationships ───
    for pattern, category in _RELATIONSHIP_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            if category == "relationship_reverse" and len(groups) >= 2:
                name = groups[0].strip().rstrip(".,!?")
                relation = groups[1].strip()
                if 2 <= len(name) <= 50:
                    learned_items.append({"key": f"{relation}_name", "value": name, "category": "people"})
            elif len(groups) >= 2:
                relation = groups[0].strip()
                name = groups[1].strip().rstrip(".,!?")
                if 2 <= len(name) <= 50:
                    learned_items.append({"key": f"{relation}_name", "value": name, "category": "people"})

    # ─── Extract preferences ───
    for pattern, category in _PREFERENCE_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            groups = match.groups()
            if category == "favorite" and len(groups) >= 2:
                fav_type = groups[0].strip()
                fav_value = groups[1].strip().rstrip(".,!?")
                if 2 <= len(fav_value) <= 80:
                    learned_items.append({"key": f"favorite_{fav_type}", "value": fav_value, "category": "preference"})
            else:
                value = groups[-1].strip().rstrip(".,!?")
                if 2 <= len(value) <= 80:
                    learned_items.append({"key": category, "value": value, "category": "preference", "append": True})

    # ─── Extract things to remember ───
    for pattern, category in _REMEMBER_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            value = match.groups()[-1].strip().rstrip(".,!?")
            if 2 <= len(value) <= 200:
                learned_items.append({
                    "key": "remembered" if category == "explicit_remember" else "sensitive",
                    "value": value,
                    "category": category,
                    "append": category == "explicit_remember",
                    "sensitive": category == "sensitive",
                })

    # ─── Extract habits ───
    for pattern, category in _HABIT_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            value = match.groups()[-1].strip().rstrip(".,!?")
            if 3 <= len(value) <= 100:
                learned_items.append({"key": category, "value": value, "category": "habit", "append": True})

    # ─── Extract interests ───
    for pattern, category in _INTEREST_PATTERNS:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            value = match.groups()[-1].strip().rstrip(".,!?")
            if 2 <= len(value) <= 80:
                learned_items.append({"key": category, "value": value, "category": "interest", "append": True})

    # ─── Detect mood (non-intrusive, just tracks) ───
    for mood, keywords in _MOOD_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower.split():
                _track_mood(mood)
                break

    # ─── Track conversation topics for interest profiling ───
    _track_topics(text_lower)

    # Save all learned items
    if learned_items:
        _save_learned(learned_items)

    return learned_items


def _track_mood(mood: str):
    """Track user mood over time for emotional awareness."""
    try:
        mem = _load_mem()
        mem.setdefault("mood_history", [])
        entry = {
            "mood": mood,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        mem["mood_history"].append(entry)
        # Keep last 50 mood entries
        if len(mem["mood_history"]) > 50:
            mem["mood_history"] = mem["mood_history"][-50:]

        # Update current mood
        mem["current_mood"] = mood
        _save_mem(mem)
    except:
        pass


def _track_topics(text: str):
    """Track frequently discussed topics to build interest profile."""
    # Common topic keywords to watch for
    TOPIC_KEYWORDS = {
        "coding": ["code", "coding", "programming", "python", "javascript", "api", "debug", "function", "class", "variable"],
        "gaming": ["game", "gaming", "play", "gta", "valorant", "minecraft", "pubg", "fortnite", "fps"],
        "music": ["song", "music", "gaana", "play", "spotify", "artist", "singer"],
        "studies": ["exam", "study", "padhai", "paper", "assignment", "homework", "class", "college", "school"],
        "movies": ["movie", "film", "series", "show", "netflix", "watch", "dekh"],
        "social_media": ["instagram", "twitter", "whatsapp", "telegram", "youtube", "reels", "story"],
        "ai": ["ai", "artificial", "machine learning", "gpt", "model", "gemini", "chatgpt", "agent"],
        "fitness": ["gym", "workout", "exercise", "run", "yoga", "diet", "health"],
    }

    try:
        mem = _load_mem()
        mem.setdefault("topic_frequency", {})

        words = set(text.lower().split())
        for topic, keywords in TOPIC_KEYWORDS.items():
            if words.intersection(keywords):
                mem["topic_frequency"][topic] = mem["topic_frequency"].get(topic, 0) + 1

        _save_mem(mem)
    except:
        pass


def get_user_profile() -> str:
    """Build a comprehensive user profile from all learned data."""
    try:
        mem = _load_mem()
        parts = []

        # Top interests from topic tracking
        topics = mem.get("topic_frequency", {})
        if topics:
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]
            top = [f"{t[0]} ({t[1]}x)" for t in sorted_topics]
            parts.append(f"Top interests: {', '.join(top)}")

        # Current mood
        mood = mem.get("current_mood")
        if mood:
            parts.append(f"Current mood: {mood}")

        # Mood trends
        mood_hist = mem.get("mood_history", [])
        if len(mood_hist) >= 3:
            recent_moods = [m["mood"] for m in mood_hist[-5:]]
            from collections import Counter
            common = Counter(recent_moods).most_common(1)[0]
            parts.append(f"Usual mood lately: {common[0]}")

        return " | ".join(parts) if parts else ""
    except:
        return ""


def _save_learned(items: list):
    """Save auto-learned items to memory.json."""
    try:
        mem = _load_mem()
        mem.setdefault("learned", [])
        mem.setdefault("facts", {})

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for item in items:
            key = item["key"]
            value = item["value"]

            # For append-type items (likes, dislikes, habits, interests)
            if item.get("append"):
                existing = mem["facts"].get(key, "")
                if existing:
                    # Don't add duplicates
                    if value.lower() not in existing.lower():
                        mem["facts"][key] = f"{existing}, {value}"
                else:
                    mem["facts"][key] = value
            else:
                mem["facts"][key] = value

            # Log in learned list with metadata
            log_entry = {
                "what": f"{key}: {value}",
                "category": item.get("category", "unknown"),
                "learned_at": now,
            }
            # Deduplicate
            recent_whats = [l.get("what", "") for l in mem["learned"][-50:]]
            if log_entry["what"] not in recent_whats:
                mem["learned"].append(log_entry)

        # Keep learned log manageable
        if len(mem["learned"]) > 300:
            mem["learned"] = mem["learned"][-300:]

        _save_mem(mem)
    except:
        pass


def get_learned_summary() -> str:
    """Get a summary of everything Jessica has learned about the user."""
    try:
        mem = _load_mem()
        learned = mem.get("learned", [])
        if not learned:
            return "I haven't learned anything specific yet, Sir."

        lines = []
        for item in learned[-15:]:
            cat_emoji = {
                "personal": "👤", "people": "👥", "preference": "❤️",
                "explicit_remember": "📌", "sensitive": "🔐",
                "habit": "🔄", "interest": "🎯", "unknown": "💡"
            }.get(item.get("category", ""), "💡")
            lines.append(f"  {cat_emoji} {item['what']} ({item.get('learned_at', '?')})")

        return "Here's what I've learned about you:\n" + "\n".join(lines)
    except:
        return "Couldn't read learning data."


# ══════════════════════════════════════════
# 🔧 Internal helpers
# ══════════════════════════════════════════

def _load_mem():
    """Load memory from disk."""
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"facts": {}, "learned": [], "usage_log": [], "command_frequency": {}, "time_patterns": {}}


def _save_mem(mem):
    """Save memory to disk."""
    try:
        mem["owner"] = "Abhiyank"
        mem["owner_protected"] = True
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
    except:
        pass
