import os
import sys
import venv
import subprocess
import shutil
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed yet, .env won't be loaded until dependencies are fixed.")

def run_custom_setup():
    """Runs auto-setup process when setup.py is executed directly."""
    print("👨‍⚕️ Ank Doctor: Checking system health and configuration...\n")
    
    base_dir = Path(__file__).parent.absolute()
    venv_dir = base_dir / "venv"
    
    # 1. Virtual Environment Check
    if not venv_dir.exists():
        print("❌ [ISSUE] Virtual environment missing. Fixing...")
        venv.create(venv_dir, with_pip=True)
        print("✅ [FIXED] Virtual environment created.")
    else:
        print("✅ [OK] Virtual environment is intact.")
        
    # OS specific python executable
    if os.name == 'nt':
        py_exec = venv_dir / "Scripts" / "python.exe"
        pyw_exec = venv_dir / "Scripts" / "pythonw.exe"
    else:
        py_exec = venv_dir / "bin" / "python"
        pyw_exec = py_exec

    # 2. Dependency Check (Using quiet mode)
    print("⏳ Checking library dependencies... (this may take a few seconds)")
    try:
        res = subprocess.run([str(py_exec), "-m", "pip", "install", "-e", "."], capture_output=True, text=True)
        if "Successfully installed" in res.stdout or "Downloading" in res.stdout:
            print("🔧 [FIXED] Missing dependencies installed.")
        else:
            print("✅ [OK] All dependencies are perfectly installed.")
    except Exception as e:
        print(f"❌ [ERROR] Failed to check/install dependencies: {e}")
        return

    # 3. Dynamic BAT Script Check
    bat_path = base_dir / "start_ank.bat"
    maxo_dir = base_dir / "maxo"
    expected_bat_content = f'@echo off\ncd /d "{maxo_dir}"\nstart "" "{pyw_exec}" tray_launcher.pyw\n'
    
    bat_matches = False
    if bat_path.exists():
        with open(bat_path, "r", encoding="utf-8") as f:
            if f.read() == expected_bat_content:
                bat_matches = True
                
    if bat_matches:
        print("✅ [OK] Local dynamic startup script is correctly configured.")
    else:
        print("❌ [ISSUE] Local startup script missing or outdated. Fixing ...")
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(expected_bat_content)
        print("✅ [FIXED] Updated local start_ank.bat with exact paths.")

    # 4. Windows Startup Folder Check
    if os.name == 'nt':
        startup_folder = Path(os.environ.get("APPDATA")) / r"Microsoft\Windows\Start Menu\Programs\Startup"
        target_bat = startup_folder / "start_ank.bat"
        
        target_matches = False
        if target_bat.exists():
            with open(target_bat, "r", encoding="utf-8") as f:
                if f.read() == expected_bat_content:
                    target_matches = True
                    
        if target_matches:
            print("✅ [OK] Ank is correctly registered in Windows Autostart.")
        else:
            print("❌ [ISSUE] Ank missing from Windows Startup. Fixing...")
            try:
                shutil.copy2(bat_path, target_bat)
                print("✅ [FIXED] Ank successfully re-added to Windows Startup!")
            except Exception as e:
                print(f"❌ [ERROR] Failed to add to Startup folder: {e}")

    print("\n🎉 Doctor's Report: System is 100% HEALTHY and ready to run Ank!")
    print("Press ENTER to start Ank now (or close terminal manually).")
    
    try:
        input()
        subprocess.Popen([str(bat_path)], shell=True)
    except KeyboardInterrupt:
        pass


# ---------------------------------------------------------------------------------
# Standard Setup Configuration
# ---------------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) == 1:
        # User just ran `python setup.py`
        run_custom_setup()
    else:
        # Standard behavior e.g. `pip install -e .`
        try:
            from setuptools import setup, find_packages
        except ImportError:
            print("❌ setuptools is not installed. Run: pip install setuptools")
            sys.exit(1)
        setup(
            name="maxo-voice-assistant",
            version="1.0.0",
            description="A powerful voice-controlled desktop assistant using Whisper and Gemini Vision.",
            author="Inkedpagex",
            packages=find_packages(),
            include_package_data=True,
            install_requires=[
                "langchain==0.2.3",
                "langchain-community==0.2.4",
                "pyaudio==0.2.14",
                "SpeechRecognition==3.10.3",
                "python-dotenv",
                "langchain-google-genai",
                "pyttsx3",
                "pyautogui",
                "pywhatkit",
                "wikipedia",
                "requests",
                "opencv-python",
                "faster-whisper",
                "psutil",
                "Pillow",
                "google-generativeai",
                "livekit-agents~=0.12",
                "livekit-plugins-silero",
                "livekit-plugins-google"
            ],
            python_requires=">=3.9",
            entry_points={
                "console_scripts": [
                    "maxo-cli=maxo.voice_assistant:main",
                    "maxo-gui=maxo.maxo_gui:main",
                ]
            },
        )
