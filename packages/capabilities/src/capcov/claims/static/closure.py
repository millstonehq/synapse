"""Call-graph closure for the ``--static scip`` producer profile (opt-in).

``scip_facts`` exports what the SCIP index says.  This module adds the two
things a *negative* static claim needs before it can be answered at all, and it
adds them **beside** that export rather than inside it:

``static_unresolved_call_site(index, file, line, symbol)``
    The resolver's ``scip_residue`` -- every call site the AST census saw that the
    SCIP index left unresolved, carried as rows instead of a count.  ``symbol``
    is the callee *as the source spells it*: an unresolved call site has no SCIP
    symbol, and that is precisely what it means for it to be in the residue.
    The resolver's rule is "name unresolved, do not drop", and a relation of
    named rows is how that rule survives into a claim.

``call_graph_closed(index, scope)``
    The completeness witness for ``static_edge`` over one scope, emitted ONLY
    when that scope's residue is empty.  Without it a "route R does not reach
    table T" claim can never be more than unresolved, because the call graph it
    would be read off might be missing an edge.

Neither relation changes the export.  ``scip_facts.export_bundle`` keys its
identity on the relations it declares (``static-relations-v1``), so emitting
these two into it would change the ``index`` digest of every existing bundle;
they are a separate fragment merged with ``combine``, and an export made
without the profile is byte-for-byte what it always was.

SCOPE
-----
``scope`` is a token of the export's own scope declaration -- the same value
the export's ``static_scope(index, scope_kind, scope_value)`` rows carry --
and it denotes a set of in-scope documents:

* ``all`` -> the single token ``"*"``, denoting every in-scope document of the
  index;
* ``package_prefix`` -> the single token that prefix, denoting every in-scope
  document (which are, by the scope's construction, exactly the documents of
  that package prefix);
* ``document_set`` -> one token per listed path, each denoting that one
  document.

A token is emitted when, and only when, (i) the call-site census was taken at
all (``census_available`` in the export's metadata: the tree-sitter side carried
both ``scip_residue`` and ``blind_spots``), (ii) the token denotes at least one
in-scope document, and (iii) no residue row falls in any of them.  Blind spots
need no separate condition: ``resolve._residue`` folds every enumerated blind
spot into the residue unconditionally, so an empty residue is also an empty
blind-spot census.

A non-empty residue is not an error and nothing is suppressed because of it:
the residue rows are exported either way, and what is withheld is only the
claim that the graph is complete.

PRODUCER
--------
Both relations are declared with producer class ``scip`` and their evidence
sources begin with it: the rows are the resolver's, not the exporter's opinion
of them.  The residue rows name the indexer that produced the index
(``scip scip-go 0.2.7``); the witness names the emission contract that was
checked (``scip capcov.claims.static.closure call-graph-closed-v1``), the same
shape ``scip_facts`` uses for its own witnesses.

Nothing here runs a tool.  ``require_scip_tools`` is the one function that
touches the environment, and it only asks the resolver to raise its own
refusal -- the message ``capcov discover --resolver scip`` prints for a missing
indexer -- so a profile that cannot index says exactly what the flag that
already exists says.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any, Iterable, Mapping

from ...scip import resolve
from ..ir import Bundle, RelationDecl, bundle_from_json
from . import scip_facts
from .combine import combine

PACK_NAME = "rules-static-closure-v1.json"
PACK_ID = "rules-static-closure-v1"
BASE_PACK_ID = "rules-static-v1"

#: Producer class of every row this module emits (``schema_replay_v1``'s
#: convention: the class is the first word of ``Evidence.source``).
PRODUCER_CLASS = "scip"
EMITTER = "capcov.claims.static.closure"
#: The witness's emission contract, named in its evidence source.
WITNESS_CALL_GRAPH = "call-graph-closed-v1"

UNRESOLVED_RELATION = "static_unresolved_call_site"
CLOSED_RELATION = "call_graph_closed"

#: The token denoting every in-scope document of the index.
SCOPE_TOKEN_ALL = "*"


class ClosureInputError(ValueError):
    """The export this fragment is built against is not one this module can read."""


def load_pack() -> dict[str, Any]:
    """The closure rule pack document, read as package data (source tree or wheel)."""
    return json.loads(resources.files(__package__).joinpath(PACK_NAME).read_text(encoding="utf-8"))


def pack_relations(pack: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    """Every relation declaration the pack carries, owned and borrowed alike."""
    pack = pack or load_pack()
    return [*pack["primitives"], *pack["borrowed_declarations"], *pack["derived"]]


def pack_bundle(pack: Mapping[str, Any] | None = None) -> Bundle:
    """The pack alone -- declarations and rules, no facts -- as a validated Bundle."""
    pack = pack or load_pack()
    return bundle_from_json({"schema_version": 1, "relations": pack_relations(pack),
                             "rules": [dict(rule) for rule in pack["rules"]]}, validate=True)


def relation_decls(pack: Mapping[str, Any] | None = None) -> dict[str, RelationDecl]:
    return {decl.name: decl for decl in pack_bundle(pack).relations}


def require_scip_tools(language: str, source_root: str | Path = ".") -> None:
    """Refuse, in ``--resolver scip``'s own words, when the SCIP toolchain is absent.

    ``resolve.resolve`` checks the indexer, the language's helper script and the
    ``scip`` CLI *before* it indexes anything, so calling it on a toolchain
    ``tools_available`` already reported absent raises that named refusal
    without doing any work.  Reusing it rather than paraphrasing it is the
    point: ``--static scip`` and ``--resolver scip`` fail with one message.
    """
    if resolve.tools_available(language):
        return
    resolve.resolve(source_root, {}, language=language)
    raise resolve.ScipToolsUnavailable(  # pragma: no cover - resolve always raises above
        f"--resolver scip: the {language} SCIP toolchain is unavailable")


def scope_tokens(scope: Mapping[str, Any], in_scope: Iterable[str]) -> dict[str, tuple[str, ...]]:
    """``{token: the in-scope documents it denotes}`` for one export's scope.

    ``scope`` is the export metadata's ``{"kind", "values"}``.  A token with no
    in-scope document denotes nothing and is dropped: "closed over nothing" is
    a vacuous truth, and a witness is a claim about documents that exist.
    """
    documents = tuple(sorted(in_scope))
    kind = scope.get("kind")
    values = tuple(scope.get("values") or ())
    if kind == scip_facts.SCOPE_ALL:
        tokens = {SCOPE_TOKEN_ALL: documents}
    elif kind == scip_facts.SCOPE_PACKAGE_PREFIX:
        tokens = {value: documents for value in values}
    elif kind == scip_facts.SCOPE_DOCUMENT_SET:
        tokens = {value: ((value,) if value in documents else ()) for value in values}
    else:
        raise ClosureInputError(f"unknown export scope kind {kind!r}")
    return {token: paths for token, paths in tokens.items() if paths}


def _metadata(export: Bundle) -> dict[str, Any]:
    metadata = dict(export.metadata)
    for key in ("index_digest", "scope", "in_scope_documents", "census_available", "producers"):
        if key not in metadata:
            raise ClosureInputError(
                f"the export carries no {key!r} metadata; pass a bundle from "
                f"scip_facts.export_bundle")
    return metadata


def residue_rows(ast_raw: Mapping[str, Any]) -> list[tuple[str, int, str]]:
    """``(file, line, symbol)`` per residue entry, in canonical order.

    Reads exactly the fields ``resolve._residue`` writes and interprets none of
    them: an entry without a usable file and line is dropped by the same rule
    ``scip_facts`` drops one, so the two modules count the same census.
    """
    rows = []
    for entry in ast_raw.get("scip_residue") or []:
        file, line = entry.get("file"), entry.get("line")
        if not (isinstance(file, str) and isinstance(line, int) and not isinstance(line, bool)):
            continue
        rows.append((file, line, str(entry.get("callee") or "")))
    return sorted(set(rows))


def closure_bundle(export: Bundle, ast_raw: Mapping[str, Any]) -> Bundle:
    """The fragment: the residue rows, the witnesses they license, and the rules.

    Built against a finished ``scip_facts`` export -- its ``index`` identity,
    its scope and its in-scope documents -- and returned *unvalidated*, because
    its evidence depends on the export's own ``scip_index`` and
    ``scip_index_tree`` rows: it is a fragment of that bundle, and
    :func:`attach` is what validates the whole.
    """
    metadata = _metadata(export)
    index = str(metadata["index_digest"])
    producers = dict(metadata["producers"])
    indexer_source = f"{PRODUCER_CLASS} {producers['indexer']} {producers['indexer_version']}"
    witness_source = f"{PRODUCER_CLASS} {EMITTER} {WITNESS_CALL_GRAPH}"
    decls = relation_decls()
    depends_on = tuple(sorted(
        record.id for record in export.evidence
        if record.atom.relation in ("scip_index", "scip_index_tree")))
    if not depends_on:
        raise ClosureInputError("the export declares no scip_index evidence to depend on")

    facts, evidence = [], []

    def add(relation: str, values: list[Any], source: str) -> None:
        row = [index, *values]
        facts.append(_atom(decls[relation], relation, row))
        evidence.append(_evidence(decls[relation], relation, row, index, source, depends_on))

    residue = residue_rows(ast_raw)
    for file, line, symbol in residue:
        add(UNRESOLVED_RELATION, [file, line, symbol], indexer_source)

    if metadata["census_available"]:
        unresolved_files = {file for file, _, _ in residue}
        for token, documents in sorted(scope_tokens(dict(metadata["scope"]),
                                                    metadata["in_scope_documents"]).items()):
            if unresolved_files.intersection(documents):
                continue
            add(CLOSED_RELATION, [token], witness_source)

    pack = pack_bundle()
    return Bundle(pack.relations, facts=tuple(facts), rules=pack.rules,
                  evidence=tuple(evidence),
                  metadata=(("emitter", EMITTER), ("pack", PACK_ID),
                            ("base_pack", BASE_PACK_ID), ("index_digest", index),
                            ("residue_rows", len(residue))))


def _atom(decl: RelationDecl, relation: str, row: list[Any]):
    from ..ir import Atom, Constant

    return Atom(relation, tuple(Constant(scip_facts._checked(relation, column, value), column.type)
                                for column, value in zip(decl.columns, row)))


def _evidence(decl: RelationDecl, relation: str, row: list[Any], index: str,
              source: str, depends_on: tuple[str, ...]):
    from ..ir import Context, Evidence

    atom = _atom(decl, relation, row)
    context = {column.name: value for column, value in zip(decl.columns, row) if column.context}
    return Evidence(scip_facts.evidence_id(index, relation, row), atom,
                    Context.from_mapping(context), source, tuple(depends_on))


def attach(export: Bundle, ast_raw: Mapping[str, Any], *bundles: Bundle,
           validate: bool = True, **combine_kwargs: Any) -> Bundle:
    """``export`` plus the closure fragment (plus any further bundles), validated.

    The one call a ``--static scip`` producer makes after exporting: it merges
    the fragment's declarations with the export's by name (``combine`` refuses a
    duplicate that is not byte-identical, so the borrowed declarations can never
    widen the frozen schema) and returns the bundle a kernel evaluates.
    """
    return combine(export, closure_bundle(export, ast_raw), *bundles,
                   validate=validate, **combine_kwargs)


__all__ = ["PACK_NAME", "PACK_ID", "BASE_PACK_ID", "PRODUCER_CLASS", "EMITTER",
           "WITNESS_CALL_GRAPH", "UNRESOLVED_RELATION", "CLOSED_RELATION", "SCOPE_TOKEN_ALL",
           "ClosureInputError", "load_pack", "pack_relations", "pack_bundle", "relation_decls",
           "require_scip_tools", "scope_tokens", "residue_rows", "closure_bundle", "attach"]
