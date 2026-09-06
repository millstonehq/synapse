"""capcov flows: inventory -> model -> plan -> browser evidence -> coverage."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from .catalog import build_catalog, render_catalog
from .discovery import discover
from .model import digest, plan, reconcile


def read(path: str) -> dict:
    return json.loads(Path(path).read_text())


def emit(path: str, value: dict, check: bool = False) -> int:
    if check:
        if not Path(path).exists() or read(path) != value:
            print(f"capcov flows: stale artifact {path}; regenerate and review")
            return 1
        return 0
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="capcov flows")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("discover")
    d.add_argument("config")
    d.add_argument("--out", required=True)
    d.add_argument("--check", action="store_true")
    p = sub.add_parser("plan")
    p.add_argument("model")
    p.add_argument("--target", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--check", action="store_true")
    catalog = sub.add_parser(
        "catalog", help="derive flow families and source dependency candidates"
    )
    catalog.add_argument("inventory")
    catalog.add_argument("--out", required=True)
    catalog.add_argument("--check", action="store_true")
    catalog.add_argument("--report")
    catalog.add_argument("--focus", help="limit the human report, never the inventory denominator")
    catalog.add_argument(
        "--require-declarations",
        action="store_true",
        help="fail on unclassified declarations or unconsumed source files",
    )
    catalog.add_argument("--quiet", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("plan")
    r.add_argument("--inventory", required=True)
    r.add_argument("--config", required=True, help="re-discover to reject stale source evidence")
    r.add_argument("--out", required=True)
    r.add_argument("--timeout", type=int, default=180)
    # Parse runner argv after -- separately, so options may follow the plan.
    c = sub.add_parser("coverage")
    c.add_argument("inventory")
    c.add_argument("model")
    c.add_argument("plan")
    c.add_argument("--run")
    c.add_argument("--out", required=True)
    g = sub.add_parser("gate")
    g.add_argument("coverage")
    g.add_argument("--baseline", help="exact named failures, each with a reason; never covered")
    report = sub.add_parser("report")
    report.add_argument("coverage")
    report.add_argument("plan")
    report.add_argument("--out", required=True)
    runner = []
    if "--" in argv:
        separator = argv.index("--")
        argv, runner = argv[:separator], argv[separator + 1 :]
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            result = discover(Path(args.config).resolve())
        elif args.command == "catalog":
            result = build_catalog(read(args.inventory))
            if not args.quiet:
                print(result["summary"])
            if args.report:
                out = Path(args.report)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(render_catalog(result, args.focus))
        elif args.command == "plan":
            result = plan(read(args.model), args.target)
        elif args.command == "run":
            if not runner:
                raise ValueError("run requires a runner command after --")
            output_path = Path(args.out).resolve()
            if output_path in {Path(p).resolve() for p in (args.plan, args.inventory, args.config)}:
                raise ValueError("run output must not overwrite its inputs")
            output_path.unlink(missing_ok=True)
            execution_plan, inventory = read(args.plan), read(args.inventory)
            if discover(Path(args.config).resolve()) != inventory:
                raise ValueError("source inventory is stale; re-discover and review")
            # Private fresh path + nonce: a successful command cannot reuse yesterday's run.
            with tempfile.TemporaryDirectory(prefix="capcov-flow-") as directory:
                output = Path(directory) / "run.json"
                nonce = uuid.uuid4().hex
                env = {
                    **os.environ,
                    "CAPCOV_FLOW_PLAN": str(Path(args.plan).resolve()),
                    "CAPCOV_FLOW_OUT": str(output),
                    "CAPCOV_FLOW_NONCE": nonce,
                }
                proc = subprocess.run(runner, env=env, timeout=args.timeout, check=False)
                if not output.exists():
                    raise ValueError("runner produced no fresh outcome evidence")
                result = read(str(output))
                if result.get("nonce") != nonce:
                    raise ValueError("runner nonce does not match this execution")
                if result.get("plan_sha256") != digest(execution_plan):
                    raise ValueError("runner did not attest the exact plan")
                if discover(Path(args.config).resolve()) != inventory:
                    raise ValueError("sources changed during execution")
                result["inventory_sha256"] = digest(inventory)
                if proc.returncode != 0 or result.get("status") != "passed":
                    result["status"] = "failed"
                    emit(args.out, result)
                    return 1
        elif args.command == "coverage":
            result = reconcile(
                read(args.inventory),
                read(args.model),
                read(args.plan),
                read(args.run) if args.run else None,
            )
            print(f"capcov flows: {result['summary']}; assurance={result['assurance']}")
        elif args.command == "report":
            coverage, execution_plan = read(args.coverage), read(args.plan)
            lines = [
                f"# {coverage['scope']}",
                "",
                f"Target: {coverage['target']}. Evidence: {coverage['assurance']}.",
                "",
                f"Complete: **{coverage['complete']}**. "
                + ", ".join(f"{key}: {value}" for key, value in coverage["summary"].items()),
                "",
                "## Executable paths",
                "",
            ]
            for scenario in execution_plan["scenarios"]:
                steps = " → ".join(s["transition"] for s in scenario["steps"])
                lines.append(f"- **{scenario['id']}**: {steps}")
            lines.extend(["", "## Blocked flows", ""])
            for blocked in coverage["blocked"]:
                lines.append(f"- {blocked['transition']}: {blocked['reason']}")
            lines.extend(
                [
                    "",
                    "## Capability obligations",
                    "",
                    "| Obligation | Status | Flows | Evidence location |",
                    "|---|---|---|---|",
                ]
            )
            for row in coverage["rows"]:
                source = row.get("source", {})
                cells = [
                    row["id"],
                    row["status"],
                    ", ".join(row["transitions"]),
                    f"{source.get('file', '')}:{source.get('line', '')}",
                ]
                lines.append("| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |")
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("\n".join(lines) + "\n")
            return 0
        else:
            coverage = read(args.coverage)
            failures = set(coverage["failures"])
            baseline = read(args.baseline) if args.baseline else {}
            if any(
                not isinstance(reason, str) or not reason.strip() for reason in baseline.values()
            ):
                raise ValueError("every baseline failure requires a reason")
            new, obsolete = failures - set(baseline), set(baseline) - failures
            for failure in sorted(new):
                print(f"FAIL {failure}")
            for failure in sorted(obsolete):
                print(f"OBSOLETE baseline: {failure}")
            print(
                f"{len(failures)} total gaps; {len(failures & set(baseline))} baselined; "
                f"complete={coverage['complete']}"
            )
            return int(bool(new or obsolete))
        status = emit(args.out, result, getattr(args, "check", False))
        if (
            args.command == "catalog"
            and args.require_declarations
            and not result["declarations_accounted"]
        ):
            print(
                "capcov flows: FAIL -- declaration census or source-file accounting is incomplete"
            )
            return 1
        return status
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"capcov flows: {exc}")
        return 1
