# livekit_tools.py — Jessica Tools for LiveKit Agents
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
import agent_state

# Add the project root to path so we can import utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pyautogui
import psutil

pyautogui.FAILSAFE = False

# ══════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════

# Browser executable paths (auto-detected on Windows)
BROWSER_PATHS = {
    "chrome": [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ],
    "edge": [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ],
    "firefox": [
        os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
    ],
    "brave": [
        os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ],
}

# Incognito/private mode flags per browser
BROWSER_INCOGNITO_FLAGS = {
    "chrome": "--incognito",
    "edge": "--inprivate",
    "firefox": "-private-window",
    "brave": "--incognito",
}

def _find_browser(browser_name: str) -> str | None:
    """Find the actual executable path for a browser."""
    name = browser_name.lower().strip()
    # Map common aliases
    aliases = {
        "google chrome": "chrome", "google": "chrome",
        "microsoft edge": "edge", "ms edge": "edge",
        "mozilla firefox": "firefox", "mozilla": "firefox",
        "brave browser": "brave",
    }
    name = aliases.get(name, name)
    paths = BROWSER_PATHS.get(name, [])
    for p in paths:
        if os.path.exists(p):
            return p
    # Try shutil.which as a fallback
    exe_names = {
        "chrome": "chrome", "edge": "msedge", "firefox": "firefox", "brave": "brave"
    }
    exe = shutil.which(exe_names.get(name, name))
    return exe

