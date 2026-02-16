"""
Custom DeepEval metrics for evaluating /discover output.

These metrics use G-Eval (LLM-as-a-judge) to evaluate:
1. Context selection quality
2. Handoff prompt clarity and actionability
3. Architecture description accuracy

GEval model selection (checked in order):
1. OPENAI_API_KEY set → GPT-4o (higher rate limits, no contention with discovery)
2. ANTHROPIC_API_KEY set → Claude Sonnet (shares rate limit with API-mode discovery)
3. Neither → GEval metrics are skipped, only deterministic metrics run
"""

import os
from typing import Optional
from deepeval.metrics import GEval, BaseMetric
from deepeval.models import AnthropicModel, GPTModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


def _get_anthropic_api_key() -> Optional[str]:
    """Get Anthropic API key from environment variables."""
    return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY")


def _has_geval_api_key() -> bool:
    """Check if any API key is available for GEval metrics."""
    return bool(os.environ.get("OPENAI_API_KEY") or _get_anthropic_api_key())


def _get_eval_model():
    """Create the evaluation model, preferring OpenAI for higher rate limits.

    OpenAI is preferred because:
    - Higher default rate limits than low-tier Anthropic keys
    - No contention with CLI-mode discovery (which uses Anthropic OAuth)
    - No contention with API-mode discovery (which uses ANTHROPIC_API_KEY)
    """
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        return GPTModel(model="gpt-4o", api_key=openai_key)

    anthropic_key = _get_anthropic_api_key()
    if anthropic_key:
        return AnthropicModel(model="claude-sonnet-4-20250514", api_key=anthropic_key)

    raise RuntimeError(
        "No API key found for GEval metrics. Set OPENAI_API_KEY (preferred) "
        "or ANTHROPIC_API_KEY in your environment."
    )


class ContextRelevanceMetric(GEval):
    """
    Evaluates whether the selected context is relevant to the task.

    Checks:
    - Are the selected files/slices relevant to implementing the task?
    - Is there unnecessary context bloating the selection?
    - Are important files missing?
    """

    def __init__(self, threshold: float = 0.7, model=None, **kwargs):
        # kwargs absorbs extra params from deepeval's copy_metrics
        super().__init__(
            name="Context Relevance",
            model=model or _get_eval_model(),
            criteria="""Evaluate whether the context selection in the handoff prompt is appropriate for the given task.

Consider:
1. RELEVANCE: Are the selected files/code slices directly relevant to the task?
2. COMPLETENESS: Does the selection include all files necessary to understand and implement the task?
3. PRECISION: Is there unnecessary or tangential code that adds noise?
4. FOCUS: Does the selection stay focused on what's needed, or does it include entire files when slices would suffice?

A good context selection:
- Includes all files that would need to be modified or understood
- Uses minimal slices rather than full files when appropriate
- Doesn't include unrelated code that would distract from the task
- Provides enough surrounding context to understand the code structure""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,  # The task
                LLMTestCaseParams.ACTUAL_OUTPUT,  # The handoff prompt with context
            ],
            threshold=threshold,
        )


class ArchitectureClarityMetric(GEval):
    """
    Evaluates whether the architecture section clearly explains the codebase.

    The architecture section should help someone unfamiliar with the codebase
    understand the relevant structure for the task.
    """

    def __init__(self, threshold: float = 0.7, model=None, **kwargs):
        # kwargs absorbs extra params from deepeval's copy_metrics
        super().__init__(
            name="Architecture Clarity",
            model=model or _get_eval_model(),
            criteria="""Evaluate the quality of the architecture description in the handoff prompt.

The architecture section should:
1. STRUCTURE: Clearly describe the relevant parts of the codebase structure
2. ROLES: Explain what each relevant module/component does
3. PATTERNS: Identify design patterns or conventions used in the code
4. SCOPE: Focus on architecture relevant to the task, not exhaustive documentation

A good architecture section:
- Can be understood by someone unfamiliar with the codebase
- Explains WHY the code is structured this way, not just WHAT exists
- Highlights the specific areas relevant to implementing the task
- Uses clear, technical language without unnecessary jargon""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,  # The task
                LLMTestCaseParams.ACTUAL_OUTPUT,  # The handoff prompt
            ],
            threshold=threshold,
        )


