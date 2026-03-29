import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    AutoSubscribe,
    mcp,
)
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import google, silero
from livekit_tools import ALL_TOOLS

CONFIG_PATH = Path(__file__).parent / "config.json"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "system.md"


def load_config():
    """Load runtime config from config.json."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"voice": "Charon", "assistant_name": "Ank", "owner": "Abhiyank", "mcp_servers": []}


def load_system_prompt():
    """Load system prompt from system.md file."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are Ank, an AI voice assistant created by Abhiyank. Address the user as Sir."


def build_mcp_servers(config):
    """Build MCP server connections from config.json."""
    servers = []
    for srv in config.get("mcp_servers", []):
        url = srv.get("url", "")
        srv_type = srv.get("type", "sse").lower()
        name = srv.get("name", "MCP Server")

        if not url:
            continue

        try:
            if srv_type == "stdio":
                # For stdio servers, url is the command, args can be in config
                servers.append(mcp.MCPServerStdio(
                    command=url,
                    args=srv.get("args", []),
                ))
            else:
                # HTTP/SSE server
                headers = {}
                if srv.get("api_key"):
                    headers["Authorization"] = f"Bearer {srv['api_key']}"
                servers.append(mcp.MCPServerHTTP(url, headers=headers if headers else None))

            logging.info(f"🔌 MCP Server configured: {name} ({url})")
        except Exception as e:
            logging.warning(f"⚠️ Failed to configure MCP server '{name}': {e}")

    return servers


load_dotenv()

async def entrypoint(ctx: JobContext):
    config = load_config()
    voice = config.get("voice", "Charon")
    system_prompt = load_system_prompt()

    logging.info(f"🚀 Ank Agent connecting to room: {ctx.job.room.name} (voice: {voice})")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    model = google.realtime.RealtimeModel(
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        voice=voice,
    )

    # Build MCP servers from config
    mcp_servers = build_mcp_servers(config)

    ank_agent = Agent(
        instructions=system_prompt,
        mcp_servers=mcp_servers if mcp_servers else None,
    )

    session = AgentSession(
        llm=model,
        vad=silero.VAD.load(
            activation_threshold=0.65,
            min_speech_duration=0.2,
            min_silence_duration=0.6,
            prefix_padding_duration=0.4,
        ),
        tools=ALL_TOOLS
    )

    @session.on("transcription")
    def on_transcription(transcription):
        if transcription.is_final:
            msg_data = json.dumps({
                "type": "transcription",
                "text": transcription.text,
                "participant": "Ank"
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(msg_data))

    await session.start(agent=ank_agent, room=ctx.room)

    logging.info("🎤 Ank is LIVE.")
    await session.generate_reply(instructions="Say: 'Ank Initialized. Systems are online, Sir.'")

async def gui_connect(room_name):
    from livekit import api, rtc
    config = load_config()
    voice = config.get("voice", "Charon")
    system_prompt = load_system_prompt()

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    room = rtc.Room()
    token = api.AccessToken(api_key, api_secret) \
        .with_identity("Ank_Agent") \
        .with_grants(api.VideoGrants(room_join=True, room=room_name)) \
        .to_jwt()

    logging.info(f"🚀 Ank Agent connecting directly to GUI room: {room_name} (voice: {voice})")
    await room.connect(url, token)

    model = google.realtime.RealtimeModel(
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        voice=voice,
    )

    # Build MCP servers from config
    mcp_servers = build_mcp_servers(config)

    ank_agent = Agent(
        instructions=system_prompt,
        mcp_servers=mcp_servers if mcp_servers else None,
    )

    session = AgentSession(
        llm=model,
        vad=silero.VAD.load(
            activation_threshold=0.65,
            min_speech_duration=0.2,
            min_silence_duration=0.6,
            prefix_padding_duration=0.4,
        ),
        tools=ALL_TOOLS
    )

    @session.on("transcription")
    def on_transcription(transcription):
        if transcription.is_final:
            msg = json.dumps({"type": "transcription", "text": transcription.text, "participant": "Ank"})
            asyncio.create_task(room.local_participant.publish_data(msg))

    await session.start(agent=ank_agent, room=room)
    logging.info("🎤 Ank is LIVE.")
    await session.generate_reply(instructions="Say: 'Ank Initialized. Systems are online, Sir.'")

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "gui-connect":
        logging.basicConfig(level=logging.INFO)
        asyncio.run(gui_connect(sys.argv[2]))
    else:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="ank_agent"))
