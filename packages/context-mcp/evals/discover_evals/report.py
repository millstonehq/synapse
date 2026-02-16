"""
Report generator for /discover evaluation runs.

Compares baseline vs. experiment runs and generates reports showing:
- Score improvements/regressions
- Timing changes
- Token usage changes
"""

import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional

import orjson
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


@dataclass
class RunSummary:
    """Summary of a single evaluation run."""

    run_id: str
    test_case_id: str
    timestamp: str

    # Scores (from deepeval)
    scores: dict[str, float]

    # Performance
    total_duration_ms: float
    input_tokens: int
    output_tokens: int
    api_calls: int

    # Selection
    files_selected: int
    slices_selected: int

    @classmethod
    def from_result_file(cls, filepath: Path) -> "RunSummary":
        """Load from a result JSON file."""
        with open(filepath, "rb") as f:
            data = orjson.loads(f.read())

        return cls(
            run_id=data.get("run_id", "unknown"),
            test_case_id=data.get("test_case_id", "unknown"),
            timestamp=data.get("timestamp", ""),
            scores=data.get("scores", {}),
            total_duration_ms=data.get("total_duration_ms", 0),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            api_calls=data.get("api_calls", 0),
            files_selected=len(data.get("selected_files", [])),
            slices_selected=len(data.get("selected_slices", [])),
        )


@dataclass
class Comparison:
    """Comparison between baseline and experiment."""

    metric: str
    baseline: float
    experiment: float
    delta: float
    delta_pct: float
    improved: bool


def load_runs(results_dir: Path, tag: Optional[str] = None) -> list[RunSummary]:
    """Load all runs from results directory, optionally filtered by tag."""
    runs = []
    for filepath in results_dir.glob("*.json"):
        try:
            summary = RunSummary.from_result_file(filepath)
            if tag is None or tag in summary.run_id:
                runs.append(summary)
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")
    return runs


def compare_runs(baseline: RunSummary, experiment: RunSummary) -> list[Comparison]:
    """Compare two runs and return metric comparisons."""
    comparisons = []

    # Compare scores
    all_metrics = set(baseline.scores.keys()) | set(experiment.scores.keys())
    for metric in all_metrics:
        b_val = baseline.scores.get(metric, 0)
        e_val = experiment.scores.get(metric, 0)
        delta = e_val - b_val
        delta_pct = (delta / b_val * 100) if b_val != 0 else 0

        comparisons.append(
            Comparison(
                metric=f"score:{metric}",
                baseline=b_val,
                experiment=e_val,
                delta=delta,
                delta_pct=delta_pct,
                improved=delta > 0,
            )
        )

    # Compare performance (lower is better for these)
    perf_metrics = [
        ("duration_ms", baseline.total_duration_ms, experiment.total_duration_ms),
        ("input_tokens", baseline.input_tokens, experiment.input_tokens),
        ("output_tokens", baseline.output_tokens, experiment.output_tokens),
        ("api_calls", baseline.api_calls, experiment.api_calls),
    ]

    for name, b_val, e_val in perf_metrics:
        delta = e_val - b_val
        delta_pct = (delta / b_val * 100) if b_val != 0 else 0

        comparisons.append(
            Comparison(
                metric=f"perf:{name}",
                baseline=b_val,
                experiment=e_val,
                delta=delta,
                delta_pct=delta_pct,
                improved=delta < 0,  # Lower is better
            )
        )

    return comparisons


def generate_report(
    baseline_tag: str,
    experiment_tag: str,
    results_dir: Path,
    output_format: str = "rich",
) -> str:
    """
    Generate a comparison report between two tagged runs.

    Args:
        baseline_tag: Tag to identify baseline runs
        experiment_tag: Tag to identify experiment runs
        results_dir: Directory containing result files
        output_format: 'rich' for terminal, 'markdown' for file

    Returns:
        Report string (or empty if using rich console)
    """
    console = Console()

    # Load runs
    baseline_runs = load_runs(results_dir, baseline_tag)
    experiment_runs = load_runs(results_dir, experiment_tag)

    if not baseline_runs:
        console.print(f"[red]No baseline runs found with tag: {baseline_tag}[/red]")
        return ""

    if not experiment_runs:
        console.print(f"[red]No experiment runs found with tag: {experiment_tag}[/red]")
        return ""

    # Group by test case
    baseline_by_case = {r.test_case_id: r for r in baseline_runs}
    experiment_by_case = {r.test_case_id: r for r in experiment_runs}

    common_cases = set(baseline_by_case.keys()) & set(experiment_by_case.keys())

    if not common_cases:
        console.print("[red]No common test cases between runs[/red]")
        return ""

    if output_format == "rich":
        _print_rich_report(
            console,
            baseline_tag,
            experiment_tag,
            baseline_by_case,
            experiment_by_case,
            common_cases,
        )
        return ""
    else:
        return _generate_markdown_report(
            baseline_tag,
            experiment_tag,
            baseline_by_case,
            experiment_by_case,
            common_cases,
        )