WEBSITE_MAP = {
    "instagram": "https://www.instagram.com/",
    "whatsapp": "https://web.whatsapp.com/",
    "facebook": "https://www.facebook.com/",
    "github": "https://github.com/",
    "youtube": "https://www.youtube.com/",
    "google": "https://www.google.com/",
    "twitter": "https://x.com/",
    "x": "https://x.com/",
    "spotify": "https://open.spotify.com/",
    "gmail": "https://mail.google.com/",
    "snapchat": "https://www.snapchat.com/",
    "zoom": "https://zoom.us/",
    "reddit": "https://www.reddit.com/",
    "linkedin": "https://www.linkedin.com/",
    "chatgpt": "https://chatgpt.com/",
    "amazon": "https://www.amazon.in/",
    "netflix": "https://www.netflix.com/",
    "discord": "https://discord.com/app",
    "telegram": "https://web.telegram.org/",
    "pinterest": "https://www.pinterest.com/",
    "notion": "https://www.notion.so/",
    "figma": "https://www.figma.com/",
    "canva": "https://www.canva.com/",
    "drive": "https://drive.google.com/",
    "maps": "https://maps.google.com/",
    "meet": "https://meet.google.com/",
    "calendar": "https://calendar.google.com/",
    "gemini": "https://gemini.google.com/",
    "flipkart": "https://www.flipkart.com/",
    "myntra": "https://www.myntra.com/",
    "swiggy": "https://www.swiggy.com/",
    "zomato": "https://www.zomato.com/",
    "best webstie": "https://de.pornhub.org/",
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

@llm.function_tool(description="Put the AI agent into sleep mode. Use when the user says 'sleep', 'so jao', 'mute ho jao', 'quiet', or anything meaning go silent. In sleep mode, the agent ignores all speech until woken up with the wake word 'Jessica'.")
async def sleep_mode() -> str:
    """Put the AI agent to sleep immediately."""
    agent_state.set_sleeping(True)
    return "SYSTEM: You are NOW in sleep mode. Say a brief goodnight message. After that, you MUST NOT respond to ANY speech. The system will handle wake word detection — you do NOT need to listen for it. Stay completely silent."

@llm.function_tool(description="Exit and stop the Jessica AI assistant completely. Use when the user says 'exit', 'band karo', 'quit', 'bye Jessica', 'shut yourself down', etc. This does NOT shutdown the computer — it only stops the AI agent process.")
async def exit_assistant() -> str:
    """Exit the Jessica AI assistant process gracefully."""
    import threading
    # Mark exit in shared state so GUI picks it up and kills everything
    agent_state.set_exit_requested(True)
    # Schedule a delayed hard-kill so the agent can say goodbye first
    def _delayed_exit():
        import time as _t
        _t.sleep(4)  # Give 4 seconds for goodbye message to finish
        os._exit(0)  # Hard exit
    threading.Thread(target=_delayed_exit, daemon=True).start()
    return "Goodbye Sir! Jessica shutting down. See you next time."

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

def _get_volume_interface():
    """Helper to get pycaw volume interface seamlessly."""
    try:
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        return devices.EndpointVolume
    except Exception:
        return None

@llm.function_tool(description="Increase system volume by N steps. 1 step = 2% (default 5 steps = 10%)")
async def volume_up(times: int = 5) -> str:
    """Increase volume.

    Args:
        times: Number of volume steps to increase
    """
    interface = _get_volume_interface()
    if interface:
        try:
            current = interface.GetMasterVolumeLevelScalar()
            new_vol = min(1.0, current + (times * 0.02))
            interface.SetMasterVolumeLevelScalar(new_vol, None)
            return f"Volume increased by {times * 2}% to {int(new_vol * 100)}%."
        except Exception:
            pass

    for _ in range(times): pyautogui.press('volumeup')
    return f"Volume up {times} steps."

@llm.function_tool(description="Decrease system volume by N steps. 1 step = 2% (default 5 steps = 10%)")
async def volume_down(times: int = 5) -> str:
    """Decrease volume.

    Args:
        times: Number of volume steps to decrease
    """
    interface = _get_volume_interface()
    if interface:
        try:
            current = interface.GetMasterVolumeLevelScalar()
            new_vol = max(0.0, current - (times * 0.02))
            interface.SetMasterVolumeLevelScalar(new_vol, None)
            return f"Volume decreased by {times * 2}% to {int(new_vol * 100)}%."
        except Exception:
            pass

    for _ in range(times): pyautogui.press('volumedown')
    return f"Volume down {times} steps."

@llm.function_tool(description="Set system volume to a specific percentage (0 to 100). Use for 'full volume' (100) or specific levels.")
async def set_volume(level: int) -> str:
    """Set system volume level to a specific percentage.

    Args:
        level: Percentage to set the volume to, from 0 to 100
    """
    level = max(0, min(100, level))
    
    interface = _get_volume_interface()
    if interface:
        try:
            interface.SetMasterVolumeLevelScalar(level / 100.0, None)
            return f"Volume set to {level}%."
        except Exception:
            pass
            
    # Fallback to key presses
    # Reset volume to 0 first (50 steps handles any volume since 50*2=100)
    for _ in range(50): pyautogui.press('volumedown')
    # Set to target level
    steps = level // 2
    for _ in range(steps): pyautogui.press('volumeup')
    return f"Volume set to {level}%."

@llm.function_tool(description="Toggle mute/unmute system volume")
async def volume_mute() -> str:
    """Toggle mute."""
    interface = _get_volume_interface()
    if interface:
        try:
            current = interface.GetMute()
            interface.SetMute(not current, None)
            return "Volume muted." if not current else "Volume unmuted."
        except Exception:
            pass
            
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

@llm.function_tool(description="Open a website by name like youtube, github, instagram, or a URL. Opens in Chrome by default.")
async def open_website(app_name: str) -> str:
    """Open a website in Chrome browser.

    Args:
        app_name: Website name (youtube, github, etc.) or full URL
    """
    name = app_name.lower().strip()
    url = WEBSITE_MAP.get(name)
    if not url:
        if "." in name:
            url = name if name.startswith("http") else f"https://{name}"
        else:
            url = f"https://www.{name}.com/"
    
    # Force Chrome to avoid YouTube PWA or other app intercepting
    try:
        subprocess.Popen(f'start chrome "{url}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        webbrowser.open(url)
    return f"Opening {app_name}."

@llm.function_tool(description="Open a website in a specific browser instead of the default. Use when the user wants to open something in Edge, Firefox, Brave, or Chrome specifically. Supported browsers: chrome, edge, firefox, brave.")
async def open_in_browser(url_or_name: str, browser: str = "chrome") -> str:
    """Open a website in a specific browser (Chrome, Edge, Firefox, or Brave).

    Args:
        url_or_name: Website name (youtube, github, etc.) or full URL to open
        browser: Browser name — chrome, edge, firefox, or brave
    """
    name = url_or_name.lower().strip()
    url = WEBSITE_MAP.get(name)
    if not url:
        if "." in name:
            url = name if name.startswith("http") else f"https://{name}"
        else:
            url = f"https://www.{name}.com/"
    
    browser_path = _find_browser(browser)
    if browser_path:
        try:
            subprocess.Popen([browser_path, url], creationflags=subprocess.CREATE_NO_WINDOW)
            return f"Opening {url_or_name} in {browser}."
        except Exception:
            pass
    
    # Fallback: try start command
    browser_cmd = {"chrome": "chrome", "edge": "msedge", "firefox": "firefox", "brave": "brave"}
    cmd = browser_cmd.get(browser.lower().strip(), browser.lower().strip())
    try:
        subprocess.Popen(f'start {cmd} "{url}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return f"Opening {url_or_name} in {browser}."
    except Exception:
        webbrowser.open(url)
        return f"Opened {url_or_name} in default browser (couldn't find {browser})."

@llm.function_tool(description="Open a website in incognito or private browsing mode. Use when the user wants private/incognito browsing. Defaults to Chrome incognito. Supports: chrome, edge, firefox, brave.")
async def open_incognito(url_or_name: str, browser: str = "chrome") -> str:
    """Open a website in incognito/private browsing mode.

    Args:
        url_or_name: Website name (youtube, github, etc.) or full URL to open
        browser: Browser to use — chrome, edge, firefox, or brave
    """
    name = url_or_name.lower().strip()
    url = WEBSITE_MAP.get(name)
    if not url:
        if "." in name:
            url = name if name.startswith("http") else f"https://{name}"
        else:
            url = f"https://www.{name}.com/"
    
    browser_key = browser.lower().strip()
    # Resolve aliases
    aliases = {
        "google chrome": "chrome", "microsoft edge": "edge", "ms edge": "edge",
        "mozilla firefox": "firefox", "brave browser": "brave",
    }
    browser_key = aliases.get(browser_key, browser_key)
    
    flag = BROWSER_INCOGNITO_FLAGS.get(browser_key, "--incognito")
    browser_path = _find_browser(browser_key)
    
    if browser_path:
        try:
            subprocess.Popen([browser_path, flag, url], creationflags=subprocess.CREATE_NO_WINDOW)
            return f"Opening {url_or_name} in {browser} incognito/private mode."
        except Exception:
            pass
    
    # Fallback: try start command
    browser_cmd = {"chrome": "chrome", "edge": "msedge", "firefox": "firefox", "brave": "brave"}
    cmd = browser_cmd.get(browser_key, browser_key)
    try:
        subprocess.Popen(f'start {cmd} {flag} "{url}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return f"Opening {url_or_name} in {browser} incognito/private mode."
    except Exception:
        webbrowser.open(url)
        return f"Opened {url_or_name} in default browser (couldn't open incognito for {browser})."

@llm.function_tool(description="Search the internet deeply and return comprehensive results. Finds web pages, scrapes their actual content, and returns detailed information. Use for any question needing real-world info: facts, people, events, prices, news, how-to, comparisons, current affairs, etc. This is the primary research tool.")
async def deep_search(query: str) -> str:
    """Deep web search — finds pages via DuckDuckGo then scrapes actual page content for detailed answers.

    Args:
        query: The search query to research
    """
    import requests
    from bs4 import BeautifulSoup
    import concurrent.futures
    import re

    def _scrape_page(url: str, timeout: int = 5) -> dict:
        """Scrape a single page and extract clean text content."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, "lxml")
            
            # Remove noise elements
            for tag in soup(["script", "style", "nav", "footer", "header", "aside",
                             "iframe", "noscript", "svg", "form", "button", "input"]):
                tag.decompose()
            # Remove hidden elements
            for tag in soup.find_all(attrs={"style": re.compile(r"display\s*:\s*none", re.I)}):
                tag.decompose()
            for tag in soup.find_all(attrs={"aria-hidden": "true"}):
                tag.decompose()
            
            # Try to find the main content area
            main_content = None
            for selector in ["article", "main", "[role='main']", ".post-content",
                             ".article-body", ".entry-content", "#content", ".content"]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            target = main_content or soup.body or soup
            
            # Extract text from paragraphs, headings, and list items for structure
            blocks = []
            for el in target.find_all(["h1", "h2", "h3", "p", "li", "td", "th", "blockquote", "pre"]):
                text = el.get_text(separator=" ", strip=True)
                if len(text) > 15:  # Skip tiny fragments
                    if el.name in ("h1", "h2", "h3"):
                        blocks.append(f"## {text}")
                    else:
                        blocks.append(text)
            
            content = "\n".join(blocks)
            # Collapse excessive whitespace
            content = re.sub(r"\n{3,}", "\n\n", content)
            content = re.sub(r" {2,}", " ", content)
            
            # Get page title
            title = soup.title.get_text(strip=True) if soup.title else url
            
            return {"url": url, "title": title, "content": content[:3000]}  # Cap per page
        except Exception:
            return {"url": url, "title": "", "content": ""}

    try:
        # Step 1: Get search results from DuckDuckGo
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=6))
        
        if not results:
            return f"No results found for: {query}"
        
        # Step 2: Collect URLs and snippets
        urls = [r.get("href", "") for r in results if r.get("href")]
        snippets = {r.get("href", ""): r.get("body", "") for r in results}
        
        # Step 3: Scrape top 3 pages in parallel for speed
        scraped = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(_scrape_page, url): url for url in urls[:3]}
            for future in concurrent.futures.as_completed(futures, timeout=8):
                try:
                    result = future.result()
                    if result["content"]:
                        scraped.append(result)
                except Exception:
                    pass
        
        # Step 4: Build comprehensive response
        output_parts = []
        
        # Add scraped deep content (primary)
        for page in scraped:
            # Trim to keep response manageable but still deep
            content = page["content"][:2000]
            output_parts.append(f"━━━ {page['title']} ━━━\n{content}")
        
        # Add remaining snippet results (for pages we didn't scrape)
        remaining = [r for r in results if r.get("href") not in [p["url"] for p in scraped]]
        if remaining:
            extras = []
            for r in remaining[:3]:
                title = r.get("title", "")
                body = r.get("body", "")
                if body:
                    extras.append(f"• {title}: {body}")
            if extras:
                output_parts.append("━━━ More Results ━━━\n" + "\n".join(extras))
        
        if not output_parts:
            # Fallback to just snippets
            snippet_text = []
            for r in results:
                body = r.get("body", "")
                title = r.get("title", "")
                if body:
                    snippet_text.append(f"• {title}: {body}")
            return f"Search results for '{query}':\n" + "\n".join(snippet_text)
        
        # Cap total output to avoid overwhelming the LLM context
        full_output = f"Deep search results for '{query}':\n\n" + "\n\n".join(output_parts)
        return full_output[:6000]
    
    except ImportError:
        return "Search unavailable. Install: pip install ddgs requests beautifulsoup4 lxml"
    except Exception as e:
        # Last resort fallback
        try:
            webbrowser.open(f"https://www.google.com/search?q={query}")
            return f"Search failed ({e}). Opened Google in browser."
        except Exception:
            return f"Search error: {e}"

@llm.function_tool(description="Search and play something on YouTube.")
async def youtube_search(query: str) -> str:
    """Search and play on YouTube in Chrome browser.

    Args:
        query: Song, video, or topic to play
    """
    try:
        import urllib.request
        import urllib.parse
        import re
        
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        html = urllib.request.urlopen(search_url).read().decode('utf-8')
        video_ids = re.findall(r'watch\?v=([a-zA-Z0-9_-]{11})', html)
        target_url = f"https://www.youtube.com/watch?v={video_ids[0]}" if video_ids else search_url
        
        # Force Chrome to avoid YouTube PWA intercepting the URL
        try:
            subprocess.Popen(f'start chrome "{target_url}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            webbrowser.open(target_url)
        
        return f"Playing '{query}' on YouTube." if video_ids else f"Showing results for '{query}' on YouTube."
    except Exception:
        url = f"https://www.youtube.com/results?search_query={query}"
        try:
            subprocess.Popen(f'start chrome "{url}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            webbrowser.open(url)
        return f"Showing results for '{query}' on YouTube."

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

@llm.function_tool(description="Close the current window")
async def close_tab() -> str:
    """Close current window."""
    pyautogui.hotkey('alt', 'f4')
    return "Closed."

@llm.function_tool(description="Refresh the current browser page")
async def refresh_page() -> str:
    """Refresh page."""
    pyautogui.hotkey('f5')
    return "Page refreshed."

@llm.function_tool(description="Search Wikipedia for information about a topic")
async def wikipedia_search(query: str) -> str:
    """Search Wikipedia.

    Args:
        query: Topic to look up
    """
    try:
        import wikipedia; return wikipedia.summary(query, sentences=2)
    except: return "Couldn't find that on Wikipedia."

@llm.function_tool(description="Copy selected text to clipboard")
async def copy_clipboard() -> str:
    """Copy to clipboard."""
    pyautogui.hotkey('ctrl', 'c')
    return "Copied."


# ══════════════════════════════════════════
# ⌨️ INPUT AUTOMATION
# ══════════════════════════════════════════

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
        resp = model.generate_content([f"You are Jessica, analyzing a screenshot. TASK: {query}. Be concise. Address user as Sir.", img])
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
        resp = model.generate_content([f"You are Jessica, expert technician. TASK: {query}. Cover errors, diagnosis, fix commands. Concise. Address Sir.", img])
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
# 🧬 LEARNING & INTELLIGENCE
# ══════════════════════════════════════════

@llm.function_tool(description="Tell the user everything you know about them. Shows auto-learned info, saved facts, preferences, and important items. Use when user asks 'what do you know about me' or 'kya pata hai tujhe mere baare me'.")
async def what_i_know() -> str:
    """Show everything known about the user — learned, facts, preferences, important items."""
    from utils.memory import _load_memory
    from utils.context import get_learned_summary, get_usage_stats
    
    mem = _load_memory()
    parts = []
    
    # Facts
    facts = mem.get("facts", {})
    user_facts = {k: v for k, v in facts.items() if k not in ["last_updated", "owner_name", "assistant_name", "assistant_creator", "persona"]}
    if user_facts:
        fact_lines = [f"  • {k.replace('_', ' ').title()}: {v}" for k, v in user_facts.items()]
        parts.append("📋 What I know:\n" + "\n".join(fact_lines))
    
    # Preferences
    prefs = mem.get("preferences", {})
    if prefs:
        pref_lines = [f"  • {k}: {v}" for k, v in prefs.items()]
        parts.append("⚙️ Your preferences:\n" + "\n".join(pref_lines))
    
    # Important items
    important = mem.get("important", [])
    if important:
        imp_lines = [f"  ⭐ {i.get('text', i) if isinstance(i, dict) else i}" for i in important[-5:]]
        parts.append("⭐ Important things:\n" + "\n".join(imp_lines))
    
    # Auto-learned
    learned = mem.get("learned", [])
    if learned:
        learn_lines = [f"  🧠 {l.get('what', '')} (learned {l.get('learned_at', '')})" for l in learned[-10:]]
        parts.append("🧠 Things I learned automatically:\n" + "\n".join(learn_lines))
    
    # Notes
    notes = mem.get("notes", [])
    if notes:
        note_lines = [f"  📝 {n.get('text', n)}" for n in notes[-5:]]
        parts.append("📝 Your notes:\n" + "\n".join(note_lines))
    
    # Usage insights
    usage = get_usage_stats()
    if "No usage" not in usage:
        parts.append("📊 " + usage)
    
    if not parts:
        return "I don't know much about you yet, Sir. Keep talking to me and I'll learn! 😊"
    
    return "\n\n".join(parts)

@llm.function_tool(description="Get smart suggestions and insights based on the user's usage patterns and time of day.")
async def get_usage_insights() -> str:
    """Get usage patterns and smart suggestions."""
    from utils.context import get_suggestion, get_usage_stats
    
    parts = []
    stats = get_usage_stats()
    if "No usage" not in stats:
        parts.append(stats)
    
    suggestion = get_suggestion()
    if suggestion:
        parts.append(f"💡 Suggestion: {suggestion}")
    
    if not parts:
        return "Not enough usage data yet. Keep using me and I'll start predicting your needs!"
    
    return "\n".join(parts)


# ══════════════════════════════════════════
# ✅ TO-DO LIST
# ══════════════════════════════════════════

# ══════════════════════════════════════════
# 💻 DEVELOPER MODE
# ══════════════════════════════════════════

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

@llm.function_tool(description="Send a WhatsApp message to a contact by name. Opens WhatsApp Web, searches for the contact, types the message, and sends it automatically.")
async def whatsapp_message(contact: str = "", message: str = "") -> str:
    """Send WhatsApp message to a contact by name using WhatsApp Web automation.

    Args:
        contact: Contact name to search for (e.g. 'Ashu', 'Mom', 'Rahul')
        message: Message text to send
    """
    import time as _time

    if not contact:
        webbrowser.open("https://web.whatsapp.com/")
        return "Opened WhatsApp Web."

    if not message:
        message = "Hi"

    # Step 1: Open WhatsApp Web
    try:
        subprocess.Popen('start chrome "https://web.whatsapp.com/"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception:
        webbrowser.open("https://web.whatsapp.com/")

    # Step 2: Wait for WhatsApp Web to load
    _time.sleep(8)

    # Step 3: Click on search bar (Ctrl+Alt+/ is WhatsApp Web shortcut for search)
    # Alternative: click on the search area
    pyautogui.hotkey('ctrl', 'alt', '/')
    _time.sleep(1)

    # Step 4: Type contact name to search
    try:
        import pyperclip
        pyperclip.copy(contact)
        pyautogui.hotkey('ctrl', 'v')
    except ImportError:
        pyautogui.write(contact, interval=0.05)
    _time.sleep(2)

    # Step 5: Press down arrow + Enter to select first matching contact
    pyautogui.press('down')
    _time.sleep(0.3)
    pyautogui.press('enter')
    _time.sleep(1.5)

    # Step 6: Type the message in the chat box
    try:
        import pyperclip
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
    except ImportError:
        pyautogui.write(message, interval=0.03)
    _time.sleep(0.5)

    # Step 7: Send
    pyautogui.press('enter')

    return f"Message '{message}' sent to {contact} on WhatsApp."

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


# (web_search merged into deep_search tool above)

# ── Type Text (type anywhere) ──

@llm.function_tool(description="Type text into the currently focused input field, chat box, or text area. Works with any app — ChatGPT, WhatsApp, Notepad, browser, etc. Use when the user wants to type or write something.")
async def type_text(text: str) -> str:
    """Type the given text into the active window.
    
    Args:
        text: The text to type into the focused input field.
    """
    try:
        import pyperclip
        import time as _time
        # Save current clipboard
        try:
            old_clip = pyperclip.paste()
        except Exception:
            old_clip = ""
        # Copy text to clipboard, paste it (supports Unicode/Hindi)
        pyperclip.copy(text)
        _time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        _time.sleep(0.3)
        # Restore old clipboard
        try:
            pyperclip.copy(old_clip)
        except Exception:
            pass
        return f"Typed: {text}"
    except ImportError:
        return "pyperclip not installed. Run: pip install pyperclip"
    except Exception as e:
        return f"Failed to type: {e}"


@llm.function_tool(description="Press Enter key to send or submit the typed message. Use after type_text when the user wants to send or submit.")
async def press_enter() -> str:
    """Press the Enter key to submit."""
    try:
        pyautogui.press("enter")
        return "Enter pressed — message sent."
    except Exception as e:
        return f"Failed: {e}"


# ══════════════════════════════════════════
# 🎙️ VOICE SWITCHING
# ══════════════════════════════════════════

VOICE_OPTIONS = {
    "aoede": {"name": "Aoede", "tone": "Breezy", "gender": "female"},
    "kore": {"name": "Kore", "tone": "Firm", "gender": "female"},
    "leda": {"name": "Leda", "tone": "Youthful", "gender": "female"},
    "zephyr": {"name": "Zephyr", "tone": "Bright", "gender": "female"},
    "puck": {"name": "Puck", "tone": "Upbeat", "gender": "male"},
    "charon": {"name": "Charon", "tone": "Informative", "gender": "male"},
    "orus": {"name": "Orus", "tone": "Firm", "gender": "male"},
    "fenrir": {"name": "Fenrir", "tone": "Excitable", "gender": "male"},
}

@llm.function_tool(description="List all available voice options. Use when user asks 'what voices are available', 'show me voices', 'konsi voices hain', etc.")
async def list_voices() -> str:
    """List all available Gemini voice options."""
    lines = ["Available voices:"]
    for key, info in VOICE_OPTIONS.items():
        lines.append(f"- {info['name']} ({info['tone']}, {info['gender']})")
    # Get current voice from config
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        with open(config_path, "r") as f:
            current = json.load(f).get("voice", "Aoede")
        lines.append(f"\nCurrently using: {current}")
    except Exception:
        pass
    return "\n".join(lines)

@llm.function_tool(description="Change the AI assistant's voice. Use when user says 'change voice to Kore', 'female voice lagao', 'male voice chahiye', etc. The voice change takes effect after restart.")
async def change_voice(voice_name: str) -> str:
    """Change the voice used by the AI assistant.
    
    Args:
        voice_name: The name of the voice to switch to (e.g. Aoede, Kore, Leda, Zephyr, Puck, Charon, Orus, Fenrir).
    """
    key = voice_name.strip().lower()
    if key not in VOICE_OPTIONS:
        options = ", ".join(info["name"] for info in VOICE_OPTIONS.values())
        return f"Unknown voice '{voice_name}'. Available voices: {options}"
    
    voice_info = VOICE_OPTIONS[key]
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["voice"] = voice_info["name"]
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        # Also update active personality if applicable
        pers_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personalities.json")
        try:
            with open(pers_path, "r", encoding="utf-8") as f:
                pers = json.load(f)
            active = pers.get("active", "")
            if active and "profiles" in pers and active in pers["profiles"]:
                pers["profiles"][active]["voice"] = voice_info["name"]
                with open(pers_path, "w", encoding="utf-8") as f:
                    json.dump(pers, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

        return f"Voice changed to {voice_info['name']} ({voice_info['tone']}, {voice_info['gender']}). The new voice will be active after restart."
    except Exception as e:
        return f"Failed to change voice: {e}"


# ══════════════════════════════════════════
# 📋 COLLECT ALL TOOLS INTO A LIST
# ══════════════════════════════════════════

ALL_TOOLS = [
    # System
    sleep_mode, exit_assistant, shutdown, restart, lock_screen,
    open_task_manager, open_control_panel, open_settings,
    open_cmd, open_powershell, open_file_explorer,
    system_info, clean_temp, close_all_apps,
    minimize_all, maximize_window, minimize_window,
    empty_recycle_bin, battery_status, uptime, running_processes,
    # Volume & Display
    volume_up, volume_down, set_volume, volume_mute, brightness,
    # Web & Browser
    open_website, open_in_browser, open_incognito,
    deep_search, youtube_search, open_multiple_tabs,
    close_tab, refresh_page, wikipedia_search, copy_clipboard,
    # Input & Typing
    select_all, undo, redo, type_text, press_enter,
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
    # Learning & Intelligence
    what_i_know, get_usage_insights,
    # Apps
    open_app, close_app,
    # Media
    play_pause, next_track, previous_track,
    # Voice
    list_voices, change_voice,
    # Misc
    whatsapp_message, ip_address, clear_memory,
]
