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
from pathlib import Path


def run_doctor():
    """Runs auto-setup process: checks venv, deps, .env, bat scripts."""
    print("👨‍⚕️ Jessica Doctor: Checking system health and configuration...\n")

    base_dir = Path(__file__).parent.absolute()
    jessica_dir = base_dir / "Jessica"
    venv_dir = base_dir / "venv"
    requirements_file = jessica_dir / "requirements.txt"
    env_file = jessica_dir / ".env"

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
    extras = ["pyperclip", "opencv-python"]
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

    # ── 5. .env File Check ──
    if env_file.exists():
        print("✅ [OK] .env file found.")
    else:
        print("⚠️  [WARNING] .env file not found. Creating template...")
        template = (
            "# Jessica AI — Environment Variables\n"
            "LIVEKIT_URL=wss://your-livekit-url.livekit.cloud\n"
            "LIVEKIT_API_KEY=your_api_key\n"
            "LIVEKIT_API_SECRET=your_api_secret\n"
            "GOOGLE_API_KEY=your_google_api_key\n"
        )
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(template)
        print("📝 [CREATED] .env template created at Jessica/.env — please fill in your keys!")

    # ── 6. Verify critical imports inside venv ──
    print("⏳ Verifying critical imports...")
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
