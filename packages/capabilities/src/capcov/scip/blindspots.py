"""Enumerate the blind spots no static resolver can see through, and diff the
AST's call sites against what SCIP managed to resolve.

This is the half SCIP cannot do. A `getattr(obj, name)`, an `eval`, a computed
`__import__` -- these have no static target for ANY resolver, SCIP included,
because the target is a value built at runtime, not a source token. capcov's
contract is that such a site is NAMED, not silently dropped: a resolver that
loses an edge reports fewer capabilities and looks identical to one that found
them all. So the hybrid keeps two things SCIP does not give you.

* ``enumerate_blind_spots`` lists every dynamic-access site (getattr / setattr /
  eval / exec / dynamic import / namespace reflection) with a file and a line.
  These are unresolvable by construction -- the enumerable-unresolved floor that
  is true no matter how good the resolver is.

* ``blind_spot_residue`` takes the call sites the AST pass SAW and the sites SCIP
  reported resolving, and returns the difference. SCIP never tells you what it
  failed to resolve; this recovers that set from the black box by subtraction --
  everything enumerated, minus everything resolved -- and marks each remainder
  unresolved rather than dropping it.

Pure stdlib AST work: nothing here imports the node/go SCIP CLIs, so the module
is always importable and the differ is testable with a resolver's output fed in
by hand, no indexer installed.
"""

from __future__ import annotations

import ast
from pathlib import Path

# The dynamic-access builtins. Each names an access whose target is a value, not
# a source token: `getattr(o, name)` reaches an attribute chosen at runtime and
# no static resolver can say which. The kind groups them by WHY they are blind,
# which is what a reader triaging the list acts on. This mapping is the single
# source of truth -- the FastAPI/SQLAlchemy adapter imports it back rather than
# keeping its own copy, so the two never disagree about what counts.
DYNAMIC_BLIND_CALLS = {
    "getattr": "attribute_by_name",
    "setattr": "attribute_by_name",
    "delattr": "attribute_by_name",
    "vars": "namespace_lookup",
    "globals": "namespace_lookup",
    "locals": "namespace_lookup",
    "eval": "dynamic_eval",
    "exec": "dynamic_eval",
    "__import__": "dynamic_import",
    "import_module": "dynamic_import",
}

_REASONS = {
    "attribute_by_name": (
        "attribute accessed by a computed name; the target is not statically "
        "knowable"
    ),
    "namespace_lookup": (
        "namespace read by reflection; its members are not statically enumerable"
    ),
    "dynamic_eval": (
        "code assembled and evaluated at runtime; there is no static call target"
    ),
    "dynamic_import": (
        "module imported by a computed name; the import target is not statically "
        "knowable"
    ),
}

_RESIDUE_REASON = "seen by the ast pass; scip returned no resolution for this site"


def constant_name_arg(node: ast.Call) -> str | None:
    """The 2nd positional argument when it is a string constant, else None.

    ``getattr(o, "field")`` is NOT blind: the name is a literal token any
    analyser can read. Only a computed name hides the access. Returning the
    literal lets a caller record the resolved form instead of inflating the
    blind-spot count with sites nobody needs to review.
    """
    if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
        value = node.args[1].value
        return value if isinstance(value, str) else None
    return None


def blind_spot_for_call(node: ast.Call) -> tuple[str, str | None] | None:
    """``(kind, statically_resolved_name)`` if the call is a dynamic-access builtin.

    ``resolved_name`` is the literal attribute/module name when the call spells
    it out (so it is NOT blind); None means the access is computed and blind.
    Returns None when the call is not a dynamic-access builtin at all.
    """
    fn = node.func
    name = (
        fn.id
        if isinstance(fn, ast.Name)
        else fn.attr
        if isinstance(fn, ast.Attribute)
        else None
    )
    if name not in DYNAMIC_BLIND_CALLS:
        return None
    return DYNAMIC_BLIND_CALLS[name], constant_name_arg(node)


def _iter_py_files(root: Path):
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        yield path


