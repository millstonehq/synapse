"""Join a static bundle into the claims judge: what ``--static BUNDLE.json`` adds.

``capcov gate --judge claims --receipt DIR`` judges a *run*.  A static bundle
(``capcov experiment claims static --static scip --out BUNDLE.json``, with the
base pack merged so its derived relations have their rules) accounts for the
same system *before* any run.  This module is the join between the two, and the
section it returns is written into ``judge.json`` under ``static``.

WHAT BINDS THEM
---------------
Nothing binds an index to a run by itself: a bundle is a statement about a tree,
a receipt a statement about a run of a build of one.  The witness that does is
``index_describes_run(index, run)`` -- emitted by the static producer for the
runs it was told this index describes (``scip_facts.export_bundle``'s
``describes_runs``) -- and the join reads it and nothing else:

* the bundle carries ``index_describes_run(IX, <this run>)``  -> ``bound``;
* it carries the relation, for other runs                     -> ``stale``;
* it carries no row of it at all                              -> ``unbound``.

Only ``bound`` reads a single row out of the bundle.  A bundle for another
commit is *stale*, in its own words, and never silently joined: an index that
describes some other run says nothing about this one, and quietly reporting its
dead entities beside this run's verdict would be exactly the "evidence from
another commit read as current" mistake.

WHAT IS REPORTED, AND WHAT IS NOT
---------------------------------
``routes`` (per surface, the ``static_capability_op`` rows: the entity and verb
a route statically binds), ``capabilities`` (per capability, its reflexion cell:
the convergences, divergences, absences and unresolved absences it participates
in), ``dead``, ``blocked`` (with the ``via`` symbol) and ``unresolved``.  Every
one of them is the static bundle's own derived row, re-derived here by the
stdlib kernel; ``kernel`` says so, because one kernel is not a differential.

``static_only`` is the one row this module derives itself: a surface the index
binds that the run never requested.  It is a negation over the runtime side, so
it is licensed only by that side's own completeness witness --
``replay_requests_closed(run)``, the replay producer's.  Without it
``runtime`` is ``unclosed`` and ``static_only`` is ``null``; with no request row
at all ``runtime`` is ``absent`` and it is ``null`` again.  A receipt that
enumerated its requests and closed them is the only case in which "not observed"
is a fact rather than a silence.

``underived`` names the relations this bundle has no rule and no fact for -- a
bundle exported without ``rules-static-v1`` merged derives no
``static_capability_op``, and an empty ``dead`` list from such a bundle must not
read as "nothing is dead".  Nothing here is an outcome, and nothing here moves
the judge's exit code: a static path is not a run.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..ir import Bundle, BundleIngestionError, bundle_from_json

#: The key the section is written under in ``judge.json``.
SECTION_KEY = "static"
#: The kernel that re-derives the bundle's rows here.  The stdlib one, always:
#: judging needs no optional tool, and one kernel is never a differential.
KERNEL = "python"

#: The witness that binds an index to a run.  Owned by the static producer.
DESCRIBES_RELATION = "index_describes_run"
#: The receipt's request rows and the replay producer's completeness witness.
REQUEST_RELATION = "replay_request"
REQUESTS_CLOSED_RELATION = "replay_requests_closed"

JOIN_BOUND = "bound"
JOIN_STALE = "stale"
JOIN_UNBOUND = "unbound"

RUNTIME_OBSERVED = "observed"
RUNTIME_UNCLOSED = "unclosed"
RUNTIME_ABSENT = "absent"

BIND_RELATION = "static_capability_op"
DEAD_RELATION = "static_entity_dead"
BLOCKED_RELATION = "static_entity_blocked"
ENTITY_UNRESOLVED_RELATION = "static_entity_unresolved"
CONVERGENCE_RELATION = "static_convergence"
DIVERGENCE_RELATION = "static_divergence"
ABSENCE_RELATION = "static_absence"
ABSENCE_UNRESOLVED_RELATION = "static_absence_unresolved"
MAP_RELATION = "capability_map"

#: The relations the section reports.  One this bundle cannot derive is named in
#: ``underived`` rather than reported as empty.
REPORTED_RELATIONS = (BIND_RELATION, DEAD_RELATION, BLOCKED_RELATION,
                      ENTITY_UNRESOLVED_RELATION, CONVERGENCE_RELATION,
                      DIVERGENCE_RELATION, ABSENCE_RELATION,
                      ABSENCE_UNRESOLVED_RELATION)
#: The reflexion cell, per capability: the four edge relations it can appear in.
CELL_RELATIONS = (CONVERGENCE_RELATION, DIVERGENCE_RELATION, ABSENCE_RELATION,
                  ABSENCE_UNRESOLVED_RELATION)

#: A surface id the replay side can be compared with: ``http:<METHOD> <path>``,
#: against a ``replay_request`` route ``<METHOD> <path>``.  A surface of any
#: other kind is not comparable with an HTTP request log, and saying it was
#: never observed would be a claim about a log that could not have carried it.
HTTP_SURFACE_PREFIX = "http:"


class StaticBundleError(ValueError):
    """The ``--static`` argument is not a readable static bundle.

    A usage error about the command line, in the class ``capcov.cli`` reports as
    exit 2 -- never a finding about the receipt and never a verdict.
    """


@dataclass(frozen=True)
class StaticBundle:
    """One static bundle as read: the validated IR and the digest of its bytes.

    The path it was read from is deliberately not carried: judge artifacts are
    publishable, so the section names the bundle by digest, as ``gate`` names
    the coverage artifact it judged.
    """

    bundle: Bundle
    sha256: str


def load(path: str | Path) -> StaticBundle:
    """Read and validate the bundle at ``path``, or raise ``StaticBundleError``.

    Validation happens here, before any judging, so an unreadable or malformed
    bundle is a named exit 2 on the command line rather than a traceback in the
    middle of a run or -- worse -- a silently empty static section.
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise StaticBundleError(f"cannot read the static bundle {str(path)!r}: {exc}") from exc
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StaticBundleError(
            f"the static bundle {str(path)!r} is not JSON: {exc}") from exc
    try:
        bundle = bundle_from_json(document, validate=True)
    except BundleIngestionError as exc:
        raise StaticBundleError(
            f"the static bundle {str(path)!r} is not a claim bundle: {exc}") from exc
    return StaticBundle(bundle, hashlib.sha256(raw).hexdigest())


