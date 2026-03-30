# livekit_tools.py — Ank Tools for LiveKit Agents
# All tools adapted for LiveKit's @function_tool decorator
# Uses docstrings for parameter descriptions (parsed by docstring_parser)
# Owner: Abhiyank

import os
import sys
import time
import datetime
import webbrowser
import subprocess
import json
import shutil
from livekit.agents import llm

# Add the project root to path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pyautogui
import psutil

pyautogui.FAILSAFE = False

# ══════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════
WEBSITE_MAP = {
    "instagram": "https://www.instagram.com/",
    "whatsapp": "https://web.whatsapp.com/",
    "facebook": "https://www.facebook.com/",
    "github": "https://github.com/",
    "youtube": "https://www.youtube.com/",
    "google": "https://www.google.com/",
    "twitter": "https://www.x.com/",
    "x": "https://www.x.com/",
    "spotify": "https://open.spotify.com/",
    "gmail": "https://mail.google.com/",
    "snapchat": "https://www.snapchat.com/",
    "zoom": "https://zoom.us/",
    "reddit": "https://www.reddit.com/",
    "linkedin": "https://www.linkedin.com/",
    "chatgpt": "https://chat.openai.com/",
    "amazon": "https://www.amazon.in/",
    "netflix": "https://www.netflix.com/",
}

FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx", ".csv"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".json", ".xml", ".bat", ".sh", ".sql"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Executables": [".exe", ".msi", ".apk"],
}


# ══════════════════════════════════════════
# 🟢 SYSTEM CONTROL
# ══════════════════════════════════════════

@llm.function_tool(description="Toggle your own sleep/mute mode. If the user tells you to sleep, call this tool and then act as if asleep.")
async def toggle_sleep() -> str:
    """Toggle the agent's sleep state."""
    state_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
    current = False
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                current = json.load(f).get("is_sleeping", False)
        except Exception: pass
    
    new_state = not current
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"is_sleeping": new_state}, f)
        return f"Sleep state toggled to {new_state}."
    except Exception as e:
        return f"Failed to toggle sleep mode: {e}"

@llm.function_tool(description="Shutdown the computer immediately. You MUST explicitly ask the user the security question 'What is your best AI agent's name?' before calling this tool. DO NOT guess the answer yourself.")
async def shutdown(answer: str) -> str:
    """Shutdown the computer. Requires security answer.
    
    Args:
        answer: The answer to the security question provided by the user.
    """
    if "jessica" not in answer.lower():
        return "Incorrect answer. Tell the user the answer was wrong and do not shutdown."
        
    os.system("shutdown /s /t 1")
    return "Answer correct. Shutting down, Sir."

@llm.function_tool(description="Restart the computer immediately. You MUST explicitly ask the user the security question 'What is your best AI agent's name?' before calling this tool. DO NOT guess the answer yourself.")
async def restart(answer: str) -> str:
    """Restart the computer. Requires security answer.
    
    Args:
        answer: The answer to the security question provided by the user.
    """
    if "jessica" not in answer.lower():
        return "Incorrect answer. Tell the user the answer was wrong and do not restart."
        
    os.system("shutdown /r /t 1")
    return "Answer correct. Restarting, Sir."

@llm.function_tool(description="Lock the screen")
async def lock_screen() -> str:
    """Lock the Windows screen."""
    pyautogui.hotkey('win', 'l')
    return "Screen locked, Sir."

@llm.function_tool(description="Put the computer to sleep mode")
async def sleep_mode() -> str:
    """Put the computer to sleep."""
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "Going to sleep, Sir."

@llm.function_tool(description="Open Windows Task Manager")
async def open_task_manager() -> str:
    """Open Task Manager."""
    subprocess.Popen("taskmgr", shell=True)
    return "Task Manager opened."

@llm.function_tool(description="Open Windows Control Panel")
async def open_control_panel() -> str:
    """Open Control Panel."""
    subprocess.Popen("control", shell=True)
    return "Control Panel opened."

@llm.function_tool(description="Open Windows Settings")
async def open_settings() -> str:
    """Open Windows Settings."""
    pyautogui.hotkey('win', 'i')
    return "Settings opened."

@llm.function_tool(description="Open Command Prompt terminal")
async def open_cmd() -> str:
    """Open Command Prompt."""
    subprocess.Popen("cmd", creationflags=subprocess.CREATE_NEW_CONSOLE)
    return "Command Prompt opened."

@llm.function_tool(description="Open PowerShell terminal")
async def open_powershell() -> str:
    """Open PowerShell."""
    subprocess.Popen("powershell", creationflags=subprocess.CREATE_NEW_CONSOLE)
    return "PowerShell opened."

@llm.function_tool(description="Open Windows File Explorer")
async def open_file_explorer() -> str:
    """Open File Explorer."""
    pyautogui.hotkey('win', 'e')
    return "File Explorer opened."