def _print_rich_report(
    console: Console,
    baseline_tag: str,
    experiment_tag: str,
    baseline_by_case: dict,
    experiment_by_case: dict,
    common_cases: set,
):
    """Print rich terminal report."""
    console.print()
    console.print(
        Panel(
            f"[bold]Comparing:[/bold] {baseline_tag} vs {experiment_tag}",
            title="/discover Evaluation Report",
            box=box.DOUBLE,
        )
    )

    for case_id in sorted(common_cases):
        baseline = baseline_by_case[case_id]
        experiment = experiment_by_case[case_id]
        comparisons = compare_runs(baseline, experiment)

        # Create table for this test case
        table = Table(
            title=f"Test Case: {case_id}",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Metric", style="dim")
        table.add_column("Baseline", justify="right")
        table.add_column("Experiment", justify="right")
        table.add_column("Delta", justify="right")
        table.add_column("", justify="center")

        for comp in comparisons:
            # Format delta with color
            if comp.improved:
                delta_str = f"[green]{comp.delta:+.2f} ({comp.delta_pct:+.1f}%)[/green]"
                status = "[green]:heavy_check_mark:[/green]"
            elif comp.delta == 0:
                delta_str = f"[dim]{comp.delta:.2f}[/dim]"
                status = "[dim]-[/dim]"
            else:
                delta_str = f"[red]{comp.delta:+.2f} ({comp.delta_pct:+.1f}%)[/red]"
                status = "[red]:x:[/red]"

            table.add_row(
                comp.metric,
                f"{comp.baseline:.2f}",
                f"{comp.experiment:.2f}",
                delta_str,
                status,
            )

        console.print(table)
        console.print()

    # Summary statistics
    total_improvements = 0
    total_regressions = 0

    for case_id in common_cases:
        comparisons = compare_runs(
            baseline_by_case[case_id], experiment_by_case[case_id]
        )
        for comp in comparisons:
            if comp.improved:
                total_improvements += 1
            elif comp.delta != 0:
                total_regressions += 1

    summary_table = Table(title="Summary", box=box.SIMPLE)
    summary_table.add_column("Stat", style="bold")
    summary_table.add_column("Value", justify="right")

    summary_table.add_row("Test Cases", str(len(common_cases)))
    summary_table.add_row(
        "Improvements", f"[green]{total_improvements}[/green]"
    )
    summary_table.add_row(
        "Regressions", f"[red]{total_regressions}[/red]"
    )

    console.print(summary_table)


def _generate_markdown_report(
    baseline_tag: str,
    experiment_tag: str,
    baseline_by_case: dict,
    experiment_by_case: dict,
    common_cases: set,
) -> str:
    """Generate markdown report."""
    lines = [
        "# /discover Evaluation Report",
        "",
        f"**Baseline:** {baseline_tag}",
        f"**Experiment:** {experiment_tag}",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
    ]

    for case_id in sorted(common_cases):
        baseline = baseline_by_case[case_id]
        experiment = experiment_by_case[case_id]
        comparisons = compare_runs(baseline, experiment)

        lines.append(f"## Test Case: {case_id}")
        lines.append("")
        lines.append("| Metric | Baseline | Experiment | Delta |")
        lines.append("|--------|----------|------------|-------|")

        for comp in comparisons:
            status = "improved" if comp.improved else ("same" if comp.delta == 0 else "regressed")
            lines.append(
                f"| {comp.metric} | {comp.baseline:.2f} | "
                f"{comp.experiment:.2f} | {comp.delta:+.2f} ({status}) |"
            )

        lines.append("")

    return "\n".join(lines)


def main():
    """CLI for report generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate /discover evaluation report")
    parser.add_argument("baseline", help="Baseline run tag")
    parser.add_argument("experiment", help="Experiment run tag")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path(__file__).parent.parent / "results",
        help="Results directory",
    )
    parser.add_argument(
        "--format",
        choices=["rich", "markdown"],
        default="rich",
        help="Output format",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file (for markdown format)",
    )

    args = parser.parse_args()

    report = generate_report(
        baseline_tag=args.baseline,
        experiment_tag=args.experiment,
        results_dir=args.results_dir,
        output_format=args.format,
    )

    if args.format == "markdown" and report:
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report saved to: {args.output}")
        else:
            print(report)


if __name__ == "__main__":
    main()
