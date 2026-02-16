"""
DeepEval test suite for /sync-docs command.

Run with:
    deepeval test run test_sync_docs.py
    deepeval test run test_sync_docs.py -k "case_001"
    deepeval test run test_sync_docs.py --verbose

Quick tests only (no real API calls):
    deepeval test run test_sync_docs.py -m "not slow"

Mock mode (fast, for CI):
    SYNC_DOCS_EVAL_MOCK=true deepeval test run test_sync_docs.py

Environment variables:
    SYNC_DOCS_EVAL_MOCK=true    - Use mock tool responses (fast, for CI)
    SYNC_DOCS_EVAL_USE_API=true - Use direct API key instead of CLI (OAuth)
    SYNC_DOCS_EVAL_MAX_TURNS    - Override max turns
    SYNC_DOCS_EVAL_METRIC_DELAY - Seconds between GEval metric evaluations (default: 15)
    OPENAI_API_KEY               - Preferred for GEval metrics (DeepEval default)
    ANTHROPIC_API_KEY            - Fallback for GEval metrics; required for API mode runner

Sync-docs runs are parallelized: all test cases run concurrently via
ThreadPoolExecutor. GEval metrics are evaluated sequentially with
rate limit delays.
"""

import os
import time
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase

from .runner import SyncDocsRunner, SyncDocsResult
from .metrics import get_standard_metrics, _has_eval_key


# Directory paths
EVALS_DIR = Path(__file__).parent.parent
TEST_CASES_DIR = EVALS_DIR / "sync_docs_test_cases"
RESULTS_DIR = EVALS_DIR / "sync_docs_results"
FIXTURES_DIR = EVALS_DIR / "fixtures"

# Default workspace (synapse repo root)
DEFAULT_WORKSPACE = Path(__file__).parent.parent.parent.parent.parent

# All evaluation case IDs
ALL_CASE_IDS = [
    "case_001_tdd_api_change",
    "case_002_prd_feature_removal",
    "case_003_system_config_change",
]


def _get_workspace_for_fixture(fixture_name: str) -> Path:
    """Get workspace directory for a given fixture name."""
    if fixture_name == "synapse":
        return DEFAULT_WORKSPACE
    fixture_path = FIXTURES_DIR / fixture_name
    if fixture_path.exists():
        return fixture_path
    return DEFAULT_WORKSPACE


DEFAULT_MAX_TURNS = 40
MOCK_MAX_TURNS = 10


def _should_use_mock() -> bool:
    return os.environ.get("SYNC_DOCS_EVAL_MOCK", "false").lower() == "true"


def _should_use_cli() -> bool:
    if _should_use_mock():
        return False
    return os.environ.get("SYNC_DOCS_EVAL_USE_API", "false").lower() != "true"


def _get_max_turns() -> int:
    env_override = os.environ.get("SYNC_DOCS_EVAL_MAX_TURNS")
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
# Parallel sync-docs infrastructure
# =========================================================================

