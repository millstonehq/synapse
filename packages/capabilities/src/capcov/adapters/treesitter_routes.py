"""treesitter-routes as a CORE adapter: routes in any tree-sitter language.

This is a thin wrapper. The discovery engine lives in `flows.discovery`
(`_discover_from_config`) and stays the shared implementation the flows CLI also
uses; here it is fed a config assembled from a `[[adapters]]` entry in
capcov.toml and its obligation inventory is projected onto the CORE adapter
contract by `adapters.build_core_dict`.

The route opinion -- WHICH calls are routes -- is the config-supplied tree-sitter
query, so one adapter serves Go, JavaScript, Python and the rest. A `methods`
allowlist drops off-verb candidates into `excluded_surfaces` (visible, not
silent); a non-literal path becomes a `dynamic-route` under `unresolved`; the
named limits of static route reading become `boundary` entries under
`unresolved`. Branch/exception candidates the engine also finds are behavioural
obligations for the `outcomes` lane and are not projected here.

Needs the optional `treesitter` extra (tree-sitter + tree-sitter-language-pack),
imported lazily by the engine, so `import capcov.adapters.treesitter_routes`
stays stdlib-only.
"""

from __future__ import annotations

from pathlib import Path

from . import build_core_dict, project_flows_unresolved
from ..flows import discovery as flows_discovery

NAME = "treesitter-routes"

# No single SCIP indexer language: the language is per-config (go, javascript,
# python, ...). The `--resolver scip` path is meaningless for a route reader
# (there is no call graph to re-source), so this stays None.
LANGUAGE = None

# Per-adapter keys copied through to the shared engine's treesitter-routes config.
_ENGINE_KEYS = (
    "methods",
    "globs",
    "files",
    "id_prefix",
    "strip_suffixes",
    "branch_nodes",
    "exception_nodes",
)


def _adapter_config(target: Path, config: dict | None) -> dict:
    """The per-adapter config: the entry T2 passes, or the matching capcov.toml one.

    When `config` is given (the multi-adapter merge path) it is used verbatim.
    Otherwise capcov.toml is read and the first `[[adapters]]` entry named
    `treesitter-routes` is used, falling back to the `[capcov]` block -- enough
    for a direct single-adapter invocation and for tests.
    """
    if config is not None:
        return config
    import tomllib

    path = target / "capcov.toml"
    data = tomllib.loads(path.read_text()) if path.exists() else {}
    for entry in data.get("adapters", []):
        if entry.get("name") == NAME:
            return entry
    return data.get("capcov", {})


def discover(
    source_root: Path, target: Path, name_match: bool = True, *, config: dict | None = None
) -> dict:
    config = _adapter_config(Path(target), config)
    if "language" not in config or "query" not in config:
        raise ValueError(
            "treesitter-routes needs 'language' and 'query' in its [[adapters]] entry"
        )
    entry: dict = {
        "kind": "treesitter-routes",
        "language": config["language"],
        "query": config["query"],
    }
    for key in _ENGINE_KEYS:
        if key in config:
            entry[key] = config[key]
    flows_cfg = {"scope": config.get("scope", NAME), "root": ".", "adapters": [entry]}
    inventory = flows_discovery._discover_from_config(
        flows_cfg, Path(source_root), "capcov.toml"
    )

    id_prefix = config.get("id_prefix", "http:")
    records: list[dict] = []
    for obligation in inventory["obligations"]:
        if obligation["kind"] != "surface":
            continue
        oid = obligation["id"]
        method = obligation.get("method")
        path = oid[len(id_prefix):] if oid.startswith(id_prefix) else oid
        # The surface identity a runtime probe must reproduce to land in `both`:
        # "http:METHOD path" when the verb is known statically, else the raw id
        # (a verb-less route is a legitimate near-miss, R2, not a match).
        core_id = f"http:{method} {path}" if method else oid
        records.append(
            {
                "id": core_id,
                "method": method,
                "path": path,
                "handler": obligation.get("handler"),
                "file": obligation["source"]["file"],
                "line": obligation["source"]["line"],
                "module": obligation["source"]["file"],
            }
        )
    return build_core_dict(
        records,
        inventory["excluded_surfaces"],
        project_flows_unresolved(inventory, NAME),
    )
