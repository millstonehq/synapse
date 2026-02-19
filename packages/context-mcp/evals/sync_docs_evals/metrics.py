"""
Custom DeepEval metrics for evaluating /sync-docs output.

These metrics evaluate:
1. Doc discovery quality (did it find the right docs?)
2. Update accuracy (are the updates correct?)
3. Staleness detection (did it identify stale content?)
4. Validation compliance (do updated docs pass synapse validate?)
5. Performance (within time budget?)

Evaluation model priority:
1. OpenAI (OPENAI_API_KEY) — default, DeepEval's native model
2. Anthropic (ANTHROPIC_API_KEY) — fallback
"""

import os
import re
from typing import Optional
from deepeval.metrics import GEval, BaseMetric
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


def _get_eval_model():
    """Get the evaluation model. Prefers OpenAI, falls back to Anthropic.

    Returns None to use DeepEval's default (OpenAI) when OPENAI_API_KEY is set.
    Returns AnthropicModel when only ANTHROPIC_API_KEY is available.
    Raises RuntimeError if neither key is found.
    """
    if os.environ.get("OPENAI_API_KEY"):
        # Use DeepEval's default OpenAI model (gpt-4o)
        return None

    anthropic_key = (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY")
    )
    if anthropic_key:
        from deepeval.models import AnthropicModel
        return AnthropicModel(model="claude-sonnet-4-20250514", api_key=anthropic_key)

    raise RuntimeError(
        "No eval model API key found. Set OPENAI_API_KEY (preferred) or "
        "ANTHROPIC_API_KEY as fallback."
    )


def _has_eval_key() -> bool:
    """Check if any eval model API key is available."""
    return bool(
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY")
    )


# =========================================================================
# GEval (LLM-as-Judge) Metrics
# =========================================================================


class UpdateAccuracyMetric(GEval):
    """
    Evaluates whether the doc updates accurately reflect the code changes.

    Checks:
    - Are the edits factually correct given the code changes?
    - Do the updates accurately describe new behavior?
    - Were the RIGHT docs updated (compared to expected_output ground truth)?
    """

    def __init__(self, threshold: float = 0.7, model=None, **kwargs):
        init_kwargs = dict(
            name="Update Accuracy",
            criteria="""Evaluate whether the documentation updates in the actual output accurately reflect the code changes described in the input.

The expected output lists the GROUND TRUTH: which documents MUST be found as stale and which sections within them should be updated. Use this as the authoritative reference.

Consider:
1. CORRECT DOCS UPDATED: Were the documents listed in the expected output actually found and updated? Missing an expected doc is a major failure.
2. CORRECT SECTIONS UPDATED: Were the specific stale sections (from expected output) identified and fixed?
3. FACTUAL ACCURACY: Do the updates correctly describe what the code now does?
4. NO HALLUCINATION: Are all claims in the updates supported by the actual code changes?

Scoring guide:
- 1.0: All expected docs found, all expected sections updated accurately
- 0.7-0.9: Most expected docs found, updates are mostly accurate
- 0.4-0.6: Some expected docs missed, or updates contain inaccuracies
- 0.0-0.3: Most expected docs missed, or updates are largely wrong""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT,
            ],
            threshold=threshold,
        )
        resolved_model = model or _get_eval_model()
        if resolved_model is not None:
            init_kwargs["model"] = resolved_model
        super().__init__(**init_kwargs)


class StalenessDetectionMetric(GEval):
    """
    Evaluates whether /sync-docs correctly identified stale content.

    Checks:
    - Did it find the docs that the ground truth says are stale?
    - Did it correctly skip docs that are still current?
    - Were the right sections identified within stale docs?
    """

    def __init__(self, threshold: float = 0.7, model=None, **kwargs):
        init_kwargs = dict(
            name="Staleness Detection",
            criteria="""Evaluate how well the sync-docs command identified stale documentation, using the expected output as ground truth.

The expected output lists which documents MUST be identified as stale and which sections within them are stale. This is the authoritative answer.

Consider:
1. RECALL: Did the actual output find ALL docs listed as expected stale in the expected output? Missing an expected stale doc is a critical failure.
2. SECTION ACCURACY: For each expected stale doc, did it identify the correct stale sections listed in the expected output?
3. FALSE NEGATIVES: Did it skip or declare "already current" any doc that the expected output says IS stale? This is a major error.
4. FALSE POSITIVES: Did it flag docs as stale that aren't in the expected list? (Minor issue if the doc is plausibly related.)

Scoring guide:
- 1.0: All expected stale docs found, correct sections identified
- 0.7-0.9: Most expected stale docs found, mostly correct sections
- 0.4-0.6: Some expected stale docs missed or declared current
- 0.0-0.3: Most expected stale docs missed""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT,
            ],
            threshold=threshold,
        )
        resolved_model = model or _get_eval_model()
        if resolved_model is not None:
            init_kwargs["model"] = resolved_model
        super().__init__(**init_kwargs)


