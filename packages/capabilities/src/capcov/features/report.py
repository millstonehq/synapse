"""Render a completeness vector as a table with Harvey-ball glyphs.

The glyph is a function of one feature's ROLLED (covered, total) pair, computed
in quarters. A feature with nothing to cover renders as '?' -- unassessed -- not
as full: an empty denominator is a question, never a green.
"""

from __future__ import annotations

import csv
import io

GLYPHS = ("○", "◔", "◑", "◕", "●")
COLUMNS = ("feature", "name", "parent", "kind", "status", "self_covered", "self_total",
           "covered", "total", "glyph")


def glyph(covered: int, total: int) -> str:
    if total <= 0:
        return "?"
    if covered >= total:
        return GLYPHS[4]
    if covered <= 0:
        return GLYPHS[0]
    quarter = round(4 * covered / total)
    return GLYPHS[max(1, min(3, quarter))]


def _rows(vector: dict) -> list[dict]:
    rows = []
    for r in vector["tree_rows"]:
        rows.append({**{k: r.get(k) for k in COLUMNS if k != "glyph"},
                     "glyph": "?" if r["status"] in ("unassessed", "deselected")
                     else glyph(r["covered"], r["total"])})
    return rows


def render(vector: dict, fmt: str = "md") -> str:
    if fmt == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
        writer.writeheader()
        for row in _rows(vector):
            writer.writerow(row)
        return buffer.getvalue()
    if fmt != "md":
        raise ValueError(f"unknown report format {fmt!r}; use md or csv")
    lines = [
        f"mandatory {vector['mandatory_covered']}/{vector['mandatory_total']} · "
        f"optional {vector['optional_covered']}/{vector['optional_total']} "
        f"({vector['optional_assessed']} assessed, {vector['optional_unassessed']} unassessed)",
        "",
        "| Feature | Kind | Status | Ball | Rolled | Own |",
        "|---|---|---|---|---|---|",
    ]
    depth = {vector["root"]: 0}
    for row in _rows(vector):
        parent = row["parent"]
        depth[row["feature"]] = 0 if parent is None else depth.get(parent, 0) + 1
        indent = "  " * depth[row["feature"]]
        lines.append(
            f"| {indent}{row['name']} | {row['kind']} | {row['status']} | {row['glyph']} | "
            f"{row['covered']}/{row['total']} | {row['self_covered']}/{row['self_total']} |"
        )
    return "\n".join(lines) + "\n"
