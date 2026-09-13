"""Turn a normalized SCIP index into the two facts capcov's core consumes:
type definitions (entities) and a resolved call graph (call edges).

WHAT SCIP BUYS, AND WHERE ITS HONESTY ENDS
------------------------------------------
SCIP is rented as the *resolver*: an indexer (scip-python, scip-go) does the
type-aware, cross-file, cross-language name resolution that a hand-written AST
pass cannot, and every reference arrives already bound to a global symbol. That
is why ``call_edges`` recovers ``router.make_job -> service.create_job`` across
two files for free -- the callee reference in one document is the very symbol
the other document defines.

But the graph SCIP yields is a **resolved-reference graph, not a labelled call
graph**, and two limits follow that this module cannot paper over:

* **A reference is not proof of a call.** An occurrence of a function symbol
  may be an invocation, or it may be passing the function as a value, storing
  it, or decorating with it. This module attributes every *reference to a
  function/method symbol* to its enclosing definition and calls it an edge; the
  fixpoint over that graph is an over-approximation of reachability, which is
  the safe direction for a coverage tool (it binds an entity that a caller
  *could* reach, never fewer).

* **SCIP is silent about what it could not resolve.** When the indexer cannot
  type a receiver -- ``session.add(job)`` on an untyped ``session`` -- it emits
  *no occurrence at all*. There is no "unresolved" marker to read here, so this
  module has nothing to enumerate and does not pretend to. The blind-spot
  inventory (getattr / eval / dynamic import / ambiguous dispatch, each with a
  file and a line) is the AST adapter's job and stays there. Keeping SCIP as the
  resolver and the AST pass as the blind-spot enumerator is the hybrid the
  ADR-0001 soundiness argument settles: never drop a name, and always be able to
  say where you are blind. A missing occurrence is exactly the kind of silent
  loss the AST differ exists to surface.

A related consequence worth naming: SCIP encodes a **constructor call as a
reference to the type**, not to an ``__init__`` method, so ``Job()`` shows up as
a type reference and never as a call edge. Construction is therefore recovered
by the entity/direct-reference side, not by this call graph.

CONTRACT
--------
Input is the dict ``runner.read_scip_index`` returns::

    {"documents": [
        {"path": str,
         "symbols":     [{"symbol", "kind", "display_name"}],
         "occurrences": [{"symbol", "is_definition", "start_line", "start_col",
                          "enclosing_start_line", "enclosing_end_line"}]}
    ]}

``kind`` is populated for scip-go (``"Struct"``, ``"Function"``, ...) and left
suffix-derived (``"type"``, ``"method"``, ``"term"``) or ``None`` for
scip-python; ``display_name`` is populated for scip-go and ``None`` for
scip-python, so this module derives one from the symbol when it is absent.
``line`` in the returned facts is the SCIP ``start_line`` as delivered -- 0-based,
unmodified -- so it stays consistent with the runner rather than silently
disagreeing with it.

This module is standard-library-only on purpose: it runs in the same CI path as
``discover``/``gate``, and the node/go indexers it depends on upstream are
guarded in ``runner`` (and skipped in tests) so a check that cannot run never
prints OK.
"""

from __future__ import annotations

import re

# kind strings that name a type definition (an entity candidate) or a
# callable. scip-python's suffix-derived kinds ("type"/"method"/"term") and
# scip-go's populated kinds ("Struct"/"Function"/"Field"/...) are folded
# together by lower-casing. Anything not recognised here falls back to the SCIP
# descriptor suffix, which is authoritative for the grammar.
_TYPE_KINDS = frozenset(
    {"type", "class", "struct", "interface", "enum", "trait", "object",
     "protocol", "typealias", "union", "record", "annotation"}
)
_CALLABLE_KINDS = frozenset(
    {"method", "function", "func", "constructor", "staticmethod",
     "classmethod", "abstractmethod"}
)

# Characters that terminate a SCIP descriptor and so cannot be part of a leaf
# name, used when deriving a display name from a symbol.
_NAME_BOUNDARY = re.compile(r"[^ \t`#./():!\[\],]+$")


def _suffix_category(symbol: str) -> str:
    """Classify a symbol by its SCIP descriptor suffix.

    ``#`` a type, ``().`` a method/function, a trailing ``.`` a term/field.
    Everything else -- parameters ``(x)``, type parameters ``[T]``, meta
    ``:``, locals -- is "other" and is neither an entity nor a callee.
    """
    s = (symbol or "").rstrip()
    if s.endswith("#"):
        return "type"
    if s.endswith("()."):
        return "callable"
    if s.endswith("."):
        return "term"
    return "other"


def _category(symbol: str, kind: str | None) -> str:
    """type / callable / term / other for a symbol.

    A populated, recognised ``kind`` (scip-go) wins; otherwise the descriptor
    suffix decides (scip-python leaves ``kind`` unset). An unrecognised kind
    string is not trusted -- it falls through to the suffix rather than being
    guessed at.
    """
    k = (kind or "").strip().lower()
    if k in _TYPE_KINDS:
        return "type"
    if k in _CALLABLE_KINDS:
        return "callable"
    return _suffix_category(symbol)


