"""Source obligations, including explicit limits of each discovery adapter.

Locations and hashes are emitted; source expressions (potential secrets) are not.
Structural candidates do not claim semantic outcomes or runtime reachability.

Adapters:
  python-routes      decorator routes, read with the stdlib `ast`.
  zoho-export        a Zoho Deluge export.
  treesitter-routes  routes in any tree-sitter-supported language. Needs the
      optional `treesitter` extra (tree-sitter + tree-sitter-language-pack),
      lazily imported so core discovery stays stdlib-only. The opinion of WHICH
      calls are routes lives in a config-supplied tree-sitter query, not here,
      so one adapter serves Go, JavaScript, Python and the rest. It sees literal
      string arguments in the nodes the query matches: a path built by
      concatenation or held in a variable is invisible -- the same precision
      floor as python-routes' literal decorator arguments -- but, unlike a
      regex, it is comment- and syntax-aware (a commented-out call is a comment
      node and never matches).
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import re
from pathlib import Path

from .model import digest
from .zoho import derive as derive_zoho


def qualify(value: object, namespace: str) -> object:
    if isinstance(value, str) and value.startswith("zoho:"):
        return "zoho:" + namespace + ":" + value[5:]
    if isinstance(value, list):
        return [qualify(item, namespace) for item in value]
    if isinstance(value, dict):
        return {key: qualify(item, namespace) for key, item in value.items()}
    return value


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


def discover(config_path: Path) -> dict:
    config = json.loads(config_path.read_text())
    root = (config_path.parent / config["root"]).resolve()
    obligations: list[dict] = []
    sources = {}
    graphs = []
    source_census = []
    analysed_files: set[str] = set()

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

    for adapter in config["adapters"]:
        kind = adapter["kind"]
        if kind == "python-routes":
            files = set(adapter.get("files", []))
            for pattern in adapter.get("globs", []):
                discovered = {
                    p.relative_to(root).as_posix()
                    for p in root.glob(pattern)
                    if p.is_file() and "__pycache__" not in p.parts
                }
                if not discovered:
                    raise ValueError(f"empty Python source glob: {pattern}")
                files.update(discovered)
            route_count = 0
            for relative in sorted(files):
                tree = ast.parse(source(relative).read_text())
                analysed_files.add(relative)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                        continue
                    for dec in node.decorator_list:
                        if not (
                            isinstance(dec, ast.Call)
                            and isinstance(dec.func, ast.Attribute)
                            and dec.func.attr in {"get", "post", "put", "patch", "delete"}
                        ):
                            continue
                        if not dec.args or not isinstance(dec.args[0], ast.Constant):
                            add(
                                f"python:{relative}:{node.name}:dynamic-route",
                                "unresolved",
                                relative,
                                node.lineno,
                            )
                            continue
                        route = adapter.get("prefix", "") + str(dec.args[0].value)
                        name = f"http:{dec.func.attr.upper()} {route}"
                        add(name, "surface", relative, dec.lineno, handler=node.name)
                        route_count += 1
                        # Both outcomes of an if, and each exception handler, are
                        # obligations until linked to a meaningful scenario.
                        for child in ast.walk(node):
                            if isinstance(child, ast.If):
                                signature = digest(ast.dump(child.test))[:12]
                                for outcome in ("true", "false"):
                                    add(
                                        f"{name}:branch:{signature}:{child.lineno}:{outcome}",
                                        "branch-candidate",
                                        relative,
                                        child.lineno,
                                        surface=name,
                                    )
                            elif isinstance(child, ast.ExceptHandler):
                                add(
                                    f"{name}:except:{child.lineno}",
                                    "exception-candidate",
                                    relative,
                                    child.lineno,
                                    surface=name,
                                )
            if not route_count:
                raise ValueError("no routes discovered in the configured Python sources")
            for category in (
                "called-function-branches",
                "mounted-route-confirmation",
                "roles-and-configurations",
                "external-effects",
            ):
                add(f"boundary:python:{category}", "unresolved", config_path.name, 1)
        elif kind == "zoho-export":
            relative = adapter["export"]
            export = source(relative)
            graph = derive_zoho(export.read_text(), relative)
            namespace = adapter.get("namespace")
            if namespace:
                graph = qualify(graph, namespace)
                for row in graph["census"]:
                    row["section"] = f"{namespace}: {row['section']}"
            graph["namespace"] = namespace
            analysed_files.add(relative)
            graphs.append({key: value for key, value in graph.items() if key != "nodes"})
            obligations.extend(graph["nodes"])
            for item in graph["unresolved"]:
                add(
                    f"boundary:zoho:source:{digest(item)[:16]}",
                    "unresolved",
                    relative,
                    item["source"]["line"],
                    owner=item["owner"],
                    reason=item["reason"],
                )
            for category in (
                "runtime-confirmation",
                "semantic-outcome-confirmation",
                "fixture-and-environment-coverage",
                "presentation-and-computed-expressions",
            ):
                prefix = f"{namespace}:" if namespace else ""
                add(f"boundary:zoho:{prefix}{category}", "unresolved", relative, 1)
        elif kind == "treesitter-routes":
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
                    method = handler = None
                    if captures.get("method"):
                        method = _route_from_literal(captures["method"][0].text.decode(), [])[0]
                        method = method.upper()
                    if captures.get("handler"):
                        handler = _route_from_literal(captures["handler"][0].text.decode(), [])[0]
                    for node in captures["path"]:
                        candidates.append((node.start_byte, node, method, handler))
                for _start, node, method, handler in sorted(candidates, key=lambda c: c[0]):
                    route, verb = _route_from_literal(node.text.decode(), strip_suffixes)
                    name = id_prefix + route
                    if name in seen:
                        continue
                    seen.add(name)
                    extra: dict[str, object] = {}
                    if method or verb:
                        extra["method"] = method or verb
                    if handler:
                        extra["handler"] = handler
                    add(name, "surface", relative, node.start_point[0] + 1, **extra)
        else:
            raise ValueError(f"unsupported discovery adapter: {kind}")
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
    # Cross-application calls resolve only against an explicitly supplied export,
    # with both source hashes in this inventory. Similar function names are not evidence.
    by_id = {item["id"]: item for item in obligations}
    resolved_dependencies = set()
    for item in list(obligations):
        if item.get("effect") != "external-call":
            continue
        namespace, _, symbol = item["callee"].partition(".")
        target = f"zoho:{namespace}:function:{symbol}"
        if target in by_id:
            graphs[0]["edges"].append(
                {
                    "from": item["id"],
                    "to": target,
                    "relation": "resolves-to",
                    "source": item["source"],
                }
            )
            resolved_dependencies.add(item["id"])

    def resolved(item: dict) -> bool:
        return (
            item.get("owner") in resolved_dependencies
            and item.get("reason") == "qualified call dependency has no source in this export"
        )

    obligations = [item for item in obligations if not resolved(item)]
    for graph in graphs:
        graph["unresolved"] = [item for item in graph["unresolved"] if not resolved(item)]
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
    }
