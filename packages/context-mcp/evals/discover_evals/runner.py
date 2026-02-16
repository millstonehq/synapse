"""
Runner for executing /discover command via Claude API.

This module simulates running the /discover slash command by:
1. Loading the discover.md prompt
2. Sending it to Claude with the task
3. Capturing the handoff prompt output
4. Recording timing and token usage

The runner can operate in three modes:
1. mock_tools=True: Use mock tool responses (fast, for testing eval infrastructure)
2. mock_tools=False with tool_handler: Use custom tool handler
3. mock_tools=False, use_mcp=True: Use real MCP server (for actual evals)
"""

import os
import subprocess
import tempfile
import time
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable, Any
from datetime import datetime

import anthropic
import orjson

from .mcp_client import SyncMCPClient

# MCP tool prefix used by Claude Code
MCP_TOOL_PREFIX = "mcp__context-helper-synapse__"

# Max characters per tool result to prevent context explosion
# Most tools: 8K chars (~2K tokens). workspace_context: 32K (final export).
MAX_TOOL_RESULT_CHARS = 8_000
MAX_WORKSPACE_CONTEXT_CHARS = 32_000


@dataclass
class DiscoverResult:
    """Result of running /discover on a task."""

    # Identification
    test_case_id: str
    run_id: str
    timestamp: str

    # The task that was given
    task: str

    # Output from /discover
    handoff_prompt: str
    selected_files: list[str] = field(default_factory=list)
    selected_slices: list[dict] = field(default_factory=list)

    # Performance metrics
    total_duration_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0

    # Tool usage tracking
    tool_calls: list[dict] = field(default_factory=list)

    # Raw conversation for debugging
    messages: list[dict] = field(default_factory=list)

    # Any errors that occurred
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, results_dir: Path) -> Path:
        """Save result to JSON file."""
        results_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.test_case_id}_{self.run_id}.json"
        filepath = results_dir / filename
        with open(filepath, "wb") as f:
            f.write(orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2))
        return filepath

    def get_tool_call_summary(self) -> dict:
        """Get a summary of tool calls by category."""
        mcp_tools = {
            "file_search", "get_file_tree", "read_file", "manage_selection",
            "workspace_context", "get_code_structure", "semantic_search", "index_code",
        }
        default_tools = {"Read", "Grep", "Glob", "Bash"}

        summary = {"mcp": [], "default": [], "other": []}
        for call in self.tool_calls:
            name = call.get("name", "")
            # Strip MCP prefix for classification
            bare_name = name.removeprefix("mcp__context-helper-synapse__")
            if bare_name in mcp_tools:
                summary["mcp"].append(bare_name)
            elif bare_name in default_tools:
                summary["default"].append(bare_name)
            else:
                summary["other"].append(name)

        return {
            "mcp_count": len(summary["mcp"]),
            "default_count": len(summary["default"]),
            "other_count": len(summary["other"]),
            "mcp_tools": list(set(summary["mcp"])),
            "default_tools": list(set(summary["default"])),
            "mcp_ratio": (
                len(summary["mcp"]) / (len(summary["mcp"]) + len(summary["default"]))
                if (len(summary["mcp"]) + len(summary["default"])) > 0
                else 1.0
            ),
        }


