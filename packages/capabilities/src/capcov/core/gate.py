"""Fail the build on anything unexplained -- and on any explanation that has
stopped being true.

An exemption list that only grows is a lie with a filename. Three rules keep
this one honest:

1. An entity in a failing cell with no exemption fails.
2. An exemption whose entity is no longer in the cell it exempts ALSO fails,
   naming itself for deletion. This is the rule usually missing, and without it
   the file rots into fiction while the build stays green.
3. Every exemption carries a reason and a date. An exemption with no reason is
   a silenced check.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .reconcile import FAILING_CELLS


class Failure:
    __slots__ = ("rule", "subject", "detail")

    def __init__(self, rule: str, subject: str, detail: str) -> None:
        self.rule, self.subject, self.detail = rule, subject, detail

    def __str__(self) -> str:
        return f"{self.rule}: {self.subject}\n    {self.detail}"


def load_exemptions(path: Path | None) -> tuple[dict[str, dict], list[Failure]]:
    if path is None or not path.exists():
        return {}, []
    doc = tomllib.loads(path.read_text())
    out: dict[str, dict] = {}
    problems: list[Failure] = []
    for item in doc.get("exempt", []):
        key = item.get("entity") or item.get("surface")
        if not key:
            problems.append(
                Failure("malformed-exemption", "<no entity or surface>", str(item))
            )
            continue
        missing = [f for f in ("reason", "date", "cell") if not item.get(f)]
        if missing:
            problems.append(
                Failure(
                    "incomplete-exemption",
                    key,
                    f"missing {', '.join(missing)}. An exemption with no reason is a "
                    "silenced check; an exemption with no cell exempts everything.",
                )
            )
            continue
        out[key] = item
    return out, problems


def gate(coverage: dict, exemptions_path: Path | None) -> list[Failure]:
    exemptions, failures = load_exemptions(exemptions_path)
    used: set[str] = set()

    for row in coverage["rows"]:
        entity, cell = row["entity"], row["cell"]
        exemption = exemptions.get(entity)
        if cell in FAILING_CELLS:
            if exemption is None:
                failures.append(
                    Failure(
                        f"unexplained-{cell}",
                        entity,
                        _explain(row),
                    )
                )
            elif exemption["cell"] != cell:
                used.add(entity)
                failures.append(
                    Failure(
                        "stale-exemption",
                        entity,
                        f"exempted as {exemption['cell']!r}, now {cell!r}. "
                        "The reason recorded no longer describes what is happening.",
                    )
                )
            else:
                used.add(entity)
        elif exemption is not None:
            used.add(entity)
            failures.append(
                Failure(
                    "obsolete-exemption",
                    entity,
                    f"exempted as {exemption['cell']!r} on {exemption['date']}, now "
                    f"{cell!r}. Delete the exemption -- it is no longer needed, and "
                    "a list that only grows stops being read.",
                )
            )

    for surface in coverage["unknown_surfaces"]:
        name = surface["surface"]
        exemption = exemptions.get(name)
        if exemption is None:
            failures.append(
                Failure(
                    "undiscovered-surface",
                    name,
                    "runtime reached this surface and discover never found it. "
                    f"It touched {', '.join(surface['entities'])}. Either the "
                    "adapter is missing an entry-point kind, or the target has "
                    "not declared it in capcov.toml.",
                )
            )
        else:
            used.add(name)

    for orphan in coverage["orphan_tests"]:
        failures.append(
            Failure(
                "orphan-test",
                orphan["test"],
                f"exercises {orphan['entity']!r}, which no longer exists. The "
                "capability was removed and its test kept passing.",
            )
        )

    for key in sorted(set(exemptions) - used):
        failures.append(
            Failure(
                "unused-exemption",
                key,
                "nothing in the coverage report matches this exemption. It names "
                "something that is gone; delete it.",
            )
        )

    return failures


def _explain(row: dict) -> str:
    if row["cell"] == "static_only":
        return (
            f"reachable from {', '.join(row['static_surfaces'][:3])}"
            f"{'...' if len(row['static_surfaces']) > 3 else ''} and no exercise "
            "touched it. This is a coverage gap: write the test."
        )
    if row["cell"] == "runtime_only":
        return (
            f"observed at {', '.join(row['runtime_surfaces'][:3])} and static "
            "analysis found no path. Either the adapter missed an entry point, "
            "or the access is dynamic -- check the blind-spot list."
        )
    return (
        "declared in the schema and neither reachable nor observed. Dead. "
        "Remove it, or say what still needs it."
    )
