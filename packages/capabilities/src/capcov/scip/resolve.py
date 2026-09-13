"""The resolver seam: source the entity pipeline's call graph from SCIP.

This is where the hybrid is wired into the entity pipeline. ``capcov discover``
normally takes its call graph from the AST adapter's own import-plus-name-match
resolution; with ``--resolver scip`` it takes the graph from a SCIP indexer
instead, which is type-aware, cross-file and multi-language where the AST pass is
none of those. The AST adapter still runs -- it remains the source of entities,
surfaces, operations and, load-bearing, the enumerated blind spots -- so the two
halves are exactly the division ADR-0001 settles: SCIP resolves, the AST pass
says where resolution is blind.

Three properties are kept and none is free:

* **fixpoint sees the same shape.** ``core.fixpoint`` consumes ``calls`` as
  ``{node: {node, ...}}`` and ``direct`` as ``{node: {entity, ...}}``. This
  module translates every SCIP call edge from a global SCIP symbol back into the
  AST adapter's own node identity (``module.dotted:qualname``) and hands fixpoint
  a ``calls`` map of exactly that shape -- so surfaces (roots), ``direct`` and
  ``ops`` all still line up and fixpoint is untouched.

* **a name is never dropped.** Every edge SCIP resolved is carried whole in the
  artifact (``scip_resolved_edges``), including the module-scope edges the
  fixpoint cannot root at. And the sites SCIP stayed *silent* about are recovered
  by subtraction: every call site the AST pass saw, minus every site SCIP
  resolved, is the enumerated residue -- named, with a file and a line, not lost.

* **it is optional.** The module imports with no node/go tooling present (it
  pulls in ``runner``/``map``/``blindspots``, all stdlib). Only ``resolve`` --
  which actually shells out to an indexer -- needs the tools, and it fails with a
  named, actionable error when they are absent rather than silently degrading.

The translation is scip-python / scip-go shaped: a symbol carries its module
backtick-quoted (``\\`shop.router\\`/make_job().``) and a descriptor tail whose
type (``#``), term (``.``) and method (``().``) components dot-join into the same
qualname the AST walker builds. A symbol this cannot parse (a parameter, a local,
a scheme this does not know) yields ``None`` and its edge is simply not rooted --
never a crash, and never a wrong node.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Callable
from pathlib import Path

from . import blindspots
from . import map as scip_map
from . import runner

# SCIP occurrence lines are 0-based and delivered unmodified by the runner; the
# AST pass (and every human-facing capcov line) is 1-based. The residue subtracts
# SCIP-resolved sites from AST-seen sites by (file, line), so SCIP's line is
# lifted into the AST's 1-based frame here -- a mismatch would make every site
# look unresolved.
_SCIP_LINE_IS_ZERO_BASED = 1

# A SCIP symbol's module is the first backtick-quoted run; the descriptor tail is
# everything after the ``/`` that follows it. Non-quoted module forms (scip's
# ``shop/__init__:`` meta symbols, ``local 0`` locals) do not match and are not
# nodes -- exactly what should be skipped.
_MODULE_RE = re.compile(r"`([^`]+)`/(.*)$")

# Characters that terminate a descriptor name in the SCIP symbol grammar.
_NAME_STOP = set("#.(:[!/`")


def _descriptor_names(descriptor: str) -> list[str] | None:
    """The dot-joinable name path of a SCIP descriptor tail, or None.

    Walks the SCIP descriptor grammar: a type (``Name#``), a term/field
    (``name.``) and a method (``name().`` or ``name(disambiguator).``) each
    contribute their leaf name. A parameter (``(name)``), a type parameter
    (``[name]``), a meta (``name:``) or a macro (``name!``) means the symbol is
    not a callable/type node in the fixpoint's sense, so the whole parse returns
    None rather than a partial, wrong qualname.
    """
    names: list[str] = []
    i, n = 0, len(descriptor)
    while i < n:
        if descriptor[i] in "([":
            # a leading '(' or '[' is a parameter / type parameter, not a node.
            return None
        if descriptor[i] == "`":
            end = descriptor.find("`", i + 1)
            if end == -1:
                return None
            name = descriptor[i + 1 : end]
            i = end + 1
        else:
            start = i
            while i < n and descriptor[i] not in _NAME_STOP:
                i += 1
            name = descriptor[start:i]
        if i >= n:
            return None  # a bare trailing name with no terminator is malformed
        term = descriptor[i]
        if term == "#":  # type
            names.append(name)
            i += 1
        elif term == ".":  # term / field
            names.append(name)
            i += 1
        elif term == "(":  # method: skip the balanced disambiguator, expect '.'
            depth = 0
            while i < n:
                if descriptor[i] == "(":
                    depth += 1
                elif descriptor[i] == ")":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
            if i < n and descriptor[i] == ".":
                names.append(name)
                i += 1
            else:
                return None
        else:  # ':' meta, '!' macro, '/' nested package, stray backtick
            return None
    return names or None


def scip_symbol_to_node(symbol: str | None) -> str | None:
    """A SCIP callable/type symbol -> the AST adapter's ``module:qualname`` node.

    ``\\`shop.router\\`/make_job().`` -> ``shop.router:make_job``;
    ``\\`app.repo\\`/Repo#fetch().`` -> ``app.repo:Repo.fetch``;
    ``\\`app.main\\`/create_app().healthz().`` -> ``app.main:create_app.healthz``.
    Returns None for a symbol with no backtick-quoted module or whose descriptor
    is not a node path (a parameter, a local, a meta symbol) -- so an edge is
    dropped from the graph rather than pointed at a fabricated node.
    """
    if not symbol:
        return None
    match = _MODULE_RE.search(symbol)
    if not match:
        return None
    names = _descriptor_names(match.group(2))
    if not names:
        return None
    return f"{match.group(1)}:{'.'.join(names)}"


def calls_graph(
    edges: list[dict], is_node: Callable[[str], bool] | None = None
) -> dict[str, set[str]]:
    """A fixpoint ``calls`` map (``{node: {node, ...}}``) from SCIP call edges.

    Each edge's caller and callee SCIP symbols are translated to AST node
    identities. An edge with no enclosing caller (a module-scope reference,
    ``caller is None``) or whose endpoints do not translate is not rooted -- it
    is still carried whole in the artifact's ``scip_resolved_edges``. When
    ``is_node`` is given, both endpoints must satisfy it, which keeps the graph
    inside the AST adapter's node namespace and drops edges into external
    libraries the same way the AST pass does.
    """
    calls: dict[str, set[str]] = {}
    for edge in edges:
        caller = scip_symbol_to_node(edge.get("caller"))
        callee = scip_symbol_to_node(edge.get("callee"))
        if caller is None or callee is None:
            continue
        if is_node is not None and not (is_node(caller) and is_node(callee)):
            continue
        calls.setdefault(caller, set()).add(callee)
    return calls


def resolved_sites(edges: list[dict]) -> list[dict]:
    """The ``{file, line}`` sites SCIP resolved, in the AST pass's 1-based frame.

    This is the right-hand side of the residue subtraction. SCIP never says what
    it failed to resolve; the sites it *did* resolve are its call-edge
    occurrences, and anything the AST saw that is absent here is a silent gap.
    """
    out: list[dict] = []
    for edge in edges:
        file, line = edge.get("file"), edge.get("line")
        if file is None or line is None:
            continue
        out.append({"file": file, "line": line + _SCIP_LINE_IS_ZERO_BASED})
    return out


def _residue(source_root: str | Path, edges: list[dict]) -> list[dict]:
    """The enumerated residue: every call site the AST saw that SCIP left blind.

    Two silences are folded together, because both are things SCIP cannot resolve
    and capcov must name rather than drop:

    * **dynamic-access blind spots** (getattr / eval / dynamic import). SCIP does
      emit an occurrence for the *builtin call itself* -- ``getattr`` resolves to
      the builtin symbol -- but resolving the ``getattr`` call is NOT resolving
      the attribute it reaches at runtime. So a SCIP occurrence on a blind-spot
      line is disregarded, and every enumerated blind spot stays in the residue
      unconditionally, carrying its kind and reason.

    * **untyped-receiver calls** SCIP emitted no occurrence for at all
      (``session.add(job)`` on an untyped ``session``). These are recovered by
      subtracting the sites SCIP resolved from the full call census -- the silent
      gap the map module's docstring names as the reason the AST differ exists.
    """
    blind = blindspots.enumerate_blind_spots(source_root)
    blind_by_key = {(b["file"], b["line"]): b for b in blind}
    census = []
    for site in blindspots.enumerate_call_sites(source_root):
        spot = blind_by_key.get((site["file"], site["line"]))
        census.append({**site, "kind": spot["kind"], "reason": spot["reason"]} if spot else site)
    resolved = [
        site
        for site in resolved_sites(edges)
        if (site["file"], site["line"]) not in blind_by_key
    ]
    return blindspots.blind_spot_residue(census, resolved)


def hybrid_raw(ast_raw: dict, normalized: dict, source_root: str | Path) -> dict:
    """Fold a normalized SCIP index into the AST adapter's raw discover output.

    Returns a copy of ``ast_raw`` with ``_calls`` replaced by the SCIP-resolved
    graph (translated into the AST node namespace) and the SCIP evidence added:
    the full resolved edge list, the SCIP-side type definitions, and the
    enumerated residue -- the call sites the AST pass saw that SCIP left
    unresolved. Everything else the AST adapter produced (entities, surfaces,
    ``_direct``, ``_ops``, blind spots, AST residue) is preserved untouched.

    Pure over ``(ast_raw, normalized)`` plus one read of the source tree for the
    call-site census, so it is fully exercised by a checked-in fixture with no
    indexer installed.
    """
    edges = scip_map.call_edges(normalized)
    node_keys = (
        set(ast_raw.get("_direct", {}))
        | set(ast_raw.get("_calls", {}))
        | {s["handler"] for s in ast_raw.get("surfaces", [])}
    )
    scip_calls = calls_graph(edges, is_node=node_keys.__contains__)
    census = blindspots.enumerate_call_sites(source_root)
    residue = _residue(source_root, edges)

    hybrid = dict(ast_raw)
    hybrid["_calls"] = scip_calls
    hybrid["resolver"] = "scip"
    hybrid["scip_resolved_edges"] = edges
    hybrid["scip_entities"] = scip_map.entities(normalized)
    hybrid["scip_residue"] = residue
    hybrid["scip_residue_summary"] = {
        "scip_resolved_edges": len(edges),
        "scip_rooted_edges": sum(len(v) for v in scip_calls.values()),
        "ast_call_sites": len(census),
        "unresolved_enumerated": len(residue),
    }
    return hybrid


class ScipToolsUnavailable(RuntimeError):
    """A SCIP indexer or the ``scip`` CLI needed by ``resolve`` is not present."""


def tools_available(language: str) -> bool:
    """True when both the indexer for ``language`` and the ``scip`` CLI resolve.

    Use to gate the live path (a test decorator, a caller deciding whether to ask
    for ``--resolver scip``). Never runs a tool.
    """
    executable = runner._INDEXERS.get(language, (None,))[0]
    if executable is None or shutil.which(executable) is None:
        return False
    try:
        runner._locate_scip_cli()
    except runner.ScipCliNotFound:
        return False
    return True


def resolve(
    source_root: str | Path,
    ast_raw: dict,
    *,
    language: str = "python",
    timeout: int = 600,
) -> dict:
    """Index ``source_root`` with SCIP and return the hybrid raw discover output.

    This is the one impure entry point: it shells out to a SCIP indexer and the
    ``scip`` CLI. It raises ``ScipToolsUnavailable`` -- naming the missing tool
    and how to install it -- rather than degrading, because a caller that asked
    for ``--resolver scip`` wants the SCIP graph or a clear reason it could not be
    built, not a quietly hand-rolled one wearing the SCIP label. The transient
    ``index.scip`` the indexer writes into the tree is removed before returning.
    """
    if language not in runner._INDEXERS:
        raise ValueError(
            f"unsupported SCIP language {language!r}; "
            f"expected one of {sorted(runner._INDEXERS)}"
        )
    executable, install_hint = runner._INDEXERS[language]
    if shutil.which(executable) is None:
        raise ScipToolsUnavailable(
            f"--resolver scip needs the {language} indexer {executable!r}, which "
            f"is not on PATH. Install it with: {install_hint}"
        )
    try:
        runner._locate_scip_cli()
    except runner.ScipCliNotFound as exc:
        raise ScipToolsUnavailable(str(exc)) from exc

    source_root = Path(source_root)
    index_path = runner.run_scip_index(source_root, language, timeout=timeout)
    try:
        normalized = runner.read_scip_index(index_path)
    finally:
        index_path.unlink(missing_ok=True)
    return hybrid_raw(ast_raw, normalized, source_root)
