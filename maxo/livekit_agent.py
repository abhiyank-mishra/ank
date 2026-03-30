import os
import sys
import asyncio
import logging
import json
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
        return {"voice": "Charon", "assistant_name": "Ank", "owner": "Abhiyank", "mcp_servers": []}


def load_personalities():
    """Load personality profiles."""
    try:
        with open(PERSONALITIES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"active": "ank", "profiles": {}}


def get_active_personality():
    """Get the currently active personality profile."""
    data = load_personalities()
    active_id = data.get("active", "ank")
    profiles = data.get("profiles", {})
    return active_id, profiles.get(active_id, {})


def load_system_prompt():
    """Load base system prompt from system.md file."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "You are Ank, an AI voice assistant created by Abhiyank. Address the user as Sir."


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
            # Return last 20 messages for context
            return data.get("messages", [])[-20:]
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
    """Build the complete system prompt with personality + memory + conversation history."""
    _, personality = get_active_personality()
    base_prompt = load_system_prompt()
    memory = load_memory()
    history = load_conversation_history()

    # Start with personality prompt (overrides base identity)
    if personality.get("prompt"):
        prompt = personality["prompt"]
    else:
        prompt = base_prompt

    # Add base capabilities from system.md (tools, web search, MCP section)
    # Extract everything after the identity section
    sections_to_keep = []
    in_section = False
    current_section = []
    for line in base_prompt.split("\n"):
        if line.strip().startswith("---") and in_section:
            sections_to_keep.append("\n".join(current_section))
            current_section = [line]
        elif line.strip().startswith("---"):
            in_section = True
            current_section = [line]
        elif in_section:
            current_section.append(line)
    if current_section:
        sections_to_keep.append("\n".join(current_section))

    if sections_to_keep:
        prompt += "\n\n" + "\n\n".join(sections_to_keep)

    # Add memory section
    if memory:
        prompt += "\n\n----------------------------------"
        prompt += "\nMEMORY - Things you remember"
        prompt += "\n----------------------------------\n"

        facts = memory.get("facts", {})
        if facts:
            prompt += "\nKnown Facts:\n"
            for key, value in facts.items():
                prompt += f"- {key}: {value}\n"

        notes = memory.get("notes", [])
        if notes:
            prompt += "\nNotes:\n"
            for note in notes[-10:]:
                prompt += f"- {note}\n"

        reminders = memory.get("reminders", [])
        if reminders:
            prompt += "\nActive Reminders:\n"
            for r in reminders:
                prompt += f"- {r}\n"

        important = memory.get("important", [])
        if important:
            prompt += "\nImportant:\n"
            for item in important:
                prompt += f"- {item}\n"

    # Add recent conversation history
    if history:
        prompt += "\n\n----------------------------------"
        prompt += "\nRECENT CONVERSATION HISTORY"
        prompt += "\n----------------------------------\n"
        prompt += "Here is what was discussed recently. Use this to maintain context:\n\n"
        for msg in history:
            role = msg.get("role", "unknown")
            text = msg.get("text", "")
            prompt += f"[{role}]: {text}\n"

        prompt += "\nIf there were any incomplete tasks mentioned above, proactively follow up on them."

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
    try:
        mcp_servers = build_mcp_servers(config)
        if mcp_servers:
            return Agent(instructions=system_prompt, mcp_servers=mcp_servers)
    except Exception:
        logging.warning("MCP not available - running without MCP tools.")

    return Agent(instructions=system_prompt)


load_dotenv()

async def entrypoint(ctx: JobContext):
    config = load_config()
    _, personality = get_active_personality()
    voice = personality.get("voice", config.get("voice", "Charon"))
    system_prompt = build_full_prompt()
    greeting = personality.get("greeting", "Systems online, Sir.")
    name = personality.get("name", "Ank")

    logging.info(f"Agent [{name}] connecting to room: {ctx.job.room.name} (voice: {voice})")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    model = google.realtime.RealtimeModel(
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        voice=voice,
    )

    ank_agent = safe_build_agent(system_prompt, config)

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
            save_conversation_message(name, transcription.text)
            msg_data = json.dumps({
                "type": "transcription",
                "text": transcription.text,
                "participant": name
            })
            asyncio.create_task(ctx.room.local_participant.publish_data(msg_data))

    await session.start(agent=ank_agent, room=ctx.room)

    logging.info(f"{name} is LIVE.")
    await session.generate_reply(instructions=f"Say: '{greeting}'")

async def gui_connect(room_name):
    from livekit import api, rtc
    config = load_config()
    _, personality = get_active_personality()
    voice = personality.get("voice", config.get("voice", "Charon"))
    system_prompt = build_full_prompt()
    greeting = personality.get("greeting", "Systems online, Sir.")
    name = personality.get("name", "Ank")

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
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        voice=voice,
    )

    ank_agent = safe_build_agent(system_prompt, config)

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
            save_conversation_message(name, transcription.text)
            msg = json.dumps({"type": "transcription", "text": transcription.text, "participant": name})
            asyncio.create_task(room.local_participant.publish_data(msg))

    await session.start(agent=ank_agent, room=room)
    logging.info(f"{name} is LIVE.")
    await session.generate_reply(instructions=f"Say: '{greeting}'")

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "gui-connect":
        logging.basicConfig(level=logging.INFO)
        asyncio.run(gui_connect(sys.argv[2]))
    else:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, agent_name="ank_agent"))