class RelationshipMappingMetric(GEval):
    """
    Evaluates whether the relationships section correctly maps dependencies.

    The relationships should show how different parts of the code interact,
    data flows, and call hierarchies relevant to the task.
    """

    def __init__(self, threshold: float = 0.7, model=None, **kwargs):
        # kwargs absorbs extra params from deepeval's copy_metrics
        super().__init__(
            name="Relationship Mapping",
            model=model or _get_eval_model(),
            criteria="""Evaluate how well the handoff prompt maps relationships between code components.

The relationships section should:
1. DATA FLOW: Show how data moves between components
2. DEPENDENCIES: Identify which modules depend on which
3. CALL CHAINS: Map relevant function/method call hierarchies
4. INTERFACES: Show how components communicate (APIs, events, etc.)

A good relationships section:
- Uses clear notation (e.g., A -> B -> C for call chains)
- Focuses on relationships relevant to the task
- Identifies the entry points and exit points for the task
- Shows both direct and indirect dependencies that matter""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            threshold=threshold,
        )


class TaskActionabilityMetric(GEval):
    """
    Evaluates whether the handoff prompt enables implementation.

    This is the key metric: could someone implement the task from this prompt
    without needing to ask clarifying questions or search for more context?
    """

    def __init__(self, threshold: float = 0.7, model=None, **kwargs):
        # kwargs absorbs extra params from deepeval's copy_metrics
        super().__init__(
            name="Task Actionability",
            model=model or _get_eval_model(),
            criteria="""Evaluate whether the handoff prompt provides enough information to implement the task.

Consider:
1. SELF-CONTAINED: Is all necessary code included inline? Could this prompt work without access to the original codebase?
2. CLEAR TASK: Is the task clearly restated and scoped?
3. IMPLEMENTATION PATH: Is it clear where to start and what to modify?
4. CONTEXT SUFFICIENCY: Are all referenced files/functions included in the context?
5. AMBIGUITY HANDLING: Are ambiguities called out, or is the path forward clear?

A highly actionable prompt:
- Contains all code needed to understand the current state
- Makes clear what needs to change and where
- Doesn't leave the implementer guessing about patterns or conventions
- Could be handed to a different person/model to implement""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            threshold=threshold,
        )


class HandoffCompletenessMetric(GEval):
    """
    Evaluates structural completeness of the handoff prompt.

    Checks that all required sections are present and properly populated.
    """

    def __init__(self, threshold: float = 0.8, model=None, **kwargs):
        # kwargs absorbs extra params from deepeval's copy_metrics
        super().__init__(
            name="Handoff Completeness",
            model=model or _get_eval_model(),
            criteria="""Evaluate whether the handoff prompt contains all required sections and structure.

Required sections:
1. TASK: Clear restatement of what needs to be done
2. ARCHITECTURE: Description of relevant codebase structure
3. SELECTED CODE CONTEXT: The actual code (inline, not references)
4. RELATIONSHIPS: How components interact
5. AMBIGUITIES: Either "None" or specific factual observations
6. IMPLEMENTATION NOTES (optional but valuable): Why these files were chosen

Check:
- Are all required sections present?
- Are sections properly populated (not empty placeholders)?
- Is the code actually included inline, not just referenced?
- Is the structure clear and well-organized?""",
            evaluation_params=[
                LLMTestCaseParams.ACTUAL_OUTPUT,
            ],
            threshold=threshold,
        )