class UpdateMinimalityMetric(GEval):
    """
    Evaluates whether updates were minimal and targeted.

    /sync-docs should make surgical edits, not rewrite entire documents.
    """

    def __init__(self, threshold: float = 0.7, model=None, **kwargs):
        init_kwargs = dict(
            name="Update Minimality",
            criteria="""Evaluate whether the sync-docs updates were minimal and targeted, using the expected output to understand which sections should have been changed.

The expected output lists the specific sections that are stale. Only these sections should be modified — everything else should be left untouched.

Consider:
1. SCOPE: Did the actual output ONLY modify sections listed as stale in the expected output? Editing sections not listed as stale is over-editing.
2. SURGICAL EDITS: Within stale sections, were changes minimal (updating specific values/descriptions) vs rewriting the entire section?
3. NO ADDITIONS: Did it avoid adding new sections, content, or embellishments not warranted by the code change?
4. STYLE PRESERVATION: Did it maintain the existing writing style and document structure?

Scoring guide:
- 1.0: Only expected stale sections modified, changes are surgical
- 0.7-0.9: Mostly correct scope, minor extra edits
- 0.4-0.6: Significant over-editing or rewriting of non-stale sections
- 0.0-0.3: Entire documents rewritten or massive scope creep""",
            evaluation_params=[
                LLMTestCaseParams.INPUT,
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT,
            ],
            threshold=threshold,
        )
        resolved_model = model or _get_eval_model()
        if resolved_model is not None:
            init_kwargs["model"] = resolved_model
        super().__init__(**init_kwargs)


class SyncCompletenessMetric(GEval):
    """
    Evaluates structural completeness of the sync-docs output.

    Checks that the summary and report follow the expected format,
    and that all expected docs are accounted for.
    """

    def __init__(self, threshold: float = 0.8, model=None, **kwargs):
        init_kwargs = dict(
            name="Sync Completeness",
            criteria="""Evaluate whether the sync-docs output is complete, using the expected output as ground truth for what should have been found.

Required elements:
1. SUMMARY: Clear summary of code changes detected
2. ALL EXPECTED DOCS ACCOUNTED FOR: Every doc listed in the expected output must appear in the actual output — either as updated or with a justified skip reason. Missing docs entirely is a critical failure.
3. STALENESS CLASSIFICATION: Each doc should be marked as STALE, CURRENT, or NEEDS_REVIEW
4. UPDATE DETAILS: For updated docs, which sections were changed and why
5. VALIDATION: Mention of running synapse validate on updated docs

Scoring guide:
- 1.0: All expected docs accounted for, well-structured output with all required sections
- 0.7-0.9: Most expected docs accounted for, minor structural gaps
- 0.4-0.6: Some expected docs missing from output, or poor structure
- 0.0-0.3: Most expected docs missing, unstructured output""",
            evaluation_params=[
                LLMTestCaseParams.ACTUAL_OUTPUT,
                LLMTestCaseParams.EXPECTED_OUTPUT,
            ],
            threshold=threshold,
        )
        resolved_model = model or _get_eval_model()
        if resolved_model is not None:
            init_kwargs["model"] = resolved_model
        super().__init__(**init_kwargs)


# =========================================================================
# Deterministic Metrics
# =========================================================================