@llm.function_tool(description="Get system info: CPU, RAM, disk, and battery status")
async def system_info() -> str:
    """Get system information including CPU, RAM, disk, and battery."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    info = f"CPU: {cpu}%, RAM: {ram.percent}% ({ram.used // (1024**3)}/{ram.total // (1024**3)} GB), Disk: {disk.percent}% used"
    try:
        batt = psutil.sensors_battery()
        if batt:
            plug = "plugged in" if batt.power_plugged else "on battery"
            info += f", Battery: {batt.percent}% ({plug})"
    except: pass
    return info

@llm.function_tool(description="Clean Windows temporary files to free space")
async def clean_temp() -> str:
    """Clean temporary files."""
    temp_dir = os.environ.get("TEMP", "")
    count = 0
    for item in os.listdir(temp_dir):
        try:
            path = os.path.join(temp_dir, item)
            if os.path.isfile(path): os.remove(path); count += 1
            elif os.path.isdir(path): shutil.rmtree(path, ignore_errors=True); count += 1
        except: pass
    return f"Cleaned {count} temp items, Sir."

@llm.function_tool(description="Close all running user apps like browsers and editors")
async def close_all_apps() -> str:
    """Close all common user applications."""
    apps = ["chrome.exe", "msedge.exe", "firefox.exe", "notepad.exe", "Code.exe", "spotify.exe", "discord.exe"]
    closed = 0
    for app in apps:
        try:
            r = subprocess.run(f'taskkill /IM "{app}" /F', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if "SUCCESS" in r.stdout: closed += 1
        except: pass
    return f"Closed {closed} apps, Sir."

@llm.function_tool(description="Minimize all windows and show desktop")
async def minimize_all() -> str:
    """Minimize all windows."""
    pyautogui.hotkey('win', 'd')
    return "Minimized all windows."

@llm.function_tool(description="Maximize the current window")
async def maximize_window() -> str:
    """Maximize current window."""
    pyautogui.hotkey('win', 'up')
    return "Window maximized."

@llm.function_tool(description="Minimize the current window")
async def minimize_window() -> str:
    """Minimize current window."""
    pyautogui.hotkey('win', 'down')
    return "Window minimized."

@llm.function_tool(description="Empty the Windows recycle bin")
async def empty_recycle_bin() -> str:
    """Empty recycle bin."""
    subprocess.run(["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
                   timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
    return "Recycle bin emptied, Sir."

@llm.function_tool(description="Get disk space on all drives")
async def disk_space() -> str:
    """Get disk space info."""
    parts = psutil.disk_partitions()
    info = []
    for p in parts:
        try:
            u = psutil.disk_usage(p.mountpoint)
            info.append(f"{p.device} {u.free/(1024**3):.1f}GB free of {u.total/(1024**3):.1f}GB")
        except: pass
    return "Disk space: " + ", ".join(info)

@llm.function_tool(description="Get battery charge level and time remaining")
async def battery_status() -> str:
    """Get battery status."""
    batt = psutil.sensors_battery()
    if batt:
        plug = "plugged in" if batt.power_plugged else "on battery"
        mins = batt.secsleft // 60 if batt.secsleft > 0 else 0
        t = f", about {mins} minutes remaining" if mins > 0 and not batt.power_plugged else ""
        return f"Battery at {batt.percent}%, {plug}{t}."
    return "No battery detected."

@llm.function_tool(description="Get how long the system has been running")
async def uptime() -> str:
    """Get system uptime."""
    boot = datetime.datetime.fromtimestamp(psutil.boot_time())
    up = datetime.datetime.now() - boot
    hours, rem = divmod(int(up.total_seconds()), 3600)
    minutes = rem // 60
    return f"System running for {hours}h {minutes}m since {boot.strftime('%I:%M %p')}."

@llm.function_tool(description="List top processes by memory usage")
async def running_processes() -> str:
    """List top running processes."""
    procs = []
    for proc in psutil.process_iter(['name', 'memory_percent']):
        try: procs.append((proc.info['name'], proc.info['memory_percent']))
        except: pass
    procs.sort(key=lambda x: x[1], reverse=True)
    lines = [f"{n}: {m:.1f}%" for n, m in procs[:8]]
    return "Top processes: " + ", ".join(lines)


# ══════════════════════════════════════════
# 🔊 VOLUME & DISPLAY
# ══════════════════════════════════════════

@llm.function_tool(description="Increase system volume by N steps. 1 step = 2% (default 5 steps = 10%)")
async def volume_up(times: int = 5) -> str:
    """Increase volume.

    Args:
        times: Number of volume steps to increase
    """
    for _ in range(times): pyautogui.press('volumeup')
    return f"Volume up {times} steps."

@llm.function_tool(description="Decrease system volume by N steps. 1 step = 2% (default 5 steps = 10%)")
async def volume_down(times: int = 5) -> str:
    """Decrease volume.

    Args:
        times: Number of volume steps to decrease
    """
    for _ in range(times): pyautogui.press('volumedown')
    return f"Volume down {times} steps."

@llm.function_tool(description="Set system volume to a specific percentage (0 to 100). Use for 'full volume' (100) or specific levels.")
async def set_volume(level: int) -> str:
    """Set system volume level to a specific percentage.

    Args:
        level: Percentage to set the volume to, from 0 to 100
    """
    level = max(0, min(100, level))
    # Reset volume to 0 first (50 steps handles any volume since 50*2=100)
    for _ in range(50): pyautogui.press('volumedown')
    # Set to target level
    steps = level // 2
    for _ in range(steps): pyautogui.press('volumeup')
    return f"Volume set to {level}%."

@llm.function_tool(description="Toggle mute/unmute system volume")
async def volume_mute() -> str:
    """Toggle mute."""
    pyautogui.press('volumemute')
    return "Mute toggled."

@llm.function_tool(description="Set screen brightness from 0 to 100")
async def brightness(level: int = 50) -> str:
    """Set brightness.

    Args:
        level: Brightness level from 0 to 100
    """
    level = max(0, min(100, level))
    subprocess.run(["powershell", "-NoProfile", "-Command",
        f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"],
        timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
    return f"Brightness set to {level}%."


# ══════════════════════════════════════════
# 🌐 WEB & BROWSER
# ══════════════════════════════════════════

@llm.function_tool(description="Open a website by name like youtube, github, instagram, or a URL")
async def open_website(app_name: str) -> str:
    """Open a website.

    Args:
        app_name: Website name (youtube, github, etc.) or full URL
    """
    name = app_name.lower().strip()
    url = WEBSITE_MAP.get(name)
    if url: webbrowser.open(url)
    elif name.startswith("http"): webbrowser.open(name)
    else: webbrowser.open(f"https://www.{name}.com/")
    return f"Opening {app_name}."

@llm.function_tool(description="Search Google for something")
async def google_search(query: str) -> str:
    """Search Google.

    Args:
        query: The search query
    """
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Searching: {query}"

@llm.function_tool(description="Search and play something on YouTube. It will find the top result and auto-play it.")
async def youtube_search(query: str) -> str:
    """Search and play on YouTube.

    Args:
        query: Song, video, or topic to play
    """
    try:
        import urllib.request
        import urllib.parse
        import re
        # Search YouTube and find the first video ID
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = urllib.request.urlopen(search_url).read().decode('utf-8')
        # Find the first video ID in the search results
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
        if video_ids:
            webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}")
            return f"Playing '{query}' on YouTube."
        else:
            webbrowser.open(search_url)
            return f"Showing search results for '{query}' on YouTube."
    except Exception:
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"Showing search results for '{query}' on YouTube."

@llm.function_tool(description="Open multiple websites at once, comma separated")
async def open_multiple_tabs(sites: str) -> str:
    """Open multiple websites.

    Args:
        sites: Comma-separated site names like 'youtube,github,gmail'
    """
    for site in [s.strip().lower() for s in sites.split(",")]:
        url = WEBSITE_MAP.get(site)
        if url: webbrowser.open(url)
        elif site.startswith("http"): webbrowser.open(site)
        else: webbrowser.open(f"https://www.{site}.com/")
        time.sleep(0.3)
    return "Tabs opened."

@llm.function_tool(description="Switch to the next window")
async def switch_tab() -> str:
    """Switch window."""
    pyautogui.hotkey('alt', 'esc')
    return "Switched."

@llm.function_tool(description="Close the current window")
async def close_tab() -> str:
    """Close current window."""
    pyautogui.hotkey('alt', 'f4')
    return "Closed."

@llm.function_tool(description="Open a new browser tab")
async def new_tab() -> str:
    """Open new tab."""
    pyautogui.hotkey('ctrl', 't')
    return "New tab opened."

@llm.function_tool(description="Open incognito/private browser window")
async def incognito() -> str:
    """Open incognito."""
    pyautogui.hotkey('ctrl', 'shift', 'n')
    return "Incognito opened."

@llm.function_tool(description="Refresh the current browser page")
async def refresh_page() -> str:
    """Refresh page."""
    pyautogui.hotkey('f5')
    return "Page refreshed."

@llm.function_tool(description="Scroll up on screen")
async def scroll_up(times: int = 5) -> str:
    """Scroll up.

    Args:
        times: Number of scroll steps
    """
    pyautogui.scroll(times)
    return "Scrolled up."

@llm.function_tool(description="Scroll down on screen")
async def scroll_down(times: int = 5) -> str:
    """Scroll down.

    Args:
        times: Number of scroll steps
    """
    pyautogui.scroll(-times)
    return "Scrolled down."

@llm.function_tool(description="Search Wikipedia for information about a topic")
async def wikipedia_search(query: str) -> str:
    """Search Wikipedia.

    Args:
        query: Topic to look up
    """
    try:
        import wikipedia; return wikipedia.summary(query, sentences=2)
    except: return "Couldn't find that on Wikipedia."

@llm.function_tool(description="Paste from clipboard and press Enter")
async def paste_clipboard() -> str:
    """Paste clipboard."""
    pyautogui.hotkey('ctrl', 'v'); pyautogui.press('enter')
    return "Pasted."

@llm.function_tool(description="Copy selected text to clipboard")
async def copy_clipboard() -> str:
    """Copy to clipboard."""
    pyautogui.hotkey('ctrl', 'c')
    return "Copied."


# ══════════════════════════════════════════
# ⌨️ INPUT AUTOMATION
# ══════════════════════════════════════════

@llm.function_tool(description="Type text using the keyboard")
async def type_text(text: str) -> str:
    """Type text.

    Args:
        text: The text to type
    """
    pyautogui.write(text, interval=0.02)
    return f"Typed: {text[:50]}"

@llm.function_tool(description="Press a keyboard key like enter, escape, tab, space")
async def press_key(key: str) -> str:
    """Press a key.

    Args:
        key: Key to press like enter, escape, tab, space
    """
    pyautogui.press(key)
    return f"Pressed {key}"

@llm.function_tool(description="Press a keyboard shortcut like ctrl+c, alt+tab")
async def hotkey(keys: str) -> str:
    """Press a hotkey combination.

    Args:
        keys: Keys separated by + like ctrl+c, alt+tab
    """
    pyautogui.hotkey(*[k.strip() for k in keys.split("+")])
    return f"Pressed {keys}"

@llm.function_tool(description="Select all content (Ctrl+A)")
async def select_all() -> str:
    """Select all."""
    pyautogui.hotkey('ctrl', 'a')
    return "Selected all."

@llm.function_tool(description="Undo last action (Ctrl+Z)")
async def undo() -> str:
    """Undo."""
    pyautogui.hotkey('ctrl', 'z')
    return "Undone."

@llm.function_tool(description="Redo last action (Ctrl+Y)")
async def redo() -> str:
    """Redo."""
    pyautogui.hotkey('ctrl', 'y')
    return "Redone."


# ══════════════════════════════════════════
# 📱 PHONE CONTROL (ADB)
# ══════════════════════════════════════════

@llm.function_tool(description="Connect to phone via ADB")
async def connect_phone() -> str:
    """Connect to phone."""
    os.system("adb connect 192.168.29.193:5555")
    return "Connecting to phone."

@llm.function_tool(description="Press phone home button via ADB")
async def phone_home_button() -> str:
    """Press phone home button."""
    os.system("adb shell input keyevent 3")
    return "Home pressed."

@llm.function_tool(description="Increase phone volume via ADB")
async def phone_volume_up() -> str:
    """Phone volume up."""
    os.system("adb shell input keyevent 24")
    return "Phone volume up."

@llm.function_tool(description="Decrease phone volume via ADB")
async def phone_volume_down() -> str:
    """Phone volume down."""
    os.system("adb shell input keyevent 25")
    return "Phone volume down."

@llm.function_tool(description="Take a phone screenshot via ADB")
async def phone_screenshot() -> str:
    """Take phone screenshot."""
    os.system("adb shell screencap -p /sdcard/screenshot.png")
    os.system('adb pull /sdcard/screenshot.png "screenshot.png"')
    return "Phone screenshot taken."


# ══════════════════════════════════════════
# 📸 VISION & SCREEN
# ══════════════════════════════════════════

@llm.function_tool(description="Take a photo using the webcam")
async def take_photo() -> str:
    """Take a webcam photo."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret: cv2.imwrite("photo.jpg", frame)
        cap.release()
        return "Photo saved as photo.jpg"
    except Exception as e: return f"Camera error: {e}"