class FileRecallMetric(BaseMetric):
    """
    Non-LLM metric: Calculates what % of expected files were selected.

    This is a deterministic metric based on ground truth.
    """

    def __init__(
        self,
        expected_files: list[str],
        threshold: float = 0.8,
        strict: bool = False,
    ):
        """
        Args:
            expected_files: List of file paths that should be selected
            threshold: Minimum recall score to pass
            strict: If True, requires exact path match; if False, allows partial match
        """
        self.expected_files = expected_files
        self.threshold = threshold
        self.strict = strict
        self.async_mode = False
        self._score = 0.0
        self._reason = ""

    @property
    def __name__(self) -> str:
        return "File Recall"

    def measure(self, test_case: LLMTestCase) -> float:
        """Calculate file recall from the actual output."""
        actual_output = test_case.actual_output

        # Extract file paths from the handoff prompt
        # Look for patterns like file paths in code blocks or "Selected Code Context"
        selected_files = self._extract_files_from_output(actual_output)

        # Calculate recall
        found = 0
        missing = []
        for expected in self.expected_files:
            if self._file_in_selection(expected, selected_files):
                found += 1
            else:
                missing.append(expected)

        self._score = found / len(self.expected_files) if self.expected_files else 1.0

        if missing:
            self._reason = f"Missing files: {', '.join(missing)}"
        else:
            self._reason = "All expected files were selected"

        return self._score

    def _extract_files_from_output(self, output: str) -> list[str]:
        """Extract file paths mentioned in the output."""
        import re

        EXT = r"(?:ts|js|py|tsx|jsx|go|rs|java|rb|md)"
        files = []

        # Pattern 1: Code block headers (```filepath or ```/abs/path:0-45 ...)
        for match in re.finditer(rf"```(\S+\.{EXT})", output):
            # Strip trailing :line-range if present
            path = re.sub(r":\d+-\d+.*$", "", match.group(1))
            files.append(path)

        # Pattern 2: Markdown headers with file paths
        for match in re.finditer(rf"^##\s+.*?([a-zA-Z0-9_/.-]+\.{EXT})", output, re.MULTILINE):
            files.append(match.group(1))

        # Pattern 3: File path mentions (path:line-range format)
        for match in re.finditer(rf"([a-zA-Z0-9_/.-]+\.{EXT}):\d+-\d+", output):
            files.append(match.group(1))

        # Pattern 4: Inline backtick filenames (`filename.ts` or `path/to/file.ts`)
        for match in re.finditer(rf"`([a-zA-Z0-9_/.-]+\.{EXT})`", output):
            files.append(match.group(1))

        # Pattern 5: Comment-style file references (// filename.ts - description)
        for match in re.finditer(rf"//\s+([a-zA-Z0-9_/.-]+\.{EXT})", output):
            files.append(match.group(1))

        # Pattern 6: Bold markdown filenames (**filename.ts**)
        for match in re.finditer(rf"\*\*([a-zA-Z0-9_/.-]+\.{EXT})\*\*", output):
            files.append(match.group(1))

        return list(set(files))

    def _file_in_selection(self, expected: str, selected: list[str]) -> bool:
        """Check if expected file is in selection (bidirectional suffix match)."""
        if self.strict:
            return expected in selected

        expected_parts = expected.replace("\\", "/").strip("/").split("/")
        for selected_file in selected:
            selected_parts = selected_file.replace("\\", "/").strip("/").split("/")
            # Match if either is a suffix of the other
            # e.g. "semantic-search.ts" matches "packages/.../tools/semantic-search.ts"
            shorter, longer = sorted(
                [expected_parts, selected_parts], key=len
            )
            if longer[-len(shorter):] == shorter:
                return True
        return False

    @property
    def score(self) -> float:
        return self._score

    @property
    def reason(self) -> str:
        return self._reason

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self._score >= self.threshold