class DocRecallMetric(BaseMetric):
    """
    Non-LLM metric: Calculates what % of expected docs were found/updated.

    This is a deterministic metric based on ground truth.
    """

    def __init__(
        self,
        expected_docs: list[str],
        threshold: float = 0.8,
    ):
        """
        Args:
            expected_docs: List of doc paths that should be found as stale
            threshold: Minimum recall score to pass
        """
        self.expected_docs = expected_docs
        self.threshold = threshold
        self.async_mode = False
        self._score = 0.0
        self._reason = ""

    @property
    def __name__(self) -> str:
        return "Doc Recall"

    def measure(self, test_case: LLMTestCase) -> float:
        """Calculate doc recall from the actual output."""
        actual_output = test_case.actual_output
        mentioned_docs = self._extract_doc_paths(actual_output)

        found = 0
        missing = []
        for expected in self.expected_docs:
            if self._doc_in_output(expected, mentioned_docs):
                found += 1
            else:
                missing.append(expected)

        self._score = found / len(self.expected_docs) if self.expected_docs else 1.0

        if missing:
            self._reason = f"Missing docs: {', '.join(missing)}"
        else:
            self._reason = "All expected docs were found"

        return self._score

    def _extract_doc_paths(self, output: str) -> list[str]:
        """Extract doc paths mentioned in the output."""
        paths = []

        # Pattern 1: content/path/to/doc.md in backticks or parens
        for match in re.finditer(r"[`(]?(content/[a-zA-Z0-9_/.-]+\.md)[`)]?", output):
            paths.append(match.group(1))

        # Pattern 2: Bold filenames with .md extension
        for match in re.finditer(r"\*\*([a-zA-Z0-9_/.-]+\.md)\*\*", output):
            paths.append(match.group(1))

        # Pattern 3: Plain file paths ending in .md
        for match in re.finditer(r"(?:^|\s)(content/\S+\.md)", output, re.MULTILINE):
            paths.append(match.group(1))

        return list(set(paths))

    def _doc_in_output(self, expected: str, mentioned: list[str]) -> bool:
        """Check if expected doc appears in output (suffix matching)."""
        expected_parts = expected.replace("\\", "/").strip("/").split("/")
        for doc_path in mentioned:
            doc_parts = doc_path.replace("\\", "/").strip("/").split("/")
            shorter, longer = sorted([expected_parts, doc_parts], key=len)
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


class DocPrecisionMetric(BaseMetric):
    """
    Non-LLM metric: Calculates what % of docs flagged as stale were expected.

    Helps identify over-detection (flagging docs that aren't actually stale).
    """

    def __init__(
        self,
        expected_docs: list[str],
        acceptable_docs: Optional[list[str]] = None,
        threshold: float = 0.5,
    ):
        self.expected_docs = expected_docs
        self.acceptable_docs = acceptable_docs or []
        self.all_valid_docs = set(expected_docs + self.acceptable_docs)
        self.threshold = threshold
        self.async_mode = False
        self._score = 0.0
        self._reason = ""

    @property
    def __name__(self) -> str:
        return "Doc Precision"

    def measure(self, test_case: LLMTestCase) -> float:
        """Calculate doc precision."""
        actual_output = test_case.actual_output
        flagged_docs = self._extract_stale_docs(actual_output)

        if not flagged_docs:
            self._score = 0.0
            self._reason = "No stale docs detected in output"
            return self._score

        valid_count = 0
        extra_docs = []
        for doc in flagged_docs:
            if self._doc_is_valid(doc):
                valid_count += 1
            else:
                extra_docs.append(doc)

        self._score = valid_count / len(flagged_docs)

        if extra_docs:
            self._reason = f"Unexpected stale docs: {', '.join(extra_docs[:5])}"
        else:
            self._reason = "All flagged docs are expected"

        return self._score

    def _extract_stale_docs(self, output: str) -> list[str]:
        """Extract docs flagged as stale/updated in the output.

        Searches the entire output for content/*.md paths. In sync-docs
        output, any mentioned doc path is one that was found as relevant
        during the sync operation. Claude uses various section headers
        (Updated Documents, Stale Documents, Changes Made, etc.) so
        we search broadly rather than matching specific sections.
        """
        paths = []

        # content/ paths in backticks or parens
        for match in re.finditer(r"[`(]?(content/[a-zA-Z0-9_/.-]+\.md)[`)]?", output):
            paths.append(match.group(1))

        # Bold filenames with .md extension
        for match in re.finditer(r"\*\*([a-zA-Z0-9_/.-]+\.md)\*\*", output):
            paths.append(match.group(1))

        # Plain file paths starting with content/
        for match in re.finditer(r"(?:^|\s)(content/\S+\.md)", output, re.MULTILINE):
            paths.append(match.group(1))

        return list(set(paths))

    def _doc_is_valid(self, doc_path: str) -> bool:
        """Check if doc matches any expected/acceptable doc (suffix match)."""
        doc_parts = doc_path.replace("\\", "/").strip("/").split("/")
        for valid in self.all_valid_docs:
            valid_parts = valid.replace("\\", "/").strip("/").split("/")
            shorter, longer = sorted([doc_parts, valid_parts], key=len)
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


