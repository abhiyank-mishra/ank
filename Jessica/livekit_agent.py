import os
import sys
import asyncio
import logging
import json
import time
from pathlib import Path
from datetime import datetime
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
PERSONALITIES_PATH = Path(__file__).parent / "personalities.json"
MEMORY_PATH = Path(__file__).parent / "memory.json"
CONVERSATION_LOG_PATH = Path(__file__).parent / "conversation_history.json"


def load_config():
    """Load runtime config from config.json."""
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"voice": "Charon", "assistant_name": "Jessica", "owner": "Abhiyank", "mcp_servers": []}


def load_personalities():
    """Load personality profiles."""
    try:
        with open(PERSONALITIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active": "jessica", "profiles": {}}


def get_active_personality():
    """Get the currently active personality profile."""
    data = load_personalities()
    active_id = data.get("active", "jessica")
    profiles = data.get("profiles", {})
    return active_id, profiles.get(active_id, {})


def load_system_prompt():
    """Load base system prompt from system.md file."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are Jessica, an AI voice assistant created by Abhiyank. Address the user as Sir."


def load_memory():
    """Load persistent memory."""
    try:
        with open(MEMORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_conversation_history():
    """Load recent conversation history for context."""
    try:
        with open(CONVERSATION_LOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Only last 3 messages — bigger history = slower response
            return data.get("messages", [])[-3:]
    except Exception:
        return []


def save_conversation_message(role, text):
    """Save a message to conversation history."""
    try:
        try:
            with open(CONVERSATION_LOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"messages": []}

        data["messages"].append({
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only last 100 messages
        data["messages"] = data["messages"][-100:]

        with open(CONVERSATION_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def build_full_prompt():
    """Build the complete system prompt — kept MINIMAL for low latency."""
    _, personality = get_active_personality()
    base_prompt = load_system_prompt()
    memory = load_memory()

    # Use personality prompt if available, otherwise use base prompt
    prompt = personality.get("prompt", base_prompt) or base_prompt

    # Only add critical memory (facts + important) — skip notes/history to reduce tokens
    if memory:
        facts = memory.get("facts", {})
        important = memory.get("important", [])
        if facts or important:
            prompt += "\n\nKNOWN FACTS: "
            if facts:
                prompt += "; ".join(f"{k}={v}" for k, v in facts.items())
            if important:
                prompt += " | IMPORTANT: " + "; ".join(important[:3])

    # NOTE: Conversation history is NOT injected into the prompt.
    # The Gemini realtime model maintains its own session context.
    # Adding history here doubles token count and adds 5-8s latency.

    return prompt


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
                servers.append(mcp.MCPServerStdio(
                    command=url,
                    args=srv.get("args", []),
                ))
            else:
                headers = {}
                if srv.get("api_key"):
                    headers["Authorization"] = f"Bearer {srv['api_key']}"
                servers.append(mcp.MCPServerHTTP(
                    url,
                    headers=headers if headers else None,
                    timeout=30,
                    client_session_timeout_seconds=30,
                ))

            logging.info(f"MCP Server configured: {name} ({url})")
        except Exception:
            logging.warning(f"MCP server '{name}' is not available, skipping.")

    return servers


def safe_build_agent(system_prompt, config):
    """Build agent with MCP servers, gracefully falling back if MCP fails."""
    # NOTE: MCP servers disabled for gemini-3.1 compatibility.
    # N8N MCP tools have complex schemas that trigger 1007 "invalid argument" errors.
    # The Agent(mcp_servers=...) API is also deprecated — migrate to MCPToolset later.
    # try:
    #     mcp_servers = build_mcp_servers(config)
    #     if mcp_servers:
    #         return Agent(instructions=system_prompt, mcp_servers=mcp_servers)
    # except Exception:
    #     logging.warning("MCP not available - running without MCP tools.")

    return Agent(instructions=system_prompt)


load_dotenv()

async def entrypoint(ctx: JobContext):
    config = load_config()
    _, personality = get_active_personality()
    voice = personality.get("voice", config.get("voice", "Aoede"))
    system_prompt = build_full_prompt()
    greeting = personality.get("greeting", "Systems online, Sir.")
    name = personality.get("name", "Jessica")

    logging.info(f"Agent [{name}] connecting to room: {ctx.job.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # NOTE: gemini-3.1-flash-live-preview does NOT support 'voice' param via LiveKit plugin.
    # Passing it causes persistent 1007 "invalid argument" errors.
    model = google.realtime.RealtimeModel(
        model="gemini-3.1-flash-live-preview",
    )

    jessica_agent = safe_build_agent(system_prompt, config)

    session = AgentSession(
        llm=model,
        vad=silero.VAD.load(
            activation_threshold=0.45,
            min_speech_duration=0.1,
            min_silence_duration=0.25,
            prefix_padding_duration=0.15,
        ),
        tools=ALL_TOOLS
    )

    @session.on("transcription")
    def on_transcription(transcription):
        if transcription.is_final:
            save_conversation_message(name, transcription.text)

    await session.start(agent=jessica_agent, room=ctx.room)
    logging.info(f"{name} is LIVE.")

    # Wait for connection to fully stabilize (gemini-3.1 has a transient 1007 on first connect)
    await asyncio.sleep(8)
    try:
        await session.generate_reply(instructions=f"Say: '{greeting}'")
    except Exception:
        logging.warning("Greeting failed — connection still stabilizing.")

async def gui_connect(room_name):
    from livekit import api, rtc
    config = load_config()
    _, personality = get_active_personality()
    voice = personality.get("voice", config.get("voice", "Aoede"))
    system_prompt = build_full_prompt()
    greeting = personality.get("greeting", "Systems online, Sir.")
    name = personality.get("name", "Jessica")

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    room = rtc.Room()
    token = api.AccessToken(api_key, api_secret) \
        .with_identity(f"{name}_Agent") \
        .with_grants(api.VideoGrants(room_join=True, room=room_name)) \
        .to_jwt()

    logging.info(f"Agent [{name}] connecting to GUI room: {room_name} (voice: {voice})")
    await room.connect(url, token)

    model = google.realtime.RealtimeModel(
        model="gemini-3.1-flash-live-preview",
    )

    jessica_agent = safe_build_agent(system_prompt, config)

    session = AgentSession(
        llm=model,
        vad=silero.VAD.load(
            activation_threshold=0.45,
            min_speech_duration=0.1,
            min_silence_duration=0.25,
            prefix_padding_duration=0.15,
        ),
        tools=ALL_TOOLS
    )

    last_user_speech_time = time.time()

    async def idle_checker_gui():
        last_known_sleep_state = False
        while True:
            await asyncio.sleep(5)
            state_file = Path(__file__).parent / "state.json"
            is_sleeping = False
            if state_file.exists():
                try:
                    with open(state_file, "r", encoding="utf-8") as f:
                        is_sleeping = json.load(f).get("is_sleeping", False)
                except Exception: pass
            
            # If sleep state was changed externally (e.g. via GUI), tell the agent so it knows
            if is_sleeping != last_known_sleep_state:
                if is_sleeping:
                    try:
                        await session.generate_reply(instructions="You are now in SLEEP MODE. Mute yourself. IGNORE ALL SPEECH from now on, unless the user says your wake word 'Jessica'. Say NOTHING right now, just enter sleep mode.")
                    except Exception: pass
                else:
                    try:
                        await session.generate_reply(instructions="You have been WOKEN UP from sleep mode. You can now listen and respond normally. Greet the user briefly.")
                    except Exception: pass
                last_known_sleep_state = is_sleeping
                
            if not is_sleeping and (time.time() - last_user_speech_time > 180):
                try:
                    with open(state_file, "w", encoding="utf-8") as f:
                        json.dump({"is_sleeping": True}, f)
                    last_known_sleep_state = True
                    await session.generate_reply(instructions="The user has been idle for over 3 minutes. BRIEFLY tell them you are entering sleep mode to save energy, and do it. Then IGNORE all speech until they say your wake word 'Jessica'.")
                except Exception: pass

    asyncio.create_task(idle_checker_gui())

    @session.on("transcription")
    def on_transcription(transcription):
        nonlocal last_user_speech_time
        if transcription.is_final:
            last_user_speech_time = time.time()
            save_conversation_message(name, transcription.text)
            msg = json.dumps({"type": "transcription", "text": transcription.text, "participant": name})
            asyncio.create_task(room.local_participant.publish_data(msg))

    await session.start(agent=jessica_agent, room=room)
    logging.info(f"{name} is LIVE.")
    await session.generate_reply(instructions=f"Say: '{greeting}'")

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "gui-connect":
        logging.basicConfig(level=logging.INFO)
        asyncio.run(gui_connect(sys.argv[2]))
    else:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="jessica_agent"))
