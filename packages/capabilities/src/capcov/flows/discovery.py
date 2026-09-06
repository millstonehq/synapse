"""Source obligations, including explicit limits of each discovery adapter.

Locations and hashes are emitted; source expressions (potential secrets) are not.
Structural candidates do not claim semantic outcomes or runtime reachability.
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
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
