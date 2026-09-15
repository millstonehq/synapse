"""target-go static path pilot helpers (EXPERIMENT-PLAN section 30).

The pilot runs the SCIP -> Datalog static path of section 29 against an
*external* Go checkout for the first time.  Everything here is either a pure
function over an already-normalized index (slice selection, coverage, the
claim-time bundle pieces) or a thin, explicitly impure wrapper around one
subprocess (``git archive``, ``git rev-parse``, tool version probes).  The
indexing itself goes through ``scip.runner.run_scip_index`` as everywhere else.

Decisions this module encodes, all recorded in section 30:

* The tree that is indexed is a ``git archive HEAD`` copy of the checkout, so
  nested ``.worktrees/*`` checkouts, untracked files and uncommitted edits are
  excluded by construction; the checkout's ``HEAD`` and ``git status
  --porcelain`` are recorded as a receipt, never used as identity.
* The slice is the import closure of the route handler's package.  scip-go
  0.2.7 emits no ``Import`` symbol roles, so the closure is computed from the
  packages of the first-party symbols each document references (a reference
  to another package's symbol is only possible through an import, so this is
  the import graph restricted to the module).  ``_test.go`` documents and
  test-binary packages (``pkg.test``, ``pkg_test``) are excluded: the route's
  production closure does not import them.
* The route handler is not observed by the tree-sitter route query (target-go
  registers ``net/http`` patterns through ``ServeMux.HandleFunc`` on a closure
  the go_app query does not match).  It is therefore declared as a labelled
  **assumption** -- ``route_handler_symbol__accepted(index, surface,
  symbol)`` with ``Evidence.kind == "assumption"`` and a source string naming
  the router line it was read from -- and one extra rule derives the pack's
  ``static_route_handler`` from it, guarded by the index's own ``scip_symbol``
  row for a callable of that name.  No ``route_site`` / ``route_handler_location``
  observation is fabricated.
* target-go issues SQL through ``database/sql`` and sends mail through its own
  ``Mailer`` implementations; the gorm/php recognizer produces no
  ``static_op_site`` rows for it.  The pilot claim is therefore
  ``static_reaches(index, handler, sink)`` for named sink symbols, not
  ``static_capability_op``.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from ...scip import resolve
from ..ir import (Atom, Bundle, Claim, Column, Constant, Context, Evidence, RelationDecl,
                  Rule, Variable)
from . import scip_facts

ARCHIVE_TIMEOUT = 300
ROUTE_HANDLER_ASSUMPTION = "route_handler_symbol__accepted"
ROUTE_HANDLER_RULE = "static_route_handler_from_accepted_symbol"
COVERAGE_THRESHOLD = 0.9
OUTCOME_SUPPORTED = "supported"
OUTCOME_UNKNOWN = "UNKNOWN"

_TEST_PACKAGE_SUFFIXES = (".test", "_test")


# ---------------------------------------------------------------------------
# target checkout


@dataclass(frozen=True)
class Checkout:
    root: str
    head: str
    porcelain: tuple[str, ...]
    module_path: str
    go_directive: str

    @property
    def dirty(self) -> bool:
        return bool(self.porcelain)

    def receipt(self) -> dict[str, Any]:
        return {"root": self.root, "head": self.head, "dirty": self.dirty,
                "porcelain": list(self.porcelain), "module_path": self.module_path,
                "go_directive": self.go_directive}


def parse_go_mod(text: str) -> tuple[str, str]:
    """``(module path, go directive)`` from a ``go.mod``; pure."""
    module = re.search(r"^module\s+(\S+)\s*$", text, re.MULTILINE)
    go = re.search(r"^go\s+(\S+)\s*$", text, re.MULTILINE)
    if module is None:
        raise ValueError("go.mod has no module directive")
    return module.group(1), go.group(1) if go else ""


def _git(root: Path, *args: str, timeout: int = 60) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                            timeout=timeout, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} exited {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def inspect_checkout(root: str | os.PathLike[str]) -> Checkout:
    """Record HEAD, porcelain status and the go.mod identity of a checkout (impure: git)."""
    path = Path(root)
    module, go = parse_go_mod((path / "go.mod").read_text(encoding="utf-8"))
    head = _git(path, "rev-parse", "HEAD").strip()
    porcelain = tuple(line for line in _git(path, "status", "--porcelain").splitlines() if line)
    return Checkout(str(path), head, porcelain, module, go)


def archive_head(root: str | os.PathLike[str], dest: str | os.PathLike[str], *,
                 timeout: int = ARCHIVE_TIMEOUT) -> Path:
    """Extract ``git archive HEAD`` of ``root`` into ``dest`` (impure: git + tar).

    The archive holds tracked files of HEAD only: no nested worktrees, no
    untracked files, no uncommitted edits.
    """
    target = Path(dest)
    target.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(["git", "-C", str(root), "archive", "--format=tar", "HEAD"],
                             capture_output=True, timeout=timeout, check=False)
    if archive.returncode != 0:
        raise RuntimeError(f"git archive exited {archive.returncode}: "
                           f"{archive.stderr.decode('utf-8', 'replace').strip()}")
    extract = subprocess.run(["tar", "-x", "-C", str(target)], input=archive.stdout,
                             capture_output=True, timeout=timeout, check=False)
    if extract.returncode != 0:
        raise RuntimeError(f"tar exited {extract.returncode}: "
                           f"{extract.stderr.decode('utf-8', 'replace').strip()}")
    return target


def index_environment(modcache: str | os.PathLike[str], gocache: str | os.PathLike[str]) -> dict[str, str]:
    """The Go environment scip-go is run under (pure): module mode, the pinned
    toolchain only, and caches under directories the caller records."""
    return {"GOFLAGS": "-mod=mod", "GOTOOLCHAIN": "local",
            "GOMODCACHE": str(modcache), "GOCACHE": str(gocache)}


def tool_receipt(names: Iterable[str] = ("scip-go", "scip", "go", "souffle")) -> dict[str, dict[str, str]]:
    """Resolved path and ``--version`` line of each tool (impure)."""
    out: dict[str, dict[str, str]] = {}
    for name in names:
        path = shutil.which(name)
        entry = {"path": path or ""}
        if path:
            argv = [path, "version"] if name == "go" else [path, "--version"]
            try:
                probe = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
                text = (probe.stdout or probe.stderr).strip().splitlines()
                # the first line that is not a banner rule: "0.2.7", "scip version
                # v0.9.0", "go version go1.27.0 ..."; the nix-built Soufflé prints
                # an empty "Version:" line, so its store path is the pin there.
                entry["version"] = next((line.strip() for line in text
                                         if line.strip() and set(line.strip()) != {"-"}), "")
            except (OSError, subprocess.TimeoutExpired) as exc:
                entry["version"] = f"probe failed: {exc}"
        out[name] = entry
    return out


def sha256_file(path: str | os.PathLike[str]) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# slice selection (pure over the normalized index)


def symbol_package(symbol: str | None) -> str | None:
    """The package path a SCIP symbol belongs to, or None for locals / unknown schemes.

    A bare package symbol (descriptor ending in ``/``) maps to itself.
    """
    tail = resolve._strip_scip_prefix(symbol)
    if tail is None:
        return None
    parsed = resolve._parse_descriptor(tail)
    if parsed is None:
        if tail.endswith("/"):
            return tail[:-1].strip("`") or None
        return None
    namespaces, _ = parsed
    return "/".join(namespaces) if namespaces else None


def document_packages(normalized: Mapping[str, Any], language: str = "go") -> dict[str, str | None]:
    """``{document path: package}`` from each document's first rooted definition."""
    to_node = resolve.normalizer(language)
    return {document["path"]: scip_facts._document_package(document, to_node)
            for document in normalized.get("documents", []) or [] if document.get("path") is not None}


