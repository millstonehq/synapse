"""
CLI for /discover evaluations.

Usage:
    # Run single test case
    discover-eval run case_001_auth --tag baseline

    # Run all test cases
    discover-eval run-all --tag baseline

    # Compare runs
    discover-eval compare baseline experiment

    # List available test cases
    discover-eval list-cases

    # Show run history
    discover-eval history
"""

import sys
from pathlib import Path
from datetime import datetime

import yaml
from rich.console import Console
from rich.table import Table

from .runner import DiscoverRunner, run_discovery
from .report import generate_report, load_runs


EVALS_DIR = Path(__file__).parent.parent
TEST_CASES_DIR = EVALS_DIR / "test_cases"
RESULTS_DIR = EVALS_DIR / "results"

console = Console()


def cmd_run(case_id: str, tag: str = None, mock: bool = False, api: bool = False, baseline: bool = False):
    """Run a single test case."""
    case_file = TEST_CASES_DIR / f"{case_id}.yaml"
    if not case_file.exists():
        console.print(f"[red]Test case not found: {case_id}[/red]")
        console.print(f"Available cases: {', '.join(c.stem for c in TEST_CASES_DIR.glob('*.yaml'))}")
        return 1

    with open(case_file) as f:
        case = yaml.safe_load(f)

    run_id = f"{tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if tag else None

    # Default to CLI mode (OAuth, 5x higher rate limits) unless --api or --mock
    use_cli = not api and not mock
    use_mcp = not use_cli and not mock
    mode_label = "baseline" if baseline else ("mock" if mock else ("API" if api else "CLI (OAuth)"))

    console.print(f"[bold]Running:[/bold] {case['name']}")
    console.print(f"[dim]Mode: {mode_label} | {case['task'][:100]}...[/dim]")
    console.print()

    result = run_discovery(
        task=case["task"],
        test_case_id=case_id,
        results_dir=RESULTS_DIR,
        mock_tools=mock,
        use_cli=use_cli,
        use_mcp=use_mcp,
        baseline=baseline,
    )

    if result.error:
        console.print(f"[red]Error: {result.error}[/red]")
        return 1

    console.print()
    console.print("[bold green]Complete![/bold green]")
    console.print(f"  Duration: {result.total_duration_ms:.0f}ms")
    console.print(f"  Tokens: {result.input_tokens} in / {result.output_tokens} out")
    console.print(f"  Files: {len(result.selected_files)}")
    console.print(f"  Slices: {len(result.selected_slices)}")

    # Show tool usage summary
    summary = result.get_tool_call_summary()
    mcp_ratio = summary["mcp_ratio"]
    ratio_color = "green" if mcp_ratio >= 0.7 else "yellow" if mcp_ratio >= 0.5 else "red"
    console.print(f"  Tool Usage: [{ratio_color}]{mcp_ratio:.0%} MCP[/{ratio_color}] "
                  f"({summary['mcp_count']} MCP, {summary['default_count']} default)")
    if summary["default_tools"]:
        console.print(f"    [dim]Default tools used: {', '.join(summary['default_tools'])}[/dim]")

    return 0


def cmd_run_all(tag: str = None, mock: bool = False, api: bool = False, baseline: bool = False):
    """Run all test cases."""
    cases = list(TEST_CASES_DIR.glob("*.yaml"))
    if not cases:
        console.print("[red]No test cases found[/red]")
        return 1

    console.print(f"[bold]Running {len(cases)} test cases[/bold]")

    results = []
    for case_file in cases:
        case_id = case_file.stem
        console.print(f"\n[cyan]>>> {case_id}[/cyan]")
        exit_code = cmd_run(case_id, tag, mock, api, baseline)
        results.append((case_id, exit_code))

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    passed = sum(1 for _, code in results if code == 0)
    console.print(f"  Passed: {passed}/{len(results)}")

    return 0 if passed == len(results) else 1


def cmd_compare(baseline: str, experiment: str, output: str = None):
    """Compare two runs."""
    generate_report(
        baseline_tag=baseline,
        experiment_tag=experiment,
        results_dir=RESULTS_DIR,
        output_format="markdown" if output else "rich",
    )
    return 0


def cmd_list_cases():
    """List available test cases."""
    cases = list(TEST_CASES_DIR.glob("*.yaml"))

    table = Table(title="Available Test Cases")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Description")

    for case_file in sorted(cases):
        with open(case_file) as f:
            case = yaml.safe_load(f)
        table.add_row(
            case_file.stem,
            case.get("name", ""),
            (case.get("description", "")[:50] + "...") if case.get("description") else "",
        )

    console.print(table)
    return 0


def cmd_history():
    """Show run history."""
    runs = load_runs(RESULTS_DIR)

    if not runs:
        console.print("[dim]No runs found[/dim]")
        return 0

    table = Table(title="Run History")
    table.add_column("Run ID", style="cyan")
    table.add_column("Test Case")
    table.add_column("Timestamp")
    table.add_column("Duration")
    table.add_column("Tokens")

    for run in sorted(runs, key=lambda r: r.timestamp, reverse=True)[:20]:
        table.add_row(
            run.run_id,
            run.test_case_id,
            run.timestamp[:19] if run.timestamp else "",
            f"{run.total_duration_ms:.0f}ms",
            f"{run.input_tokens + run.output_tokens}",
        )

    console.print(table)
    return 0


def main():
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="/discover evaluation framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a single test case")
    run_parser.add_argument("case_id", help="Test case ID (e.g., case_001_auth)")
    run_parser.add_argument("--tag", help="Tag for this run (for comparison)")
    run_parser.add_argument("--mock", action="store_true", help="Use mock tool responses")
    run_parser.add_argument(
        "--api", action="store_true",
        help="Use direct API key instead of CLI (OAuth). Default is CLI mode with higher rate limits.",
    )
    run_parser.add_argument(
        "--baseline", action="store_true",
        help="Run baseline (no slash command, no MCP tools) for comparison.",
    )

    # run-all command
    run_all_parser = subparsers.add_parser("run-all", help="Run all test cases")
    run_all_parser.add_argument("--tag", help="Tag for this run")
    run_all_parser.add_argument("--mock", action="store_true", help="Use mock tool responses")
    run_all_parser.add_argument(
        "--api", action="store_true",
        help="Use direct API key instead of CLI (OAuth). Default is CLI mode with higher rate limits.",
    )
    run_all_parser.add_argument(
        "--baseline", action="store_true",
        help="Run baseline (no slash command, no MCP tools) for comparison.",
    )

    # compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two runs")
    compare_parser.add_argument("baseline", help="Baseline run tag")
    compare_parser.add_argument("experiment", help="Experiment run tag")
    compare_parser.add_argument("--output", help="Output file (markdown)")

    # list-cases command
    subparsers.add_parser("list-cases", help="List available test cases")

    # history command
    subparsers.add_parser("history", help="Show run history")

    args = parser.parse_args()

    if args.command == "run":
        sys.exit(cmd_run(args.case_id, args.tag, args.mock, args.api, args.baseline))
    elif args.command == "run-all":
        sys.exit(cmd_run_all(args.tag, args.mock, args.api, args.baseline))
    elif args.command == "compare":
        sys.exit(cmd_compare(args.baseline, args.experiment, args.output))
    elif args.command == "list-cases":
        sys.exit(cmd_list_cases())
    elif args.command == "history":
        sys.exit(cmd_history())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
