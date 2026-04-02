"""
Jessica Doctor — System health checker & auto-setup script.
Run: python doctor.py
Owner: Abhiyank
"""

import os
import sys
import venv
import subprocess
import shutil
import json
import time
import webbrowser
from pathlib import Path


def ensure_memory_json(jessica_dir):
    """Check if memory.json exists, create it if missing."""
    memory_file = jessica_dir / "memory.json"
    if memory_file.exists():
        print("✅ [OK] memory.json found.")
    else:
        print("⚠️  [WARNING] memory.json not found. Creating default...")
        default_memory = {
            "owner": "Abhiyank",
            "owner_protected": True,
            "created_at": __import__("datetime").datetime.now().isoformat(),
            "facts": {
                "owner_name": "Abhiyank",
                "assistant_name": "Jessica",
                "assistant_creator": "Abhiyank",
                "persona": "Jessica, professional yet friendly, like J.A.R.V.I.S.",
            },
            "notes": [],
            "reminders": [],
            "preferences": {},
            "important": [],
        }
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(default_memory, f, indent=2, ensure_ascii=False)
        print("✅ [CREATED] memory.json with default structure.")


def setup_env_interactive(jessica_dir, py_exec):
    """Interactive .env setup — manual or auto (opens Chrome to LiveKit)."""
    env_file = jessica_dir / ".env"

    if env_file.exists():
        print("✅ [OK] .env file found.")
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                content = f.read()
            # Check if it's just a template with placeholder values
            if "your_api_key" in content or "your_google_api_key" in content or "your-livekit-url" in content:
                print("⚠️  [WARNING] .env has placeholder values — needs real keys!")
            else:
                return  # .env exists and has real values
        except Exception:
            return
    else:
        print("⚠️  [WARNING] .env file not found.")

    print()
    print("━" * 55)
    print("🔧 Environment Setup Required")
    print("━" * 55)
    print()
    print("  Jessica needs the following API keys:")
    print("  ├── LIVEKIT_URL       (from livekit.com)")
    print("  ├── LIVEKIT_API_KEY   (from livekit.com)")
    print("  ├── LIVEKIT_API_SECRET(from livekit.com)")
    print("  └── GOOGLE_API_KEY    (from aistudio.google.com)")
    print()
    print("  How do you want to set up?")
    print("  [1] MANUAL — I'll enter the keys myself")
    print("  [2] AUTO   — Open Chrome and guide me to LiveKit")
    print()

    choice = input("  Choose (1 or 2): ").strip()

    if choice == "2":
        # AUTO mode — open Chrome and navigate to LiveKit
        print()
        print("🌐 Opening LiveKit in your browser...")
        print("   Step 1: Sign up / Sign in at livekit.com")
        print("   Step 2: Create a new project (or use existing)")
        print("   Step 3: Go to Settings → Keys")
        print("   Step 4: Copy your URL, API Key, and API Secret")
        print()

        # Try to open in the system's default Chrome
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]

        chrome_opened = False
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                try:
                    subprocess.Popen([chrome_path, "https://cloud.livekit.io/"])
                    chrome_opened = True
                    break
                except Exception:
                    continue

        if not chrome_opened:
            # Fallback to default browser
            webbrowser.open("https://cloud.livekit.io/")

        print("   ✅ Browser opened! Get your LiveKit credentials.")
        print()

        time.sleep(2)

        # Also open Google AI Studio for API key
        print("🌐 Also opening Google AI Studio for your Google API Key...")
        if chrome_opened:
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    try:
                        subprocess.Popen([chrome_path, "https://aistudio.google.com/apikey"])
                        break
                    except Exception:
                        continue
        else:
            webbrowser.open("https://aistudio.google.com/apikey")

        print("   ✅ Browser opened! Get your Google API Key.")
        print()
        print("━" * 55)
        print("   Now enter your keys below (paste from browser):")
        print("━" * 55)
        print()

    elif choice == "1":
        print()
        print("━" * 55)
        print("   Enter your API keys below:")
        print("━" * 55)
        print()

    else:
        print("⚠️  Invalid choice. Creating template .env...")
        template = (
            "# Jessica AI — Environment Variables\n"
            "LIVEKIT_URL=wss://your-livekit-url.livekit.cloud\n"
            "LIVEKIT_API_KEY=your_api_key\n"
            "LIVEKIT_API_SECRET=your_api_secret\n"
            "GOOGLE_API_KEY=your_google_api_key\n"
        )
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(template)
        print("📝 [CREATED] .env template — please fill in your keys later!")
        return

    # Collect keys from user
    livekit_url = input("  LIVEKIT_URL (wss://...): ").strip()
    livekit_key = input("  LIVEKIT_API_KEY: ").strip()
    livekit_secret = input("  LIVEKIT_API_SECRET: ").strip()
    google_key = input("  GOOGLE_API_KEY: ").strip()

    # Validate
    if not all([livekit_url, livekit_key, livekit_secret, google_key]):
        print()
        print("⚠️  Some keys are empty. Creating .env with what you provided...")
        print("   You can edit Jessica/.env later to add missing keys.")

    # Write .env
    env_content = (
        "# Jessica AI — Environment Variables\n"
        f"LIVEKIT_URL={livekit_url or 'wss://your-livekit-url.livekit.cloud'}\n"
        f"LIVEKIT_API_KEY={livekit_key or 'your_api_key'}\n"
        f"LIVEKIT_API_SECRET={livekit_secret or 'your_api_secret'}\n"
        f"GOOGLE_API_KEY={google_key or 'your_google_api_key'}\n"
    )
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)

    print()
    print("✅ [SAVED] .env file created with your keys!")


