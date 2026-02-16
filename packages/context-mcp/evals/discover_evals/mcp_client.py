"""
MCP Client for connecting to the context-helper-synapse MCP server.

This module provides a client that spawns the context-mcp server as a subprocess
and allows calling MCP tools for the /discover evaluation framework.
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """
    Client for the context-mcp server.

    Spawns the MCP server as a subprocess and provides methods to call tools.
    """

    def __init__(
        self,
        workspace_dirs: list[str],
        server_path: Optional[Path] = None,
    ):
        """
        Initialize the MCP client.

        Args:
            workspace_dirs: Workspace directories for the MCP server to index
            server_path: Optional path to the context-mcp-server binary.
                         Defaults to finding it in the package dist.
        """
        self.workspace_dirs = workspace_dirs
        self.server_path = server_path or self._find_server()
        self._session: Optional[ClientSession] = None
        self._context_manager = None

    def _find_server(self) -> Path:
        """Find the context-mcp-server binary."""
        # Look in common locations relative to this file
        candidates = [
            # Relative to evals directory
            Path(__file__).parent.parent.parent / "dist/index.js",
            # Installed globally via npm
            Path("context-mcp-server"),
        ]

        for candidate in candidates:
            if candidate.exists() or str(candidate) == "context-mcp-server":
                return candidate

        raise FileNotFoundError(
            "Could not find context-mcp-server. "
            "Run 'npm run build' in packages/context-mcp first."
        )

    def _get_server_params(self) -> StdioServerParameters:
        """Get the parameters for spawning the MCP server."""
        # The server reads workspace dirs from environment variables
        env = {
            **os.environ,
            "NODE_NO_WARNINGS": "1",
            "WORKSPACE_DIRS": ",".join(self.workspace_dirs),
        }

        # Use the first workspace as cwd so relative paths resolve correctly
        cwd = self.workspace_dirs[0] if self.workspace_dirs else None

        if str(self.server_path).endswith(".js"):
            # Running from source/dist
            return StdioServerParameters(
                command="node",
                args=[str(self.server_path)],
                env=env,
                cwd=cwd,
            )
        else:
            # Running installed binary
            return StdioServerParameters(
                command=str(self.server_path),
                args=[],
                env=env,
                cwd=cwd,
            )

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry - start the MCP server."""
        server_params = self._get_server_params()

        # Create the stdio connection
        self._stdio_cm = stdio_client(server_params)
        read, write = await self._stdio_cm.__aenter__()

        # Create and initialize the session
        self._session_cm = ClientSession(read, write)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - stop the MCP server."""
        if self._session_cm:
            await self._session_cm.__aexit__(exc_type, exc_val, exc_tb)
        if self._stdio_cm:
            await self._stdio_cm.__aexit__(exc_type, exc_val, exc_tb)

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server with full schemas."""
        if not self._session:
            raise RuntimeError("Client not connected. Use 'async with' context manager.")

        result = await self._session.list_tools()
        tools = []
        for t in result.tools:
            tool_def = {
                "name": t.name,
                "description": t.description or "",
            }
            # Get input schema - handle both camelCase and snake_case attrs
            input_schema = getattr(t, 'inputSchema', None) or getattr(t, 'input_schema', None)
            if input_schema:
                # Convert to dict if it's a Pydantic model or similar
                if hasattr(input_schema, 'model_dump'):
                    tool_def["input_schema"] = input_schema.model_dump()
                elif hasattr(input_schema, 'dict'):
                    tool_def["input_schema"] = input_schema.dict()
                else:
                    tool_def["input_schema"] = dict(input_schema) if input_schema else {}
            tools.append(tool_def)
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Call a tool on the MCP server.

        Args:
            name: Tool name (e.g., 'file_search', 'manage_selection')
            arguments: Tool arguments

        Returns:
            The tool result as a dict
        """
        if not self._session:
            raise RuntimeError("Client not connected. Use 'async with' context manager.")

        result = await self._session.call_tool(name, arguments)

        # Parse the result content
        if result.content and len(result.content) > 0:
            content = result.content[0]
            # The server returns JSON text
            if hasattr(content, 'text'):
                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return {"text": content.text}

        return {"result": "ok"}


class SyncMCPClient:
    """
    Synchronous wrapper for MCPClient.

    This provides a synchronous interface for use with the DiscoverRunner,
    which currently uses synchronous code.
    """

    def __init__(
        self,
        workspace_dirs: list[str],
        server_path: Optional[Path] = None,
    ):
        self.workspace_dirs = workspace_dirs
        self.server_path = server_path
        self._client: Optional[MCPClient] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def __enter__(self) -> "SyncMCPClient":
        """Start the MCP server."""
        # Create a new event loop for this context
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._client = MCPClient(self.workspace_dirs, self.server_path)
        self._loop.run_until_complete(self._client.__aenter__())

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the MCP server."""
        if self._client and self._loop:
            self._loop.run_until_complete(
                self._client.__aexit__(exc_type, exc_val, exc_tb)
            )
        if self._loop:
            self._loop.close()
            self._loop = None

    def list_tools(self) -> list[dict]:
        """List available tools."""
        if not self._client or not self._loop:
            raise RuntimeError("Client not started. Use 'with' context manager.")
        return self._loop.run_until_complete(self._client.list_tools())

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call a tool synchronously."""
        if not self._client or not self._loop:
            raise RuntimeError("Client not started. Use 'with' context manager.")
        return self._loop.run_until_complete(self._client.call_tool(name, arguments))


def create_mcp_tool_handler(workspace_dirs: list[str]) -> tuple[callable, callable]:
    """
    Create a tool handler function for use with DiscoverRunner.

    This returns a tuple of (tool_handler, cleanup_function).
    The cleanup function should be called when done to stop the MCP server.

    Args:
        workspace_dirs: Workspace directories for the MCP server

    Returns:
        Tuple of (tool_handler, cleanup)
    """
    client = SyncMCPClient(workspace_dirs)
    client.__enter__()

    def tool_handler(tool_name: str, tool_input: dict) -> dict:
        """Handle a tool call by forwarding to the MCP server."""
        return client.call_tool(tool_name, tool_input)

    def cleanup():
        """Stop the MCP server."""
        client.__exit__(None, None, None)

    return tool_handler, cleanup


if __name__ == "__main__":
    # Quick test of the MCP client
    import sys

    async def test_client():
        workspace = sys.argv[1] if len(sys.argv) > 1 else str(Path.cwd())
        print(f"Testing MCP client with workspace: {workspace}")

        async with MCPClient([workspace]) as client:
            # List tools
            tools = await client.list_tools()
            print(f"\nAvailable tools ({len(tools)}):")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description'][:60]}...")

            # Try a file search
            print("\nTesting file_search...")
            result = await client.call_tool("file_search", {
                "pattern": "runner",
                "mode": "path",
                "max_results": 5,
            })
            print(f"Search result: {json.dumps(result, indent=2)[:500]}")

    asyncio.run(test_client())
