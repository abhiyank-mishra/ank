"""
Jessica AI — Floating Desktop Widget + Background Agent Launcher
Personality switching, voice control, auto-restart.
Only one instance can run at a time.
"""

import os
import sys
import subprocess
import threading
import json
import tkinter as tk
from tkinter import Menu
from pathlib import Path

from PIL import Image, ImageTk, ImageDraw, ImageFont

# Paths
SCRIPT_DIR = Path(__file__).parent
ICON_PATH = SCRIPT_DIR / "logo.png"
FALLBACK_ICON = SCRIPT_DIR / "jessica_icon.ico"
VENV_PYTHON = SCRIPT_DIR.parent / "venv" / "Scripts" / "python.exe"
AGENT_SCRIPT = SCRIPT_DIR / "livekit_agent.py"
LOG_FILE = SCRIPT_DIR / "jessica_agent.log"
LOCK_FILE = SCRIPT_DIR / "jessica.lock"
PERSONALITIES_PATH = SCRIPT_DIR / "personalities.json"
CONFIG_PATH = SCRIPT_DIR / "config.json"
STATE_PATH = SCRIPT_DIR / "state.json"

# Widget config
WIDGET_SIZE = 70
GLOW_SIZE = 86
PULSE_SPEED = 50


# ─────────────────────── Personality Helpers ─────────────────────────