class PerformanceMetric(BaseMetric):
    """
    Non-LLM metric: Checks if sync-docs completed within the time budget.

    Target: < 3 minutes (180,000ms) for typical changes.
    """

    def __init__(
        self,
        duration_ms: float,
        threshold_ms: float = 180_000,
    ):
        self.duration_ms = duration_ms
        self.threshold_ms = threshold_ms
        self.threshold = 0.5  # Binary: pass if under budget
        self.async_mode = False
        self._score = 0.0
        self._reason = ""

    @property
    def __name__(self) -> str:
        return "Performance"

    def measure(self, test_case: LLMTestCase) -> float:
        """Check if duration is within budget."""
        if self.duration_ms <= self.threshold_ms:
            self._score = 1.0
            self._reason = f"Completed in {self.duration_ms:.0f}ms (budget: {self.threshold_ms:.0f}ms)"
        else:
            self._score = max(0.0, self.threshold_ms / self.duration_ms)
            self._reason = (
                f"Over budget: {self.duration_ms:.0f}ms "
                f"(budget: {self.threshold_ms:.0f}ms, "
                f"{self.duration_ms / self.threshold_ms:.1f}x over)"
            )
        return self._score

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


class MCPSearchUsageMetric(BaseMetric):
    """
    Non-LLM metric: Measures whether /sync-docs uses MCP search tools
    instead of Glob/Grep to find vault docs.

    The command should use semantic_search and file_search from the MCP server,
    not Glob or Grep which don't leverage the indexed search.
    """

    MCP_SEARCH_TOOLS = {"semantic_search", "file_search"}
    BAD_SEARCH_TOOLS = {"Glob", "Grep"}

    def __init__(
        self,
        tool_calls: list[dict],
        threshold: float = 0.7,
    ):
        self.tool_calls = tool_calls
        self.threshold = threshold
        self.async_mode = False
        self._score = 0.0
        self._reason = ""

    @property
    def __name__(self) -> str:
        return "MCP Search Usage"

    @staticmethod
    def _targets_vault_docs(call: dict) -> bool:
        """Check if a Glob/Grep call is searching vault docs (content/ paths)."""
        tool_input = call.get("input", {})
        search_path = tool_input.get("path", "")
        search_pattern = tool_input.get("pattern", "")
        return "content" in search_path or "content" in search_pattern

    def measure(self, test_case: LLMTestCase) -> float:
        """Calculate MCP search usage ratio.

        Only Glob/Grep calls that target vault docs (content/ paths) are
        counted as "bad" search calls. Glob/Grep for source code exploration
        is legitimate and not penalized.
        """
        if not self.tool_calls:
            self._score = 1.0
            self._reason = "No tool calls to evaluate"
            return self._score

        mcp_search_calls = 0
        bad_search_calls = 0

        for call in self.tool_calls:
            tool_name = call.get("name", "")
            bare_name = tool_name.removeprefix("mcp__context-helper-synapse__")

            if bare_name in self.MCP_SEARCH_TOOLS:
                mcp_search_calls += 1
            elif tool_name in self.BAD_SEARCH_TOOLS and self._targets_vault_docs(call):
                bad_search_calls += 1

        total_search = mcp_search_calls + bad_search_calls
        if total_search == 0:
            self._score = 1.0
            self._reason = "No search tools used (Glob/Grep used only for source code)"
            return self._score

        self._score = mcp_search_calls / total_search

        if bad_search_calls == 0:
            self._reason = f"All {mcp_search_calls} doc searches used MCP tools"
        else:
            self._reason = (
                f"MCP: {mcp_search_calls}, Glob/Grep on vault: {bad_search_calls}"
            )

        return self._score

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


# =========================================================================
# Convenience function
# =========================================================================