@llm.function_tool(description="Take a screenshot of the computer screen")
async def take_screenshot() -> str:
    """Take a screenshot."""
    shot = pyautogui.screenshot()
    shot.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot.png"))
    return "Screenshot saved."

@llm.function_tool(description="Take a screenshot and analyze what's on screen using AI vision")
async def read_screen(query: str = "What is on this screen?") -> str:
    """Read and analyze the screen using Gemini Vision.

    Args:
        query: What to look for or analyze on the screen
    """
    try:
        import google.generativeai as genai
        from PIL import Image
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screen_capture.png")
        pyautogui.screenshot(path)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash')
        img = Image.open(path)
        resp = model.generate_content([f"You are Ank, analyzing a screenshot. TASK: {query}. Be concise. Address user as Sir.", img])
        return f"Screen Analysis: {resp.text}"
    except Exception as e: return f"Vision Error: {e}"

@llm.function_tool(description="Take a screenshot and deeply analyze for errors or bugs")
async def analyze_screen(query: str = "Find any errors on screen.") -> str:
    """Deep analysis of screen for errors.

    Args:
        query: What to analyze or look for
    """
    try:
        import google.generativeai as genai
        from PIL import Image
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "error_check.png")
        pyautogui.screenshot(path)
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-2.0-flash')
        img = Image.open(path)
        resp = model.generate_content([f"You are Ank, expert technician. TASK: {query}. Cover errors, diagnosis, fix commands. Concise. Address Sir.", img])
        return f"Technical Analysis: {resp.text}"
    except Exception as e: return f"Vision Error: {e}"


