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
is a fact rather than a silence.  Closure is not the whole of it: the comparison
is by route spelling, ``replay_request`` mandates no spelling, and a run whose
routes are not ``<METHOD> <path>`` is named in ``runtime_routes_not_comparable``
with ``static_only`` withheld -- a naming difference is not an unrequested route.

``underived`` names the reported relations this bundle cannot derive, and
``withheld`` says of every null row key why it is null.  Both are the same rule
applied twice.  A bundle exported without ``rules-static-v1`` merged has no rule
and no fact for ``static_edge``, so nothing that reads it derives anything and
nothing that negates it is anything but a negation over silence -- an empty
``dead`` list from such a bundle must not read as "nothing is dead", and an
empty ``static_absence`` must not read as "the model and the code agree".  And a
relation the kernel *can* derive is still withheld when the completeness witness
its negation is licensed by carries no row for this index: ``closure_witnesses``
reports which of ``call_graph_closed``, ``capability_map_closed`` and
``capability_edge_closed`` the bound index carries, and the key each licenses is
``null`` rather than ``[]`` when it does not.  Nothing here is an outcome, and
nothing here moves the judge's exit code: a static path is not a run.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from ..ir import Bundle, BundleIngestionError, bundle_from_json

#: The key the section is written under in ``judge.json``.
SECTION_KEY = "static"
#: The kernel that re-derives the bundle's rows here.  The stdlib one, always:
#: judging needs no optional tool, and one kernel is never a differential.
KERNEL = "python"
#: The bounds it evaluates under.  ``None`` is the evaluator's own defaults,
#: which are finite on purpose (rows, iterations, provenance nodes, seconds); a
#: bundle that exceeds them does not close, and this join reports that as its
#: own operational failure -- named, with no rows -- never as a verdict and
#: never as a traceback over one already decided.
LIMITS: Any = None

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

#: The completeness witnesses the reported relations are negated under, each
#: owned by the producer that can know the closure it certifies and each keyed
#: by the index it is about.
CALL_GRAPH_CLOSED_RELATION = "call_graph_closed"
MAP_CLOSED_RELATION = "capability_map_closed"
EDGE_CLOSED_RELATION = "capability_edge_closed"
CLOSURE_WITNESSES = (CALL_GRAPH_CLOSED_RELATION, MAP_CLOSED_RELATION,
                     EDGE_CLOSED_RELATION)

#: Per reported relation, the witnesses that license *its* negation, from the
#: pack's own rules: ``static_divergence`` negates ``capability_edge`` under
#: ``capability_edge_closed``; ``static_absence`` negates ``static_low_edge``
#: under ``capability_map_closed`` (through ``static_low_edge_closed``) and
#: ``call_graph_closed``; ``static_entity_dead`` negates ``static_entity_bound``
#: under ``call_graph_closed``.  A relation whose witness carries no row for
#: this index derives nothing -- and an empty list would read as "the model and
#: the code agree" when what happened is that nobody closed the model.
WITNESSED_BY = {
    DIVERGENCE_RELATION: (EDGE_CLOSED_RELATION,),
    ABSENCE_RELATION: (MAP_CLOSED_RELATION, CALL_GRAPH_CLOSED_RELATION),
    DEAD_RELATION: (CALL_GRAPH_CLOSED_RELATION,),
}

#: The reason a relation is withheld for want of a derivation rather than for
#: want of a witness.
UNDERIVED_REASON = "underived"

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

