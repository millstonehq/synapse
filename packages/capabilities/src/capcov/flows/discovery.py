"""Source obligations, including explicit limits of each discovery adapter.

Locations and hashes are emitted; source expressions (potential secrets) are not.
Structural candidates do not claim semantic outcomes or runtime reachability.

Two generic mechanisms cover the two classes of input, and everything else is
config:

  treesitter-routes  the sole code reader: routes in any tree-sitter-supported
      language. Needs the optional `treesitter` extra (tree-sitter +
      tree-sitter-language-pack), lazily imported so core discovery stays
      stdlib-only. The opinion of WHICH calls are routes lives in a
      config-supplied tree-sitter query, not here, so one adapter serves Go,
      JavaScript, Python and the rest. It sees literal string arguments in the
      nodes the query matches: a path built by concatenation or held in a
      variable is invisible and emits an unresolved dynamic-route obligation --
      but, unlike a regex, it is comment- and syntax-aware (a commented-out call
      is a comment node and never matches). When the query also captures the
      enclosing handler as @handler, its subtree is walked for branch-candidate
      (per branch node, both outcomes) and exception-candidate (per exception
      handler) obligations; the branch and exception node types are config-driven
      (branch_nodes, exception_nodes) with per-language defaults. An optional
      `methods` allowlist records a matched, route-shaped candidate whose verb is
      outside the set under `excluded_surfaces` instead of as a surface -- the
      query saw it and the verb filter dropped it, so it is filtered, not absent.

  openapi-json       a declarative contract reader: OpenAPI is one config of the
      generic structured-spec engine (structured_spec.OPENAPI_SPEC), not a
      bespoke adapter. Same obligations, same boundaries, same ids.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from pathlib import Path

from .model import digest
from .structured_spec import OPENAPI_SPEC, derive as derive_structured_spec


# Standard tree-sitter predicates. The binding applies these when it runs the
# query, but it exposes no API to read #eq?/#match? back, so we parse them from
# the query text and re-check each match ourselves. Redundant where the binding
# already filters; the actual filter if a binding ever stops -- and, unit-tested
# directly, it makes "predicates are honoured" our guarantee, not the binding's.
_TS_PREDICATE = re.compile(
    r"\(#(?P<neg>not-)?(?P<op>eq|match)\?\s+@(?P<cap>[\w.\-]+)\s+"
    r'(?:"(?P<lit>(?:\\.|[^"\\])*)"|@(?P<cap2>[\w.\-]+))\s*\)'
)
_TS_UNESCAPE = {r"\\": "\\", r"\"": '"', r"\n": "\n", r"\t": "\t", r"\r": "\r"}
_ROUTE_QUOTES = "\"'`"
_ROUTE_METHOD = re.compile(r"^(GET|POST|PUT|PATCH|DELETE) ")


def _ts_unescape(text: str) -> str:
    return re.sub(r'\\[\\"ntr]', lambda m: _TS_UNESCAPE[m.group(0)], text)


def _ts_predicates(query: str) -> list[dict]:
    predicates: list[dict] = []
    for match in _TS_PREDICATE.finditer(query):
        literal = match.group("lit")
        entry: dict = {
            "op": match.group("op"),
            "neg": bool(match.group("neg")),
            "cap": match.group("cap"),
            "cap2": match.group("cap2"),
            "lit": _ts_unescape(literal) if literal is not None else None,
        }
        if entry["op"] == "match" and entry["lit"] is not None:
            entry["re"] = re.compile(entry["lit"])
        predicates.append(entry)
    return predicates


def _ts_satisfied(predicates: list[dict], captures: dict) -> bool:
    for predicate in predicates:
        left = captures.get(predicate["cap"])
        if not left:
            # The predicate names a capture this match never bound; it belongs
            # to a different pattern and does not constrain this one.
            continue
        texts = [node.text.decode() for node in left]
        if predicate["op"] == "eq":
            if predicate["cap2"] is not None:
                right = captures.get(predicate["cap2"])
                if not right:
                    continue
                ok = set(texts) == {node.text.decode() for node in right}
            else:
                ok = all(text == predicate["lit"] for text in texts)
        else:
            ok = all(predicate["re"].search(text) is not None for text in texts)
        if predicate["neg"]:
            ok = not ok
        if not ok:
            return False
    return True


def _route_from_literal(text: str, strip_suffixes: list[str]) -> tuple[str, str | None]:
    if text[:1] in _ROUTE_QUOTES:
        text = text[1:]
    if text[-1:] in _ROUTE_QUOTES:
        text = text[:-1]
    method = None
    verb = _ROUTE_METHOD.match(text)
    if verb:
        method = verb.group(1)
        text = text[verb.end() :]
    for suffix in strip_suffixes:
        if suffix and text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return text, method


# One if/for/except is a structural obligation until a scenario links it; the
# node types that count as a branch or an exception handler are language-specific,
# so the config may override them and these are the sensible per-language defaults.
_DEFAULT_BRANCH_NODES = ("if_statement",)
_DEFAULT_EXCEPTION_NODES = {
    "python": ("except_clause",),
    "javascript": ("catch_clause",),
    "typescript": ("catch_clause",),
    "tsx": ("catch_clause",),
    "go": ("defer_statement",),
}


def _is_string_literal(node: object) -> bool:
    """A path arg is resolvable only if it is a literal string; an identifier or a
    concatenation is unresolvable and yields a dynamic-route obligation instead."""
    if "string" in node.type:  # type: ignore[attr-defined]
        return True
    text = node.text.decode()  # type: ignore[attr-defined]
    return bool(text) and text[0] in _ROUTE_QUOTES


def _handler_name(node: object) -> str | None:
    """A clean identifier for the handler, never the function's source text (a
    body may hold a secret; the docstring's promise is locations and hashes only)."""
    if node.child_count == 0:  # type: ignore[attr-defined]
        return _route_from_literal(node.text.decode(), [])[0] or None  # type: ignore[attr-defined]
    name = node.child_by_field_name("name")  # type: ignore[attr-defined]
    if name is not None and name.child_count == 0:
        return name.text.decode()
    return None