# ══════════════════════════════════════════
# 📅 PRODUCTIVITY
# ══════════════════════════════════════════

@llm.function_tool(description="Tell the current time")
async def tell_time() -> str:
    """Get current time."""
    return datetime.datetime.now().strftime("%I:%M %p")

@llm.function_tool(description="Tell the current date")
async def tell_date() -> str:
    """Get current date."""
    return datetime.datetime.now().strftime("%A, %B %d, %Y")

@llm.function_tool(description="Set a timer for N minutes that alerts when done")
async def set_timer(minutes: int = 1) -> str:
    """Set a countdown timer.

    Args:
        minutes: Number of minutes for the timer
    """
    subprocess.Popen(
        f'powershell -NoProfile -Command "Start-Sleep -Seconds {minutes*60}; '
        f'Add-Type -AssemblyName System.Speech; '
        f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.Speak('Timer complete! {minutes} minutes are up, Sir.'); $s.Dispose()\"",
        shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return f"Timer set for {minutes} minutes."

@llm.function_tool(description="Get a current timestamp for stopwatch tracking")
async def stopwatch() -> str:
    """Get stopwatch timestamp."""
    return f"Time mark: {datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}"

@llm.function_tool(description="Calculate a math expression like 2+2 or 100/4")
async def calculator(expression: str) -> str:
    """Do a calculation.

    Args:
        expression: Math expression like 2+2, 100/4, 15*3
    """
    allowed = set("0123456789+-*/().% ")
    if all(c in allowed for c in expression):
        return f"{expression} = {eval(expression)}"
    return "Invalid expression."

@llm.function_tool(description="Open weather info for a city in browser")
async def weather(city: str = "") -> str:
    """Get weather.

    Args:
        city: City name to get weather for
    """
    webbrowser.open(f"https://www.google.com/search?q=weather+{city}" if city else "https://www.google.com/search?q=weather+today")
    return "Opening weather."

@llm.function_tool(description="Open Google Translate for text translation")
async def translate(text: str, language: str = "en") -> str:
    """Translate text.

    Args:
        text: Text to translate
        language: Target language code like hi, es, fr
    """
    import urllib.parse
    webbrowser.open(f"https://translate.google.com/?sl=auto&tl={language}&text={urllib.parse.quote(text)}")
    return "Opening translation."


# ══════════════════════════════════════════
# 📂 FILE MANAGEMENT
# ══════════════════════════════════════════

@llm.function_tool(description="Search for files by name in Desktop, Documents, Downloads")
async def search_files(query: str) -> str:
    """Search files.

    Args:
        query: Filename or part of filename to search
    """
    user_dir = os.path.expanduser("~")
    found = []
    for d in ["Desktop", "Documents", "Downloads"]:
        sd = os.path.join(user_dir, d)
        if not os.path.exists(sd): continue
        for root, dirs, files in os.walk(sd):
            dirs[:] = [x for x in dirs if not x.startswith('.')]
            for f in files:
                if query.lower() in f.lower():
                    found.append(f)
                    if len(found) >= 10: break
            if len(found) >= 10: break
    return f"Found: {', '.join(found[:5])}" if found else f"No files matching '{query}'."

@llm.function_tool(description="Open a file with its default application")
async def open_file(filename: str) -> str:
    """Open a file.

    Args:
        filename: Filename or full path to open
    """
    if os.path.exists(filename):
        os.startfile(filename); return f"Opened {os.path.basename(filename)}"
    for d in ["Desktop", "Documents", "Downloads"]:
        sd = os.path.join(os.path.expanduser("~"), d)
        if not os.path.exists(sd): continue
        for root, dirs, files in os.walk(sd):
            for f in files:
                if filename.lower() in f.lower():
                    os.startfile(os.path.join(root, f)); return f"Opened {f}"
    return f"Couldn't find '{filename}'"

@llm.function_tool(description="Organize files in a folder into categorized subfolders")
async def organize_files(folder: str = "") -> str:
    """Organize files into categories.

    Args:
        folder: Folder path to organize, defaults to Downloads
    """
    if not folder: folder = os.path.join(os.path.expanduser("~"), "Downloads")
    if not os.path.exists(folder): return "Folder not found."
    moved = 0
    for f in os.listdir(folder):
        fp = os.path.join(folder, f)
        if os.path.isdir(fp): continue
        ext = os.path.splitext(f)[1].lower()
        cat = "Others"
        for c, exts in FILE_CATEGORIES.items():
            if ext in exts: cat = c; break
        os.makedirs(os.path.join(folder, cat), exist_ok=True)
        try: shutil.move(fp, os.path.join(folder, cat, f)); moved += 1
        except: pass
    return f"Organized {moved} files."

@llm.function_tool(description="List files in a folder")
async def list_files(folder: str = "") -> str:
    """List folder contents.

    Args:
        folder: Folder path, defaults to Desktop
    """
    if not folder: folder = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(folder): return "Folder not found."
    items = os.listdir(folder)[:20]
    return f"{os.path.basename(folder)}: " + ", ".join(items)

@llm.function_tool(description="Create a new folder")
async def create_folder(name: str, location: str = "") -> str:
    """Create folder.

    Args:
        name: Folder name
        location: Parent path, defaults to Desktop
    """
    if not location: location = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(os.path.join(location, name), exist_ok=True)
    return f"Created folder: {name}"

@llm.function_tool(description="Get file info — size, type, modified date")
async def file_info(filename: str) -> str:
    """Get file information.

    Args:
        filename: Filename to get info about
    """
    path = filename if os.path.exists(filename) else None
    if not path:
        for d in ["Desktop", "Documents", "Downloads"]:
            sd = os.path.join(os.path.expanduser("~"), d)
            if not os.path.exists(sd): continue
            for root, dirs, files in os.walk(sd):
                for f in files:
                    if filename.lower() in f.lower():
                        path = os.path.join(root, f); break
                if path: break
            if path: break
    if not path: return f"File '{filename}' not found."
    s = os.stat(path)
    return f"{os.path.basename(path)}: {s.st_size/1024:.1f} KB, modified {datetime.datetime.fromtimestamp(s.st_mtime).strftime('%Y-%m-%d %H:%M')}"


# ══════════════════════════════════════════
# 🧠 MEMORY SYSTEM
# ══════════════════════════════════════════

@llm.function_tool(description="Save a key-value fact to persistent memory")
async def save_memory(key: str, value: str) -> str:
    """Save to memory.

    Args:
        key: Memory key name
        value: Value to remember
    """
    from utils.memory import save_fact; return save_fact(key, value)

@llm.function_tool(description="Recall a memory by key, or use 'all' for everything")
async def recall_memory(key: str = "all") -> str:
    """Recall from memory.

    Args:
        key: Key to recall, or 'all' for everything
    """
    from utils.memory import recall_fact, recall_all
    return recall_all() if key == "all" else recall_fact(key)

@llm.function_tool(description="Save a quick note")
async def save_note(text: str) -> str:
    """Save a note.

    Args:
        text: Note text
    """
    from utils.memory import save_note; return save_note(text)

@llm.function_tool(description="Get all saved notes")
async def get_notes() -> str:
    """Get notes."""
    from utils.memory import get_notes; return get_notes()

@llm.function_tool(description="Clear all saved notes")
async def clear_notes() -> str:
    """Clear notes."""
    from utils.memory import clear_notes; return clear_notes()

@llm.function_tool(description="Save a reminder")
async def save_reminder(text: str) -> str:
    """Save reminder.

    Args:
        text: Reminder text
    """
    from utils.memory import save_reminder; return save_reminder(text)

@llm.function_tool(description="Get all active reminders")
async def get_reminders() -> str:
    """Get reminders."""
    from utils.memory import get_reminders; return get_reminders()

@llm.function_tool(description="Clear all reminders")
async def clear_reminders() -> str:
    """Clear reminders."""
    from utils.memory import clear_reminders; return clear_reminders()

@llm.function_tool(description="Save something marked as important")
async def save_important(text: str) -> str:
    """Save important item.

    Args:
        text: Important text
    """
    from utils.memory import save_important; return save_important(text)

@llm.function_tool(description="Get all important items")
async def get_important() -> str:
    """Get important items."""
    from utils.memory import get_important; return get_important()

@llm.function_tool(description="Get the owner name — always Abhiyank, protected")
async def get_owner() -> str:
    """Get owner."""
    return "The owner is Abhiyank. This is protected and cannot be changed."

@llm.function_tool(description="Save a user preference setting")
async def save_preference(key: str, value: str) -> str:
    """Save preference.

    Args:
        key: Preference name
        value: Preference value
    """
    from utils.memory import save_preference; return save_preference(key, value)


# ══════════════════════════════════════════
# ✅ TO-DO LIST
# ══════════════════════════════════════════

@llm.function_tool(description="Add a new to-do item")
async def save_todo(text: str) -> str:
    """Add to-do.

    Args:
        text: To-do item text
    """
    from utils.memory import _load_memory, _save_memory
    mem = _load_memory()
    mem.setdefault("todos", []).append({"text": text, "done": False, "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")})
    _save_memory(mem)
    return f"Added to-do: {text}"