#: And the shape the *other* side must have for that comparison to mean
#: anything: ``<METHOD> <path>``, which is what an ``http:`` surface id becomes
#: with its prefix stripped.  ``schema_replay_v1.json`` mandates no shape for a
#: ``replay_request`` route, and this repository's own receipt fixtures disagree
#: about it -- one records ``POST /api/issues``, another records a bare path
#: with no method.  Against a receipt spelling its routes the other way every
#: statically bound surface would compare unequal to every request, and
#: "bound statically, never requested" would be a claim about a naming
#: difference.  A run whose request set is not in this shape is not comparable,
#: and the negation over it is withheld rather than answered.
ROUTE_SHAPE = re.compile(r"^[A-Za-z]+ /")


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
    """Relations this bundle can produce a row of, transitively over rule bodies.

    A relation is derivable when the bundle carries a fact of it, when its
    declaration is *primitive* -- an EDB relation whose producer owns the
    extension, so an empty one is that producer's own enumeration and not a
    silence -- or when some rule heading it has every body atom derivable,
    negated atoms included.

    Transitivity is the point.  A bundle exported by the profile alone declares
    ``static_edge`` and leaves the rules that head it to ``rules-static-v1``: in
    such a bundle ``static_edge`` is derived, ruleless and factless, so
    ``static_low_edge`` reads a relation nothing can populate, every model edge
    is "unlifted", and ``static_absence`` reports every edge of the reviewer's
    model as absent under a witness that certifies the completeness of a
    relation this bundle cannot derive.  Naming only ``static_edge``'s immediate
    readers is not enough; a relation is derivable only if its premises are.
    """
    derivable = {fact.relation for fact in bundle.facts}
    derivable |= {decl.name for decl in bundle.relations if decl.primitive}
    pending = [rule for rule in bundle.rules
               if rule.head.relation not in derivable]
    changed = True
    while changed:
        changed = False
        remaining = []
        for rule in pending:
            if rule.head.relation in derivable:
                continue
            body = {relation for atom in rule.body
                    if (relation := getattr(atom, "relation", None)) is not None}
            if body <= derivable:
                derivable.add(rule.head.relation)
                changed = True
            else:
                remaining.append(rule)
        pending = remaining
    return frozenset(derivable)


def _closure(bundle: Bundle) -> dict[str, list[tuple]]:
    from ..evaluator import evaluate

    report = evaluate(bundle, LIMITS)
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