def build_expected_output(ground_truth: dict) -> str:
    """Build an expected_output string from test case ground truth.

    This provides the GEval judge with concrete ground truth so it can
    evaluate the actual output against what SHOULD have happened, rather
    than just grading whether the summary sounds plausible.

    Args:
        ground_truth: The ground_truth dict from a test case YAML, containing
            expected_stale_docs, acceptable_docs, expected_stale_sections, etc.

    Returns:
        A structured string describing the expected behavior.
    """
    lines = ["## Ground Truth for Evaluation", ""]

    # Expected stale docs
    expected_docs = ground_truth.get("expected_stale_docs", [])
    if expected_docs:
        lines.append("### Documents that MUST be found as stale and updated:")
        for doc in expected_docs:
            lines.append(f"- `{doc}`")
        lines.append("")

    # Acceptable docs (not required but not wrong to flag)
    acceptable = ground_truth.get("acceptable_docs", [])
    if acceptable:
        lines.append("### Documents that are acceptable to flag (optional):")
        for doc in acceptable:
            lines.append(f"- `{doc}`")
        lines.append("")

    # Expected stale sections — collect from all section keys
    section_keys = [k for k in ground_truth if k.startswith("expected_stale_sections")]
    for key in section_keys:
        sections_dict = ground_truth[key]
        if isinstance(sections_dict, dict):
            for doc_id, sections in sections_dict.items():
                lines.append(f"### Stale sections in `{doc_id}`:")
                for section in sections:
                    lines.append(f"- {section}")
                lines.append("")

    return "\n".join(lines)


def get_standard_metrics(
    expected_docs: Optional[list[str]] = None,
    acceptable_docs: Optional[list[str]] = None,
    ground_truth: Optional[dict] = None,
    tool_calls: Optional[list[dict]] = None,
    duration_ms: Optional[float] = None,
    thresholds: Optional[dict] = None,
) -> tuple[list[BaseMetric], Optional[str]]:
    """
    Get the standard set of metrics for evaluating /sync-docs.

    Args:
        expected_docs: Docs that must be found/updated (for recall/precision)
        acceptable_docs: Docs that are acceptable to flag (for precision)
        ground_truth: Full ground_truth dict from test case YAML (for GEval expected_output)
        tool_calls: List of tool calls made during sync (for MCP usage metric)
        duration_ms: Total duration in ms (for performance metric)
        thresholds: Optional dict of metric_name -> threshold overrides

    Returns:
        Tuple of (list of metrics, expected_output string or None).
        The expected_output should be passed to LLMTestCase for GEval metrics.
    """
    thresholds = thresholds or {}
    metrics = []
    expected_output = None

    if ground_truth:
        expected_output = build_expected_output(ground_truth)

    if _has_eval_key():
        metrics.extend([
            UpdateAccuracyMetric(threshold=thresholds.get("update_accuracy", 0.7)),
            StalenessDetectionMetric(threshold=thresholds.get("staleness_detection", 0.7)),
            UpdateMinimalityMetric(threshold=thresholds.get("update_minimality", 0.7)),
            SyncCompletenessMetric(threshold=thresholds.get("sync_completeness", 0.8)),
        ])
    else:
        import warnings
        warnings.warn(
            "No OPENAI_API_KEY or ANTHROPIC_API_KEY found — skipping GEval metrics. "
            "Only deterministic metrics (DocRecall, DocPrecision, MCP, Performance) will run.",
            stacklevel=2,
        )

    if expected_docs:
        metrics.append(
            DocRecallMetric(
                expected_docs=expected_docs,
                threshold=thresholds.get("doc_recall", 0.8),
            )
        )
        metrics.append(
            DocPrecisionMetric(
                expected_docs=expected_docs,
                acceptable_docs=acceptable_docs,
                threshold=thresholds.get("doc_precision", 0.5),
            )
        )

    if tool_calls is not None:
        metrics.append(
            MCPSearchUsageMetric(
                tool_calls=tool_calls,
                threshold=thresholds.get("mcp_search_usage", 0.5),
            )
        )

    if duration_ms is not None:
        metrics.append(
            PerformanceMetric(
                duration_ms=duration_ms,
                threshold_ms=thresholds.get("performance_ms", 180_000),
            )
        )

    return metrics, expected_output