class MCPToolUsageMetric(BaseMetric):
    """
    Non-LLM metric: Measures how well /discover uses MCP tools vs default tools.

    The /discover command should use context-helper-synapse MCP tools for:
    - file_search (instead of Grep/Glob)
    - get_file_tree (instead of Bash ls/find)
    - read_file (MCP version, instead of Read tool)
    - manage_selection (for curating context)
    - workspace_context (for token counts)
    - get_code_structure (for architecture)
    - semantic_search (for conceptual search)

    Using default tools (Read, Grep, Glob, Bash) is suboptimal because:
    - They don't leverage the indexed chunks
    - They don't integrate with the selection system
    - They're less efficient for large codebases
    """

    # MCP tools that /discover SHOULD use
    MCP_TOOLS = {
        "file_search",
        "get_file_tree",
        "read_file",  # MCP version
        "manage_selection",
        "workspace_context",
        "get_code_structure",
        "semantic_search",
        "index_code",
    }

    # Default tools that indicate suboptimal behavior
    DEFAULT_TOOLS = {
        "Read",
        "Grep",
        "Glob",
        "Bash",
    }

    # Bash commands that are particularly bad (searching/reading)
    BAD_BASH_PATTERNS = [
        "grep",
        "rg ",  # ripgrep
        "find ",
        "cat ",
        "head ",
        "tail ",
        "less ",
        "awk ",
        "sed ",
    ]

    def __init__(
        self,
        tool_calls: list[dict],
        threshold: float = 0.7,
        strict: bool = False,
    ):
        """
        Args:
            tool_calls: List of tool call dicts with 'name' and optionally 'input'
            threshold: Minimum MCP usage ratio to pass
            strict: If True, ANY default tool usage fails the metric
        """
        self.tool_calls = tool_calls
        self.threshold = threshold
        self.strict = strict
        self.async_mode = False
        self._score = 0.0
        self._reason = ""
        self._details = {}

    @property
    def __name__(self) -> str:
        return "MCP Tool Usage"

    def measure(self, test_case: LLMTestCase) -> float:
        """Calculate MCP tool usage ratio."""
        if not self.tool_calls:
            self._score = 1.0  # No tool calls = nothing to evaluate
            self._reason = "No tool calls to evaluate"
            return self._score

        mcp_calls = 0
        default_calls = 0
        bad_bash_calls = 0
        tool_breakdown = {"mcp": [], "default": [], "other": []}

        for call in self.tool_calls:
            tool_name = call.get("name", "")
            tool_input = call.get("input", {})

            # Strip MCP prefix for classification (CLI mode includes it)
            bare_name = tool_name.removeprefix("mcp__context-helper-synapse__")

            if bare_name in self.MCP_TOOLS:
                mcp_calls += 1
                tool_breakdown["mcp"].append(bare_name)

            elif tool_name in self.DEFAULT_TOOLS:
                default_calls += 1
                tool_breakdown["default"].append(tool_name)

                # Check for particularly bad Bash usage
                if tool_name == "Bash":
                    command = tool_input.get("command", "")
                    for pattern in self.BAD_BASH_PATTERNS:
                        if pattern in command:
                            bad_bash_calls += 1
                            break

            else:
                # Other tools (Task, etc.) - neutral
                tool_breakdown["other"].append(tool_name)

        total_search_tools = mcp_calls + default_calls
        if total_search_tools == 0:
            self._score = 1.0
            self._reason = "No search/read tools used"
            return self._score

        # Calculate score: ratio of MCP tools to total search tools
        self._score = mcp_calls / total_search_tools

        # Store details for reporting
        self._details = {
            "mcp_calls": mcp_calls,
            "default_calls": default_calls,
            "bad_bash_calls": bad_bash_calls,
            "breakdown": tool_breakdown,
        }

        # Build reason
        if self.strict and default_calls > 0:
            self._score = 0.0
            self._reason = (
                f"Strict mode: {default_calls} default tool(s) used "
                f"({', '.join(set(tool_breakdown['default']))})"
            )
        elif default_calls == 0:
            self._reason = f"Excellent! All {mcp_calls} search calls used MCP tools"
        else:
            default_list = ", ".join(set(tool_breakdown["default"]))
            self._reason = (
                f"MCP: {mcp_calls}, Default: {default_calls} ({default_list})"
            )
            if bad_bash_calls > 0:
                self._reason += f" - {bad_bash_calls} bad Bash pattern(s)"

        return self._score

    @property
    def score(self) -> float:
        return self._score

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def details(self) -> dict:
        return self._details

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self._score >= self.threshold


