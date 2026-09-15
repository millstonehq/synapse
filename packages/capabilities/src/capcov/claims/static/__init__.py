"""Static (SCIP-derived) claim inputs: the frozen primitive schema and its exporter.

``schema_static_v1.json`` is the frozen declaration set for section 29 of the
experiment plan -- every primitive static relation, its typed columns, the one
``index`` digest context column, the completeness witnesses and the two
compatibility relations. It is loaded here, never edited here: a change to it is
a schema version, not a patch.

``scip_facts`` turns a retained SCIP index (``runner.read_scip_index(...,
retain=True)`` or ``normalize_scip_json(..., retain=True)``) plus the
tree-sitter side's raw discover dict into a validated claims ``Bundle`` of facts
and evidence keyed by that index's digest.
"""

from __future__ import annotations

import json
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parent / "schema_static_v1.json"


def load_static_schema() -> dict:
    """The frozen static schema document (``{"schema_version", "relations", ...}``)."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


__all__ = ["SCHEMA_PATH", "load_static_schema"]
