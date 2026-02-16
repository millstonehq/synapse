"""
DeepEval test suite for /discover command.

Run with:
    deepeval test run test_discover.py
    deepeval test run test_discover.py -k "case_001"
    deepeval test run test_discover.py --verbose

Quick tests only (no real API calls):
    deepeval test run test_discover.py -m "not slow"

Mock mode (fast, for CI):
    DISCOVER_EVAL_MOCK=true deepeval test run test_discover.py

Environment variables:
    DISCOVER_EVAL_MOCK=true    - Use mock tool responses (fast, for CI)
    DISCOVER_EVAL_MOCK=false   - Use real MCP server (default for evals)
    DISCOVER_EVAL_USE_API=true - Use direct API key instead of CLI (OAuth)
    DISCOVER_EVAL_METRIC_DELAY - Seconds between GEval metric evaluations (default: 15)
    ANTHROPIC_API_KEY or DEEPEVAL_ANTHROPIC_API_KEY - Required for API mode evals

Discovery runs are parallelized: all 4 test cases run concurrently via
ThreadPoolExecutor, reducing wall time from ~8 min to ~2 min. GEval
metrics (when ANTHROPIC_API_KEY is set) are evaluated sequentially with
rate limit delays between test cases.
"""

import os
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from .runner import DiscoverRunner, DiscoverResult
from .metrics import get_standard_metrics, _get_anthropic_api_key, _has_geval_api_key


# Directory paths
EVALS_DIR = Path(__file__).parent.parent
TEST_CASES_DIR = EVALS_DIR / "test_cases"
RESULTS_DIR = EVALS_DIR / "results"
FIXTURES_DIR = EVALS_DIR / "fixtures"

# Default workspace for MCP server (synapse repo root)
DEFAULT_WORKSPACE = Path(__file__).parent.parent.parent.parent.parent

# All evaluation case IDs (used for parametrized tests and parallel discovery)
ALL_CASE_IDS = [
    "case_001_auth",
    "case_002_refactor",
    "case_003_api_endpoint",
    "case_004_mcp_semantic_search",
]


def _get_workspace_for_fixture(fixture_name: str) -> Path:
    """Get workspace directory for a given fixture name."""
    if fixture_name == "synapse":
        return DEFAULT_WORKSPACE
    fixture_path = FIXTURES_DIR / fixture_name
    if fixture_path.exists():
        return fixture_path
    # Fallback to default if fixture doesn't exist
    return DEFAULT_WORKSPACE

# Real MCP discovery needs many turns (each turn = one Claude API call ~5-20s)
# Increased from 25 to 35 - sometimes LLM needs more turns before producing handoff
DEFAULT_MAX_TURNS = 35
MOCK_MAX_TURNS = 10


def _should_use_mock() -> bool:
    """Check if mock mode is enabled via environment variable."""
    return os.environ.get("DISCOVER_EVAL_MOCK", "false").lower() == "true"


def _should_use_cli() -> bool:
    """Check if CLI mode (OAuth) should be used.

    Default is CLI mode unless:
    - Mock mode is enabled (mock requires API runner for tool simulation)
    - DISCOVER_EVAL_USE_API=true is set (explicit API mode opt-in)
    """
    if _should_use_mock():
        return False  # Mock mode requires API runner
    return os.environ.get("DISCOVER_EVAL_USE_API", "false").lower() != "true"


def _get_max_turns() -> int:
    """Get max turns based on mock mode or environment override."""
    # Allow override via environment variable for testing early termination
    env_override = os.environ.get("DISCOVER_EVAL_MAX_TURNS")
    if env_override:
        return int(env_override)
    return MOCK_MAX_TURNS if _should_use_mock() else DEFAULT_MAX_TURNS


def load_test_case(case_id: str) -> dict:
    """Load a test case from YAML."""
    case_file = TEST_CASES_DIR / f"{case_id}.yaml"
    if not case_file.exists():
        raise FileNotFoundError(f"Test case not found: {case_file}")
    with open(case_file) as f:
        return yaml.safe_load(f)


def get_all_test_cases() -> list[str]:
    """Get all test case IDs."""
    return [f.stem for f in TEST_CASES_DIR.glob("*.yaml")]


# =========================================================================
# Parallel discovery infrastructure
# =========================================================================