def is_test_document(path: str, package: str | None) -> bool:
    return path.endswith("_test.go") or bool(package and package.endswith(_TEST_PACKAGE_SUFFIXES))


@dataclass(frozen=True)
class ImportClosure:
    start: str
    packages: tuple[str, ...]
    documents: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    excluded_test_documents: tuple[str, ...]
    occurrences: int

    def receipt(self) -> dict[str, Any]:
        return {"start": self.start, "packages": list(self.packages), "document_count": len(self.documents),
                "documents": list(self.documents), "edge_count": len(self.edges),
                "excluded_test_documents": len(self.excluded_test_documents),
                "occurrences": self.occurrences}


def package_closure(normalized: Mapping[str, Any], module: str, start_package: str, *,
                    language: str = "go", include_tests: bool = False) -> ImportClosure:
    """The first-party import closure of ``start_package`` (pure).

    Edges are ``document package -> package of a referenced first-party
    symbol`` (any non-definition occurrence).  scip-go emits no ``Import``
    roles, and a cross-package reference is only possible through an import,
    so this is the module-restricted import graph.  Test documents are
    excluded unless ``include_tests``.
    """
    packages = document_packages(normalized, language)
    documents = normalized.get("documents", []) or []
    excluded = tuple(sorted(path for path, package in packages.items()
                            if is_test_document(path, package)))
    edges: dict[str, set[str]] = {}
    for document in documents:
        path = document.get("path")
        source = packages.get(path)
        if source is None or (not include_tests and path in excluded):
            continue
        for occ in document.get("occurrences", []) or []:
            if occ.get("is_definition"):
                continue
            target = symbol_package(occ.get("symbol"))
            if target and target.startswith(module) and target != source:
                edges.setdefault(source, set()).add(target)
    seen = {start_package}
    frontier = [start_package]
    while frontier:
        package = frontier.pop()
        for target in sorted(edges.get(package, ())):
            if target not in seen:
                seen.add(target)
                frontier.append(target)
    in_slice = tuple(sorted(path for path, package in packages.items()
                            if package in seen and (include_tests or path not in excluded)))
    occurrences = sum(len(d.get("occurrences", []) or []) for d in documents if d.get("path") in set(in_slice))
    edge_rows = tuple(sorted((src, dst) for src, targets in edges.items() if src in seen
                             for dst in targets if dst in seen))
    return ImportClosure(start_package, tuple(sorted(seen)), in_slice, edge_rows, excluded, occurrences)


