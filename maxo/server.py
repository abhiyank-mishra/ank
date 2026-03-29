"""
Ank Web Server — Serves the web UI and provides LiveKit token + settings API.
Owner: Abhiyank
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import webbrowser
from pathlib import Path

from dotenv import load_dotenv
from aiohttp import web

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# LiveKit credentials
LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")

WEB_DIR = Path(__file__).parent / "web"
CONFIG_PATH = Path(__file__).parent / "config.json"
AGENT_PROCESS = None


def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"voice": "Charon", "assistant_name": "Ank", "owner": "Abhiyank", "mcp_servers": []}


def save_config(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)


async def handle_token(request):
    """Generate a LiveKit JWT token for the web client."""
    from livekit import api

    data = await request.json()
    room_name = data.get("room", f"ank-room-{int(time.time())}")
    identity = data.get("identity", "Abhiyank")

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )

    return web.json_response(
        {"token": token, "url": LIVEKIT_URL, "room": room_name}
    )


async def handle_status(request):
    """Return server and agent status."""
    global AGENT_PROCESS
    agent_alive = AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None
    config = load_config()
    return web.json_response(
        {
            "server": "online",
            "agent": "running" if agent_alive else "stopped",
            "livekit_url": LIVEKIT_URL,
            "voice": config.get("voice", "Charon"),
            "mcp_servers": len(config.get("mcp_servers", [])),
        }
    )


async def handle_agent_start(request):
    """Start the LiveKit agent in dev mode."""
    global AGENT_PROCESS
    if AGENT_PROCESS and AGENT_PROCESS.poll() is None:
        return web.json_response({"status": "already_running"})

    start_agent_process()
    return web.json_response({"status": "started", "pid": AGENT_PROCESS.pid if AGENT_PROCESS else 0})


async def handle_agent_stop(request):
    """Stop the LiveKit agent."""
    global AGENT_PROCESS
    if AGENT_PROCESS and AGENT_PROCESS.poll() is None:
        AGENT_PROCESS.terminate()
        AGENT_PROCESS = None
        return web.json_response({"status": "stopped"})
    return web.json_response({"status": "not_running"})


# ── Settings API ──

async def handle_get_settings(request):
    """Return current settings."""
    config = load_config()
    return web.json_response(config)


async def handle_save_settings(request):
    """Save settings to config.json."""
    data = await request.json()
    config = load_config()

    if "voice" in data:
        config["voice"] = data["voice"]
    if "mcp_servers" in data:
        config["mcp_servers"] = data["mcp_servers"]
    if "assistant_name" in data:
        config["assistant_name"] = data["assistant_name"]

    save_config(config)
    return web.json_response({"status": "saved", "config": config})


async def handle_add_mcp_server(request):
    """Add an MCP server to config."""
    data = await request.json()
    config = load_config()
    server_entry = {
        "name": data.get("name", "Unnamed"),
        "url": data.get("url", ""),
        "type": data.get("type", "sse"),
    }
    config.setdefault("mcp_servers", []).append(server_entry)
    save_config(config)
    return web.json_response({"status": "added", "mcp_servers": config["mcp_servers"]})


async def handle_remove_mcp_server(request):
    """Remove an MCP server by index."""
    data = await request.json()
    idx = data.get("index", -1)
    config = load_config()
    servers = config.get("mcp_servers", [])
    if 0 <= idx < len(servers):
        removed = servers.pop(idx)
        save_config(config)
        return web.json_response({"status": "removed", "removed": removed, "mcp_servers": servers})
    return web.json_response({"status": "invalid_index"})


async def handle_index(request):
    """Serve the main page."""
    return web.FileResponse(WEB_DIR / "index.html")


def create_app():
    app = web.Application()

    # API routes
    app.router.add_post("/api/token", handle_token)
    app.router.add_get("/api/status", handle_status)
    app.router.add_post("/api/agent/start", handle_agent_start)
    app.router.add_post("/api/agent/stop", handle_agent_stop)

    # Settings API
    app.router.add_get("/api/settings", handle_get_settings)
    app.router.add_post("/api/settings", handle_save_settings)
    app.router.add_post("/api/mcp/add", handle_add_mcp_server)
    app.router.add_post("/api/mcp/remove", handle_remove_mcp_server)

    # Static files
    app.router.add_get("/", handle_index)
    app.router.add_static("/", WEB_DIR, show_index=True)

    return app


def start_agent_process():
    """Start the LiveKit agent process in dev mode."""
    global AGENT_PROCESS
    if AGENT_PROCESS and AGENT_PROCESS.poll() is None:
        print("  ⚡ Agent already running.")
        return

    agent_path = Path(__file__).parent / "livekit_agent.py"
    AGENT_PROCESS = subprocess.Popen(
        [sys.executable, str(agent_path), "dev"],
        cwd=str(Path(__file__).parent),
        env=os.environ.copy(),
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
    )
    print(f"  ⚡ Agent started (PID: {AGENT_PROCESS.pid})")


if __name__ == "__main__":
    PORT = int(os.getenv("ANK_PORT", 3000))
    print(f"\n╔══════════════════════════════════════╗")
    print(f"  ║    Ank Web Server — v2.0             ║")
    print(f"  ║    http://localhost:{PORT}           ║")
    print(f"  ║    Owner: Abhiyank                   ║")
    print(f"  ╚══════════════════════════════════════╝\n")

    # Auto-start agent
    print("  🚀 Auto-starting Ank Agent...")
    start_agent_process()

    app = create_app()

    async def on_startup(app):
        webbrowser.open(f"http://localhost:{PORT}")

    app.on_startup.append(on_startup)
    web.run_app(app, host="0.0.0.0", port=PORT, print=lambda *a: None)
