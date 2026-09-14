"""Adapters know about a language and a stack. Nothing below this package does.

An adapter answers four questions and nothing else: where are the entities,
where are the surfaces, where are the entry points, and what calls what. The
core does the fixpoint, the reconciliation and the gate against the artifact an
adapter emits, which is what makes a second stack a day's work rather than a
fork.

Two of the registered adapters read *routes and contracts* rather than a stack:
`treesitter-routes` and `structured-spec` wrap the shared discovery engine
(`flows.discovery`) and project its obligation inventory onto the CORE adapter
contract. The bridge and the multi-adapter merge live here so every adapter
speaks the one shape the fixpoint, reconcile and gate already read.
"""

from __future__ import annotations

from types import ModuleType

# Registry entries are dotted-path strings, imported lazily by `load`. Nothing
# here imports cli, a probe, or the browser seam at module load -- the whole
# point of the strings is that adding a route reader does not drag the runtime
# side into every `import capcov.adapters`.
REGISTRY = {
    "python-fastapi-sqlalchemy": "capcov.adapters.python_fastapi_sqlalchemy",
    "treesitter-routes": "capcov.adapters.treesitter_routes",
    "structured-spec": "capcov.adapters.structured_spec",
}


def load(name: str) -> ModuleType:
    import importlib

    if name not in REGISTRY:
        raise SystemExit(
            f"unknown adapter {name!r}; have: {', '.join(sorted(REGISTRY))}"
        )
    return importlib.import_module(REGISTRY[name])


# --------------------------------------------------------------------------
# The obligation -> entity/surface bridge (route/contract adapters).
#
# The route world has surfaces, never DB tables; the core reconcile is
# entity-centric. The core adapter interface note settles it: "entity is any
# obligation identity." So each surface obligation becomes a core ENTITY and a
# core SURFACE bound to itself at hop 0 -- the fixpoint then emits exactly one
# capability (entity=id, surface=id, operations=[verb->CRUD], evidence
# hops:0/kind:"direct") per route, and the four cells read for a route target as
# both / static_only (coverage gap) / runtime_only (undiscovered surface).