def _run_single_discovery(case_id: str) -> tuple[str, DiscoverResult]:
    """Run discovery for a single case (thread-safe).

    Each invocation creates its own DiscoverRunner, subprocess, and MCP server.
    No shared mutable state between concurrent calls.
    """
    case = load_test_case(case_id)
    fixture = case.get("fixture", "synapse")
    workspace = _get_workspace_for_fixture(fixture)
    use_cli = _should_use_cli()
    use_mock = _should_use_mock()

    runner = DiscoverRunner(
        model="claude-sonnet-4-20250514",
        workspace_dir=workspace,
        use_mcp=not use_mock and not use_cli,
        use_cli=use_cli,
    )

    result = runner.run(
        task=case["task"],
        test_case_id=case_id,
        mock_tools=use_mock,
        max_turns=_get_max_turns(),
    )
    result.save(RESULTS_DIR)
    return case_id, result


@pytest.fixture(scope="session")
def discovery_results() -> dict[str, DiscoverResult]:
    """Run all discoveries in parallel, return cached results.

    Phase 1 (this fixture): Run 4 discoveries concurrently via ThreadPoolExecutor.
    Each discovery spawns its own claude --print subprocess (~2 min each).
    Wall time: ~2 min (vs ~8 min sequential).

    Phase 2 (individual tests): Evaluate metrics on cached results sequentially.
    """
    results: dict[str, DiscoverResult] = {}

    with ThreadPoolExecutor(max_workers=len(ALL_CASE_IDS)) as executor:
        futures = {
            executor.submit(_run_single_discovery, cid): cid
            for cid in ALL_CASE_IDS
        }
        for future in as_completed(futures):
            case_id = futures[future]
            try:
                _, result = future.result()
                results[case_id] = result
            except Exception as e:
                # Create a failed result so the test can report the error
                results[case_id] = DiscoverResult(
                    test_case_id=case_id,
                    run_id="error",
                    timestamp="",
                    task="",
                    handoff_prompt="",
                    error=f"Discovery thread failed: {type(e).__name__}: {e}",
                )

    return results


# =========================================================================
# Evaluation tests (parallel discovery, sequential metric evaluation)
# =========================================================================

class TestDiscoverEvaluations:
    """
    Test class for /discover evaluations.

    Discoveries run in parallel via a session-scoped fixture (ThreadPoolExecutor).
    Each test evaluates metrics on the cached result. GEval metrics (when
    ANTHROPIC_API_KEY is set) are spaced with rate limit delays.

    These tests are marked @pytest.mark.slow since real MCP evals take
    several minutes per test case (multiple Claude API turns).
    """

    @pytest.mark.slow
    @pytest.mark.parametrize("case_id", ALL_CASE_IDS)
    def test_discover_case(
        self, case_id: str, discovery_results: dict[str, DiscoverResult]
    ):
        """Evaluate /discover output for a test case."""
        case = load_test_case(case_id)
        result = discovery_results[case_id]

        # Fail fast if discovery itself errored
        if result.error:
            pytest.fail(f"Discovery failed for {case_id}: {result.error}")

        # Build test case for deepeval
        test_case = LLMTestCase(
            input=case["task"],
            actual_output=result.handoff_prompt,
        )

        # Get metrics with ground truth and tool calls
        metrics = get_standard_metrics(
            expected_files=case["ground_truth"]["required_files"],
            recommended_files=case["ground_truth"].get("recommended_files"),
            tool_calls=result.tool_calls,
            thresholds=case.get("thresholds"),
        )

        # Separate GEval (LLM-as-judge) from deterministic metrics.
        # GEval metrics each send the full handoff prompt (~5-15K tokens).
        # DeepEval's assert_test fires all metrics concurrently, which bursts
        # over the 30K TPM rate limit. Evaluate them sequentially with delays.
        from deepeval.metrics import GEval
        geval_metrics = [m for m in metrics if isinstance(m, GEval)]
        deterministic_metrics = [m for m in metrics if not isinstance(m, GEval)]

        # Deterministic metrics are instant (no API calls)
        if deterministic_metrics:
            assert_test(test_case, deterministic_metrics)

        # GEval metrics: evaluate one at a time with rate limit spacing.
        # Default delay: 3s for OpenAI (fast window reset), 15s for Anthropic.
        if geval_metrics:
            using_openai = bool(os.environ.get("OPENAI_API_KEY"))
            default_delay = "3" if using_openai else "15"
            delay = float(os.environ.get("DISCOVER_EVAL_METRIC_DELAY", default_delay))
            failures = []
            for metric in geval_metrics:
                if delay > 0:
                    time.sleep(delay)
                metric.measure(test_case)
                if not metric.is_successful():
                    failures.append(
                        f"  {metric.name}: score={metric.score:.2f} "
                        f"(threshold={metric.threshold}), reason={metric.reason}"
                    )
            if failures:
                pytest.fail(
                    f"GEval metrics failed for {case_id}:\n" + "\n".join(failures)
                )


