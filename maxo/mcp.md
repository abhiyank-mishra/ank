# MCP Server Integration Guide for Ank

## What is MCP?
MCP (Model Context Protocol) is a standard that connects AI agents with external tools and data sources. It allows your agent to dynamically discover and execute tools exposed by external servers.

## How MCP Works in Ank
1. MCP server URLs are stored in `config.json` under `mcp_servers`
2. When the agent starts, it connects to each MCP server automatically
3. The tools from those servers appear alongside your existing tools
4. The LLM can call MCP tools just like it calls local function tools

## Supported Server Types

### HTTP/SSE Servers (Remote)
- Use the URL ending in `/sse` for Server-Sent Events transport
- Use the URL ending in `/mcp` for streamable HTTP transport
- Example: `https://your-server.com/sse`

### Stdio Servers (Local CLI)
- Local processes that communicate over stdin/stdout
- Example: `npx -y @modelcontextprotocol/server-filesystem /path/to/dir`

## Adding MCP Servers
Add MCP servers via the Ank Web UI Settings panel:
1. Click the ⚙️ gear icon
2. Go to the "MCP Servers" section
3. Enter server name, URL, and type (sse/stdio)
4. Click "Add Server"
5. Restart the agent for changes to take effect

## Configuration Format (config.json)
```json
{
    "mcp_servers": [
        {
            "name": "My N8N Server",
            "url": "https://my-n8n.com/mcp/sse",
            "type": "sse"
        }
    ]
}
```

## Environment Variables
You can also set MCP server URLs in `.env`:
```
MCP_SERVER_URL=https://your-server.com/sse
```

## Notes
- If an MCP server fails to connect, the agent still starts (graceful failure)
- MCP tools are combined with local function tools automatically
- The agent can call both local and MCP tools seamlessly
