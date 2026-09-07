"""Conservative recognition of explicit FastAPI-style route registrations.

Only literal paths/methods and unshadowed module-defined handlers are resolved.
No imports or source expressions are executed or emitted.
"""

from __future__ import annotations

import ast
from collections import Counter


def explicit_routes(tree: ast.Module):
    definitions = {
        node.name: node for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    }
    bindings = Counter()
    wildcard_import = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            bindings[node.name] += 1
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store | ast.Del):
            bindings[node.id] += 1
        elif isinstance(node, ast.arg):
            bindings[node.arg] += 1
        elif isinstance(node, ast.ExceptHandler | ast.MatchAs | ast.MatchStar) and node.name:
            bindings[node.name] += 1
        elif isinstance(node, ast.MatchMapping) and node.rest:
            bindings[node.rest] += 1
        elif isinstance(node, ast.alias):
            wildcard_import |= node.name == "*"
            bindings[node.asname or node.name.split(".")[0]] += 1
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and call.func.attr == "add_api_route"):
            continue
        keywords = {item.arg: item.value for item in call.keywords}
        path = call.args[0] if call.args else keywords.get("path")
        endpoint = call.args[1] if len(call.args) > 1 else keywords.get("endpoint")
        methods = keywords.get("methods", ast.List(elts=[ast.Constant(value="GET")]))
        handler = definitions.get(endpoint.id) if isinstance(endpoint, ast.Name) else None
        valid = (
            len(call.args) <= 2 and None not in keywords and len(keywords) == len(call.keywords)
            and not (call.args and "path" in keywords)
            and not (len(call.args) > 1 and "endpoint" in keywords)
            and isinstance(path, ast.Constant) and isinstance(path.value, str)
            and path.value.startswith("/")
            and isinstance(methods, ast.List | ast.Tuple | ast.Set) and bool(methods.elts)
            and all(isinstance(m, ast.Constant) and isinstance(m.value, str)
                    and m.value.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"}
                    for m in methods.elts)
            and handler is not None and bindings[handler.name] == 1 and not wildcard_import
        )
        if valid:
            yield call, path.value, sorted({m.value.upper() for m in methods.elts}), handler
        else:
            yield call, None, [], None