# =========================================================================
# Performance tests (timing, token usage) - use mocks for baselines
# =========================================================================

@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY"),
    reason="Performance tests require ANTHROPIC_API_KEY (mock mode uses direct API)",
)
class TestDiscoverPerformance:
    """Performance-focused tests for /discover.

    These tests use mock_tools=True for consistent timing baselines.
    Requires ANTHROPIC_API_KEY since mock mode uses the direct API runner.
    """

    @pytest.fixture
    def runner(self) -> DiscoverRunner:
        return DiscoverRunner(
            workspace_dir=DEFAULT_WORKSPACE,
            use_mcp=False,  # Use mock for performance baselines
            use_cli=False,  # Mock tests need API runner
        )

    @pytest.mark.slow
    def test_timing_under_threshold(self, runner: DiscoverRunner):
        """Test that /discover completes within time budget."""
        case = load_test_case("case_001_auth")

        result = runner.run(
            task=case["task"],
            test_case_id="timing_test",
            mock_tools=True,  # Use mock for timing baseline
        )

        # Should complete within 120 seconds (mock) or 600 seconds (real)
        max_duration_ms = 120_000 if result.api_calls < 5 else 600_000
        assert result.total_duration_ms < max_duration_ms, (
            f"Discovery took {result.total_duration_ms}ms, "
            f"expected < {max_duration_ms}ms"
        )

    @pytest.mark.slow
    def test_token_efficiency(self, runner: DiscoverRunner):
        """Test that token usage is reasonable."""
        case = load_test_case("case_001_auth")

        result = runner.run(
            task=case["task"],
            test_case_id="token_test",
            mock_tools=True,
        )

        # Reasonable bounds for a discovery task
        assert result.output_tokens < 50_000, (
            f"Output tokens ({result.output_tokens}) exceeds budget"
        )

    @pytest.mark.slow
    def test_api_call_efficiency(self, runner: DiscoverRunner):
        """Test that discovery doesn't make excessive API calls."""
        case = load_test_case("case_001_auth")

        result = runner.run(
            task=case["task"],
            test_case_id="api_call_test",
            mock_tools=True,
            max_turns=30,
        )

        # Should complete in reasonable number of turns
        assert result.api_calls <= 25, (
            f"Discovery made {result.api_calls} API calls, expected <= 25"
        )


# =========================================================================
# Quick smoke test (fast, for CI)
# =========================================================================

def test_smoke():
    """Quick smoke test to verify the framework works."""
    from .metrics import get_standard_metrics, _get_anthropic_api_key
    from .runner import DiscoverRunner, MCP_TOOL_PREFIX
    from .mcp_client import MCPClient, SyncMCPClient

    # Verify MCP client can be imported
    assert MCPClient is not None
    assert SyncMCPClient is not None

    # Verify tool prefix is set
    assert MCP_TOOL_PREFIX == "mcp__context-helper-synapse__"

    # CLI mode doesn't need API key
    runner_cli = DiscoverRunner(use_cli=True)
    assert runner_cli is not None
    assert runner_cli.use_cli is True
    assert runner_cli.client is None

    api_key = _get_anthropic_api_key()
    if api_key:
        # Full smoke: API runner + metrics (requires API key)
        runner = DiscoverRunner(use_cli=False)
        assert runner is not None
        assert runner.client is not None
        metrics = get_standard_metrics(expected_files=["test.ts"])
        assert len(metrics) > 0
    else:
        # No API key: verify API runner fails fast with clear error
        with pytest.raises(RuntimeError, match="No Anthropic API key found"):
            DiscoverRunner(use_cli=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