def _cells(rows: Mapping[str, list[list[Any]]], mapped: Iterable[str],
           withheld: Mapping[str, list[str]]) -> dict[str, dict[str, Any]]:
    """Per capability, the reflexion cell: who it converges/diverges with, what is absent.

    A cell relation this bundle withholds -- for want of a derivation or of the
    witness its negation is licensed by -- is ``null`` in every cell, never an
    empty list: "no divergence" and "nobody closed the model" are different
    sentences and must not print the same.
    """
    names = set(mapped)
    for relation in CELL_RELATIONS:
        if relation in withheld:
            continue
        for row in rows.get(relation, ()):
            names.update(row)
    cells: dict[str, dict[str, Any]] = {}
    for name in sorted(names):
        cells[name] = {relation: (None if relation in withheld else
                                  sorted({row[1] for row in rows.get(relation, ())
                                          if row[0] == name}))
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
        # the routes the run requested that cannot be compared with a surface
        # id at all, because they are not spelled `<METHOD> <path>`
        "runtime_routes_not_comparable": None,
        "underived": None,
        # per withheld relation, why: `underived`, or the completeness witness
        # that carries no row for this index
        "withheld": None,
        # per closure witness, the joined indexes it does carry a row for
        "closure_witnesses": None,
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

    #: The indexes each witness carries a row for, among the joined ones.  Read
    #: out of the closure, so a witness a rule derives counts as one.
    carried = {name: {row[0] for row in closure.get(name, ())} for name in CLOSURE_WITNESSES}
    document["closure_witnesses"] = {name: sorted(indexes & carried[name])
                                     for name in CLOSURE_WITNESSES}
    withheld: dict[str, list[str]] = {}
    for relation in REPORTED_RELATIONS:
        reasons = ([UNDERIVED_REASON] if relation not in derivable else [])
        reasons += [witness for witness in WITNESSED_BY.get(relation, ())
                    if not indexes <= carried[witness]]
        if reasons:
            withheld[relation] = reasons
    document["underived"] = [name for name in REPORTED_RELATIONS if name not in derivable]
    document["withheld"] = withheld

    def reported(relation: str) -> list[list[Any]] | None:
        return None if relation in withheld else rows(relation)

    binds = reported(BIND_RELATION)
    if binds is not None:
        document["routes"] = {}
        for surface, entity, verb in binds:
            document["routes"].setdefault(surface, []).append([entity, verb])
    document["dead"] = reported(DEAD_RELATION)
    document["blocked"] = reported(BLOCKED_RELATION)
    document["unresolved"] = reported(ENTITY_UNRESOLVED_RELATION)
    document["capabilities"] = _cells(
        {relation: rows(relation) for relation in CELL_RELATIONS},
        {row[1] for row in rows(MAP_RELATION)} if MAP_RELATION in derivable else (),
        withheld)
    not_comparable = sorted(route for route in routes if not ROUTE_SHAPE.match(route))
    if binds is not None and runtime == RUNTIME_OBSERVED:
        document["runtime_routes_not_comparable"] = not_comparable
        if not not_comparable:
            # the only row this module derives, and the only negation in the
            # section: licensed by the replay producer's own closed request set,
            # over a request set spelled the way surface ids are
            document["static_only"] = [[surface, entity, verb]
                                       for surface, entity, verb in binds
                                       if (route := _route_of(surface)) is not None
                                       and route not in routes]
            document["static_only_licensed_by"] = REQUESTS_CLOSED_RELATION
            document["surfaces_not_comparable"] = sorted(
                {surface for surface, _entity, _verb in binds if _route_of(surface) is None})
    return document


def summary_line(document: Mapping[str, Any]) -> str:
    """One line for stdout: what the bundle is, and what the join made of it.

    A bound bundle that reported no row -- because it would not evaluate, or
    because the relation the counts are over is withheld -- is said in one line
    here too.  It is printed after judge.json is written and before the judge's
    own exit code is returned, so it counts nothing it has not got: a traceback
    on this line would replace a verdict that has already been decided.
    """
    join = document["join"]
    head = f"static bundle {document['bundle']['sha256'][:12]} {join['status']}"
    if join["status"] != JOIN_BOUND:
        return f"{head}: {join['message']}"
    error = document.get("error")
    if error or document["routes"] is None:
        reason = error or _withheld_reason(document, BIND_RELATION)
        return f"{head} to run {join['run']}: no rows read: {reason}"

    def count(key: str) -> str:
        value = document[key]
        return "-" if value is None else str(len(value))

    return (f"{head} to run {join['run']}: {count('routes')} surface(s) bound, "
            f"{count('dead')} dead, {count('blocked')} blocked; "
            f"runtime {document['runtime']}, static_only {count('static_only')} "
            f"(kernel {document['kernel']})")


def _withheld_reason(document: Mapping[str, Any], relation: str) -> str:
    """Why ``relation`` is null, in the section's own words."""
    reasons = (document.get("withheld") or {}).get(relation) or []
    if not reasons:
        return f"the bundle reported no {relation} row"
    if reasons == [UNDERIVED_REASON]:
        return f"{relation} is not derivable in this bundle"
    return f"{relation} withheld: {', '.join(reasons)}"


__all__ = ["SECTION_KEY", "KERNEL", "LIMITS", "DESCRIBES_RELATION", "REQUEST_RELATION",
           "REQUESTS_CLOSED_RELATION", "JOIN_BOUND", "JOIN_STALE", "JOIN_UNBOUND",
           "RUNTIME_OBSERVED", "RUNTIME_UNCLOSED", "RUNTIME_ABSENT", "BIND_RELATION",
           "DEAD_RELATION", "BLOCKED_RELATION", "ENTITY_UNRESOLVED_RELATION",
           "CONVERGENCE_RELATION", "DIVERGENCE_RELATION", "ABSENCE_RELATION",
           "ABSENCE_UNRESOLVED_RELATION", "MAP_RELATION", "REPORTED_RELATIONS",
           "CELL_RELATIONS", "CALL_GRAPH_CLOSED_RELATION", "MAP_CLOSED_RELATION",
           "EDGE_CLOSED_RELATION", "CLOSURE_WITNESSES", "WITNESSED_BY",
           "UNDERIVED_REASON", "ROUTE_SHAPE", "StaticBundleError", "StaticBundle",
           "load", "runtime_side", "section", "summary_line"]