# HTTP verb -> CRUD. Weak but declared (R2): the browser has no faithful source
# for per-operation coverage, so this is the honest static claim, no more. Verbs
# outside the set (HEAD, OPTIONS, a route with no method) claim no operation
# rather than guess one.
_VERB_TO_CRUD = {
    "GET": "read",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

_ZERO_RESIDUE_SUMMARY = {
    "resolved_by_import": 0,
    "resolved_by_name": 0,
    "ambiguous": 0,
    "external": 0,
    "chained": 0,
    "builtin_shadowed": 0,
}


def build_core_dict(
    surface_records: list[dict],
    excluded_surfaces: dict,
    unresolved: list[dict],
) -> dict:
    """Assemble a CORE adapter dict from normalized surface records.

    Each record is ``{id, method, path, handler, file, line, module}`` where
    ``id`` is the ``"http:METHOD path"`` surface identity (the string a runtime
    probe must reproduce to land in `both`). The record's ``id`` is used as the
    fixpoint root key -- surface ids are unique, so a handler function serving
    two routes never cross-binds one route's entity onto the other's surface.

    `blind_spots`, `residue` and `residue_summary` are emitted REQUIRED-but-empty
    because `cli.cmd_discover` reads them unconditionally; a route reader has no
    call graph and therefore no residue. `excluded_surfaces` and `unresolved` are
    first-class top-level keys carrying the honest denominator (Property 3):
    verb-allowlist drops and the named limits of static reading, never dropped
    silently.
    """
    entities: list[dict] = []
    surfaces: list[dict] = []
    direct: dict[str, set[str]] = {}
    ops: dict[str, dict[str, set[str]]] = {}
    for record in surface_records:
        sid = record["id"]
        root = sid  # unique node id: one route, one entity, no cross-binding.
        entities.append(
            {
                "name": sid,
                "symbol": None,
                "module": record.get("module"),
                "file": record.get("file"),
                "line": record.get("line"),
            }
        )
        surfaces.append(
            {
                "id": sid,
                "kind": "http",
                "method": record.get("method"),
                "path": record.get("path"),
                "handler": root,
                # The source-level handler name when the query captured one; the
                # node id above is what the fixpoint keys on.
                "handler_symbol": record.get("handler"),
                "file": record.get("file"),
                "line": record.get("line"),
                "mounted": True,
            }
        )
        direct[root] = {sid}
        crud = _VERB_TO_CRUD.get((record.get("method") or "").upper())
        if crud:
            ops[root] = {sid: {crud}}
    entities.sort(key=lambda e: e["name"])
    surfaces.sort(key=lambda s: (s["path"] or "", s["method"] or "", s["id"]))
    return {
        "entities": entities,
        "surfaces": surfaces,
        "_direct": direct,
        "_calls": {},
        "_ops": ops,
        "_evidence": {},
        "residue": [],
        "residue_summary": dict(_ZERO_RESIDUE_SUMMARY),
        "blind_spots": [],
        "excluded_surfaces": excluded_surfaces,
        "unresolved": unresolved,
    }


def project_flows_unresolved(inventory: dict, adapter_name: str) -> list[dict]:
    """The flows inventory's honest limits, projected to `{adapter, kind, reason}`.

    Two kinds of "could not resolve" reach the surface denominator (Property 3),
    each named, never dropped:

    * adapters that ran and produced no surface at all (`inventory["unresolved"]`);
    * `kind == "unresolved"` obligations -- a non-literal (dynamic) route path,
      and the boundary obligations that spell out what static route/spec reading
      cannot confirm (`boundary:*`).

    `kind` classifies each for the gate (T4): ``no-surfaces``, ``dynamic-route``,
    ``boundary``. Branch- and exception-candidate obligations are NOT included --
    they are behavioural obligations at the `outcomes` lane's granularity, not
    surfaces, and folding them into the surface denominator would fail the gate
    for the wrong reason.
    """
    out: list[dict] = []
    for entry in inventory.get("unresolved", []):
        out.append(
            {
                "adapter": adapter_name,
                "kind": "no-surfaces",
                "reason": entry.get("reason"),
                "flows_kind": entry.get("kind"),
            }
        )
    for obligation in inventory.get("obligations", []):
        if obligation.get("kind") != "unresolved":
            continue
        oid = obligation["id"]
        if oid.endswith(":dynamic-route"):
            kind = "dynamic-route"
        elif oid.startswith("boundary:"):
            kind = "boundary"
        else:
            kind = "unresolved"
        out.append(
            {
                "adapter": adapter_name,
                "kind": kind,
                "reason": obligation.get("reason") or oid,
                "id": oid,
                "source": obligation.get("source"),
            }
        )
    return out


# --------------------------------------------------------------------------
# Multi-adapter merge (`[[adapters]]`).
#
# Defined here; invoked by cli.cmd_discover (T2) after it runs each adapter. A
# single-adapter list returns that adapter's dict unchanged, so an existing
# `adapter = "..."` consumer sees byte-identical output.


def _obligation_ids(discovery: dict) -> set[str]:
    ids = {surface["id"] for surface in discovery.get("surfaces", [])}
    ids |= {entity["name"] for entity in discovery.get("entities", [])}
    return ids


def merge(discoveries: list[dict]) -> dict:
    """Merge several core adapter dicts into one, or raise on a shared id.

    The existing `duplicate obligation IDs` invariant, applied at the adapter
    boundary: a surface id or entity name emitted by two adapters is a collision
    the four-cell cannot represent (it keys on entity name), so the merge raises
    rather than silently letting one clobber the other. Qualify the surfaces (a
    per-adapter prefix) to keep them distinct.
    """
    if not discoveries:
        raise ValueError("merge requires at least one adapter discovery")
    if len(discoveries) == 1:
        return discoveries[0]

    seen: set[str] = set()
    for discovery in discoveries:
        ids = _obligation_ids(discovery)
        clash = ids & seen
        if clash:
            raise ValueError(
                "duplicate obligation IDs across adapters: "
                + ", ".join(sorted(clash))
                + "; qualify separate application surfaces"
            )
        seen |= ids

    entities: list[dict] = []
    surfaces: list[dict] = []
    direct: dict[str, set[str]] = {}
    calls: dict[str, set[str]] = {}
    ops: dict[str, dict[str, set[str]]] = {}
    evidence: dict[str, list[dict]] = {}
    blind: list[dict] = []
    residue: list[dict] = []
    residue_summary = dict(_ZERO_RESIDUE_SUMMARY)
    excluded_surfaces: list[dict] = []
    unresolved: list[dict] = []

    for discovery in discoveries:
        entities.extend(discovery.get("entities", []))
        surfaces.extend(discovery.get("surfaces", []))
        for key, values in discovery.get("_direct", {}).items():
            direct.setdefault(key, set()).update(values)
        for key, values in discovery.get("_calls", {}).items():
            calls.setdefault(key, set()).update(values)
        for key, table_ops in discovery.get("_ops", {}).items():
            for table, verbs in table_ops.items():
                ops.setdefault(key, {}).setdefault(table, set()).update(verbs)
        for key, items in discovery.get("_evidence", {}).items():
            evidence.setdefault(key, []).extend(items)
        blind.extend(discovery.get("blind_spots", []))
        residue.extend(discovery.get("residue", []))
        for cell, count in discovery.get("residue_summary", {}).items():
            residue_summary[cell] = residue_summary.get(cell, 0) + count
        excluded = discovery.get("excluded_surfaces") or {"count": 0, "surfaces": []}
        excluded_surfaces.extend(excluded.get("surfaces", []))
        unresolved.extend(discovery.get("unresolved", []))

    entities.sort(key=lambda e: e["name"])
    surfaces.sort(key=lambda s: (s.get("path") or "", s.get("method") or "", s["id"]))
    return {
        "entities": entities,
        "surfaces": surfaces,
        "_direct": direct,
        "_calls": calls,
        "_ops": ops,
        "_evidence": evidence,
        "residue": residue,
        "residue_summary": residue_summary,
        "blind_spots": blind,
        "excluded_surfaces": {
            "count": len(excluded_surfaces),
            "surfaces": excluded_surfaces,
        },
        "unresolved": unresolved,
    }
