"""
Jessica AI — Premium Floating Desktop Widget + Background Agent Launcher
Voice switching, personality control, sleep/wake, auto-restart.
Only one instance can run at a time.
"""

import os
import sys
import subprocess
import threading
import json
import math
import tkinter as tk
from tkinter import Menu
from pathlib import Path

from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter

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

# Widget config — larger for better visuals
WIDGET_SIZE = 56
GLOW_SIZE = 88
CANVAS_SIZE = 88
PULSE_SPEED = 30
RING_WIDTH = 3

# Available Gemini voices
VOICE_OPTIONS = [
    {"id": "aoede", "name": "Aoede", "tone": "Breezy", "gender": "♀ Female"},
    {"id": "kore", "name": "Kore", "tone": "Firm", "gender": "♀ Female"},
    {"id": "leda", "name": "Leda", "tone": "Youthful", "gender": "♀ Female"},
    {"id": "zephyr", "name": "Zephyr", "tone": "Bright", "gender": "♀ Female"},
    {"id": "puck", "name": "Puck", "tone": "Upbeat", "gender": "♂ Male"},
    {"id": "charon", "name": "Charon", "tone": "Informative", "gender": "♂ Male"},
    {"id": "orus", "name": "Orus", "tone": "Firm", "gender": "♂ Male"},
    {"id": "fenrir", "name": "Fenrir", "tone": "Excitable", "gender": "♂ Male"},
]

# Premium color palette
COLORS = {
    "bg_dark": "#0a0e1a",
    "bg_card": "#111827",
    "bg_hover": "#1e293b",
    "accent": "#3b82f6",
    "accent_glow": "#60a5fa",
    "accent_cyan": "#06b6d4",
    "success": "#10b981",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "text": "#f1f5f9",
    "text_dim": "#94a3b8",
    "border": "#1e293b",
    "menu_bg": "#0f172a",
    "menu_fg": "#e2e8f0",
    "menu_active_bg": "#1e3a5f",
    "menu_active_fg": "#60a5fa",
    "ring_base": "#1e3a5f",
}


# ─────────────────────── Config Helpers ──────────────────────────────

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"voice": "Aoede", "assistant_name": "Jessica", "owner": "Abhiyank"}


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


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


# ─────────────────────── Hex to RGB ─────────────────────────────────

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


# ─────────────────────── Premium Floating Widget ────────────────────