def load_personalities():
    try:
        with open(PERSONALITIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active": "jessica", "profiles": {}}


def save_active_personality(persona_id):
    data = load_personalities()
    data["active"] = persona_id
    with open(PERSONALITIES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_active_profile():
    data = load_personalities()
    active = data.get("active", "jessica")
    profile = data.get("profiles", {}).get(active, {})
    return active, profile


# ─────────────────────── Single Instance Lock ───────────────────────

def _is_pid_alive(pid):
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return False
    except Exception:
        return False


def acquire_lock():
    if LOCK_FILE.exists():
        try:
            old_pid = int(LOCK_FILE.read_text().strip())
            if _is_pid_alive(old_pid):
                return False
        except (ValueError, OSError):
            pass
    LOCK_FILE.write_text(str(os.getpid()))
    return True


def release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except OSError:
        pass


# ─────────────────────── Floating Widget ────────────────────────────

class FloatingAnk:
    def __init__(self):
        self.process = None
        self._log_handle = None
        self.agent_running = False
        self.pulse_alpha = 0
        self.pulse_direction = 1
        self._restarting = False

        # Load active personality
        self.active_id, self.active_profile = get_active_profile()
        self.glow_color = tuple(self.active_profile.get("glow_color", [42, 73, 122]))

        # --- Tkinter Window ---
        self.root = tk.Tk()
        self.root.title("Jessica AI")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "#010101")
        self.root.configure(bg="#010101")

        # Position: bottom-right corner
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - GLOW_SIZE - 30
        y = screen_h - GLOW_SIZE - 80
        self.root.geometry(f"{GLOW_SIZE}x{GLOW_SIZE}+{x}+{y}")

        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=GLOW_SIZE, height=GLOW_SIZE,
            bg="#010101", highlightthickness=0, bd=0,
        )
        self.canvas.pack()

        # Load icon
        self._load_icon()
        self._draw_widget()

        # Sleep toggle button — shows green dot when awake, zzz when sleeping
        is_sleeping = False
        if STATE_PATH.exists():
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    is_sleeping = json.load(f).get("is_sleeping", False)
            except Exception: pass
        
        self.sleep_btn = tk.Button(
            self.root,
            text="💤" if is_sleeping else "●",
            font=("Segoe UI", 8),
            bg="#1a1a2e",
            fg="#ff5252" if is_sleeping else "#00e676",
            bd=0,
            activebackground="#ffab40",
            command=self._toggle_sleep
        )
        self.sleep_btn.place(x=GLOW_SIZE - 22, y=0, width=22, height=22)

        # Drag
        self._drag_data = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)

        # Right-click menu
        self._build_menu()
        self.canvas.bind("<Button-3>", self._show_menu)

        # Double click for status
        self.canvas.bind("<Double-Button-1>", self._show_status)

        # Clean exit
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

    def _build_menu(self):
        """Build the right-click menu with personality & voice options."""
        self.menu = Menu(self.root, tearoff=0, font=("Segoe UI", 10))

        # --- Personality submenu ---
        persona_menu = Menu(self.menu, tearoff=0, font=("Segoe UI", 10))
        data = load_personalities()
        profiles = data.get("profiles", {})
        active = data.get("active", "jessica")

        for pid, profile in profiles.items():
            name = profile.get("name", pid)
            gender = profile.get("gender", "?")
            voice = profile.get("voice", "?")
            marker = " [active]" if pid == active else ""
            label = f"{name} ({gender}, {voice}){marker}"
            # Use default arg to capture pid in closure
            persona_menu.add_command(
                label=label,
                command=lambda p=pid: self._switch_personality(p)
            )

        self.menu.add_cascade(label="Switch Personality", menu=persona_menu)
        self.menu.add_separator()

        # --- Actions ---
        self.menu.add_command(label="Restart Agent", command=self._restart_agent)
        self.menu.add_command(label="Open Logs", command=self._open_logs)
        self.menu.add_separator()
        self.menu.add_command(label="Quit", command=self._quit)

    def _switch_personality(self, persona_id):
        """Switch to a different personality and restart the agent."""
        save_active_personality(persona_id)

        # Update local state
        self.active_id, self.active_profile = get_active_profile()
        self.glow_color = tuple(self.active_profile.get("glow_color", [42, 73, 122]))

        # Rebuild menu to show new active marker
        self._build_menu()

        # Show notification
        name = self.active_profile.get("name", persona_id)
        self._show_tooltip(f"Switching to {name}...", "#ffab40")

        # Restart agent with new personality
        self.root.after(500, self._restart_agent)

    def _restart_agent(self):
        """Stop and restart the agent process."""
        if self._restarting:
            return
        self._restarting = True

        def do_restart():
            self._stop_agent()
            import time
            time.sleep(1)
            self._start_agent()
            self._restarting = False

        threading.Thread(target=do_restart, daemon=True).start()

    def _load_icon(self):
        try:
            if ICON_PATH.exists():
                img = Image.open(str(ICON_PATH))
            elif FALLBACK_ICON.exists():
                img = Image.open(str(FALLBACK_ICON))
            else:
                img = Image.new("RGBA", (256, 256), (0, 200, 120, 255))

            img = img.convert("RGBA").resize((WIDGET_SIZE, WIDGET_SIZE), Image.LANCZOS)

            mask = Image.new("L", (WIDGET_SIZE, WIDGET_SIZE), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, WIDGET_SIZE, WIDGET_SIZE), fill=255)

            self.icon_img = Image.new("RGBA", (WIDGET_SIZE, WIDGET_SIZE), (0, 0, 0, 0))
            self.icon_img.paste(img, (0, 0), mask)

        except Exception:
            self.icon_img = Image.new("RGBA", (WIDGET_SIZE, WIDGET_SIZE), (0, 0, 0, 0))
            draw = ImageDraw.Draw(self.icon_img)
            draw.ellipse((0, 0, WIDGET_SIZE, WIDGET_SIZE), fill=(0, 200, 120, 255))

    def _create_glow_frame(self, intensity):
        frame = Image.new("RGBA", (GLOW_SIZE, GLOW_SIZE), (1, 1, 1, 0))
        draw = ImageDraw.Draw(frame)
        offset = (GLOW_SIZE - WIDGET_SIZE) // 2

        r, g, b = self.glow_color

        for i in range(4, 0, -1):
            alpha = int(intensity * 40 / i)
            c = (r, g, b, alpha)
            draw.ellipse(
                (offset - i * 2, offset - i * 2,
                 offset + WIDGET_SIZE + i * 2, offset + WIDGET_SIZE + i * 2),
                outline=c, width=2
            )

        frame.paste(self.icon_img, (offset, offset), self.icon_img)
        return frame

    def _draw_widget(self):
        frame = self._create_glow_frame(0.5)
        self._tk_img = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(GLOW_SIZE // 2, GLOW_SIZE // 2, image=self._tk_img)

    def _pulse_animation(self):
        if not self.agent_running:
            self._draw_widget()
            self.root.after(PULSE_SPEED * 4, self._pulse_animation)
            return

        self.pulse_alpha += 0.04 * self.pulse_direction
        if self.pulse_alpha >= 1.0:
            self.pulse_alpha = 1.0
            self.pulse_direction = -1
        elif self.pulse_alpha <= 0.2:
            self.pulse_alpha = 0.2
            self.pulse_direction = 1

        frame = self._create_glow_frame(self.pulse_alpha)
        self._tk_img = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(GLOW_SIZE // 2, GLOW_SIZE // 2, image=self._tk_img)
        self.root.after(PULSE_SPEED, self._pulse_animation)

    # --- Drag ---
    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _toggle_sleep(self):
        """Toggle sleep/mute state for the agent."""
        current = False
        if STATE_PATH.exists():
            try:
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    current = json.load(f).get("is_sleeping", False)
            except Exception: pass
        
        new_state = not current
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({"is_sleeping": new_state}, f)
        
        # Update button: zzz when sleeping, green dot when awake
        self.sleep_btn.config(
            text="💤" if new_state else "●",
            fg="#ff5252" if new_state else "#00e676"
        )
        self._show_tooltip("Jessica is sleeping 💤" if new_state else "Jessica is awake ●", "#ff5252" if new_state else "#00e676")

    # --- Menu ---
    def _show_menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def _show_tooltip(self, text, color="#00e676"):
        """Show a premium tooltip near the widget with accent border."""
        tip = tk.Toplevel(self.root)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(bg="#2a497a")  # Accent border color

        # Inner frame for content with dark bg
        inner = tk.Frame(tip, bg="#0d1b2a", padx=2, pady=2)
        inner.pack(padx=2, pady=2)

        label = tk.Label(
            inner, text=text,
            font=("Segoe UI", 11, "bold"),
            fg=color, bg="#0d1b2a",
            padx=18, pady=10,
        )
        label.pack()

        wx = self.root.winfo_x()
        wy = self.root.winfo_y()
        tip.geometry(f"+{wx - 80}+{wy - 55}")
        
        # Fade out after 2.5 seconds
        tip.after(2500, tip.destroy)

    def _show_status(self, event):
        name = self.active_profile.get("name", "Jessica")
        gender = self.active_profile.get("gender", "?")
        voice = self.active_profile.get("voice", "?")

        if self.process and self.process.poll() is None:
            status = f"{name} ({gender}) - Running"
            color = "#00e676"
        else:
            status = f"{name} ({gender}) - Stopped"
            color = "#ff5252"

        self._show_tooltip(f"{status}\nVoice: {voice}", color)

    def _open_logs(self):
        if LOG_FILE.exists():
            os.startfile(str(LOG_FILE))

    def _quit(self):
        self._stop_agent()
        release_lock()
        self.root.destroy()

    # --- Agent Process ---
    def _start_agent(self):
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        self._log_handle = open(LOG_FILE, "w", encoding="utf-8")

        self.process = subprocess.Popen(
            [str(VENV_PYTHON), str(AGENT_SCRIPT), "console"],
            cwd=str(SCRIPT_DIR),
            env=env,
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self.agent_running = True

    def _stop_agent(self):
        self.agent_running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        if self._log_handle:
            self._log_handle.close()
            self._log_handle = None

    def _monitor_agent(self):
        if self.process:
            self.process.wait()
            self.agent_running = False

    def run(self):
        self._start_agent()
        self.root.after(100, self._pulse_animation)
        threading.Thread(target=self._monitor_agent, daemon=True).start()
        self.root.mainloop()
        self._stop_agent()
        release_lock()


if __name__ == "__main__":
    if not acquire_lock():
        sys.exit(0)

    try:
        app = FloatingAnk()
        app.run()
    except Exception:
        release_lock()