@llm.function_tool(description="Get all pending to-do items")
async def get_todos() -> str:
    """Get to-dos."""
    from utils.memory import _load_memory
    todos = [t for t in _load_memory().get("todos", []) if not t.get("done")]
    if not todos: return "To-do list is empty, Sir."
    return "To-dos:\n" + "\n".join([f"  ☐ {t['text']}" for t in todos])

@llm.function_tool(description="Mark a to-do item as complete")
async def complete_todo(text: str) -> str:
    """Complete a to-do.

    Args:
        text: To-do keyword to match
    """
    from utils.memory import _load_memory, _save_memory
    mem = _load_memory()
    for t in mem.get("todos", []):
        if text.lower() in t["text"].lower() and not t.get("done"):
            t["done"] = True; _save_memory(mem); return f"Completed: {t['text']}"
    return "No matching to-do found."

@llm.function_tool(description="Clear all to-do items")
async def clear_todos() -> str:
    """Clear to-dos."""
    from utils.memory import _load_memory, _save_memory
    mem = _load_memory(); mem["todos"] = []; _save_memory(mem)
    return "To-do list cleared."


# ══════════════════════════════════════════
# 💻 DEVELOPER MODE
# ══════════════════════════════════════════

@llm.function_tool(description="Run a terminal/shell command and return output")
async def run_command(command: str) -> str:
    """Run a shell command.

    Args:
        command: The command to run
    """
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
        out = r.stdout.strip() or r.stderr.strip()
        return out[:300] if out else "Command executed."
    except subprocess.TimeoutExpired: return "Timed out."
    except Exception as e: return f"Error: {e}"