def _leaf_name(symbol: str) -> str:
    """Best-effort human name from a symbol's trailing descriptor.

    scip-python emits no ``display_name``; the leaf of the symbol is the only
    name available. ``...Job#`` -> ``Job``; ``...create_job().`` ->
    ``create_job``; ``...Server#Addr.`` -> ``Addr``. Falls back to the whole
    symbol when it has no recognisable descriptor tail.
    """
    s = (symbol or "").rstrip()
    if s.endswith("()."):
        s = s[:-3]                      # empty-disambiguator method
    elif s.endswith(")."):
        s = s[: s.rfind("(")]           # method with a disambiguator
    elif s.endswith(")"):
        inner = s[s.rfind("(") + 1 : -1]  # parameter (name)
        return inner or s
    elif s.endswith("]"):
        inner = s[s.rfind("[") + 1 : -1]  # type parameter [name]
        return inner or s
    elif s and s[-1] in "#.:!/":
        s = s[:-1]
    match = _NAME_BOUNDARY.search(s)
    return match.group(0) if match else (symbol or "")


def _symbol_table(normalized: dict) -> dict[str, dict]:
    """symbol -> its {kind, display_name}, merged across every document.

    A callee reference in one document is defined -- and carries its kind and
    name -- in another, so classification and naming need the whole index, not
    just the document the occurrence sits in. First writer wins; a symbol is
    defined once.
    """
    table: dict[str, dict] = {}
    for document in normalized.get("documents", []) or []:
        for sym in document.get("symbols", []) or []:
            name = sym.get("symbol")
            if name and name not in table:
                table[name] = sym
    return table


def entities(normalized: dict) -> list[dict]:
    """Type/class/struct definitions, as ``{id, file, line, display_name}``.

    Every definition occurrence whose symbol is a type is enumerated -- and
    only that this is a *type definition* is decided here. Whether a given type
    is a persistence entity (a mapped class, a table) is a framework question
    that stays with the AST adapter; this layer just lists the type-defs SCIP
    resolved.
    """
    table = _symbol_table(normalized)
    out: list[dict] = []
    seen: set[str] = set()
    for document in normalized.get("documents", []) or []:
        path = document.get("path")
        for occ in document.get("occurrences", []) or []:
            if not occ.get("is_definition"):
                continue
            symbol = occ.get("symbol")
            if not symbol or symbol in seen:
                continue
            info = table.get(symbol, {})
            if _category(symbol, info.get("kind")) != "type":
                continue
            seen.add(symbol)
            out.append(
                {
                    "id": symbol,
                    "file": path,
                    "line": occ.get("start_line"),
                    "display_name": info.get("display_name") or _leaf_name(symbol),
                }
            )
    out.sort(key=lambda e: (e["file"] or "", _line_key(e["line"]), e["id"]))
    return out


def call_edges(normalized: dict) -> list[dict]:
    """Resolved call edges, as ``{caller, callee, file, line}``.

    For every occurrence that is a *reference* (not a definition) to a
    function/method symbol, the caller is the definition whose
    ``enclosing_range`` (line span) the reference falls inside -- innermost when
    several nest -- and the edge runs caller -> callee. The callee is a global
    SCIP symbol, so an edge to a definition in another file needs no extra work:
    that is where the cross-file resolution comes from.

    ``caller`` is ``None`` for a reference at module/import scope with no
    enclosing definition; the edge is kept rather than dropped (see the module
    docstring on never losing a name), and a consumer building the fixpoint's
    ``calls`` map simply skips the ``None`` root.
    """
    table = _symbol_table(normalized)
    edges: list[dict] = []
    for document in normalized.get("documents", []) or []:
        path = document.get("path")
        occurrences = document.get("occurrences", []) or []
        enclosers = [
            (
                occ["enclosing_start_line"],
                occ["enclosing_end_line"],
                occ.get("symbol"),
            )
            for occ in occurrences
            if occ.get("is_definition")
            and occ.get("enclosing_start_line") is not None
            and occ.get("enclosing_end_line") is not None
        ]
        for occ in occurrences:
            if occ.get("is_definition"):
                continue
            symbol = occ.get("symbol")
            if not symbol:
                continue
            info = table.get(symbol, {})
            if _category(symbol, info.get("kind")) != "callable":
                continue
            line = occ.get("start_line")
            edges.append(
                {
                    "caller": _innermost_caller(enclosers, line),
                    "callee": symbol,
                    "file": path,
                    "line": line,
                }
            )

    seen: set[tuple] = set()
    deduped: list[dict] = []
    for edge in edges:
        key = (edge["caller"], edge["callee"], edge["file"], edge["line"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(edge)
    deduped.sort(
        key=lambda e: (
            e["file"] or "",
            _line_key(e["line"]),
            e["caller"] or "",
            e["callee"] or "",
        )
    )
    return deduped


def _innermost_caller(
    enclosers: list[tuple[int, int, str | None]], line: int | None
) -> str | None:
    """The symbol of the tightest enclosing definition whose line span holds
    ``line``. Innermost = the latest-starting span, breaking ties by the
    earliest end, which is the correctly nested one."""
    if line is None:
        return None
    best: tuple[int, int, str | None] | None = None
    for start, end, symbol in enclosers:
        if start <= line <= end:
            if best is None or start > best[0] or (start == best[0] and end < best[1]):
                best = (start, end, symbol)
    return best[2] if best else None


def _line_key(line: int | None) -> int:
    """Sort key that keeps a ``None`` line ahead of real ones deterministically."""
    return line if line is not None else -1
