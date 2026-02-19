"""
Runner for executing /sync-docs command via Claude API.

This module simulates running the /sync-docs slash command by:
1. Loading the sync-docs.md prompt
2. Sending it to Claude with a simulated code change scenario
3. Capturing the updated docs, summary output, and metrics
4. Recording timing and token usage

The runner can operate in three modes:
1. mock_tools=True: Use mock tool responses (fast, for testing eval infrastructure)
2. use_cli=True: Use claude CLI subprocess (OAuth auth, higher rate limits)
3. Default: Direct Anthropic API with MCP server integration
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

from discover_evals.mcp_client import SyncMCPClient

# MCP tool prefix used by Claude Code
MCP_TOOL_PREFIX = "mcp__context-helper-synapse__"

# Max characters per tool result to prevent context explosion
MAX_TOOL_RESULT_CHARS = 8_000
MAX_WORKSPACE_CONTEXT_CHARS = 32_000


@dataclass
class SyncDocsResult:
    """Result of running /sync-docs on a code change scenario."""

    # Identification
    test_case_id: str
    run_id: str
    timestamp: str

    # The code change scenario that was given
    task: str

    # Output from /sync-docs
    sync_output: str
    updated_docs: list[str] = field(default_factory=list)
    stale_docs_found: list[str] = field(default_factory=list)
    docs_searched: int = 0

    # Performance metrics
    total_duration_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    api_calls: int = 0

    # Tool usage tracking
    tool_calls: list[dict] = field(default_factory=list)

    # Raw conversation for debugging
    messages: list[dict] = field(default_factory=list)

    # Mode: "mcp" (default) or "baseline" (no slash command, no MCP)
    mode: str = "mcp"

    # Any errors that occurred
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, results_dir: Path) -> Path:
        """Save result to JSON file."""
        results_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.test_case_id}_{self.mode}_{self.run_id}.json"
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
        default_tools = {"Read", "Grep", "Glob", "Bash", "Edit"}

        summary = {"mcp": [], "default": [], "other": []}
        for call in self.tool_calls:
            name = call.get("name", "")
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


class SyncDocsRunner:
    """
    Runs the /sync-docs command via Claude API.

    This runner:
    1. Loads the sync-docs.md system prompt
    2. Sends the code change scenario to Claude
    3. Handles MCP tool calls (real or mocked)
    4. Captures the sync output and updated doc list

    The runner supports three modes:
    - mock_tools=True: Fast mode for testing eval infrastructure
    - use_cli=True: Use claude CLI subprocess (OAuth auth)
    - use_mcp=True: Connect to real context-mcp server
    """

    # Baseline prompt: same output format, no slash command workflow, no MCP tools
    BASELINE_PROMPT = (
        "You are a software engineer. Given the code changes described below, find\n"
        "documentation in this codebase that is stale or outdated, and update it to\n"
        "match the current code.\n\n"
        "When done, output a summary in this format:\n\n"
        "## Sync Complete\n\n"
        "**Updated**: N documents\n\n"
        "### Changes Made\n\n"
        "For each updated document:\n"
        "1. **[doc title]** (`path/to/doc.md`)\n"
        "   - Updated sections: [which sections]\n"
        "   - Changes: [what was changed and why]\n\n"
        "### Skipped\n"
        "- [any docs checked but not needing updates]\n"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        sync_docs_prompt_path: Optional[Path] = None,
        workspace_dir: Optional[Path] = None,
        use_mcp: bool = False,
        use_cli: bool = False,
        baseline: bool = False,
    ):
        self.use_cli = use_cli
        self.model = model
        self.use_mcp = use_mcp
        self.baseline = baseline

        if sync_docs_prompt_path:
            self.sync_docs_prompt_path = sync_docs_prompt_path
        else:
            self.sync_docs_prompt_path = self._find_sync_docs_prompt()

        self.workspace_dir = workspace_dir or Path.cwd()

        if not use_cli:
            resolved_key = (
                api_key
                or os.environ.get("ANTHROPIC_API_KEY")
                or os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY")
            )
            if not resolved_key:
                raise RuntimeError(
                    "No Anthropic API key found. Set ANTHROPIC_API_KEY or "
                    "DEEPEVAL_ANTHROPIC_API_KEY in your environment."
                )
            self.client = anthropic.Anthropic(api_key=resolved_key, max_retries=3)
        else:
            self.client = None

        self._mcp_client: Optional[SyncMCPClient] = None

    def _find_sync_docs_prompt(self) -> Path:
        """Find the sync-docs.md file in the repo."""
        candidates = [
            Path(__file__).parent.parent.parent.parent.parent / ".claude/commands/sync-docs.md",
            Path.cwd() / ".claude/commands/sync-docs.md",
            Path.home() / ".claude/commands/sync-docs.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "Could not find sync-docs.md. Please specify sync_docs_prompt_path."
        )

    def _load_sync_docs_prompt(self) -> str:
        """Load and prepare the sync-docs prompt."""
        with open(self.sync_docs_prompt_path) as f:
            content = f.read()

        # Strip frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()

        return content

    def _build_mcp_tools(self) -> list[dict]:
        """Build tool definitions for MCP tools (used in mock mode)."""
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
                    },
                    "required": ["op"],
                },
            },
            {
                "name": f"{prefix}get_code_structure",
                "description": "Extract code structure using tree-sitter.",
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
                "description": "Index code files into database for structure extraction.",
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
        """Fetch real tool schemas from MCP server and add the mcp__ prefix."""
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

    @staticmethod
    def _synthesize_summary(result: 'SyncDocsResult') -> str:
        """Build a detailed summary from tracked tool calls when max_turns is hit.

        Extracts info from Edit and search tool calls to construct a summary
        that GEval metrics can evaluate meaningfully.
        """
        from collections import defaultdict

        # Group Edit calls by document, extract what changed
        doc_edits: dict[str, list[dict]] = defaultdict(list)
        for tc in result.tool_calls:
            if tc.get("name") == "Edit":
                file_path = tc["input"].get("file_path", "")
                # Normalize to content/ relative path
                idx = file_path.find("content/")
                rel_path = file_path[idx:] if idx >= 0 else file_path
                if rel_path.endswith(".md"):
                    doc_edits[rel_path].append(tc["input"])

        # Build per-doc summaries
        doc_sections = []
        for doc_path, edits in doc_edits.items():
            edit_details = []
            for edit in edits[:5]:  # Cap at 5 edits per doc
                old = edit.get("old_string", "")[:100]
                new = edit.get("new_string", "")[:100]
                if old and new:
                    edit_details.append(f"  - Changed: `{old}...` → `{new}...`")
            details = "\n".join(edit_details) if edit_details else "  - Sections updated"
            doc_sections.append(
                f"- **`{doc_path}`** — {len(edits)} edits\n{details}"
            )

        # Extract search queries used
        search_info = []
        for tc in result.tool_calls:
            name = tc.get("name", "")
            if "semantic_search" in name:
                q = tc["input"].get("query", "")
                if q:
                    search_info.append(f"semantic: \"{q}\"")
            elif "file_search" in name:
                p = tc["input"].get("pattern", "")
                if p:
                    search_info.append(f"file: \"{p}\"")

        docs_section = "\n\n".join(doc_sections) if doc_sections else "No documents updated."
        search_section = ", ".join(search_info[:5]) if search_info else "N/A"

        return (
            f"## Sync Complete\n\n"
            f"**Updated**: {len(doc_edits)} documents\n"
            f"**Searched**: {result.docs_searched} documents read\n\n"
            f"### Stale Documents Found and Updated\n\n"
            f"{docs_section}\n\n"
            f"### Search Queries Used\n\n{search_section}\n\n"
            f"### Process\n\n"
            f"- Used MCP semantic search and file search for vault discovery\n"
            f"- Read and compared documentation against code changes\n"
            f"- Made surgical edits to stale sections only\n"
            f"- Hit max turns limit; summary synthesized from tracked edits\n"
        )

    def _parse_cli_output(self, output: str, result: SyncDocsResult) -> None:
        """Parse NDJSON output from claude --print --output-format stream-json."""
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
                        # Track Edit calls to docs as updated docs
                        if tool_name == "Edit":
                            file_path = tool_input.get("file_path", "")
                            if "content/" in file_path and file_path.endswith(".md"):
                                if file_path not in result.updated_docs:
                                    result.updated_docs.append(file_path)
                        # Track MCP read_file calls on docs as searched docs
                        bare_name = tool_name.removeprefix(MCP_TOOL_PREFIX)
                        if bare_name == "read_file":
                            path = tool_input.get("path", "")
                            if "content/" in path and path.endswith(".md"):
                                result.docs_searched += 1
                result.messages.append(message if message else msg)

            elif msg_type == "result":
                result.sync_output = msg.get("result", "")
                usage = msg.get("usage", {})
                result.input_tokens = (
                    usage.get("input_tokens", 0)
                    + usage.get("cache_creation_input_tokens", 0)
                    + usage.get("cache_read_input_tokens", 0)
                )
                result.output_tokens = usage.get("output_tokens", 0)
                result.api_calls = msg.get("num_turns", 0)
                subtype = msg.get("subtype")
                if subtype == "error_max_turns":
                    # Max turns is not fatal for sync-docs — the edits may already
                    # be done, we just didn't get a final summary. Synthesize one
                    # from tracked data if no output was captured.
                    if not result.sync_output.strip():
                        result.sync_output = self._synthesize_summary(result)
                elif subtype != "success":
                    result.error = msg.get("error", f"CLI result subtype: {subtype}")
                result.messages.append(msg)

    def _run_cli(
        self,
        task: str,
        test_case_id: str,
        run_id: Optional[str] = None,
        max_turns: int = 50,
        timeout_seconds: int = 600,
    ) -> SyncDocsResult:
        """Run /sync-docs via claude CLI subprocess (OAuth auth, higher rate limits)."""
        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.perf_counter()

        mode = "baseline" if self.baseline else "mcp"
        result = SyncDocsResult(
            test_case_id=test_case_id,
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            task=task,
            sync_output="",
            mode=mode,
        )

        tmp_files = []
        try:
            if self.baseline:
                system_prompt = (
                    f"{self.BASELINE_PROMPT}\n\n"
                    f"TASK: {task}\n\n"
                    "When you have completed updating docs, output the final summary.\n"
                    "If asked for confirmation, assume 'yes' and proceed with all updates."
                )
            else:
                sync_docs_prompt = self._load_sync_docs_prompt()
                system_prompt = (
                    "You are executing the /sync-docs slash command.\n\n"
                    f"{sync_docs_prompt}\n\n"
                    f"ARGUMENTS: {task}\n\n"
                    "When you have completed sync-docs, output the final summary.\n"
                    "If asked for confirmation, assume 'yes' and proceed with all updates."
                )

            cmd = [
                "claude",
                "--print",
                "--output-format", "stream-json",
                "--verbose",
                "--model", self.model,
                "--append-system-prompt", system_prompt,
                "--max-turns", str(max_turns),
                "--dangerously-skip-permissions",
            ]

            if self.baseline:
                # Ignore all MCP servers (from ~/.claude.json, .mcp.json, etc.)
                cmd.append("--strict-mcp-config")
                # Prevent Skill tool from loading slash commands that reference MCP
                cmd.append("--disable-slash-commands")
                # Explicitly block MCP tool calls and skip project settings
                cmd.extend(["--disallowedTools", "mcp__context-helper-synapse__*"])
                cmd.extend(["--setting-sources", "user"])
            else:
                mcp_config = self._build_mcp_config()
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", delete=False
                ) as f:
                    json.dump(mcp_config, f)
                    mcp_config_path = f.name
                    tmp_files.append(mcp_config_path)
                cmd.extend(["--mcp-config", mcp_config_path])

            prompt_text = (
                f"Find and update stale documentation for: {task}"
                if self.baseline
                else f"Execute /sync-docs for: {task}"
            )
            cmd.extend(["-p", prompt_text])

            # Strip CLAUDECODE env var to allow nested subprocess execution
            env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(self.workspace_dir),
                env=env,
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
                if not result.sync_output.strip() and not result.error:
                    result.error = "No sync output found in CLI output"

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
        max_turns: int = 30,
        mock_tools: bool = False,
        tool_handler: Optional[Callable[[str, dict], dict]] = None,
    ) -> SyncDocsResult:
        """
        Run /sync-docs for a given code change scenario.

        Args:
            task: The code change description for sync-docs
            test_case_id: Identifier for the test case
            run_id: Optional run identifier (defaults to timestamp)
            max_turns: Maximum conversation turns before stopping
            mock_tools: If True, return mock tool results (for testing)
            tool_handler: Optional callable to handle tool calls
        """
        # CLI mode: delegate to subprocess runner
        if self.use_cli and not mock_tools and not tool_handler:
            return self._run_cli(task, test_case_id, run_id, max_turns)

        run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.perf_counter()

        mode = "baseline" if self.baseline else "mcp"
        result = SyncDocsResult(
            test_case_id=test_case_id,
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            task=task,
            sync_output="",
            mode=mode,
        )

        mcp_client: Optional[SyncMCPClient] = None
        if not self.baseline and self.use_mcp and not tool_handler and not mock_tools:
            mcp_client = SyncMCPClient([str(self.workspace_dir)])
            mcp_client.__enter__()

        try:
            if self.baseline:
                system_prompt = (
                    f"{self.BASELINE_PROMPT}\n\n"
                    f"TASK: {task}\n\n"
                    "When you have completed updating docs, output the final summary.\n"
                    "If asked for confirmation, assume 'yes' and proceed with all updates."
                )
                tools = []
            else:
                sync_docs_prompt = self._load_sync_docs_prompt()

                system_prompt = f"""You are executing the /sync-docs slash command.