@llm.function_tool(description="Open any Windows application by name")
async def open_app(app_name: str) -> str:
    """Open an application.

    Args:
        app_name: Application name like notepad, chrome, vscode
    """
    try: subprocess.Popen(f'start "" "{app_name}"', shell=True); return f"Opening {app_name}"
    except: pass
    pyautogui.hotkey('win'); time.sleep(0.5)
    pyautogui.write(app_name, interval=0.03); time.sleep(0.8)
    pyautogui.press('enter')
    return f"Searching and opening {app_name}"

@llm.function_tool(description="Close an application by name")
async def close_app(app_name: str) -> str:
    """Close an application.

    Args:
        app_name: Application name to close
    """
    r = subprocess.run(f'taskkill /IM "{app_name}.exe" /F', shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return f"Closed {app_name}." if "SUCCESS" in r.stdout else f"Attempted to close {app_name}."

@llm.function_tool(description="Install a Python pip package")
async def install_package(package: str) -> str:
    """Install pip package.

    Args:
        package: Package name to install
    """
    r = subprocess.run(f"pip install {package}", shell=True, capture_output=True, text=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
    if "Successfully installed" in r.stdout: return f"Installed {package}."
    if "already satisfied" in r.stdout: return f"{package} already installed."
    return r.stdout[:200] or r.stderr[:200]

@llm.function_tool(description="Clone a GitHub repository to Desktop")
async def clone_repo(repo: str) -> str:
    """Clone a GitHub repo.

    Args:
        repo: GitHub repo URL or user/repo format
    """
    if not repo.startswith("http"): repo = f"https://github.com/{repo}.git"
    dest = os.path.join(os.path.expanduser("~"), "Desktop")
    r = subprocess.run(f'git clone {repo}', shell=True, capture_output=True, text=True, timeout=60, cwd=dest, creationflags=subprocess.CREATE_NO_WINDOW)
    return "Cloned to Desktop." if r.returncode == 0 else r.stderr[:200]

@llm.function_tool(description="Create a new project with boilerplate code")
async def create_project(project_type: str = "python", name: str = "my_project") -> str:
    """Create a project boilerplate.

    Args:
        project_type: Type - 'python' or 'web'
        name: Project name
    """
    base = os.path.join(os.path.expanduser("~"), "Desktop", name)
    os.makedirs(base, exist_ok=True)
    if "python" in project_type.lower():
        with open(os.path.join(base, "main.py"), "w") as f:
            f.write(f'def main():\n    print("Hello from {name}!")\n\nif __name__ == "__main__":\n    main()\n')
        return f"Python project '{name}' created on Desktop."
    elif "web" in project_type.lower():
        with open(os.path.join(base, "index.html"), "w") as f:
            f.write(f'<!DOCTYPE html><html><head><title>{name}</title></head><body><h1>{name}</h1></body></html>')
        return f"Web project '{name}' created on Desktop."
    return f"Unknown type '{project_type}'."


# ══════════════════════════════════════════
# 🎵 MEDIA CONTROL
# ══════════════════════════════════════════

@llm.function_tool(description="Toggle play/pause for media")
async def play_pause() -> str:
    """Play/pause media."""
    pyautogui.hotkey('playpause')
    return "Play/pause toggled."

@llm.function_tool(description="Skip to next track")
async def next_track() -> str:
    """Next track."""
    pyautogui.hotkey('nexttrack')
    return "Next track."

@llm.function_tool(description="Go to previous track")
async def previous_track() -> str:
    """Previous track."""
    pyautogui.hotkey('prevtrack')
    return "Previous track."


# ══════════════════════════════════════════
# 🔄 SMART AUTOMATION MODES
# ══════════════════════════════════════════

@llm.function_tool(description="Activate work mode — opens Gmail, GitHub, VS Code")
async def work_mode() -> str:
    """Start work mode."""
    webbrowser.open("https://mail.google.com/"); time.sleep(0.5)
    webbrowser.open("https://github.com/"); time.sleep(0.5)
    try: subprocess.Popen('code', shell=True)
    except: pass
    return "Work mode activated."

@llm.function_tool(description="Activate study mode — opens YouTube, Docs, Google")
async def study_mode() -> str:
    """Start study mode."""
    for url in ["https://www.youtube.com/", "https://docs.google.com/", "https://www.google.com/"]:
        webbrowser.open(url); time.sleep(0.5)
    return "Study mode activated."

@llm.function_tool(description="Activate chill mode — opens Spotify and YouTube")
async def chill_mode() -> str:
    """Start chill mode."""
    webbrowser.open("https://open.spotify.com/"); time.sleep(0.5)
    webbrowser.open("https://www.youtube.com/")
    return "Chill mode activated."

@llm.function_tool(description="Activate gaming mode — closes heavy apps for performance")
async def gaming_mode() -> str:
    """Start gaming mode."""
    for app in ["chrome.exe", "msedge.exe", "Teams.exe", "Slack.exe", "discord.exe"]:
        try: subprocess.run(f'taskkill /IM "{app}" /F', shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass
    return "Gaming mode activated!"

@llm.function_tool(description="Activate presentation mode — silences notifications")
async def presentation_mode() -> str:
    """Start presentation mode."""
    pyautogui.hotkey('win', 'a'); time.sleep(0.5); pyautogui.press('escape')
    return "Presentation mode enabled."

@llm.function_tool(description="Enable night mode — reduce blue light for eye comfort")
async def night_mode() -> str:
    """Enable night mode."""
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command",
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current\\default$windows.data.bluelightreduction.bluelightreductionstate\\windows.data.bluelightreduction.bluelightreductionstate' -Name 'Data' -Value ([byte[]](2,0,0,0,10,0,0,0,6,0,0,0,1,0))"],
            timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
        return "Night mode enabled."
    except: return "Attempted night mode."

@llm.function_tool(description="Get a daily briefing: time, date, battery, system status, reminders")
async def daily_briefing() -> str:
    """Generate daily briefing."""
    from utils.memory import get_reminders, get_notes
    now = datetime.datetime.now()
    parts = [f"Good {'morning' if now.hour<12 else 'afternoon' if now.hour<17 else 'evening'}, Sir.",
             f"It's {now.strftime('%A, %B %d, %Y')} at {now.strftime('%I:%M %p')}."]
    try:
        b = psutil.sensors_battery()
        if b: parts.append(f"Battery: {b.percent}% ({'plugged in' if b.power_plugged else 'on battery'}).")
    except: pass
    parts.append(f"CPU: {psutil.cpu_percent(interval=0.3)}%, RAM: {psutil.virtual_memory().percent}%.")
    r = get_reminders()
    parts.append(r if "No active" not in r else "No pending reminders.")
    return " ".join(parts)

@llm.function_tool(description="Send a WhatsApp message via WhatsApp Web")
async def whatsapp_message(contact: str = "", message: str = "") -> str:
    """Send WhatsApp message.

    Args:
        contact: Contact name
        message: Message text
    """
    if contact and message:
        import urllib.parse
        webbrowser.open(f"https://wa.me/?text={urllib.parse.quote(message)}")
        return "Opening WhatsApp."
    webbrowser.open("https://web.whatsapp.com/")
    return "Opened WhatsApp Web."

@llm.function_tool(description="Change conversation mode: Professional, Friendly, or Technical")
async def set_mode(mode: str = "Professional") -> str:
    """Set conversation mode.

    Args:
        mode: Mode name - Professional, Friendly, or Technical
    """
    from utils.memory import save_preference
    save_preference("conversation_mode", mode.capitalize())
    return f"Mode set to {mode}."

@llm.function_tool(description="Get usage statistics of most used commands")
async def usage_stats() -> str:
    """Get usage stats."""
    from utils.context import get_usage_stats; return get_usage_stats()

@llm.function_tool(description="Get WiFi connection status and signal strength")
async def wifi_status() -> str:
    """Get WiFi status."""
    r = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW)
    info = {}
    for line in r.stdout.split('\n'):
        if ':' in line:
            k, _, v = line.partition(':')
            k, v = k.strip().lower(), v.strip()
            if 'ssid' in k and 'bssid' not in k: info['network'] = v
            elif 'signal' in k: info['signal'] = v
    return f"WiFi: {info.get('network', '?')} ({info.get('signal', '?')})" if info else "Not connected."

@llm.function_tool(description="Get local and public IP address")
async def ip_address() -> str:
    """Get IP addresses."""
    import socket
    local = socket.gethostbyname(socket.gethostname())
    try:
        import urllib.request
        public = urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode()
        return f"Local: {local}, Public: {public}"
    except: return f"Local: {local}"

@llm.function_tool(description="Clear conversation memory")
async def clear_memory() -> str:
    """Clear memory."""
    return "Memory cleared, Sir."


# ══════════════════════════════════════════
# 🌐 WEB SEARCH (DuckDuckGo)
# ══════════════════════════════════════════

@llm.function_tool(description="Search the internet using DuckDuckGo and return results. Use this whenever the user asks about current events, news, facts, definitions, prices, or anything needing real-time internet knowledge.")
async def web_search(query: str) -> str:
    """Search the web using DuckDuckGo.

    Args:
        query: The search query to look up on the internet
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return f"No results found for: {query}"
        summary = []
        for r in results[:5]:
            title = r.get("title", "")
            body = r.get("body", "")
            summary.append(f"• {title}: {body}")
        return f"Search results for '{query}':\n" + "\n".join(summary)
    except ImportError:
        return "DuckDuckGo search not available. Install: pip install duckduckgo-search"
    except Exception as e:
        return f"Search error: {e}"


# ══════════════════════════════════════════
# 📋 COLLECT ALL TOOLS INTO A LIST
# ══════════════════════════════════════════

ALL_TOOLS = [
    # System
    shutdown, restart, lock_screen, sleep_mode,
    open_task_manager, open_control_panel, open_settings,
    open_cmd, open_powershell, open_file_explorer,
    system_info, clean_temp, close_all_apps,
    minimize_all, maximize_window, minimize_window,
    empty_recycle_bin, disk_space, battery_status, uptime, running_processes,
    # Volume & Display
    volume_up, volume_down, set_volume, volume_mute, brightness,
    # Web & Browser
    open_website, google_search, youtube_search, open_multiple_tabs,
    switch_tab, close_tab, new_tab, incognito, refresh_page,
    scroll_up, scroll_down, wikipedia_search, paste_clipboard, copy_clipboard,
    # Web Search
    web_search,
    # Input
    type_text, press_key, hotkey, select_all, undo, redo,
    # Phone
    connect_phone, phone_home_button, phone_volume_up, phone_volume_down, phone_screenshot,
    # Vision
    take_photo, take_screenshot, read_screen, analyze_screen,
    # Productivity
    tell_time, tell_date, set_timer, stopwatch, calculator, weather, translate,
    # Files
    search_files, open_file, organize_files, list_files, create_folder, file_info,
    # Memory
    save_memory, recall_memory, save_note, get_notes, clear_notes,
    save_reminder, get_reminders, clear_reminders,
    save_important, get_important, get_owner, save_preference,
    # To-Do
    save_todo, get_todos, complete_todo, clear_todos,
    # Developer
    run_command, open_app, close_app, install_package, clone_repo, create_project,
    # Media
    play_pause, next_track, previous_track,
    # Automation
    work_mode, study_mode, chill_mode, gaming_mode, presentation_mode, night_mode,
    daily_briefing, whatsapp_message, set_mode, usage_stats, wifi_status, ip_address,
    clear_memory,
]