# ---------------------------------------------------------------------------
# coverage over the exported slice (pure over bundle facts)


def _rows(bundle: Bundle, relation: str) -> list[list[Any]]:
    return [[term.value for term in fact.terms] for fact in bundle.facts if fact.relation == relation]


@dataclass(frozen=True)
class Coverage:
    total_edges: int
    rooted_edges: int
    unrooted: dict[str, str] = field(default_factory=dict)   # symbol -> reason
    rooted: frozenset[str] = frozenset()

    @property
    def ratio(self) -> float:
        return self.rooted_edges / self.total_edges if self.total_edges else 0.0

    def receipt(self) -> dict[str, Any]:
        reasons: dict[str, int] = {}
        for reason in self.unrooted.values():
            reasons[reason] = reasons.get(reason, 0) + 1
        return {"total_edges": self.total_edges, "rooted_edges": self.rooted_edges,
                "ratio": round(self.ratio, 6), "unrooted_symbols": len(self.unrooted),
                "unrooted_reasons": dict(sorted(reasons.items())), "rooted_symbols": len(self.rooted)}


def edge_coverage(exported: Bundle) -> Coverage:
    """``rooted edges / resolved edges``: a ``scip_may_reference`` row is rooted
    when both endpoints carry a ``scip_symbol_node`` row."""
    rooted = frozenset(row[1] for row in _rows(exported, "scip_symbol_node"))
    unrooted = {row[1]: row[2] for row in _rows(exported, "scip_symbol_unrooted")}
    edges = [(row[1], row[2]) for row in _rows(exported, "scip_may_reference")]
    rooted_edges = sum(1 for caller, callee in edges if caller in rooted and callee in rooted)
    return Coverage(len(edges), rooted_edges, unrooted, rooted)


def closure_symbols(relations: Any, index: str, root: str) -> list[str]:
    """The root plus every ``static_reaches(index, root, dst)`` destination, sorted."""
    rows = dict(relations).get("static_reaches", ()) if not isinstance(relations, Mapping) else relations.get("static_reaches", ())
    return sorted({root, *(row[2] for row in rows if row[0] == index and row[1] == root)})


def unrooted_on_closure(coverage: Coverage, closure: Iterable[str]) -> dict[str, str]:
    return {symbol: coverage.unrooted[symbol] for symbol in closure if symbol in coverage.unrooted}


def outcome(*, claim_supported: bool, coverage: Coverage, unrooted_closure: Mapping[str, str],
            deep_unresolved: int, threshold: float = COVERAGE_THRESHOLD) -> tuple[str, list[str]]:
    """``supported`` or ``UNKNOWN`` with the reasons; the section-30 decision rule."""
    reasons: list[str] = []
    if not claim_supported:
        reasons.append("route claim not supported in both kernels")
    if coverage.ratio < threshold:
        reasons.append(f"rooted-edge coverage {coverage.ratio:.4f} < {threshold}")
    if unrooted_closure:
        reasons.append(f"{len(unrooted_closure)} unrooted symbol(s) on the route closure")
    if deep_unresolved:
        reasons.append(f"{deep_unresolved} deep-unresolved row(s)")
    return (OUTCOME_SUPPORTED if not reasons else OUTCOME_UNKNOWN), reasons