class DiscoverRunner:
    """
    Runs the /discover command via Claude API.

    This runner:
    1. Loads the discover.md system prompt
    2. Sends the task to Claude
    3. Handles MCP tool calls (real or mocked)
    4. Captures the final handoff prompt

    The runner supports three modes:
    - mock_tools=True: Fast mode for testing eval infrastructure
    - use_mcp=True: Connect to real context-mcp server
    - tool_handler=fn: Custom tool handler function
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        discover_prompt_path: Optional[Path] = None,
        workspace_dir: Optional[Path] = None,
        use_mcp: bool = False,
        use_cli: bool = False,
    ):
        """
        Initialize the runner.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
            model: Claude model to use
            discover_prompt_path: Path to discover.md prompt file
            workspace_dir: Workspace directory for MCP server
            use_mcp: If True, use real MCP server for tool calls
            use_cli: If True, use claude CLI subprocess (OAuth auth, 5x higher rate limits)
        """
        self.use_cli = use_cli
        self.model = model
        self.use_mcp = use_mcp

        # Find the discover.md prompt
        if discover_prompt_path:
            self.discover_prompt_path = discover_prompt_path
        else:
            # Default: look in the synapse repo
            self.discover_prompt_path = self._find_discover_prompt()

        self.workspace_dir = workspace_dir or Path.cwd()

        # Only need API client for non-CLI mode
        if not use_cli:
            # Check multiple env var names for flexibility
            resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY")
            if not resolved_key:
                raise RuntimeError(
                    "No Anthropic API key found. Set ANTHROPIC_API_KEY or "
                    "DEEPEVAL_ANTHROPIC_API_KEY in your environment."
                )
            # Let the SDK handle rate limit retries with proper backoff
            self.client = anthropic.Anthropic(api_key=resolved_key, max_retries=3)
        else:
            self.client = None

        # MCP client (created per-run if use_mcp=True)
        self._mcp_client: Optional[SyncMCPClient] = None

    def _find_discover_prompt(self) -> Path:
        """Find the discover.md file in the repo."""
        # Try common locations
        candidates = [
            Path(__file__).parent.parent.parent.parent.parent / ".claude/commands/discover.md",
            Path.cwd() / ".claude/commands/discover.md",
            Path.home() / ".claude/commands/discover.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "Could not find discover.md. Please specify discover_prompt_path."
        )

    def _load_discover_prompt(self) -> str:
        """Load and prepare the discover prompt."""
        with open(self.discover_prompt_path) as f:
            content = f.read()

        # Strip frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        return content

    def _build_mcp_tools(self) -> list[dict]:
        """
        Build tool definitions for MCP tools (used in mock mode).

        Tool names include the mcp__context-helper-synapse__ prefix to match
        what the discover.md prompt expects.
        """
        prefix = MCP_TOOL_PREFIX
        return [
            {
                "name": f"{prefix}workspace_context",
                "description": "Get workspace context including selection, tokens, and file contents",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "What to include: selection, code, files, tree, tokens",
                        }
                    },
                },
            },
            {
                "name": f"{prefix}get_file_tree",
                "description": "Get workspace file tree structure",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["files", "roots"]},
                        "mode": {"type": "string", "enum": ["auto", "full", "folders"]},
                        "path": {"type": "string"},
                        "max_depth": {"type": "number"},
                    },
                    "required": ["type"],
                },
            },
            {
                "name": f"{prefix}file_search",
                "description": "Search files with FTS5 + BM25 ranking for content, fast file system search for paths",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "mode": {"type": "string", "enum": ["auto", "path", "content", "both"]},
                        "include_content": {"type": "boolean"},
                        "max_results": {"type": "number"},
                        "filter": {
                            "type": "object",
                            "properties": {
                                "extensions": {"type": "array", "items": {"type": "string"}},
                                "exclude": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "required": ["pattern"],
                },
            },
            {
                "name": f"{prefix}semantic_search",
                "description": "Hybrid semantic + lexical search using embeddings and FTS5",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "mode": {"type": "string", "enum": ["hybrid", "semantic", "lexical"]},
                        "include_content": {"type": "boolean"},
                        "max_results": {"type": "number"},
                        "filter": {
                            "type": "object",
                            "properties": {
                                "extensions": {"type": "array", "items": {"type": "string"}},
                                "exclude": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": f"{prefix}read_file",
                "description": "Read file contents with optional line range",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "start_line": {"type": "number"},
                        "end_line": {"type": "number"},
                    },
                    "required": ["path"],
                },
            },
            {
                "name": f"{prefix}manage_selection",
                "description": "Manage context selection - add/remove files, track what will be sent to LLM",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "op": {
                            "type": "string",
                            "enum": ["get", "add", "remove", "set", "clear", "preview", "promote", "demote"],
                        },
                        "paths": {"type": "array", "items": {"type": "string"}},
                        "mode": {"type": "string", "enum": ["full", "slices", "codemap_only"]},
                        "slices": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "ranges": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "startLine": {"type": "number"},
                                                "endLine": {"type": "number"},
                                                "description": {"type": "string"},
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "required": ["op"],
                },
            },
            {
                "name": f"{prefix}get_code_structure",
                "description": "Extract code structure using tree-sitter. Returns function signatures, class definitions, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "paths": {"type": "array", "items": {"type": "string"}},
                        "scope": {"type": "string", "enum": ["paths", "selected"]},
                    },
                    "required": ["paths"],
                },
            },
            {
                "name": f"{prefix}index_code",
                "description": "Index code files into database for structure extraction. Must be called before get_code_structure.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "paths": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["paths"],
                },
            },
        ]

    def _get_tools_from_mcp(self, mcp_client: SyncMCPClient) -> list[dict]:
        """
        Fetch real tool schemas from MCP server and add the mcp__ prefix.

        This ensures tool definitions match exactly what the server supports,
        while using the prefixed names that discover.md expects.
        """
        raw_tools = mcp_client.list_tools()
        tools = []
        for t in raw_tools:
            tool_def = {
                "name": f"{MCP_TOOL_PREFIX}{t['name']}",
                "description": t.get("description", ""),
                "input_schema": t.get("input_schema", {"type": "object", "properties": {}}),
            }
            tools.append(tool_def)
        return tools

    def _build_mcp_config(self) -> dict:
        """Build MCP server configuration for claude CLI --mcp-config flag."""
        server_path = Path(__file__).parent.parent.parent / "dist/index.js"
        if not server_path.exists():
            raise FileNotFoundError(
                f"Could not find context-mcp-server at {server_path}. "
                "Run 'npm run build' in packages/context-mcp first."
            )
        return {
            "mcpServers": {
                "context-helper-synapse": {
                    "command": "node",
                    "args": [str(server_path.resolve())],
                    "env": {
                        "WORKSPACE_DIRS": str(self.workspace_dir),
                    },
                }
            }
        }

    def _parse_cli_output(self, output: str, result: DiscoverResult) -> None:
        """Parse NDJSON output from claude --print --output-format stream-json.

        Each line is a JSON object. Key message types:
        - type: "system" - init info (tools, model, session)
        - type: "assistant" - contains message.content[] with tool_use/text blocks
          NOTE: stream-json may split a single API response into multiple assistant
          messages (text + tool_use separately). Use result message for token totals.
        - type: "result" - final result with handoff text, aggregate usage, and metadata
        """
        for line in output.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "assistant":
                # Extract tool calls from assistant messages
                message = msg.get("message", {})
                content = message.get("content", [])
                for block in content:
                    if block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        result.tool_calls.append({
                            "name": tool_name,
                            "input": tool_input,
                        })
                        # Track file selections
                        bare_name = tool_name.removeprefix(MCP_TOOL_PREFIX)
                        if bare_name == "manage_selection":
                            if tool_input.get("op") in ["add", "set"]:
                                if "paths" in tool_input:
                                    result.selected_files.extend(tool_input["paths"])
                                if "slices" in tool_input:
                                    result.selected_slices.extend(tool_input["slices"])
                result.messages.append(message if message else msg)

            elif msg_type == "result":
                result.handoff_prompt = msg.get("result", "")
                # Use aggregate usage from result (not per-message, which double-counts)
                usage = msg.get("usage", {})
                result.input_tokens = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                )
                result.output_tokens = usage.get("output_tokens", 0)
                result.api_calls = msg.get("num_turns", 0)
                if msg.get("subtype") != "success":
                    result.error = msg.get("error", f"CLI result subtype: {msg.get('subtype')}")
                result.messages.append(msg)

    def _run_cli(
        self,
        task: str,
        test_case_id: str,
        run_id: Optional[str] = None,
        max_turns: int = 50,
        timeout_seconds: int = 600,
    ) -> DiscoverResult:
        """Run /discover via claude CLI subprocess (OAuth auth, higher rate limits).

        Uses claude --print with --mcp-config to pass the context-mcp server
        configuration. Claude Code handles the multi-turn tool use internally.
        """
        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.perf_counter()

        result = DiscoverResult(
            test_case_id=test_case_id,
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            task=task,
            handoff_prompt="",
        )

        tmp_files = []
        try:
            # Build system prompt with discover instructions
            discover_prompt = self._load_discover_prompt()
            system_prompt = (
                "You are executing the /discover slash command.\n\n"
                f"{discover_prompt}\n\n"
                f"ARGUMENTS: {task}\n\n"
                "When you have completed discovery and built the handoff prompt, "
                "output it as your final message.\n"
                "The handoff prompt should be self-contained with all code inline."
            )

            # Write temp MCP config (only temp file needed)
            mcp_config = self._build_mcp_config()
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(mcp_config, f)
                mcp_config_path = f.name
                tmp_files.append(mcp_config_path)

            cmd = [
                "claude",
                "--print",
                "--output-format", "stream-json",
                "--verbose",
                "--model", self.model,
                "--mcp-config", mcp_config_path,
                "--append-system-prompt", system_prompt,
                "--max-turns", str(max_turns),
                "--dangerously-skip-permissions",
                "-p", f"Execute /discover for: {task}",
            ]

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(self.workspace_dir),
            )

            if proc.returncode != 0:
                result.error = (
                    f"claude CLI exited with code {proc.returncode}: "
                    f"{proc.stderr[:1000]}"
                )
            elif not proc.stdout.strip():
                result.error = "claude CLI produced no output"
            else:
                self._parse_cli_output(proc.stdout, result)
                if not result.handoff_prompt.strip() and not result.error:
                    result.error = "No handoff prompt found in CLI output"

        except subprocess.TimeoutExpired:
            result.error = f"claude CLI timed out after {timeout_seconds}s"
        except FileNotFoundError as e:
            if "claude" in str(e).lower():
                result.error = (
                    "claude CLI not found. Install Claude Code: "
                    "npm install -g @anthropic-ai/claude-code"
                )
            else:
                result.error = f"FileNotFoundError: {e}"
        except Exception as e:
            import traceback
            result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
        finally:
            for tmp_path in tmp_files:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

        result.total_duration_ms = (time.perf_counter() - start_time) * 1000
        return result

    @staticmethod
    def _truncate_tool_result(tool_name: str, result_str: str) -> str:
        """Truncate tool result to prevent context explosion."""
        # workspace_context gets a larger budget since it's the final export
        if "workspace_context" in tool_name:
            max_chars = MAX_WORKSPACE_CONTEXT_CHARS
        else:
            max_chars = MAX_TOOL_RESULT_CHARS

        if len(result_str) > max_chars:
            return result_str[:max_chars] + f"\n\n... [truncated, {len(result_str)} total chars]"
        return result_str

    def run(
        self,
        task: str,
        test_case_id: str,
        run_id: Optional[str] = None,
        max_turns: int = 25,
        mock_tools: bool = False,
        tool_handler: Optional[Callable[[str, dict], dict]] = None,
    ) -> DiscoverResult:
        """
        Run /discover for a given task.

        Args:
            task: The task description to discover context for
            test_case_id: Identifier for the test case
            run_id: Optional run identifier (defaults to timestamp)
            max_turns: Maximum conversation turns before stopping
            mock_tools: If True, return mock tool results (for testing)
            tool_handler: Optional callable to handle tool calls

        Tool Resolution Order:
        1. If use_cli=True (and no mock/handler override), delegate to CLI runner
        2. If tool_handler is provided, use it
        3. If mock_tools=True, use mock responses
        4. If self.use_mcp=True, use real MCP server
        5. Otherwise, return an error

        Returns:
            DiscoverResult with the handoff prompt and metrics
        """
        # CLI mode: delegate to subprocess runner (unless mock/handler needed)
        if self.use_cli and not mock_tools and not tool_handler:
            return self._run_cli(task, test_case_id, run_id, max_turns)

        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.perf_counter()

        result = DiscoverResult(
            test_case_id=test_case_id,
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            task=task,
            handoff_prompt="",
        )

        # Start MCP client if using real MCP
        mcp_client: Optional[SyncMCPClient] = None
        if self.use_mcp and not tool_handler and not mock_tools:
            mcp_client = SyncMCPClient([str(self.workspace_dir)])
            mcp_client.__enter__()

        try:
            # Load discover prompt
            discover_prompt = self._load_discover_prompt()

            # Build system prompt
            system_prompt = f"""You are executing the /discover slash command.

