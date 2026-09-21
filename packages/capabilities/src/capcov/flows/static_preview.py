"""``flows plan --static BUNDLE.json``: what a static account says about a planned transition.

``capcov flows plan MODEL --target browser`` walks the *model*: a BFS over
``requires``/``adds`` that knows nothing about the code (``flows/model.py``).
A static bundle (``capcov experiment claims static --static scip --out
BUNDLE.json``, with the rule packs merged) accounts for the *code* before any
run.  This module is the join between the two, and everything it produces is an
annotation written beside the plan, never inside it.

WHAT IT DOES NOT DO
-------------------
It does not plan.  ``plan()`` is called first and is not passed this bundle; the
scenario list, the blocked list, ``model_sha256`` and ``states_explored`` are
byte-for-byte what they are without the flag.  Nothing is pruned: a transition
whose obligation surface the index says is *dead* is **flagged**, and the model
reviewer decides whether the model is wrong, the code is wrong, or the index is
looking at another tree.  A planner that dropped it would be deciding that
question by deleting the evidence, and a persistence assertion on a dead-looking
surface is exactly the kind of thing a reviewer wants to see fail.

WHAT BINDS THE TWO
------------------
Only the obligation surface id.  A flow model is a reviewer artifact about a
system; a bundle is a producer's account of a tree.  There is no
``index_describes_run`` here -- there is no run -- so the join key is the
spelling of ``obligations: ["http:GET /jobs/{id}"]`` against the index's own
``static_route_declared_surface``, and the annotation says so in ``join``.  The
bundle is named by the digest of its bytes and by the index it carries, so a
reviewer can check for themselves that it is the tree they meant.

An obligation of a *kind* the index declares no surface of -- ``"read"``, or
``ui:...`` against an index that only ever declared ``http:`` routes -- is not
compared at all: it is listed in ``not_comparable``.  Calling it undeclared
would be a claim about a route inventory that could not have carried it.

THE FOUR STATUSES, AND WHAT LICENSES EACH
-----------------------------------------
``bound``       the index binds this surface to at least one store
                (``static_capability_op``): a positive fact, no witness needed.
``blocked``     an unresolved call site is reachable from this surface's handler
                (``static_unresolved_on`` over ``static_reaches_eq``), named in
                ``via``.  Also a positive fact -- the doubt is *witnessed*, not
                inferred -- and it dominates ``bound``: a store set with a
                blocked path is a lower bound, which ``stores_closed: false``
                says beside it.
``dead``        declared, binds no store, and the store set is closed
                (``static_route_reaches_table_closed``, which the closure pack
                derives from ``call_graph_closed``).  The only negative status
                over the code, and it carries the witness that licenses it.
``undeclared``  the index declares no such surface, under its own
                ``static_route_inventory_closed``.  The only negative status
                over the route inventory, and likewise licensed.
``unresolved``  everything else, with the reason in the surface's own words:
                nothing was closed, so nothing is claimed.  An index that cannot
                see a store is not an index that says there is none.

``authorization`` is the same shape over the authz sink: ``authorized`` from
``static_route_authorized``, ``gap`` from the pack's own
``static_route_authorization_gap`` (which is itself gated on
``static_route_authorized_closed``), ``unresolved`` otherwise.  An authz sink on
the path is not an authz *outcome*: it says a check is reachable, never that
anyone was refused.  Only a run can say that.

A relation the bundle has no rule and no fact for is named in ``underived``, and
every status that would have needed it is ``unresolved`` naming it -- an empty
store set from a bundle without the base pack must not read as "this route
touches nothing".
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from ..claims.static.join import (KERNEL, StaticBundle, StaticBundleError, closure,
                                  derivable_relations, load)

#: The key the annotation is written under in plan.json, beside the plan.
KEY = "static"
#: What binds a bundle to a flow model: the obligation surface id, and nothing
#: else.  Named in the document so a reader never has to guess.
JOIN_KEY = "obligation surface id"

STATUS_BOUND = "bound"
STATUS_BLOCKED = "blocked"
STATUS_DEAD = "dead"
STATUS_UNDECLARED = "undeclared"
STATUS_UNRESOLVED = "unresolved"
#: The two statuses a reviewer is asked to look at.  Neither prunes anything.
FLAGGED_STATUSES = (STATUS_DEAD, STATUS_UNDECLARED)

AUTHZ_AUTHORIZED = "authorized"
AUTHZ_GAP = "gap"
AUTHZ_UNRESOLVED = "unresolved"

INDEX_RELATION = "scip_index"
DECLARED_RELATION = "static_route_declared_surface"
HANDLER_RELATION = "static_route_handler"
BIND_RELATION = "static_capability_op"
REACHES_EQ_RELATION = "static_reaches_eq"
UNRESOLVED_ON_RELATION = "static_unresolved_on"
STORES_CLOSED_RELATION = "static_route_reaches_table_closed"
INVENTORY_CLOSED_RELATION = "static_route_inventory_closed"
AUTHORIZED_RELATION = "static_route_authorized"
AUTHZ_GAP_RELATION = "static_route_authorization_gap"
AUTHZ_CLOSED_RELATION = "static_route_authorized_closed"

#: The relations the preview reads, so ``underived`` is one list a reader can
#: check a status against rather than a fact about this module's source.
READ_RELATIONS = (DECLARED_RELATION, HANDLER_RELATION, BIND_RELATION,
                  REACHES_EQ_RELATION, UNRESOLVED_ON_RELATION, STORES_CLOSED_RELATION,
                  INVENTORY_CLOSED_RELATION, AUTHORIZED_RELATION, AUTHZ_GAP_RELATION)

#: At most this many ``via`` symbols per surface, with ``via_total`` saying how
#: many there were: a plan artifact is reviewed by a person, and an unbounded
#: list of symbols in it is neither reviewable nor bounded.
VIA_LIMIT = 8


class StaticPreviewError(ValueError):
    """The bundle cannot be previewed against this model, in its own words.

    A usage error about the command line -- ``flows`` reports it the way it
    reports every other one -- never a finding about the model and never a
    verdict about the code.
    """


def _rows(derived: Mapping[str, list[tuple]], relation: str, index: str) -> list[tuple]:
    return sorted(tuple(row[1:]) for row in derived.get(relation, ())
                  if row and row[0] == index)


def _indexes(derived: Mapping[str, list[tuple]]) -> list[str]:
    """The indexes this bundle is about, by its own identity relation.

    ``scip_index`` is the producer's statement of what it indexed.  A bundle
    carrying none of it, but carrying route surfaces, is still about whatever
    index those rows are keyed by, and is read that way rather than refused for
    a missing identity row it was never required to carry.
    """
    indexes = {row[0] for row in derived.get(INDEX_RELATION, ()) if row}
    if indexes:
        return sorted(indexes)
    return sorted({row[0] for row in derived.get(DECLARED_RELATION, ()) if row})


def _kinds(surfaces: Iterable[str]) -> frozenset[str]:
    return frozenset(surface.split(":", 1)[0] for surface in surfaces if ":" in surface)


def _comparable(obligation: str, declared: frozenset[str], kinds: frozenset[str],
                inventory_derivable: bool) -> bool:
    """Whether the index could have had anything to say about this obligation.

    A declared surface obviously could.  So could an undeclared one of a kind
    the index declares surfaces of -- that is the case ``undeclared`` is for.
    An obligation of any other kind (``"read"``, ``ui:...`` against an
    http-only inventory) is outside what this index enumerates, and no status
    over it would be a fact.

    That reasoning needs a route inventory to reason from.  A bundle that
    cannot derive ``static_route_declared_surface`` at all declares no surface
    of any kind, so *every* obligation would look like a kind mismatch -- which
    would report a bundle missing its rule pack as a model naming the wrong
    kinds.  Such a bundle compares everything and resolves nothing: each
    obligation is ``unresolved``, naming the relation it has no rule for.
    """
    if not inventory_derivable:
        return True
    return obligation in declared or (":" in obligation
                                      and obligation.split(":", 1)[0] in kinds)


def _authorization(surface: str, authorized: set[str], gaps: set[str],
                   derivable: frozenset[str]) -> dict[str, Any]:
    if surface in authorized:
        return {"status": AUTHZ_AUTHORIZED, "licensed_by": AUTHORIZED_RELATION,
                "reason": f"{AUTHORIZED_RELATION} names an authz sink on a path from this surface"}
    if surface in gaps:
        return {"status": AUTHZ_GAP, "licensed_by": AUTHZ_CLOSED_RELATION,
                "reason": (f"{AUTHZ_GAP_RELATION}: no authz sink on any path, under "
                           f"{AUTHZ_CLOSED_RELATION}")}
    missing = [name for name in (AUTHORIZED_RELATION, AUTHZ_GAP_RELATION)
               if name not in derivable]
    return {"status": AUTHZ_UNRESOLVED, "licensed_by": None,
            "reason": (f"neither {AUTHORIZED_RELATION} nor {AUTHZ_GAP_RELATION} covers this "
                       f"surface" + (f"; underived here: {', '.join(missing)}" if missing else
                                     f"; {AUTHZ_CLOSED_RELATION} licenses no gap for it"))}


def _surface(surface: str, *, declared: frozenset[str], binds: dict[str, list[list[str]]],
             handlers: dict[str, list[str]], via: list[str], stores_closed: bool,
             inventory_closed: bool, inventory_derivable: bool, derivable: frozenset[str],
             authorization: dict[str, Any]) -> dict[str, Any]:
    operations = sorted(binds.get(surface, ()))
    entry: dict[str, Any] = {
        "operations": operations,
        "stores": sorted({entity for entity, _verb in operations}),
        "stores_closed": stores_closed,
        "stores_closed_witness": STORES_CLOSED_RELATION,
        "handlers": sorted(handlers.get(surface, ())),
        "via": via[:VIA_LIMIT],
        "via_total": len(via),
        "authorization": authorization,
    }
    if surface not in declared:
        if not inventory_derivable:
            entry["status"] = STATUS_UNRESOLVED
            entry["reason"] = (f"this bundle has no rule and no fact for "
                               f"{DECLARED_RELATION}, so it enumerates no surface to compare "
                               f"this obligation with; export it with the rule packs merged")
            return entry
        entry["status"] = STATUS_UNDECLARED if inventory_closed else STATUS_UNRESOLVED
        entry["reason"] = (
            f"the index declares no such surface, and {INVENTORY_CLOSED_RELATION} "
            f"closes its route inventory" if inventory_closed else
            f"the index declares no such surface and carries no {INVENTORY_CLOSED_RELATION} "
            f"row, so it does not say there is none")
        return entry
    if via:
        entry["status"] = STATUS_BLOCKED
        entry["reason"] = (f"{UNRESOLVED_ON_RELATION} names {len(via)} unresolved call site "
                           f"owner(s) reachable from this surface's handler; the store set is a "
                           f"lower bound")
        return entry
    if operations:
        entry["status"] = STATUS_BOUND
        entry["reason"] = f"{BIND_RELATION} binds {len(operations)} operation(s) to this surface"
        return entry
    if stores_closed:
        entry["status"] = STATUS_DEAD
        entry["reason"] = (f"declared, no {BIND_RELATION} row, and {STORES_CLOSED_RELATION} "
                           f"closes this surface's store set")
        return entry
    entry["status"] = STATUS_UNRESOLVED
    missing = [name for name in (BIND_RELATION, STORES_CLOSED_RELATION,
                                 UNRESOLVED_ON_RELATION) if name not in derivable]
    entry["reason"] = (f"declared, no {BIND_RELATION} row, and no {STORES_CLOSED_RELATION} row "
                       f"for it"
                       + (f"; underived here: {', '.join(missing)}" if missing else ""))
    return entry


def annotate(static: StaticBundle, model: Mapping[str, Any]) -> dict[str, Any]:
    """The ``static`` annotation for ``plan.json``: per surface, and per transition.

    ``model`` is the flow model ``plan()`` was given -- already validated by it,
    so every transition here has a nonempty ``obligations`` list.  Raises
    ``StaticPreviewError`` when the bundle cannot be previewed at all; it never
    raises about the model, which is the reviewer's document, not the bundle's.
    """
    try:
        derived = closure(static.bundle)
    except (ValueError, RecursionError) as exc:
        raise StaticPreviewError(f"the static bundle did not evaluate: {exc}") from exc
    indexes = _indexes(derived)
    if not indexes:
        raise StaticPreviewError(
            f"the static bundle carries no {INDEX_RELATION} and no {DECLARED_RELATION} row, "
            f"so it is about no index this plan could be previewed against")
    if len(indexes) > 1:
        raise StaticPreviewError(
            f"the static bundle carries {len(indexes)} indexes "
            f"({', '.join(name[:12] for name in indexes[:4])}...); a preview against more than "
            f"one index is more than one preview -- export one bundle per index")
    index = indexes[0]
    derivable = derivable_relations(static.bundle)

    declared = frozenset(row[0] for row in _rows(derived, DECLARED_RELATION, index))
    kinds = _kinds(declared)
    binds: dict[str, list[list[str]]] = {}
    for surface, entity, verb in _rows(derived, BIND_RELATION, index):
        binds.setdefault(surface, []).append([entity, verb])
    handlers: dict[str, list[str]] = {}
    for surface, symbol in _rows(derived, HANDLER_RELATION, index):
        handlers.setdefault(surface, []).append(symbol)
    unresolved_on = {row[0] for row in _rows(derived, UNRESOLVED_ON_RELATION, index)}
    reaches: dict[str, set[str]] = {}
    for src, dst in _rows(derived, REACHES_EQ_RELATION, index):
        reaches.setdefault(src, set()).add(dst)
    stores_closed = {row[0] for row in _rows(derived, STORES_CLOSED_RELATION, index)}
    # arity 1: the witness is about the index and nothing else, so a row of it
    # for this index is the whole of what it says.  It licenses a negation over
    # `static_route_declared_surface`, so it licenses nothing at all in a bundle
    # that cannot derive that relation: a completeness witness for a relation
    # with no rule certifies the completeness of a silence.
    inventory_derivable = DECLARED_RELATION in derivable
    inventory_closed = (bool(_rows(derived, INVENTORY_CLOSED_RELATION, index))
                        and inventory_derivable)
    authorized = {row[0] for row in _rows(derived, AUTHORIZED_RELATION, index)}
    gaps = {row[0] for row in _rows(derived, AUTHZ_GAP_RELATION, index)}

    def via_of(surface: str) -> list[str]:
        owners: set[str] = set()
        for handler in handlers.get(surface, ()):
            owners |= (reaches.get(handler, set()) | {handler}) & unresolved_on
        return sorted(owners)

    transitions = {}
    surfaces: dict[str, dict[str, Any]] = {}
    not_comparable: set[str] = set()
    for transition in model.get("transitions", ()):
        name = transition.get("id")
        obligations = sorted(transition.get("obligations") or ())
        compared = [ob for ob in obligations
                    if _comparable(ob, declared, kinds, inventory_derivable)]
        not_comparable |= set(obligations) - set(compared)
        for surface in compared:
            if surface not in surfaces:
                surfaces[surface] = _surface(
                    surface, declared=declared, binds=binds, handlers=handlers,
                    via=via_of(surface), stores_closed=surface in stores_closed,
                    inventory_closed=inventory_closed,
                    inventory_derivable=inventory_derivable, derivable=derivable,
                    authorization=_authorization(surface, authorized, gaps, derivable))
        stores = sorted({store for surface in compared
                         for store in surfaces[surface]["stores"]})
        transitions[name] = {
            "obligations": obligations,
            "surfaces": {surface: surfaces[surface]["status"] for surface in compared},
            "stores": stores,
            "stores_closed": bool(compared) and all(surfaces[surface]["stores_closed"]
                                                    for surface in compared),
            "flags": [f"{surfaces[surface]['status']} surface {surface}: "
                      f"{surfaces[surface]['reason']}"
                      for surface in compared
                      if surfaces[surface]["status"] in FLAGGED_STATUSES],
            "not_comparable": sorted(set(obligations) - set(compared)),
        }
    return {
        "bundle": {"sha256": static.sha256, "facts": len(static.bundle.facts),
                   "rules": len(static.bundle.rules),
                   "relations": len(static.bundle.relations)},
        "index": index,
        "kernel": KERNEL,
        "join": JOIN_KEY,
        "route_inventory_closed": inventory_closed,
        "underived": [name for name in READ_RELATIONS if name not in derivable],
        "surfaces": surfaces,
        "transitions": transitions,
        "not_comparable": sorted(not_comparable),
        "flagged": sorted(name for name, entry in transitions.items() if entry["flags"]),
    }


def summary_line(annotation: Mapping[str, Any]) -> str:
    """One line for stdout: what was previewed, and what a reviewer is asked to look at."""
    surfaces = annotation["surfaces"]
    counts: dict[str, int] = {}
    for entry in surfaces.values():
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
    tally = ", ".join(f"{count} {status}" for status, count in sorted(counts.items())) or "none"
    return (f"capcov flows: static preview from bundle {annotation['bundle']['sha256'][:12]} "
            f"(index {annotation['index'][:12]}, kernel {annotation['kernel']}): "
            f"{len(surfaces)} obligation surface(s) -- {tally}; "
            f"{len(annotation['flagged'])} transition(s) flagged, "
            f"{len(annotation['not_comparable'])} obligation(s) not comparable; "
            f"nothing pruned")


def report_lines(annotation: Mapping[str, Any]) -> list[str]:
    """The ``flows report`` static preview table: one row per transition and surface.

    Short on purpose.  The reason a status was reached is in plan.json, in the
    surface's own words; the table is the thing a reviewer reads first, so it
    carries the status, the store set and whether that set is closed -- a store
    list without its closure is the one thing here that could be misread as a
    statement that there are no others.
    """
    lines = ["", "## Static preview", "",
             f"Bundle `{annotation['bundle']['sha256'][:12]}`, index "
             f"`{annotation['index'][:12]}`, kernel {annotation['kernel']}; joined by "
             f"{annotation['join']}. Annotation only -- no transition was pruned.",
             "",
             "| Transition | Obligation surface | Status | Stores | Store set | Authz |",
             "|---|---|---|---|---|---|"]
    for name, entry in sorted(annotation["transitions"].items()):
        for surface, status in sorted(entry["surfaces"].items()):
            detail = annotation["surfaces"][surface]
            cells = [name, surface, status,
                     ", ".join(detail["stores"]) or "-",
                     "closed" if detail["stores_closed"] else "lower bound",
                     detail["authorization"]["status"]]
            lines.append("| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |")
    flagged = annotation["flagged"]
    lines.extend(["", f"Flagged for review: {', '.join(flagged) if flagged else 'none'}."])
    if annotation["not_comparable"]:
        lines.append(f"Not comparable with this index: "
                     f"{', '.join(annotation['not_comparable'])}.")
    if annotation["underived"]:
        lines.append(f"Underived in this bundle: {', '.join(annotation['underived'])}.")
    return lines


__all__ = ["KEY", "JOIN_KEY", "STATUS_BOUND", "STATUS_BLOCKED", "STATUS_DEAD",
           "STATUS_UNDECLARED", "STATUS_UNRESOLVED", "FLAGGED_STATUSES", "AUTHZ_AUTHORIZED",
           "AUTHZ_GAP", "AUTHZ_UNRESOLVED", "READ_RELATIONS", "VIA_LIMIT",
           "StaticPreviewError", "StaticBundleError", "load", "annotate", "summary_line",
           "report_lines"]