# ---------------------------------------------------------------------------
# claim-time bundle pieces


def _fact(relation: str, decl: RelationDecl, values: Mapping[str, Any], evidence_id: str, source: str,
          depends_on: Iterable[str] = (), kind: str = "fact") -> tuple[Atom, Evidence]:
    atom = Atom(relation, tuple(Constant(values[column.name], column.type) for column in decl.columns))
    context = {name: values[name] for name in decl.context_indices}
    return atom, Evidence(evidence_id, atom, Context.from_mapping(context), source, tuple(depends_on), kind)


ROUTE_HANDLER_DECL = RelationDecl(
    ROUTE_HANDLER_ASSUMPTION,
    (Column("index", "digest", True), Column("surface", "symbol"), Column("symbol", "symbol")),
    modality="assumption", binding="static", primitive=True, context_indices=("index",))

# static_route_handler(IX,S,Sym) :- route_handler_symbol__accepted(IX,S,Sym),
#                                   scip_symbol(IX,Sym,_,"callable",_).
ROUTE_HANDLER_RULES = (
    Rule(Atom("static_route_handler", (Variable("IX"), Variable("S"), Variable("Sym"))),
         (Atom(ROUTE_HANDLER_ASSUMPTION, (Variable("IX"), Variable("S"), Variable("Sym"))),
          Atom("scip_symbol", (Variable("IX"), Variable("Sym"), Variable("Kind"),
                               Constant("callable", "symbol"), Variable("Display")))),
         name=ROUTE_HANDLER_RULE),
)


def route_handler_assumption(index: str, surface: str, handler_symbol: str, *, declared_from: str,
                             index_evidence_id: str | None = None) -> Bundle:
    """A bundle declaring the route handler as a labelled assumption plus the
    one rule that lets the pack's ``static_route_handler`` read it.

    ``declared_from`` names the router source line(s) a human read the
    binding from; it becomes ``Evidence.source`` so the leaf says what it is.
    """
    row = [index, surface, handler_symbol]
    atom, evidence = _fact(
        ROUTE_HANDLER_ASSUMPTION, ROUTE_HANDLER_DECL,
        {"index": index, "surface": surface, "symbol": handler_symbol},
        scip_facts.evidence_id(index, ROUTE_HANDLER_ASSUMPTION, row),
        f"human-declared from router source: {declared_from}",
        [index_evidence_id] if index_evidence_id else (), kind="assumption")
    return Bundle((ROUTE_HANDLER_DECL,), facts=(atom,), rules=ROUTE_HANDLER_RULES, evidence=(evidence,))


def source_tree_observation(decls: Mapping[str, RelationDecl], tree_digest: str, *,
                            source: str = "pilot claim-time observation of the archived tree") -> tuple[Atom, Evidence]:
    return _fact("source_tree_observed", decls["source_tree_observed"], {"tree_digest": tree_digest},
                 f"static:claim-time:source_tree_observed:{scip_facts.row_digest('source_tree_observed', [tree_digest])[:12]}",
                 source)


def reaches_claim(index: str, root: str, dst: str, claim_id: str) -> Claim:
    return Claim("static_reaches", (Constant(index, "digest"), Constant(root, "symbol"), Constant(dst, "symbol")),
                 Context.from_mapping({"index": index}), id=claim_id)


def module_prefix_violations(exported: Bundle, module: str) -> list[str]:
    """Rooted symbols *defined* in this index whose package is not under ``module``."""
    rooted = {row[1] for row in _rows(exported, "scip_symbol_node")}
    defined = {row[3] for row in _rows(exported, "scip_definition_site")}
    return sorted(symbol for symbol in defined & rooted
                  if not (symbol_package(symbol) or "").startswith(module))


__all__ = [
    "ARCHIVE_TIMEOUT", "ROUTE_HANDLER_ASSUMPTION", "ROUTE_HANDLER_RULE", "ROUTE_HANDLER_DECL",
    "ROUTE_HANDLER_RULES", "COVERAGE_THRESHOLD", "OUTCOME_SUPPORTED", "OUTCOME_UNKNOWN",
    "Checkout", "parse_go_mod", "inspect_checkout", "archive_head", "index_environment", "tool_receipt",
    "sha256_file", "symbol_package", "document_packages", "is_test_document", "ImportClosure",
    "package_closure", "Coverage", "edge_coverage", "closure_symbols", "unrooted_on_closure", "outcome",
    "route_handler_assumption", "source_tree_observation", "reaches_claim", "module_prefix_violations",
]