def _fact_rows(bundle: Bundle, relation: str) -> list[tuple]:
    return [tuple(term.value for term in fact.terms)
            for fact in bundle.facts if fact.relation == relation]


def runtime_side(exported: Any, run: str) -> dict[str, Any]:
    """The run's request routes and whether the replay producer closed them.

    ``exported`` is the receipt exporter's result (``replay_facts.ExportResult``)
    the judge already built; a receipt it refused carries no bundle, and that is
    reported as no runtime side at all rather than as an empty one.
    """
    bundle = getattr(exported, "bundle", None)
    if bundle is None:
        return {"routes": frozenset(), "routes_closed": False}
    routes = frozenset(row[3] for row in _fact_rows(bundle, REQUEST_RELATION)
                       if row[0] == run)
    closed = any(row[0] == run
                 for row in _fact_rows(bundle, REQUESTS_CLOSED_RELATION))
    return {"routes": routes, "routes_closed": closed}


def _derivable(bundle: Bundle) -> frozenset[str]:
    """Relations this bundle can produce a row of: a rule heads it, or it has facts."""
    return frozenset({rule.head.relation for rule in bundle.rules}
                     | {fact.relation for fact in bundle.facts})


def _closure(bundle: Bundle) -> dict[str, list[tuple]]:
    from ..evaluator import evaluate

    report = evaluate(bundle)
    if report.status.value != "complete":
        raise ValueError(f"the static bundle did not evaluate: {report.message}")
    return {name: [tuple(row) for row in rows] for name, rows in report.relations}


def _route_of(surface: str) -> str | None:
    """The ``replay_request`` route an HTTP surface would be requested as."""
    if not surface.startswith(HTTP_SURFACE_PREFIX):
        return None
    return surface[len(HTTP_SURFACE_PREFIX):]


def _join_status(bundle: Bundle, run: str) -> dict[str, Any]:
    describes = sorted(set(_fact_rows(bundle, DESCRIBES_RELATION)))
    indexes = sorted({row[0] for row in describes if row[1] == run})
    described_runs = sorted({row[1] for row in describes})
    if indexes:
        return {"status": JOIN_BOUND, "run": run, "indexes": indexes,
                "describes_runs": described_runs,
                "message": f"{DESCRIBES_RELATION} binds this bundle to run {run!r}"}
    if described_runs:
        return {"status": JOIN_STALE, "run": run, "indexes": [],
                "describes_runs": described_runs,
                "message": (f"the static bundle describes "
                            f"{', '.join(repr(name) for name in described_runs[:5])}"
                            + (" ..." if len(described_runs) > 5 else "")
                            + f", not run {run!r}; it is evidence about another run and "
                              f"is not joined")}
    return {"status": JOIN_UNBOUND, "run": run, "indexes": [], "describes_runs": [],
            "message": (f"the static bundle carries no {DESCRIBES_RELATION} row, so nothing "
                        f"binds it to run {run!r}; export it with the run it describes")}


def _cells(rows: Mapping[str, list[list[Any]]],
           mapped: Iterable[str]) -> dict[str, dict[str, list[str]]]:
    """Per capability, the reflexion cell: who it converges/diverges with, what is absent."""
    names = set(mapped)
    for relation in CELL_RELATIONS:
        for row in rows.get(relation, ()):
            names.update(row)
    cells: dict[str, dict[str, list[str]]] = {}
    for name in sorted(names):
        cells[name] = {relation: sorted({row[1] for row in rows.get(relation, ())
                                         if row[0] == name})
                       for relation in CELL_RELATIONS}
    return cells