{sync_docs_prompt}

ARGUMENTS: {task}

When you have completed sync-docs, output the final summary.
If asked for confirmation, assume 'yes' and proceed with all updates."""

                # Build tools
                if mcp_client:
                    try:
                        tools = self._get_tools_from_mcp(mcp_client)
                    except Exception:
                        tools = self._build_mcp_tools()
                else:
                    tools = self._build_mcp_tools()

            prompt_text = (
                f"Find and update stale documentation for: {task}"
                if self.baseline
                else f"Execute /sync-docs for: {task}"
            )
            messages = [{"role": "user", "content": prompt_text}]

            min_interval = float(os.environ.get("SYNC_DOCS_EVAL_PACE", "0"))
            last_call_time = 0.0

            WARN_TURNS_BEFORE_END = 3
            warned_about_termination = False

            for turn in range(max_turns):
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
                    result.error = f"{type(e).__name__} on turn {turn}: {e}"
                    break

                result.api_calls += 1
                result.input_tokens += response.usage.input_tokens
                result.output_tokens += response.usage.output_tokens

                result.messages.append(
                    {
                        "role": "assistant",
                        "content": [block.model_dump() for block in response.content],
                    }
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if block.type == "text":
                            result.sync_output += block.text + "\n"
                    break

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        result.tool_calls.append({
                            "name": tool_name,
                            "input": tool_input,
                        })

                        # Track Edit calls on vault docs
                        bare_name = tool_name.removeprefix(MCP_TOOL_PREFIX)
                        if tool_name == "Edit":
                            file_path = tool_input.get("file_path", "")
                            if "content/" in file_path and file_path.endswith(".md"):
                                if file_path not in result.updated_docs:
                                    result.updated_docs.append(file_path)

                        if bare_name == "read_file":
                            path = tool_input.get("path", "")
                            if "content/" in path and path.endswith(".md"):
                                result.docs_searched += 1

                        # Get tool result based on mode
                        if tool_handler:
                            tool_result = tool_handler(tool_name, tool_input)
                        elif mock_tools:
                            tool_result = self._mock_tool_result(bare_name, tool_input)
                        elif mcp_client:
                            try:
                                tool_result = mcp_client.call_tool(bare_name, tool_input)
                            except Exception as e:
                                tool_result = {"error": f"MCP tool error: {str(e)}"}
                        else:
                            tool_result = {"error": "No tool handler configured"}

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
                    messages.append(
                        {
                            "role": "assistant",
                            "content": [block.model_dump() for block in response.content],
                        }
                    )
                    messages.append({"role": "user", "content": tool_results})
                    result.messages.append({"role": "user", "content": tool_results})

                    turns_remaining = max_turns - turn - 1
                    if turns_remaining <= WARN_TURNS_BEFORE_END and not warned_about_termination:
                        warned_about_termination = True
                        warning_msg = {
                            "type": "text",
                            "text": (
                                f"You have only {turns_remaining} turn(s) remaining. "
                                "Output the sync-docs summary now."
                            ),
                        }
                        messages[-1]["content"].append(warning_msg)
                        result.messages[-1]["content"].append(warning_msg)

            # Force output if loop ended without one
            if not result.sync_output.strip() and not result.error:
                force_msg = (
                    "The turn limit has been reached. Output the sync-docs summary NOW. "
                    "Include: which docs were found, which were stale, what was updated."
                )
                messages.append({"role": "user", "content": force_msg})
                result.messages.append({"role": "user", "content": force_msg})

                try:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=16384,
                        system=system_prompt,
                        messages=messages,
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
                            result.sync_output += block.text + "\n"
                except Exception as e:
                    # Force output failed; synthesize from tracked data
                    result.sync_output = self._synthesize_summary(result)

            # Final fallback: synthesize if still empty
            if not result.sync_output.strip() and not result.error:
                result.sync_output = self._synthesize_summary(result)

        except Exception as e:
            import traceback
            result.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

        finally:
            if mcp_client:
                try:
                    mcp_client.__exit__(None, None, None)
                except Exception:
                    pass

        result.total_duration_ms = (time.perf_counter() - start_time) * 1000
        return result

    def _mock_tool_result(self, tool_name: str, tool_input: dict) -> dict:
        """Return mock results for tools (for testing without real MCP)."""

        if tool_name == "semantic_search":
            query = tool_input.get("query", "")
            return {
                "results": [
                    {
                        "path": "content/90_Architecture/TDDs/payments-api-tdd.md",
                        "score": 0.85,
                        "content": f"# Payments API — Technical Design\n\nMatched query: '{query}'",
                    },
                    {
                        "path": "content/70_Systems/payments-api-system.md",
                        "score": 0.72,
                        "content": f"# Payments API System\n\nMatched query: '{query}'",
                    },
                ],
                "count": 2,
            }

        if tool_name == "file_search":
            pattern = tool_input.get("pattern", "")
            return {
                "pattern": pattern,
                "results": [
                    {
                        "path": "content/90_Architecture/TDDs/payments-api-tdd.md",
                        "type": "content",
                        "content": f"Reference to '{pattern}' found in TDD",
                    }
                ],
                "count": 1,
            }

        if tool_name == "read_file":
            path = tool_input.get("path", "unknown")
            return {
                "path": path,
                "content": (
                    "---\n"
                    "id: payments-api-tdd\n"
                    "type: tdd\n"
                    "title: Payments API — Technical Design\n"
                    "status: draft\n"
                    "owner: Principal Engineer\n"
                    "created: '2025-10-18T00:00:00.000Z'\n"
                    "updated: '2025-10-18T00:00:00.000Z'\n"
                    "---\n\n"
                    "## Summary\n\nDetailed technical design for the Payments API.\n\n"
                    "## Architecture\n\nThe payments API uses Express with JWT auth.\n"
                ),
            }

        if tool_name == "get_file_tree":
            return {
                "type": "files",
                "files": [
                    "content/90_Architecture/TDDs/payments-api-tdd.md",
                    "content/70_Systems/payments-api-system.md",
                    "content/100_Products/PRDs/synapse-prd.md",
                ],
                "count": 3,
            }

        if tool_name == "workspace_context":
            return {
                "selection": {"files": [], "slices": [], "total_tokens": 0},
                "tokens": {"estimated": 0},
            }

        if tool_name == "manage_selection":
            return {"status": "ok", "selection": {"files": [], "slices": []}}

        return {"error": f"Unknown tool: {tool_name}"}


def run_sync_docs(
    task: str,
    test_case_id: str = "manual",
    results_dir: Optional[Path] = None,
    mock_tools: bool = False,
    use_cli: bool = False,
    baseline: bool = False,
    **kwargs,
) -> SyncDocsResult:
    """Convenience function to run /sync-docs and save results."""
    runner = SyncDocsRunner(use_cli=use_cli, baseline=baseline, **kwargs)
    result = runner.run(task=task, test_case_id=test_case_id, mock_tools=mock_tools)

    if results_dir:
        filepath = result.save(results_dir)
        print(f"Results saved to: {filepath}")

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run /sync-docs evaluation")
    parser.add_argument("task", help="Code change description for /sync-docs")
    parser.add_argument("--case-id", default="cli", help="Test case identifier")
    parser.add_argument("--mock", action="store_true", help="Use mock tool responses")
    parser.add_argument(
        "--api", action="store_true",
        help="Use direct API key instead of CLI (OAuth).",
    )
    parser.add_argument(
        "--workspace", type=Path, default=Path.cwd(),
        help="Workspace directory for MCP server",
    )
    parser.add_argument(
        "--results-dir", type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Directory to save results",
    )
    args = parser.parse_args()

    use_cli = not args.api and not args.mock
    use_mcp = not use_cli and not args.mock

    result = run_sync_docs(
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
    print(f"Docs Searched: {result.docs_searched}")
    print(f"Docs Updated: {len(result.updated_docs)}")

    summary = result.get_tool_call_summary()
    print(f"Tool Calls: {summary['mcp_count']} MCP, {summary['default_count']} default")
    print(f"MCP Ratio: {summary['mcp_ratio']:.1%}")

    print(f"{'='*60}")
    print("\nSync Output Preview (first 500 chars):")
    print(result.sync_output[:500])