def run_doctor():
    """Runs auto-setup process: checks venv, deps, .env, bat scripts."""
    print("👨‍⚕️ Jessica Doctor: Checking system health and configuration...\n")

    base_dir = Path(__file__).parent.absolute()
    jessica_dir = base_dir / "Jessica"
    venv_dir = base_dir / "venv"
    requirements_file = jessica_dir / "requirements.txt"

    # ── 0. Memory.json Check ──
    ensure_memory_json(jessica_dir)

    # ── 1. Virtual Environment Check ──
    if not venv_dir.exists():
        print("❌ [ISSUE] Virtual environment missing. Creating...")
        venv.create(venv_dir, with_pip=True)
        print("✅ [FIXED] Virtual environment created.")
    else:
        print("✅ [OK] Virtual environment is intact.")

    # OS specific python executable
    if os.name == 'nt':
        py_exec = venv_dir / "Scripts" / "python.exe"
        pip_exec = venv_dir / "Scripts" / "pip.exe"
        pyw_exec = venv_dir / "Scripts" / "pythonw.exe"
    else:
        py_exec = venv_dir / "bin" / "python"
        pip_exec = venv_dir / "bin" / "pip"
        pyw_exec = py_exec

    if not py_exec.exists():
        print("❌ [ERROR] Python executable not found in venv. Try deleting venv/ and rerunning doctor.")
        return

    # ── 2. Upgrade pip first ──
    print("⏳ Upgrading pip...")
    try:
        subprocess.run(
            [str(py_exec), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True, text=True, timeout=120
        )
        print("✅ [OK] pip is up to date.")
    except Exception as e:
        print(f"⚠️  pip upgrade skipped: {e}")

    # ── 3. Install dependencies from requirements.txt ──
    if not requirements_file.exists():
        print(f"❌ [ERROR] requirements.txt not found at: {requirements_file}")
        print("   Expected location: Jessica/requirements.txt")
        return

    print(f"⏳ Installing dependencies from {requirements_file.name}... (this may take a minute)")
    try:
        res = subprocess.run(
            [str(py_exec), "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True, text=True, timeout=600
        )
        if res.returncode != 0:
            print(f"❌ [ERROR] pip install failed:\n{res.stderr[-500:]}")
            return
        if "Successfully installed" in res.stdout:
            print("🔧 [FIXED] Missing dependencies installed.")
        else:
            print("✅ [OK] All dependencies are already installed.")
    except subprocess.TimeoutExpired:
        print("❌ [ERROR] pip install timed out after 10 minutes.")
        return
    except Exception as e:
        print(f"❌ [ERROR] Failed to install dependencies: {e}")
        return

    # ── 4. Install extra packages used in tools but not in requirements.txt ──
    extras = ["pyperclip", "opencv-python", "pynput"]
    for pkg in extras:
        try:
            res = subprocess.run(
                [str(py_exec), "-m", "pip", "install", pkg],
                capture_output=True, text=True, timeout=120
            )
            if "Successfully installed" in res.stdout:
                print(f"🔧 [FIXED] Installed extra package: {pkg}")
        except Exception:
            pass

    # ── 5. .env File Check (Interactive) ──
    setup_env_interactive(jessica_dir, py_exec)

    # ── 6. Verify critical imports inside venv ──
    print("\n⏳ Verifying critical imports...")
    critical_imports = [
        ("dotenv", "python-dotenv"),
        ("livekit.agents", "livekit-agents"),
        ("livekit.plugins.google", "livekit-plugins-google"),
        ("livekit.plugins.silero", "livekit-plugins-silero"),
        ("aiohttp", "aiohttp"),
        ("pyautogui", "pyautogui"),
        ("psutil", "psutil"),
        ("PIL", "Pillow"),
    ]
    all_ok = True
    for module, pkg_name in critical_imports:
        res = subprocess.run(
            [str(py_exec), "-c", f"import {module}"],
            capture_output=True, text=True, timeout=30
        )
        if res.returncode == 0:
            print(f"  ✅ {pkg_name}")
        else:
            print(f"  ❌ {pkg_name} — import failed!")
            all_ok = False

    if not all_ok:
        print("\n⚠️  Some imports failed. Try: venv\\Scripts\\pip install -r Jessica\\requirements.txt")

    # ── 7. Dynamic BAT Script Check ──
    bat_path = base_dir / "start_jessica.bat"
    expected_bat_content = f'@echo off\ncd /d "{jessica_dir}"\nstart "" "{pyw_exec}" tray_launcher.pyw\n'

    bat_matches = False
    if bat_path.exists():
        try:
            with open(bat_path, "r", encoding="utf-8") as f:
                if f.read() == expected_bat_content:
                    bat_matches = True
        except Exception:
            pass

    if bat_matches:
        print("✅ [OK] Startup script (start_jessica.bat) is correctly configured.")
    else:
        print("🔧 [FIXING] Creating/updating start_jessica.bat...")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(expected_bat_content)
        print("✅ [FIXED] start_jessica.bat updated with correct paths.")

    # ── 8. Windows Startup Folder Check ──
    if os.name == 'nt':
        appdata = os.environ.get("APPDATA")
        if appdata:
            startup_folder = Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"
            target_bat = startup_folder / "start_jessica.bat"

            target_matches = False
            if target_bat.exists():
                try:
                    with open(target_bat, "r", encoding="utf-8") as f:
                        if f.read() == expected_bat_content:
                            target_matches = True
                except Exception:
                    pass

            if target_matches:
                print("✅ [OK] Jessica is registered in Windows Autostart.")
            else:
                print("🔧 [FIXING] Adding Jessica to Windows Startup...")
                try:
                    shutil.copy2(bat_path, target_bat)
                    print("✅ [FIXED] Jessica added to Windows Startup!")
                except Exception as e:
                    print(f"❌ [ERROR] Failed to add to Startup folder: {e}")

            # Clean up old Ank startup script if exists
            old_bat = startup_folder / "start_ank.bat"
            if old_bat.exists():
                try:
                    old_bat.unlink()
                    print("🧹 [CLEANUP] Removed old start_ank.bat from Startup.")
                except Exception:
                    pass

    # ── 9. Automations directory ──
    automations_dir = base_dir / "automations"
    if not automations_dir.exists():
        automations_dir.mkdir(exist_ok=True)
        print("📁 [CREATED] automations/ directory for automation recordings.")
    else:
        print("✅ [OK] automations/ directory exists.")

    # ── Done ──
    print("\n" + "=" * 55)
    print("🎉 Jessica Doctor Report: System check complete!")
    print("=" * 55)

    if all_ok:
        print("✅ All systems HEALTHY — Jessica is ready to run!\n")
    else:
        print("⚠️  Some issues remain — check the errors above.\n")

    print("Press ENTER to start Jessica now (or close this window).")

    try:
        input()
        if bat_path.exists():
            subprocess.Popen([str(bat_path)], shell=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run_doctor()