class FilePrecisionMetric(BaseMetric):
    """
    Non-LLM metric: Calculates what % of selected files were expected.

    Helps identify over-selection (too much context).
    """

    def __init__(
        self,
        expected_files: list[str],
        recommended_files: Optional[list[str]] = None,
        threshold: float = 0.5,  # Lower threshold since extra context isn't always bad
    ):
        self.expected_files = expected_files
        self.recommended_files = recommended_files or []
        self.all_valid_files = set(expected_files + self.recommended_files)
        self.threshold = threshold
        self.async_mode = False
        self._score = 0.0
        self._reason = ""

    @property
    def __name__(self) -> str:
        return "File Precision"

    def measure(self, test_case: LLMTestCase) -> float:
        """Calculate file precision."""
        actual_output = test_case.actual_output
        selected_files = self._extract_files_from_output(actual_output)

        if not selected_files:
            self._score = 0.0
            self._reason = "No files detected in output"
            return self._score

        # Count how many selected files are valid
        valid_count = 0
        extra_files = []
        for selected in selected_files:
            if self._file_is_valid(selected):
                valid_count += 1
            else:
                extra_files.append(selected)

        self._score = valid_count / len(selected_files)

        if extra_files:
            self._reason = f"Extra files selected: {', '.join(extra_files[:5])}"
            if len(extra_files) > 5:
                self._reason += f" (and {len(extra_files) - 5} more)"
        else:
            self._reason = "All selected files are relevant"

        return self._score

    def _extract_files_from_output(self, output: str) -> list[str]:
        """Same extraction logic as FileRecallMetric."""
        import re
        EXT = r"(?:ts|js|py|tsx|jsx|go|rs|java|rb|md)"
        files = []
        for match in re.finditer(rf"```(\S+\.{EXT})", output):
            path = re.sub(r":\d+-\d+.*$", "", match.group(1))
            files.append(path)
        for match in re.finditer(rf"^##\s+.*?([a-zA-Z0-9_/.-]+\.{EXT})", output, re.MULTILINE):
            files.append(match.group(1))
        for match in re.finditer(rf"([a-zA-Z0-9_/.-]+\.{EXT}):\d+-\d+", output):
            files.append(match.group(1))
        for match in re.finditer(rf"`([a-zA-Z0-9_/.-]+\.{EXT})`", output):
            files.append(match.group(1))
        for match in re.finditer(rf"//\s+([a-zA-Z0-9_/.-]+\.{EXT})", output):
            files.append(match.group(1))
        for match in re.finditer(rf"\*\*([a-zA-Z0-9_/.-]+\.{EXT})\*\*", output):
            files.append(match.group(1))
        return list(set(files))

    def _file_is_valid(self, selected: str) -> bool:
        """Check if selected file matches any expected/recommended file (bidirectional)."""
        selected_parts = selected.replace("\\", "/").strip("/").split("/")
        for valid in self.all_valid_files:
            valid_parts = valid.replace("\\", "/").strip("/").split("/")
            shorter, longer = sorted(
                [selected_parts, valid_parts], key=len
            )
            if longer[-len(shorter):] == shorter:
                return True
        return False

    @property
    def score(self) -> float:
        return self._score

    @property
    def reason(self) -> str:
        return self._reason

    async def a_measure(self, test_case: LLMTestCase, *args, **kwargs) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self._score >= self.threshold


# Convenience function to get all standard metrics
def get_standard_metrics(
    expected_files: Optional[list[str]] = None,
    recommended_files: Optional[list[str]] = None,
    tool_calls: Optional[list[dict]] = None,
    thresholds: Optional[dict] = None,
) -> list[BaseMetric]:
    """
    Get the standard set of metrics for evaluating /discover.

    Args:
        expected_files: Files that must be selected (for recall/precision)
        recommended_files: Files that are good to have (for precision)
        tool_calls: List of tool calls made during discovery (for MCP usage metric)
        thresholds: Optional dict of metric_name -> threshold overrides

    Returns:
        List of metrics to use with deepeval
    """
    thresholds = thresholds or {}

    # GEval (LLM-as-judge) metrics require an API key (OpenAI or Anthropic).
    # When running discovery via CLI (OAuth) without any API key set,
    # skip GEval metrics and only use deterministic ones.
    metrics = []

    if _has_geval_api_key():
        metrics.extend([
            ContextRelevanceMetric(threshold=thresholds.get("context_relevance", 0.7)),
            ArchitectureClarityMetric(threshold=thresholds.get("architecture_clarity", 0.7)),
            RelationshipMappingMetric(threshold=thresholds.get("relationship_mapping", 0.7)),
            TaskActionabilityMetric(threshold=thresholds.get("task_actionability", 0.7)),
            HandoffCompletenessMetric(threshold=thresholds.get("handoff_completeness", 0.8)),
        ])
    else:
        import warnings
        warnings.warn(
            "No OPENAI_API_KEY or ANTHROPIC_API_KEY found — skipping GEval metrics. "
            "Only deterministic metrics (FileRecall, FilePrecision, MCPToolUsage) will run. "
            "Set OPENAI_API_KEY (preferred) or ANTHROPIC_API_KEY to enable full evaluation.",
            stacklevel=2,
        )

    if expected_files:
        metrics.append(
            FileRecallMetric(
                expected_files=expected_files,
                threshold=thresholds.get("file_recall", 0.8),
            )
        )
        metrics.append(
            FilePrecisionMetric(
                expected_files=expected_files,
                recommended_files=recommended_files,
                threshold=thresholds.get("file_precision", 0.5),
            )
        )

    if tool_calls is not None:
        metrics.append(
            MCPToolUsageMetric(
                tool_calls=tool_calls,
                threshold=thresholds.get("mcp_tool_usage", 0.7),
                strict=thresholds.get("mcp_tool_usage_strict", False),
            )
        )

    return metrics