{discover_prompt}

ARGUMENTS: {task}

When you have completed discovery and built the handoff prompt, output it as your final message.
The handoff prompt should be self-contained with all code inline."""

            # Build tools - prefer real schemas from MCP server when available
            if mcp_client:
                try:
                    tools = self._get_tools_from_mcp(mcp_client)
                except Exception:
                    tools = self._build_mcp_tools()
            else:
                tools = self._build_mcp_tools()

            # Initial message
            messages = [{"role": "user", "content": f"Execute /discover for: {task}"}]

            # Conversation loop
            # Pacing between calls (env var in seconds, 0 = no pacing, let SDK retry)
            min_interval = float(os.environ.get("DISCOVER_EVAL_PACE", "0"))
            last_call_time = 0.0

            # Early termination: warn LLM when approaching max_turns
            WARN_TURNS_BEFORE_END = 3
            warned_about_termination = False

            for turn in range(max_turns):
                # Optional pacing between requests
                if min_interval > 0 and turn > 0:
                    elapsed = time.perf_counter() - last_call_time
                    if elapsed < min_interval:
                        time.sleep(min_interval - elapsed)

                try:
                    last_call_time = time.perf_counter()
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=16384,
                        system=system_prompt,
                        tools=tools,
                        messages=messages,
                    )
                except (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
                    # SDK already retried max_retries times; log and stop
                    result.error = f"{type(e).__name__} on turn {turn}: {e}"
                    break

                result.api_calls += 1
                result.input_tokens += response.usage.input_tokens
                result.output_tokens += response.usage.output_tokens

                # Store message for debugging
                result.messages.append(
                    {
                        "role": "assistant",
                        "content": [block.model_dump() for block in response.content],
                    }
                )

                # Check if we're done (no tool use, just text)
                if response.stop_reason == "end_turn":
                    # Extract the final text as handoff prompt
                    for block in response.content:
                        if block.type == "text":
                            result.handoff_prompt += block.text + "\n"
                    break

                # Handle tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        # Track all tool calls for MCP usage metric
                        result.tool_calls.append({
                            "name": tool_name,
                            "input": tool_input,
                        })

                        # Track file selections - check with and without prefix
                        bare_name = tool_name.removeprefix(MCP_TOOL_PREFIX)
                        if bare_name == "manage_selection":
                            if tool_input.get("op") in ["add", "set"]:
                                if "paths" in tool_input:
                                    result.selected_files.extend(tool_input["paths"])
                                if "slices" in tool_input:
                                    result.selected_slices.extend(tool_input["slices"])

                        # Get tool result based on mode
                        if tool_handler:
                            # Custom handler takes priority
                            tool_result = tool_handler(tool_name, tool_input)
                        elif mock_tools:
                            # Mock mode - strip prefix for mock handler
                            tool_result = self._mock_tool_result(bare_name, tool_input)
                        elif mcp_client:
                            # Real MCP server - strip prefix since MCP uses bare names
                            try:
                                tool_result = mcp_client.call_tool(bare_name, tool_input)
                            except Exception as e:
                                tool_result = {"error": f"MCP tool error: {str(e)}"}
                        else:
                            tool_result = {"error": "No tool handler configured"}

                        # Serialize and truncate to prevent context explosion
                        result_str = json.dumps(tool_result)
                        result_str = self._truncate_tool_result(tool_name, result_str)

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_str,
                            }
                        )

                if tool_results:
                    # Add assistant message (required before tool results)
                    messages.append(
                        {
                            "role": "assistant",
                            "content": [block.model_dump() for block in response.content],
                        }
                    )
                    # Add tool results
                    messages.append({"role": "user", "content": tool_results})
                    result.messages.append({"role": "user", "content": tool_results})

                    # Early termination warning: inject message when approaching max_turns
                    turns_remaining = max_turns - turn - 1
                    if turns_remaining <= WARN_TURNS_BEFORE_END and not warned_about_termination:
                        warned_about_termination = True
                        warning_msg = {
                            "type": "text",
                            "text": (
                                f"⚠️ IMPORTANT: You have only {turns_remaining} turn(s) remaining. "
                                "You MUST output the complete handoff prompt on your next response. "
                                "If you haven't already, call workspace_context to export your selection, "
                                "then immediately output the handoff prompt. Do not make any other tool calls."
                            ),
                        }
                        # Append to the last user message (tool results)
                        messages[-1]["content"].append(warning_msg)
                        result.messages[-1]["content"].append(warning_msg)

            # Force handoff if loop ended without one
            if not result.handoff_prompt.strip() and not result.error:
                # Make one final API call WITHOUT tools to force the handoff output
                force_msg = (
                    "The turn limit has been reached. You MUST now output the complete handoff prompt "
                    "based on everything you've discovered so far. Output the handoff prompt NOW - "
                    "no more tool calls are available. Include all sections: TASK, ARCHITECTURE, "
                    "SELECTED CODE CONTEXT (with inline code), RELATIONSHIPS, and AMBIGUITIES."
                )
                messages.append({"role": "user", "content": force_msg})
                result.messages.append({"role": "user", "content": force_msg})

                try:
                    # Call without tools to force text output
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=16384,
                        system=system_prompt,
                        messages=messages,
                        # No tools parameter = can only output text
                    )
                    result.api_calls += 1
                    result.input_tokens += response.usage.input_tokens
                    result.output_tokens += response.usage.output_tokens

                    result.messages.append(
                        {
                            "role": "assistant",
                            "content": [block.model_dump() for block in response.content],
                        }
                    )

                    for block in response.content:
                        if block.type == "text":
                            result.handoff_prompt += block.text + "\n"

                except Exception as e:
                    result.error = f"Force handoff failed: {type(e).__name__}: {e}"

        except Exception as e:
            import traceback
            result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

        finally:
            # Clean up MCP client
            if mcp_client:
                try:
                    mcp_client.__exit__(None, None, None)
                except Exception:
                    pass  # Ignore cleanup errors

        result.total_duration_ms = (time.perf_counter() - start_time) * 1000
        return result

    def _mock_tool_result(self, tool_name: str, tool_input: dict) -> dict:
        """Return mock results for tools (for testing without real MCP)."""

        if tool_name == "workspace_context":
            return {
                "selection": {"files": [], "slices": [], "total_tokens": 0},
                "tokens": {"estimated": 0},
            }

        if tool_name == "get_file_tree":
            return {
                "type": "files",
                "files": [
                    "src/index.ts",
                    "src/auth/login.ts",
                    "src/auth/logout.ts",
                    "src/models/user.ts",
                    "src/routes/api.ts",
                    "package.json",
                    "README.md",
                ],
                "count": 7,
            }

        if tool_name == "file_search":
            pattern = tool_input.get("pattern", "")
            return {
                "pattern": pattern,
                "results": [
                    {
                        "path": "src/auth/login.ts",
                        "type": "content",
                        "line_range": [10, 50],
                        "content": f"// Mock content matching '{pattern}'",
                    }
                ],
                "count": 1,
            }

        if tool_name == "read_file":
            return {
                "path": tool_input.get("path", "unknown"),
                "content": "// Mock file content\nexport function example() {}",
            }

        if tool_name == "manage_selection":
            return {"status": "ok", "selection": {"files": [], "slices": []}}

        if tool_name == "get_code_structure":
            return {
                "structures": [
                    {
                        "path": "src/auth/login.ts",
                        "symbols": [
                            {"name": "login", "type": "function", "line": 10},
                            {"name": "validateCredentials", "type": "function", "line": 25},
                        ],
                    }
                ]
            }

        return {"error": f"Unknown tool: {tool_name}"}


def run_discovery(
    task: str,
    test_case_id: str = "manual",
    results_dir: Optional[Path] = None,
    mock_tools: bool = False,
    use_cli: bool = False,
    **kwargs,
) -> DiscoverResult:
    """Convenience function to run /discover and save results.

    Args:
        task: Task description for /discover
        test_case_id: Identifier for the test case
        results_dir: Directory to save results (None to skip saving)
        mock_tools: If True, use mock tool responses (API mode only)
        use_cli: If True, use claude CLI subprocess (OAuth, higher rate limits)
        **kwargs: Additional args passed to DiscoverRunner.__init__
    """
    runner = DiscoverRunner(use_cli=use_cli, **kwargs)
    result = runner.run(task=task, test_case_id=test_case_id, mock_tools=mock_tools)

    if results_dir:
        filepath = result.save(results_dir)
        print(f"Results saved to: {filepath}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run /discover evaluation")
    parser.add_argument("task", help="Task description for /discover")
    parser.add_argument("--case-id", default="cli", help="Test case identifier")
    parser.add_argument("--mock", action="store_true", help="Use mock tool responses")
    parser.add_argument(
        "--api", action="store_true",
        help="Use direct API key instead of CLI (OAuth). Default is CLI mode with higher rate limits.",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace directory for MCP server",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Directory to save results",
    )
    args = parser.parse_args()

    # Default to CLI mode (OAuth, 5x higher rate limits) unless --api or --mock
    use_cli = not args.api and not args.mock
    # When using API mode, enable MCP unless mocking
    use_mcp = not use_cli and not args.mock

    result = run_discovery(
        task=args.task,
        test_case_id=args.case_id,
        results_dir=args.results_dir,
        mock_tools=args.mock,
        use_cli=use_cli,
        use_mcp=use_mcp,
        workspace_dir=args.workspace,
    )

    print(f"\n{'='*60}")
    print(f"Test Case: {result.test_case_id}")
    print(f"Duration: {result.total_duration_ms:.0f}ms")
    print(f"API Calls: {result.api_calls}")
    print(f"Tokens: {result.input_tokens} in / {result.output_tokens} out")
    print(f"Files Selected: {len(result.selected_files)}")
    print(f"Slices Selected: {len(result.selected_slices)}")

    # Show tool usage summary
    summary = result.get_tool_call_summary()
    print(f"Tool Calls: {summary['mcp_count']} MCP, {summary['default_count']} default")
    print(f"MCP Ratio: {summary['mcp_ratio']:.1%}")

    print(f"{'='*60}")
    print("\nHandoff Prompt Preview (first 500 chars):")
    print(result.handoff_prompt[:500])
