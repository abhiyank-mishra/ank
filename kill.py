"""
Jessica Kill Switch — Complete Uninstaller (Self-Destructing)
Run: python kill.py
This will remove ALL Jessica components, then delete itself.
Only a goodbye .txt file will remain.
Owner: Abhiyank
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path


def kill_jessica_processes():
    """Kill all running Jessica-related processes."""
    try:
        import psutil
        killed = 0
        my_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.pid == my_pid:
                    continue
                cmdline = " ".join(proc.info.get('cmdline') or []).lower()
                if any(keyword in cmdline for keyword in [
                    'tray_launcher.pyw', 'livekit_agent.py',
                    'jessica', 'start_jessica.bat'
                ]):
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if killed:
            print(f"  🔪 Terminated {killed} Jessica process(es).")
        else:
            print(f"  ✅ No running Jessica processes found.")
    except ImportError:
        try:
            subprocess.run(
                ['taskkill', '/F', '/FI', 'WINDOWTITLE eq Jessica*'],
                capture_output=True, timeout=10
            )
        except Exception:
            pass
        print("  ⚠️  Process check done (psutil not available).")


def remove_startup_entries():
    """Remove Jessica from Windows startup — FIRST PRIORITY."""
    if os.name != 'nt':
        print("  ⏭  Skipping (not Windows).")
        return

    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("  ⚠️  Could not find APPDATA folder.")
        return

    startup_folder = Path(appdata) / r"Microsoft\Windows\Start Menu\Programs\Startup"

    for bat_name in ["start_jessica.bat", "start_ank.bat"]:
        bat_file = startup_folder / bat_name
        if bat_file.exists():
            try:
                bat_file.unlink()
                print(f"  🗑️  Removed {bat_name} from Windows Startup.")
            except Exception as e:
                print(f"  ❌ Failed to remove {bat_name}: {e}")


def nuke_everything(base_dir):
    """Remove EVERYTHING except this script (which self-destructs at the end)."""

    kill_script = Path(__file__).resolve()

    # ── Remove venv (biggest item) ──
    venv_dir = base_dir / "venv"
    if venv_dir.exists():
        print("  ⏳ Removing virtual environment...")
        try:
            shutil.rmtree(venv_dir, ignore_errors=True)
            print("  🗑️  venv/ removed.")
        except Exception as e:
            print(f"  ⚠️  venv removal partial: {e}")

    # ── Remove automations directory ──
    automations_dir = base_dir / "automations"
    if automations_dir.exists():
        try:
            shutil.rmtree(automations_dir, ignore_errors=True)
            print("  🗑️  automations/ removed.")
        except Exception:
            pass

    # ── Remove Jessica subdirectory entirely ──
    jessica_dir = base_dir / "Jessica"
    if jessica_dir.exists():
        print("  ⏳ Removing Jessica/ directory...")
        try:
            shutil.rmtree(jessica_dir, ignore_errors=True)
            print("  🗑️  Jessica/ removed.")
        except Exception as e:
            print(f"  ⚠️  Jessica/ removal partial: {e}")

    # ── Remove .git directory ──
    git_dir = base_dir / ".git"
    if git_dir.exists():
        try:
            shutil.rmtree(git_dir, ignore_errors=True)
            print("  🗑️  .git/ removed.")
        except Exception:
            pass

    # ── Remove all remaining files in base_dir (except this script) ──
    for item in base_dir.iterdir():
        if item.resolve() == kill_script:
            continue  # Skip self for now — will be deleted last
        if item.name == "goodbye.txt":
            continue  # Skip the goodbye file

        try:
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                print(f"  🗑️  {item.name}/ removed.")
            else:
                item.unlink()
                print(f"  🗑️  {item.name} removed.")
        except Exception as e:
            print(f"  ⚠️  Could not remove {item.name}: {e}")


def run_kill():
    """Main kill switch — scorched earth mode."""
    print()
    print("=" * 60)
    print("  💀  JESSICA KILL SWITCH — TOTAL WIPE  💀")
    print("=" * 60)
    print()
    print("  ⚠️  This will PERMANENTLY remove EVERYTHING:")
    print("  ├── All running Jessica processes")
    print("  ├── Windows auto-start entry")
    print("  ├── Virtual environment (venv/)")
    print("  ├── ALL source code & config files")
    print("  ├── .git repository")
    print("  └── This script itself (kill.py)")
    print()
    print("  📝 Only a goodbye.txt will remain.")
    print()

    confirm = input("  ❓ Type 'yes' to NUKE everything: ").strip().lower()

    if confirm not in ("yes", "y"):
        print("\n  ✅ Kill switch CANCELLED. Nothing was removed.")
        return

    print()
    base_dir = Path(__file__).parent.absolute()
    kill_script = Path(__file__).resolve()

    # ═══ Step 1: Kill all running processes ═══
    print("🔪 Step 1/5: Killing running processes...")
    kill_jessica_processes()
    time.sleep(1)
    print()

    # ═══ Step 2: Remove auto-start (FIRST!) ═══
    print("🚫 Step 2/5: Removing auto-start from Windows Startup...")
    remove_startup_entries()
    print()

    # ═══ Step 3: Create goodbye.txt BEFORE deleting everything ═══
    print("📝 Step 3/5: Writing goodbye note...")
    goodbye_path = base_dir / "goodbye.txt"
    try:
        with open(goodbye_path, "w", encoding="utf-8") as f:
            f.write("Thank You For Use And Throw ;)\n")
        print("  ✅ goodbye.txt created.")
    except Exception as e:
        print(f"  ⚠️  Could not create goodbye.txt: {e}")
    print()

    # ═══ Step 4: Nuke everything ═══
    print("💣 Step 4/5: Removing all files and directories...")
    nuke_everything(base_dir)
    print()

    # ═══ Step 5: Self-destruct ═══
    print("💥 Step 5/5: Self-destructing kill.py...")
    print()
    print("=" * 60)
    print("  ✅  KILL SWITCH COMPLETE!")
    print("  📝  Only goodbye.txt remains.")
    print("  👋  Thank You For Use And Throw ;)")
    print("=" * 60)
    print()

    # Schedule self-deletion via a background cmd process
    # (Can't delete ourselves while running, so we use a delayed cmd trick)
    if os.name == 'nt':
        # Create a tiny batch command that waits 2 seconds, then deletes kill.py
        bat_cmd = f'ping 127.0.0.1 -n 3 > nul & del /f /q "{kill_script}"'
        subprocess.Popen(
            f'cmd /c "{bat_cmd}"',
            shell=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        # On Linux/Mac, use a background process
        subprocess.Popen(
            f'sleep 2 && rm -f "{kill_script}"',
            shell=True,
        )

    print("  kill.py will self-delete in 3 seconds...")
    time.sleep(1)


if __name__ == "__main__":
    run_kill()