def _render_callee(node: ast.Call) -> str:
    """A readable name for a call's target: ``f``, ``a.b.c``, or the node type
    for a call on an expression (``f()()``). Best-effort; never raises."""
    fn = node.func
    parts: list[str] = []
    while isinstance(fn, ast.Attribute):
        parts.append(fn.attr)
        fn = fn.value
    if isinstance(fn, ast.Name):
        parts.append(fn.id)
    else:
        parts.append(type(fn).__name__)
    return ".".join(reversed(parts))


def enumerate_call_sites(py_source_tree: str | Path) -> list[dict]:
    """Every call site under ``py_source_tree``, as ``{file, line, callee}``.

    This is the left-hand side of the SCIP residue subtraction: the complete set
    of call sites the AST pass SAW, so that ``blind_spot_residue`` can name the
    ones SCIP stayed silent about. It deliberately includes ordinary calls, not
    just dynamic-access builtins -- because SCIP's most important silent gap is
    an ordinary method call on a receiver it could not type (``session.add(job)``
    on an untyped ``session`` emits no occurrence at all), and only a full call
    census surfaces it. ``file`` is POSIX and tree-relative; ``line`` is the
    1-based ``ast`` line, matching ``enumerate_blind_spots``. Sorted by
    (file, line, callee) for a stable diff.
    """
    root = Path(py_source_tree)
    out: list[dict] = []
    for path in _iter_py_files(root):
        rel = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            out.append(
                {"file": rel, "line": node.lineno, "callee": _render_callee(node)}
            )
    out.sort(key=lambda c: (c["file"], c["line"], c["callee"]))
    return out


def enumerate_blind_spots(py_source_tree: str | Path) -> list[dict]:
    """Every dynamic-access blind spot under ``py_source_tree``.

    Returns ``{file, line, kind, reason}`` per site, ``file`` POSIX and relative
    to the tree root, sorted by (file, line) so the list is stable to diff. Only
    genuinely blind sites are returned: a ``getattr(o, "literal")`` is
    statically resolvable and omitted, matching the adapter's own blind /
    not-blind split.
    """
    root = Path(py_source_tree)
    out: list[dict] = []
    for path in _iter_py_files(root):
        rel = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            classified = blind_spot_for_call(node)
            if classified is None:
                continue
            kind, resolved = classified
            if resolved is not None:
                # the literal form -- statically readable, so not a blind spot
                continue
            out.append(
                {
                    "file": rel,
                    "line": node.lineno,
                    "kind": kind,
                    "reason": _REASONS[kind],
                }
            )
    out.sort(key=lambda b: (b["file"], b["line"]))
    return out


def _site_key(site: dict) -> tuple[str, int]:
    return (site["file"], site["line"])


def blind_spot_residue(
    ast_call_sites: list[dict],
    scip_resolved_sites: list[dict],
    reason: str = _RESIDUE_REASON,
) -> list[dict]:
    """The call sites the AST pass SAW but SCIP did NOT resolve, matched by file+line.

    SCIP reports what it resolved and stays silent about the rest, so its own
    unresolved list is recovered here by subtraction: every site in
    ``ast_call_sites`` whose (file, line) is absent from ``scip_resolved_sites``.
    Each remainder is returned with the original site's fields preserved, plus
    ``resolved: False`` and a ``reason`` -- NAMED, not dropped, which is the
    capcov property the hybrid must not lose to a black-box resolver.

    Matching is exact on (file, line); both sides must use the same file
    convention (tree-relative POSIX, as ``enumerate_blind_spots`` emits). When a
    site already carries its own ``reason`` (e.g. a blind-spot kind), it is kept
    and the residue clause is appended, so no information is lost.
    """
    resolved_keys = {_site_key(s) for s in scip_resolved_sites}
    residue: list[dict] = []
    for site in ast_call_sites:
        if _site_key(site) in resolved_keys:
            continue
        prior = site.get("reason")
        residue.append(
            {
                **site,
                "resolved": False,
                "reason": f"{prior}; {reason}" if prior else reason,
            }
        )
    residue.sort(key=_site_key)
    return residue