class FloatingJessica:
    def __init__(self):
        self.process = None
        self._log_handle = None
        self.agent_running = False
        self.pulse_phase = 0.0
        self._restarting = False
        self._tooltip_win = None
        self._frame_count = 0

        # Load active personality
        self.active_id, self.active_profile = get_active_profile()
        self.glow_color = tuple(self.active_profile.get("glow_color", [59, 130, 246]))

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
        x = screen_w - CANVAS_SIZE - 30
        y = screen_h - CANVAS_SIZE - 80
        self.root.geometry(f"{CANVAS_SIZE}x{CANVAS_SIZE}+{x}+{y}")

        # Canvas
        self.canvas = tk.Canvas(
            self.root, width=CANVAS_SIZE, height=CANVAS_SIZE,
            bg="#010101", highlightthickness=0, bd=0,
        )
        self.canvas.pack()

        # Load & prepare icon
        self._load_icon()
        self._draw_widget(0.0)

        # Sleep state overlay — positioned as status dot
        is_sleeping = self._read_sleep_state()

        self.sleep_btn = tk.Label(
            self.root,
            text="💤" if is_sleeping else "🟢",
            font=("Segoe UI", 6),
            bg="#010101",
            fg=COLORS["text"],
            cursor="hand2",
        )
        self.sleep_btn.place(x=CANVAS_SIZE - 18, y=2, width=16, height=16)
        self.sleep_btn.bind("<Button-1>", lambda e: self._toggle_sleep())

        # Drag
        self._drag_data = {"x": 0, "y": 0}
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)

        # Right-click context menu
        self._build_menu()
        self.canvas.bind("<Button-3>", self._show_menu)

        # Double click for status
        self.canvas.bind("<Double-Button-1>", self._show_status)

        # Hover effects
        self.canvas.bind("<Enter>", self._on_hover_enter)
        self.canvas.bind("<Leave>", self._on_hover_leave)
        self._hover = False

        # Clean exit
        self.root.protocol("WM_DELETE_WINDOW", self._quit)

        # Periodic sleep state sync (in case agent changes it)
        self._sync_sleep_state()

    # ─── Sleep state helpers ───

    def _read_sleep_state(self):
        try:
            if STATE_PATH.exists():
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f).get("is_sleeping", False)
        except Exception:
            pass
        return False

    def _read_exit_requested(self):
        """Check if the agent has requested a full exit."""
        try:
            if STATE_PATH.exists():
                with open(STATE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f).get("exit_requested", False)
        except Exception:
            pass
        return False

    def _sync_sleep_state(self):
        """Periodically sync sleep state from disk. Auto-quit if exit requested."""
        # Check for exit request first
        if self._read_exit_requested():
            self.root.after(100, self._quit)
            return

        is_sleeping = self._read_sleep_state()
        self.sleep_btn.config(
            text="💤" if is_sleeping else "🟢",
        )
        self.root.after(2000, self._sync_sleep_state)

    # ─── Menu ───

    def _build_menu(self):
        """Build the premium right-click context menu."""
        self.menu = Menu(
            self.root, tearoff=0,
            font=("Segoe UI", 10),
            bg=COLORS["menu_bg"],
            fg=COLORS["menu_fg"],
            activebackground=COLORS["menu_active_bg"],
            activeforeground=COLORS["menu_active_fg"],
            bd=1,
            relief="flat",
        )

        # ── Voice Switcher submenu ──
        voice_menu = Menu(
            self.menu, tearoff=0,
            font=("Segoe UI", 10),
            bg=COLORS["menu_bg"],
            fg=COLORS["menu_fg"],
            activebackground=COLORS["menu_active_bg"],
            activeforeground=COLORS["menu_active_fg"],
        )

        config = load_config()
        active_id, active_profile = get_active_profile()
        current_voice = active_profile.get("voice", config.get("voice", "Aoede")).lower()

        # Female voices header
        voice_menu.add_command(
            label="── Female Voices ──",
            state="disabled",
            font=("Segoe UI", 9, "bold"),
        )
        for v in VOICE_OPTIONS:
            if "Female" in v["gender"]:
                marker = " ✓" if v["name"].lower() == current_voice else ""
                voice_menu.add_command(
                    label=f"  {v['name']}  —  {v['tone']}{marker}",
                    command=lambda vid=v["id"], vname=v["name"]: self._switch_voice(vid, vname),
                )

        voice_menu.add_separator()

        # Male voices header
        voice_menu.add_command(
            label="── Male Voices ──",
            state="disabled",
            font=("Segoe UI", 9, "bold"),
        )
        for v in VOICE_OPTIONS:
            if "Male" in v["gender"]:
                marker = " ✓" if v["name"].lower() == current_voice else ""
                voice_menu.add_command(
                    label=f"  {v['name']}  —  {v['tone']}{marker}",
                    command=lambda vid=v["id"], vname=v["name"]: self._switch_voice(vid, vname),
                )

        self.menu.add_cascade(label="🎙  Voice", menu=voice_menu)

        # ── Personality submenu ──
        persona_menu = Menu(
            self.menu, tearoff=0,
            font=("Segoe UI", 10),
            bg=COLORS["menu_bg"],
            fg=COLORS["menu_fg"],
            activebackground=COLORS["menu_active_bg"],
            activeforeground=COLORS["menu_active_fg"],
        )
        data = load_personalities()
        profiles = data.get("profiles", {})
        active = data.get("active", "jessica")

        for pid, profile in profiles.items():
            name = profile.get("name", pid)
            marker = "  ✓" if pid == active else ""
            persona_menu.add_command(
                label=f"  {name}{marker}",
                command=lambda p=pid: self._switch_personality(p),
            )

        if profiles:
            self.menu.add_cascade(label="👤  Personality", menu=persona_menu)

        self.menu.add_separator()

        # ── Actions ──
        self.menu.add_command(label="🔄  Restart Agent", command=self._restart_agent)
        self.menu.add_command(label="😴  Toggle Sleep", command=self._toggle_sleep)
        self.menu.add_command(label="📄  Open Logs", command=self._open_logs)
        self.menu.add_separator()
        self.menu.add_command(label="❌  Quit Jessica", command=self._quit)

    def _switch_voice(self, voice_id, voice_name):
        """Switch voice in config and personalities, then restart agent."""
        config = load_config()
        config["voice"] = voice_name
        save_config(config)

        # Also update active personality's overriding voice
        data = load_personalities()
        active = data.get("active", "jessica")
        if "profiles" in data and active in data["profiles"]:
            data["profiles"][active]["voice"] = voice_name
            with open(PERSONALITIES_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

        # Rebuild menu to show new checkmark
        self._build_menu()

        self._show_tooltip(f"Voice → {voice_name}", COLORS["accent_glow"], subtitle="Restarting agent...")
        self.root.after(800, self._restart_agent)

    def _switch_personality(self, persona_id):
        """Switch to a different personality and restart the agent."""
        save_active_personality(persona_id)
        self.active_id, self.active_profile = get_active_profile()
        self.glow_color = tuple(self.active_profile.get("glow_color", [59, 130, 246]))
        self._build_menu()

        name = self.active_profile.get("name", persona_id)
        self._show_tooltip(f"Switching to {name}...", COLORS["warning"])
        self.root.after(500, self._restart_agent)

    def _restart_agent(self):
        """Stop and restart the agent process."""
        if self._restarting:
            return
        self._restarting = True

        def do_restart():
            self._stop_agent()
            import time
            time.sleep(1.5)
            self._start_agent()
            self._restarting = False
            self.root.after(0, lambda: self._show_tooltip("Agent restarted ✓", COLORS["success"]))

        threading.Thread(target=do_restart, daemon=True).start()

    # ─── Icon & Visuals ───

    def _load_icon(self):
        """Load and prepare the icon with premium circular crop and shadow."""
        try:
            if ICON_PATH.exists():
                img = Image.open(str(ICON_PATH))
            elif FALLBACK_ICON.exists():
                img = Image.open(str(FALLBACK_ICON))
            else:
                # Generate a gradient circle with "J" as fallback
                img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Gradient fill
                for i in range(128):
                    r = int(59 + i * 0.7)
                    g = int(130 - i * 0.2)
                    b = int(246 - i * 0.3)
                    draw.ellipse((i, i, 255 - i, 255 - i), fill=(r, g, b, 255))
                # Draw "J" letter
                try:
                    font = ImageFont.truetype("segoeui.ttf", 120)
                except Exception:
                    font = ImageFont.load_default()
                draw.text((78, 50), "J", fill=(255, 255, 255, 255), font=font)

            img = img.convert("RGBA").resize((WIDGET_SIZE, WIDGET_SIZE), Image.LANCZOS)

            # Circular mask with smooth anti-aliased edges
            # Use a higher resolution mask and downscale for AA
            aa_scale = 4
            aa_size = WIDGET_SIZE * aa_scale
            mask_large = Image.new("L", (aa_size, aa_size), 0)
            draw_mask = ImageDraw.Draw(mask_large)
            draw_mask.ellipse((0, 0, aa_size - 1, aa_size - 1), fill=255)
            mask = mask_large.resize((WIDGET_SIZE, WIDGET_SIZE), Image.LANCZOS)

            self.icon_img = Image.new("RGBA", (WIDGET_SIZE, WIDGET_SIZE), (0, 0, 0, 0))
            self.icon_img.paste(img, (0, 0), mask)

        except Exception:
            self.icon_img = Image.new("RGBA", (WIDGET_SIZE, WIDGET_SIZE), (0, 0, 0, 0))
            draw = ImageDraw.Draw(self.icon_img)
            draw.ellipse((0, 0, WIDGET_SIZE - 1, WIDGET_SIZE - 1), fill=(59, 130, 246, 255))

    def _create_premium_frame(self, phase):
        """Create a premium frame with animated orbital ring and soft glow."""
        frame = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (1, 1, 1, 0))
        draw = ImageDraw.Draw(frame)

        cx, cy = CANVAS_SIZE // 2, CANVAS_SIZE // 2
        offset = (CANVAS_SIZE - WIDGET_SIZE) // 2

        r, g, b = self.glow_color

        # ── Layer 1: Soft ambient glow behind everything ──
        if self.agent_running:
            glow_intensity = 0.5 + 0.5 * math.sin(phase * 2)
            # Outer soft glow
            for i in range(12, 0, -1):
                alpha = int(glow_intensity * 18 * (12 - i) / 12)
                alpha = min(alpha, 60)
                radius = WIDGET_SIZE // 2 + i + 3
                draw.ellipse(
                    (cx - radius, cy - radius, cx + radius, cy + radius),
                    fill=(r, g, b, alpha),
                )

        # ── Layer 2: Animated orbital ring ──
        if self.agent_running:
            ring_radius = WIDGET_SIZE // 2 + 6
            # Draw the ring track (dim)
            draw.ellipse(
                (cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius),
                outline=(r, g, b, 30), width=2,
            )
            # Draw bright arc segment that rotates
            arc_start_deg = (phase * 57.3 * 2) % 360  # Convert radians to degrees
            arc_length = 90 + 30 * math.sin(phase * 3)
            draw.arc(
                (cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius),
                start=arc_start_deg,
                end=arc_start_deg + arc_length,
                fill=(r, g, b, 200), width=RING_WIDTH,
            )
            # Secondary arc (opposite side, dimmer)
            draw.arc(
                (cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius),
                start=(arc_start_deg + 180) % 360,
                end=(arc_start_deg + 180 + arc_length * 0.6) % 360,
                fill=(r, g, b, 80), width=2,
            )
        else:
            # Static ring when not running
            ring_radius = WIDGET_SIZE // 2 + 6
            draw.ellipse(
                (cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius),
                outline=(100, 100, 100, 60), width=2,
            )

        # ── Layer 3: Inner ring (border around icon) ──
        inner_ring_r = WIDGET_SIZE // 2 + 1
        if self.agent_running:
            border_alpha = int(150 + 80 * math.sin(phase * 4))
            draw.ellipse(
                (cx - inner_ring_r, cy - inner_ring_r, cx + inner_ring_r, cy + inner_ring_r),
                outline=(r, g, b, border_alpha), width=2,
            )
        else:
            draw.ellipse(
                (cx - inner_ring_r, cy - inner_ring_r, cx + inner_ring_r, cy + inner_ring_r),
                outline=(80, 80, 80, 100), width=1,
            )

        # ── Layer 4: The icon itself ──
        frame.paste(self.icon_img, (offset, offset), self.icon_img)

        # ── Layer 5: Status dot (bottom-right, small indicator) ──
        dot_radius = 5
        dot_x = cx + WIDGET_SIZE // 2 - 2
        dot_y = cy + WIDGET_SIZE // 2 - 2

        is_sleeping = self._read_sleep_state()
        if is_sleeping:
            dot_color = hex_to_rgb(COLORS["warning"])
        elif self.agent_running:
            dot_color = hex_to_rgb(COLORS["success"])
        else:
            dot_color = hex_to_rgb(COLORS["danger"])

        # Dot glow
        draw.ellipse(
            (dot_x - dot_radius - 2, dot_y - dot_radius - 2,
             dot_x + dot_radius + 2, dot_y + dot_radius + 2),
            fill=(*dot_color, 60),
        )
        # Dot
        draw.ellipse(
            (dot_x - dot_radius, dot_y - dot_radius,
             dot_x + dot_radius, dot_y + dot_radius),
            fill=(*dot_color, 255),
        )
        # Dot inner highlight
        draw.ellipse(
            (dot_x - dot_radius + 2, dot_y - dot_radius + 2,
             dot_x + dot_radius - 2, dot_y + dot_radius - 2),
            fill=(*tuple(min(c + 60, 255) for c in dot_color), 180),
        )

        return frame

    def _draw_widget(self, phase=0.0):
        frame = self._create_premium_frame(phase)
        self._tk_img = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(CANVAS_SIZE // 2, CANVAS_SIZE // 2, image=self._tk_img)

    def _pulse_animation(self):
        """Smooth animation loop."""
        self._frame_count += 1

        # Smooth phase progression
        self.pulse_phase += 0.04 if self.agent_running else 0.01

        # Hover boost
        if self._hover:
            self.pulse_phase += 0.02

        self._draw_widget(self.pulse_phase)

        interval = PULSE_SPEED if self.agent_running else PULSE_SPEED * 3
        self.root.after(interval, self._pulse_animation)

    # ─── Hover effects ───

    def _on_hover_enter(self, event):
        self._hover = True

    def _on_hover_leave(self, event):
        self._hover = False

    # ─── Drag ───

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    # ─── Sleep toggle ───

    def _toggle_sleep(self):
        """Toggle sleep/wake state for the agent."""
        current = self._read_sleep_state()
        new_state = not current

        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump({"is_sleeping": new_state, "exit_requested": False}, f)

        self.sleep_btn.config(
            text="💤" if new_state else "🟢",
        )

        if new_state:
            self._show_tooltip("Jessica is sleeping 💤", COLORS["warning"])
        else:
            self._show_tooltip("Jessica is awake!", COLORS["success"])

    # ─── Premium Tooltip ───

    def _show_tooltip(self, text, color=None, subtitle=None):
        """Show a glassmorphism-style tooltip near the widget."""
        color = color or COLORS["accent_glow"]

        # Destroy previous tooltip if exists
        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass

        tip = tk.Toplevel(self.root)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.configure(bg=COLORS["border"])
        self._tooltip_win = tip

        # Inner card
        inner = tk.Frame(tip, bg=COLORS["bg_card"], padx=0, pady=0)
        inner.pack(padx=1, pady=1)

        # Color accent bar on left side
        accent_bar = tk.Frame(inner, bg=color, width=3)
        accent_bar.pack(side="left", fill="y")

        # Content area
        content = tk.Frame(inner, bg=COLORS["bg_card"], padx=14, pady=8)
        content.pack(side="left")

        # Main text
        label = tk.Label(
            content, text=text,
            font=("Segoe UI", 11, "bold"),
            fg=color, bg=COLORS["bg_card"],
        )
        label.pack(anchor="w")

        # Subtitle (optional)
        if subtitle:
            sub = tk.Label(
                content, text=subtitle,
                font=("Segoe UI", 9),
                fg=COLORS["text_dim"], bg=COLORS["bg_card"],
            )
            sub.pack(anchor="w")

        # Position above widget
        tip.update_idletasks()
        tw = tip.winfo_reqwidth()
        wx = self.root.winfo_x()
        wy = self.root.winfo_y()
        tip.geometry(f"+{wx - tw + CANVAS_SIZE}+{wy - 55}")

        # Auto-dismiss
        tip.after(2800, lambda: self._dismiss_tooltip(tip))

    def _dismiss_tooltip(self, tip):
        try:
            tip.destroy()
            if self._tooltip_win == tip:
                self._tooltip_win = None
        except Exception:
            pass

    # ─── Status ───

    def _show_status(self, event):
        config = load_config()
        name = self.active_profile.get("name", "Jessica")
        voice = config.get("voice", "Aoede")
        is_sleeping = self._read_sleep_state()

        if self.process and self.process.poll() is None:
            status = "Running"
            color = COLORS["success"]
            emoji = "🟢"
        else:
            status = "Stopped"
            color = COLORS["danger"]
            emoji = "🔴"

        if is_sleeping:
            status = "Sleeping"
            color = COLORS["warning"]
            emoji = "💤"

        self._show_tooltip(
            f"{emoji}  {name}  —  {status}",
            color,
            subtitle=f"Voice: {voice}",
        )

    def _show_menu(self, event):
        # Rebuild menu each time to refresh checkmarks
        self._build_menu()
        self.menu.tk_popup(event.x_root, event.y_root)

    def _open_logs(self):
        if LOG_FILE.exists():
            os.startfile(str(LOG_FILE))

    def _quit(self):
        self._stop_agent()
        release_lock()
        self.root.destroy()

    # ─── Agent Process ───

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

        # Reset state.json so next launch starts clean
        try:
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump({"is_sleeping": False, "exit_requested": False}, f)
        except Exception:
            pass

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
        app = FloatingJessica()
        app.run()
    except Exception:
        release_lock()
