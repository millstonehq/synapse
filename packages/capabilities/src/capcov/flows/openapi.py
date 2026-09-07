"""Inventory declared HTTP operations, without confusing a contract with runtime.

No network access, reference resolution, schema validation or server selection.
Descriptions/examples/security values are deliberately not copied into reports.
"""

from __future__ import annotations

import json
import re

from .model import digest

METHODS = frozenset({"get", "put", "post", "delete", "options", "head", "patch", "trace"})
PATH_FIELDS = METHODS | {"$ref", "summary", "description", "servers", "parameters"}


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON member in OpenAPI document")
        result[key] = value
    return result


def derive(text: str, relative: str, prefix: str = "") -> list[dict]:
    document = json.loads(text, object_pairs_hook=_object)
    if not isinstance(document, dict) or not re.fullmatch(
        r"3\.[01]\.\d+", str(document.get("openapi", ""))
    ):
        raise ValueError("openapi-json requires an OpenAPI 3.0.x or 3.1.x object")
    if not isinstance(prefix, str) or (prefix and (
        not prefix.startswith("/") or prefix.endswith("/") or any(c in prefix for c in "?#{}")
    )):
        raise ValueError("OpenAPI prefix must be empty or an absolute path without a trailing slash")
    paths = document.get("paths", {})
    if not isinstance(paths, dict):
        raise ValueError("OpenAPI paths must be an object")
    obligations = []
    namespace = digest([relative, prefix])[:16]

    def boundary(category: str, reason: str, pointer: str = "") -> None:
        obligations.append({
            "id": f"boundary:openapi:{namespace}:{category}", "kind": "unresolved",
            "source": {"file": relative, "line": 1, "pointer": pointer}, "reason": reason,
        })

    for category, reason in {
        "runtime-and-omitted-routes": "declared operations do not confirm mounted routes or discover omitted routes",
        "business-outcomes": "schemas do not establish business outcomes, branches or external effects",
        "roles-and-configurations": "authorization and deployment configurations require separate evidence",
        "schemas-and-references": "parameters, responses, schemas and references are not resolved or validated",
        "servers-and-bindings": "server URLs are not selected; consumer must verify the explicit path prefix and target binding",
        "callbacks-webhooks-and-extensions": "callbacks, webhooks and specification extensions are not inventoried as operations",
    }.items():
        boundary(category, reason)

    shapes = set()
    operation_count = 0
    for path, item in paths.items():
        if path.startswith("x-"):
            continue
        if not path.startswith("/") or any(c in path for c in "?#"):
            raise ValueError("OpenAPI path must be an absolute path without a query or fragment")
        shape = re.sub(r"\{[^{}]+\}", "{}", path)
        if shape in shapes:
            raise ValueError("equivalent templated OpenAPI paths")
        shapes.add(shape)
        if not isinstance(item, dict):
            raise ValueError("OpenAPI Path Item must be an object")
        pointer = "/paths/" + path.replace("~", "~0").replace("/", "~1")
        unknown = set(item) - PATH_FIELDS
        if any(not key.startswith("x-") for key in unknown):
            raise ValueError("unsupported OpenAPI Path Item field")
        if "$ref" in item:
            boundary("path-ref:" + digest(path)[:16],
                     "unresolved Path Item reference; inline operations do not account for referenced operations", pointer)
        methods = METHODS & item.keys()
        if not methods:
            boundary("empty-path:" + digest(path)[:16],
                     "path has no inline operations; referenced or filtered operations remain unknown", pointer)
        for method in sorted(methods):
            if not isinstance(item[method], dict):
                raise ValueError("OpenAPI Operation must be an object")
            obligations.append({
                "id": f"http:{method.upper()} {prefix}{path}", "kind": "surface",
                "source": {"file": relative, "line": 1, "pointer": pointer + "/" + method},
                "declaration": "openapi",
            })
            operation_count += 1
    if not operation_count:
        boundary("no-operations", "document declares no inline HTTP operations; this is not an empty complete system")
    return obligations
