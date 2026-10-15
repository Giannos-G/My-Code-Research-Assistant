"""Connects to multiple MCP servers at once, merges their tools into a
single OpenAI-compatible tool list, and routes tool calls back to the
right server session."""

import os
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"
EXA_MCP_URL = "https://mcp.exa.ai/mcp"


class MultiMCP:
    """Holds live sessions to several MCP servers and exposes their tools
    as one combined, OpenAI-compatible tool list."""

    def __init__(self) -> None:
        self._stack = AsyncExitStack()
        self._sessions: dict[str, ClientSession] = {}
        self._tool_owner: dict[str, str] = {}
        self.openai_tools: list[dict] = []

    async def connect(self, server_name: str, url: str, headers: dict | None = None) -> None:
        http_client = create_mcp_http_client(headers=headers) if headers else None
        read, write = await self._stack.enter_async_context(
            streamable_http_client(url, http_client=http_client)
        )
        session = await self._stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self._sessions[server_name] = session

        tools_result = await session.list_tools()
        for tool in tools_result.tools:
            if tool.name in self._tool_owner:
                continue  # first server to register a tool name wins
            self._tool_owner[tool.name] = server_name
            self.openai_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema
                        or {"type": "object", "properties": {}},
                    },
                }
            )

    async def call_tool(self, name: str, arguments: dict) -> str:
        server_name = self._tool_owner.get(name)
        if server_name is None:
            return f"Unknown tool: {name}"
        session = self._sessions[server_name]
        result = await session.call_tool(name, arguments)
        parts = [getattr(item, "text", None) for item in result.content]
        parts = [p for p in parts if p]
        return "\n".join(parts) if parts else "(no output)"

    async def aclose(self) -> None:
        await self._stack.aclose()


async def connect_all() -> MultiMCP:
    """Connect to every configured MCP server and return the combined client."""
    multi = MultiMCP()

    github_token = os.environ.get("GITHUB_MCP_TOKEN")
    if github_token:
        await multi.connect(
            "github",
            GITHUB_MCP_URL,
            headers={
                "Authorization": f"Bearer {github_token}",
                "X-MCP-Toolsets": "context,repos,code_search",
                "X-MCP-Readonly": "true",
            },
        )

    exa_key = os.environ.get("EXA_API_KEY")
    if exa_key:
        await multi.connect("exa", f"{EXA_MCP_URL}?exaApiKey={exa_key}")

    return multi