def _run_single_sync(case_id: str) -> tuple[str, SyncDocsResult]:
    """Run sync-docs for a single case (thread-safe)."""
    case = load_test_case(case_id)
    fixture = case.get("fixture", "synapse_vault")
    workspace = _get_workspace_for_fixture(fixture)
    use_cli = _should_use_cli()
    use_mock = _should_use_mock()

    runner = SyncDocsRunner(
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
def sync_docs_results() -> dict[str, SyncDocsResult]:
    """Run all sync-docs evals in parallel, return cached results."""
    results: dict[str, SyncDocsResult] = {}

    with ThreadPoolExecutor(max_workers=len(ALL_CASE_IDS)) as executor:
        futures = {
            executor.submit(_run_single_sync, cid): cid
            for cid in ALL_CASE_IDS
        }
        for future in as_completed(futures):
            case_id = futures[future]
            try:
                _, result = future.result()
                results[case_id] = result
            except Exception as e:
                results[case_id] = SyncDocsResult(
                    test_case_id=case_id,
                    run_id="error",
                    timestamp="",
                    task="",
                    sync_output="",
                    error=f"Sync thread failed: {type(e).__name__}: {e}",
                )

    return results


# =========================================================================
# Evaluation tests
# =========================================================================

class TestSyncDocsEvaluations:
    """
    Test class for /sync-docs evaluations.

    Sync-docs runs execute in parallel via session-scoped fixture.
    Each test evaluates metrics on the cached result.
    """

    @pytest.mark.slow
    @pytest.mark.parametrize("case_id", ALL_CASE_IDS)
    def test_sync_docs_case(
        self, case_id: str, sync_docs_results: dict[str, SyncDocsResult]
    ):
        """Evaluate /sync-docs output for a test case."""
        case = load_test_case(case_id)
        result = sync_docs_results[case_id]

        if result.error:
            pytest.fail(f"Sync-docs failed for {case_id}: {result.error}")

        test_case = LLMTestCase(
            input=case["task"],
            actual_output=result.sync_output,
        )

        metrics = get_standard_metrics(
            expected_docs=case["ground_truth"]["expected_stale_docs"],
            acceptable_docs=case["ground_truth"].get("acceptable_docs"),
            tool_calls=result.tool_calls,
            duration_ms=result.total_duration_ms,
            thresholds=case.get("thresholds"),
        )

        # Separate GEval from deterministic metrics
        from deepeval.metrics import GEval
        geval_metrics = [m for m in metrics if isinstance(m, GEval)]
        deterministic_metrics = [m for m in metrics if not isinstance(m, GEval)]

        # Run deterministic metrics
        if deterministic_metrics:
            assert_test(test_case, deterministic_metrics)

        # Run GEval metrics sequentially with rate limit delays
        if geval_metrics:
            delay = float(os.environ.get("SYNC_DOCS_EVAL_METRIC_DELAY", "15"))
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
# Performance tests
# =========================================================================

@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY"),
    reason="Performance tests require ANTHROPIC_API_KEY (mock mode uses direct API)",
)
class TestSyncDocsPerformance:
    """Performance-focused tests using mock tools for consistent baselines."""

    @pytest.fixture
    def runner(self) -> SyncDocsRunner:
        return SyncDocsRunner(
            workspace_dir=DEFAULT_WORKSPACE,
            use_mcp=False,
            use_cli=False,
        )

    @pytest.mark.slow
    def test_timing_under_threshold(self, runner: SyncDocsRunner):
        """Test that /sync-docs completes within time budget."""
        case = load_test_case("case_001_tdd_api_change")

        result = runner.run(
            task=case["task"],
            test_case_id="timing_test",
            mock_tools=True,
        )

        # Mock should complete in < 120s, real in < 3 min
        max_duration_ms = 120_000 if result.api_calls < 5 else 180_000
        assert result.total_duration_ms < max_duration_ms, (
            f"Sync-docs took {result.total_duration_ms}ms, "
            f"expected < {max_duration_ms}ms"
        )

    @pytest.mark.slow
    def test_token_efficiency(self, runner: SyncDocsRunner):
        """Test that token usage is reasonable."""
        case = load_test_case("case_001_tdd_api_change")

        result = runner.run(
            task=case["task"],
            test_case_id="token_test",
            mock_tools=True,
        )

        assert result.output_tokens < 50_000, (
            f"Output tokens ({result.output_tokens}) exceeds budget"
        )


# =========================================================================
# Quick smoke test
# =========================================================================

def test_smoke():
    """Quick smoke test to verify the framework works."""
    from .metrics import get_standard_metrics, _has_eval_key
    from .runner import SyncDocsRunner, MCP_TOOL_PREFIX

    assert MCP_TOOL_PREFIX == "mcp__context-helper-synapse__"

    # CLI mode doesn't need API key
    runner_cli = SyncDocsRunner(use_cli=True)
    assert runner_cli is not None
    assert runner_cli.use_cli is True
    assert runner_cli.client is None

    if _has_eval_key():
        metrics = get_standard_metrics(
            expected_docs=["content/90_Architecture/TDDs/test-tdd.md"],
        )
        assert len(metrics) > 0

    # API runner requires ANTHROPIC_API_KEY
    anthropic_key = (
        os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("DEEPEVAL_ANTHROPIC_API_KEY")
    )
    if anthropic_key:
        runner = SyncDocsRunner(use_cli=False)
        assert runner is not None
        assert runner.client is not None
    else:
        with pytest.raises(RuntimeError, match="No Anthropic API key found"):
            SyncDocsRunner(use_cli=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