def _descendants(node: object):
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        for index in range(current.child_count):  # type: ignore[attr-defined]
            stack.append(current.child(index))  # type: ignore[attr-defined]


def discover(config_path: Path) -> dict:
    """Run the discovery engine on a config file on disk.

    Thin wrapper over `_discover_from_config`: the flows CLI reads a
    `discovery.json`, while the promoted core adapters assemble the same config
    in memory from `capcov.toml` and call the shared engine directly. Kept
    byte-identical for existing flows callers -- the parsed config, its parent as
    the base for `root`, and the file name used in the route boundary provenance.
    """
    config = json.loads(config_path.read_text())
    return _discover_from_config(config, config_path.parent, config_path.name)


def _discover_from_config(config: dict, base: Path, config_name: str) -> dict:
    """The discovery engine over an already-parsed config.

    `base` is the directory `config["root"]` is resolved against; `config_name`
    is the label stamped on the route-reading boundary obligations (a real file
    name for the flows CLI, `capcov.toml` for a core adapter). This is an
    additive extraction: `discover(config_path)` is its only on-disk caller and
    its behaviour is unchanged.
    """
    root = (base / config["root"]).resolve()
    obligations: list[dict] = []
    sources = {}
    graphs = []
    source_census = []
    analysed_files: set[str] = set()
    route_boundaries_added = False
    # Provenance the coverage denominator would otherwise hide: route-shaped
    # candidates the query could see but filtered out, and declared adapters that
    # resolved to no surface at all. Neither adds obligations; both make a
    # silently narrowed N legible instead of implied by absence.
    excluded_surfaces: list[dict] = []
    unresolved_adapters: list[dict] = []

    def source(relative: str) -> Path:
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"missing or out-of-root source: {relative}")
        sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path

    def add(name: str, kind: str, file: str, line: int, **extra: object) -> None:
        obligations.append(
            {"id": name, "kind": kind, "source": {"file": file, "line": line}, **extra}
        )

    for relative in config.get("supporting_files", []):
        source(relative)

    for scope in config.get("source_sets", []):
        directory = (root / scope["directory"]).resolve()
        if not directory.is_relative_to(root) or not directory.is_dir():
            raise ValueError(f"missing or out-of-root source set: {scope['directory']}")
        exclusions = scope.get("exclude", {})
        if any(not reason.strip() for reason in exclusions.values()):
            raise ValueError("source exclusions require reasons")
        matched = 0
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            local = path.relative_to(directory).as_posix()
            if any(fnmatch.fnmatch(local, pattern) for pattern in exclusions):
                continue
            relative = path.relative_to(root).as_posix()
            source(relative)
            matched += 1
            recognised = path.suffix in scope["extensions"]
            source_census.append({"file": relative, "classified": recognised})
            if not recognised:
                add(
                    f"boundary:file:{relative}",
                    "unresolved",
                    relative,
                    1,
                    reason="file type has no configured discovery adapter",
                )
        if not matched:
            raise ValueError(f"empty source set: {scope['directory']}")

    adapters = config["adapters"]
    if not adapters:
        unresolved_adapters.append({
            "adapter": None,
            "kind": None,
            "reason": "no discovery adapters declared; no language resolves to surfaces",
        })
    for index, adapter in enumerate(adapters):
        kind = adapter["kind"]
        surfaces_before = sum(1 for o in obligations if o["kind"] == "surface")
        if kind == "treesitter-routes":
            try:
                import tree_sitter as ts
                from tree_sitter_language_pack import get_language
            except ImportError as exc:
                raise ValueError("treesitter-routes needs the 'treesitter' extra") from exc
            language = get_language(adapter["language"])
            query = ts.Query(language, adapter["query"])
            predicates = _ts_predicates(adapter["query"])
            parser = ts.Parser(language)
            id_prefix = adapter.get("id_prefix", "http:")
            strip_suffixes = adapter.get("strip_suffixes", ["{$}"])
            branch_nodes = set(adapter.get("branch_nodes", _DEFAULT_BRANCH_NODES))
            exception_nodes = set(
                adapter.get(
                    "exception_nodes", _DEFAULT_EXCEPTION_NODES.get(adapter["language"], ())
                )
            )
            # Optional recognised-verb allowlist. When declared, a matched
            # route-shaped candidate whose verb is outside it is filtered into
            # excluded_surfaces rather than emitted as a surface -- the generic
            # analogue of the retired Python reader's HTTP-verb whitelist.
            methods_allow = adapter.get("methods")
            if methods_allow is not None:
                methods_allow = {str(m).upper() for m in methods_allow}
            files = set(adapter.get("files", []))
            for pattern in adapter.get("globs", []):
                discovered = {
                    p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file()
                }
                if not discovered:
                    raise ValueError(f"empty treesitter source glob: {pattern}")
                files.update(discovered)
            seen: set[str] = set()
            for relative in sorted(files):
                tree = parser.parse(source(relative).read_bytes())
                analysed_files.add(relative)
                candidates = []
                for _pattern, captures in ts.QueryCursor(query).matches(tree.root_node):
                    if "path" not in captures or not _ts_satisfied(predicates, captures):
                        continue
                    method = None
                    if captures.get("method"):
                        method = _route_from_literal(captures["method"][0].text.decode(), [])[0]
                        method = method.upper()
                    # The query may capture the enclosing handler node; walking its
                    # subtree yields the branch and exception candidates below.
                    handler_node = captures["handler"][0] if captures.get("handler") else None
                    for node in captures["path"]:
                        candidates.append((node.start_byte, node, method, handler_node))
                for _start, node, method, handler_node in sorted(candidates, key=lambda c: c[0]):
                    line = node.start_point[0] + 1
                    if not _is_string_literal(node):
                        # The call is a route but the path is not a literal, so it
                        # yields an unresolved dynamic-route obligation.
                        add(
                            f"{relative}:{line}:{node.start_point[1]}:dynamic-route",
                            "unresolved",
                            relative,
                            line,
                        )
                        continue
                    route, verb = _route_from_literal(node.text.decode(), strip_suffixes)
                    effective_method = method or verb
                    if (
                        methods_allow is not None
                        and effective_method is not None
                        and effective_method not in methods_allow
                    ):
                        # Route-shaped, but the verb is outside the recognised set:
                        # the query saw it and the filter dropped it. Report it,
                        # do not inflate the denominator with it.
                        excluded_surfaces.append({
                            "file": relative,
                            "line": line,
                            "method": effective_method,
                            "path": route,
                            "handler": _handler_name(handler_node) if handler_node is not None else None,
                            "reason": "route method not in the configured recognised verb set",
                        })
                        continue
                    name = id_prefix + route
                    if name in seen:
                        continue
                    seen.add(name)
                    extra: dict[str, object] = {}
                    if effective_method:
                        extra["method"] = effective_method
                    handler = _handler_name(handler_node) if handler_node is not None else None
                    if handler:
                        extra["handler"] = handler
                    add(name, "surface", relative, line, **extra)
                    if handler_node is None:
                        continue
                    # Both outcomes of a branch, and each exception handler, are
                    # obligations until linked to a scenario.
                    for child in _descendants(handler_node):
                        if child.type in branch_nodes:
                            condition = child.child_by_field_name("condition")
                            signature = digest((condition or child).text.decode())[:12]
                            branch_line = child.start_point[0] + 1
                            for outcome in ("true", "false"):
                                add(
                                    f"{name}:branch:{signature}:{branch_line}:{outcome}",
                                    "branch-candidate",
                                    relative,
                                    branch_line,
                                    surface=name,
                                )
                        elif child.type in exception_nodes:
                            exc_line = child.start_point[0] + 1
                            add(
                                f"{name}:except:{exc_line}",
                                "exception-candidate",
                                relative,
                                exc_line,
                                surface=name,
                            )
            if not route_boundaries_added:
                # These limits describe what static route reading cannot resolve;
                # emitted once even across several route adapters. The ids retain
                # the `boundary:python:` token because model.reconcile credits the
                # literal `boundary:python:mounted-route-confirmation` when a
                # runtime mount census clears it -- renaming here without model.py
                # would silently drop that credit.
                for category in (
                    "called-function-branches",
                    "mounted-route-confirmation",
                    "roles-and-configurations",
                    "external-effects",
                ):
                    add(f"boundary:python:{category}", "unresolved", config_name, 1)
                route_boundaries_added = True
        elif kind == "openapi-json":
            relative = adapter["document"]
            document = source(relative)
            obligations.extend(
                derive_structured_spec(
                    document.read_text(), OPENAPI_SPEC, relative, adapter.get("prefix", "")
                )
            )
            graphs.append({
                "edges": [], "census": [],
                "unresolved": [{
                    "source": {"file": relative, "line": 1},
                    "reason": "OpenAPI references have not been resolved by this adapter",
                }],
            })
            analysed_files.add(relative)
        else:
            raise ValueError(f"unsupported discovery adapter: {kind}")
        if sum(1 for o in obligations if o["kind"] == "surface") == surfaces_before:
            unresolved_adapters.append({
                "adapter": index,
                "kind": kind,
                "reason": "adapter declared but produced no surface obligations",
            })
    for entry in source_census:
        if entry["classified"] and entry["file"] not in analysed_files:
            entry["classified"] = False
            add(
                f"boundary:file:{entry['file']}",
                "unresolved",
                entry["file"],
                1,
                reason="source file was not consumed by a discovery adapter",
            )
    ids = [o["id"] for o in obligations]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate obligation IDs; qualify separate application surfaces")
    if not ids:
        raise ValueError("discovery produced no obligations")
    return {
        "version": 1,
        "scope": config["scope"],
        "config_sha256": digest(config),
        "sources": sources,
        "obligations": sorted(obligations, key=lambda o: o["id"]),
        "graphs": graphs,
        "source_census": source_census,
        "excluded_surfaces": {
            "count": len(excluded_surfaces),
            "surfaces": sorted(
                excluded_surfaces,
                key=lambda s: (s["file"], s["line"], s["method"], s["path"]),
            ),
        },
        "unresolved": sorted(
            unresolved_adapters,
            key=lambda u: (-1 if u["adapter"] is None else u["adapter"], u["kind"] or ""),
        ),
    }
