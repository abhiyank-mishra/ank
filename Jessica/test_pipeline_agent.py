
"""
Jessica AI — Latency Benchmark Test
Tests different VAD and model configurations to find the fastest setup.

Compares:
  - gemini-2.5-flash-native-audio-preview (your current model)
  - gemini-2.0-flash-live-001 (alternative realtime model)

Includes precise latency measurement for each response.

Usage:
  py test_pipeline_agent.py console
"""

import os
import sys
import asyncio
import logging
import time
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    AutoSubscribe,
)
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import google, silero
from livekit_tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = "You are Jessica, an AI voice assistant. Address user as Sir. Keep replies to 1 sentence max."

# ════════════════════════════════════════════════
# CHANGE THIS TO TEST DIFFERENT MODELS:
# ════════════════════════════════════════════════
# Option 1: "gemini-2.5-flash-native-audio-preview-09-2025" (your current model)
# Option 2: "gemini-2.5-flash-native-audio-preview-12-2025" (newer version)
# Option 3: "gemini-2.5-flash-native-audio-latest"          (latest stable)
# Option 4: "gemini-3.1-flash-live-preview"                 (next gen!)
# TEST_MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
TEST_MODEL = "gemini-3.1-flash-live-preview"
TEST_VOICE = "Charon"


async def entrypoint(ctx: JobContext):
    logging.info(f"=== LATENCY TEST MODE ===")
    logging.info(f"Model: {TEST_MODEL}")
    logging.info(f"Voice: {TEST_VOICE}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    model_kwargs = {"model": TEST_MODEL}
    # Some models (gemini-3.1) may not support custom voices — only add if supported
    if TEST_VOICE and "3.1" not in TEST_MODEL:
        model_kwargs["voice"] = TEST_VOICE
    
    model = google.realtime.RealtimeModel(**model_kwargs)

    jessica_agent = Agent(instructions=SYSTEM_PROMPT)

    # Aggressive VAD settings for minimum latency
    session = AgentSession(
        llm=model,
        vad=silero.VAD.load(
            activation_threshold=0.45,   # Very sensitive
            min_speech_duration=0.1,     # Detect short words
            min_silence_duration=0.25,   # React 250ms after silence
            prefix_padding_duration=0.15,
        ),
        tools=ALL_TOOLS,
    )

    # ── Precise Latency Measurement ──
    latency_log = []
    t_user_done = None

    @session.on("user_speech_committed")
    def on_user_committed(msg):
        nonlocal t_user_done
        t_user_done = time.time()
        logging.info(f"📥 User finished speaking")

    @session.on("agent_speech_started")
    def on_agent_started():
        nonlocal t_user_done
        if t_user_done:
            latency_ms = (time.time() - t_user_done) * 1000
            latency_log.append(latency_ms)
            avg = sum(latency_log) / len(latency_log)
            logging.info(f"⚡ Response latency: {latency_ms:.0f}ms  |  Avg: {avg:.0f}ms  |  Samples: {len(latency_log)}")
            t_user_done = None

    await session.start(agent=jessica_agent, room=ctx.room)
    logging.info(f"Jessica LATENCY TEST is LIVE. Speak and watch the console for timing.")
    await session.generate_reply(instructions="Say exactly: 'Latency test mode active, Sir. Speak something and I will respond as fast as possible.'")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="jessica_latency_test"))