def _empty_section(static: StaticBundle, join: dict[str, Any], runtime: str,
                   runtime_routes: int) -> dict[str, Any]:
    return {
        "bundle": {"sha256": static.sha256, "facts": len(static.bundle.facts),
                   "rules": len(static.bundle.rules),
                   "relations": len(static.bundle.relations)},
        "join": join,
        "kernel": KERNEL,
        "runtime": runtime,
        "runtime_routes": runtime_routes,
        "routes": None,
        "capabilities": None,
        "dead": None,
        "blocked": None,
        "unresolved": None,
        "static_only": None,
        # the witness that licenses that negation, named where it is read: a
        # "not observed" that cites nothing is a silence wearing a verdict
        "static_only_licensed_by": None,
        "surfaces_not_comparable": None,
        "underived": None,
    }


def section(static: StaticBundle, *, run: str, routes: Iterable[str],
            routes_closed: bool) -> dict[str, Any]:
    """The ``static`` section of ``judge.json``: the join, and what it licenses.

    ``routes`` is what the receipt's ``replay_request`` rows requested and
    ``routes_closed`` whether the receipt's own witness closed that set.  A
    bundle that is not bound to ``run`` is reported as exactly that, with no
    rows: the section is never a statement about a run the bundle does not
    describe.
    """
    routes = frozenset(routes)
    runtime = (RUNTIME_ABSENT if not routes
               else RUNTIME_OBSERVED if routes_closed else RUNTIME_UNCLOSED)
    join = _join_status(static.bundle, run)
    document = _empty_section(static, join, runtime, len(routes))
    if join["status"] != JOIN_BOUND:
        return document
    try:
        closure = _closure(static.bundle)
    except (ValueError, RecursionError) as exc:
        # the bundle validated and then would not evaluate: an operational
        # failure of this join, named, with no rows and no effect on the verdict
        document["error"] = str(exc)[:4000]
        return document
    indexes = set(join["indexes"])
    derivable = _derivable(static.bundle)

    def rows(relation: str) -> list[list[Any]]:
        return sorted([list(row[1:]) for row in closure.get(relation, ())
                       if row[0] in indexes])

    binds = rows(BIND_RELATION)
    document["underived"] = [name for name in REPORTED_RELATIONS if name not in derivable]
    document["routes"] = {}
    for surface, entity, verb in binds:
        document["routes"].setdefault(surface, []).append([entity, verb])
    document["dead"] = rows(DEAD_RELATION)
    document["blocked"] = rows(BLOCKED_RELATION)
    document["unresolved"] = rows(ENTITY_UNRESOLVED_RELATION)
    document["capabilities"] = _cells(
        {relation: rows(relation) for relation in CELL_RELATIONS},
        {row[1] for row in rows(MAP_RELATION)} if MAP_RELATION in derivable else ())
    if BIND_RELATION in derivable and runtime == RUNTIME_OBSERVED:
        # the only row this module derives, and the only negation in the
        # section: licensed by the replay producer's own closed request set
        document["static_only"] = [[surface, entity, verb]
                                   for surface, entity, verb in binds
                                   if (route := _route_of(surface)) is not None
                                   and route not in routes]
        document["static_only_licensed_by"] = REQUESTS_CLOSED_RELATION
        document["surfaces_not_comparable"] = sorted(
            {surface for surface, _entity, _verb in binds if _route_of(surface) is None})
    return document


def summary_line(document: Mapping[str, Any]) -> str:
    """One line for stdout: what the bundle is, and what the join made of it."""
    join = document["join"]
    head = f"static bundle {document['bundle']['sha256'][:12]} {join['status']}"
    if join["status"] != JOIN_BOUND:
        return f"{head}: {join['message']}"
    static_only = document["static_only"]
    return (f"{head} to run {join['run']}: {len(document['routes'])} surface(s) bound, "
            f"{len(document['dead'])} dead, {len(document['blocked'])} blocked; "
            f"runtime {document['runtime']}, static_only "
            f"{len(static_only) if static_only is not None else '-'} "
            f"(kernel {document['kernel']})")


__all__ = ["SECTION_KEY", "KERNEL", "DESCRIBES_RELATION", "REQUEST_RELATION",
           "REQUESTS_CLOSED_RELATION", "JOIN_BOUND", "JOIN_STALE", "JOIN_UNBOUND",
           "RUNTIME_OBSERVED", "RUNTIME_UNCLOSED", "RUNTIME_ABSENT", "BIND_RELATION",
           "DEAD_RELATION", "BLOCKED_RELATION", "ENTITY_UNRESOLVED_RELATION",
           "CONVERGENCE_RELATION", "DIVERGENCE_RELATION", "ABSENCE_RELATION",
           "ABSENCE_UNRESOLVED_RELATION", "MAP_RELATION", "REPORTED_RELATIONS",
           "CELL_RELATIONS", "StaticBundleError", "StaticBundle", "load",
           "runtime_side", "section", "summary_line"]
