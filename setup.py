from setuptools import setup, find_packages

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
        "livekit-agents[silero,google]~=1.4",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "maxo-cli=maxo.voice_assistant:main",
            "maxo-gui=maxo.maxo_gui:main",
        ]
    },
)
