# capcov adapter plugins — bringing your own reader

capcov ships two GENERIC adapters: `treesitter-routes` (any source with a
tree-sitter grammar) and `structured-spec` (any declarative contract, OpenAPI
being one profile). They are two generic mechanisms, not a ban on bespoke ones.

A clean-room rebuild *out of* a legacy or low-code platform — Zoho Deluge,
Salesforce Apex, COBOL, a Retool/Airtable export — starts from a source with **no
tree-sitter grammar and no structured form**. That source needs a bespoke reader.
capcov takes one as a **plugin at the edge**: it lives in a consumer repo or a
contrib package, and an adapter entry names it. The core owns the adapter
contract, the two generic readers and the loader; a bespoke reader is never
special-cased into the core engine.

## Declaring a plugin

Any adapter entry may carry a `plugin` key:

```
plugin = "dotted.module:callable"
```

When `plugin` is given, capcov imports `callable` from `dotted.module` and invokes
it **instead of** dispatching on a built-in `kind`. `kind` (flows path) / the
adapter `name` (core path) becomes a **free label** — used only for provenance and
error text, no longer required to match a built-in.

When an entry's `kind`/`name` is neither a built-in nor accompanied by a `plugin`,
capcov raises a clear error that names this seam rather than dropping the source
silently. "capcov cannot read this source" stays visible.

The dotted string is `module_path:attribute`. A malformed string, a missing
attribute, or a non-callable target raises a specific error.

## The two callable contracts

A plugin produces the **same per-adapter result the built-in of its path
produces**, and capcov merges it **identically** — so a plugin's honest-denominator
carriers (`excluded_surfaces`, `unresolved`) reach the coverage denominator
unchanged, exactly as a built-in adapter's do.

### FLOWS path — `flows.discovery._discover_from_config` / `flows.discovery.discover(config)`

This is the path ladle's `product_flows.py` drives via `discover(config)`.

```python
def reader(adapter: dict, root: pathlib.Path) -> dict:
    ...
```

* `adapter` — the adapter entry from the discovery config (its `plugin` string
  and any bespoke keys the reader defines). `kind`, if present, is a free label.
* `root` — the resolved discovery root (`(base / config["root"]).resolve()`), the
  same directory the built-in readers read their sources under.

Return a dict:

| key                 | required | shape                                                                                   |
| ------------------- | -------- | --------------------------------------------------------------------------------------- |
| `obligations`       | yes      | list of `{"id": str, "kind": str, "source": {"file": str, "line": int}, **extra}`. A discovered surface is `kind == "surface"` (with optional `"method"`, `"handler"`); a limit the reader cannot resolve is `kind == "unresolved"`. |
| `excluded_surfaces` | no       | list of `{"file", "line", "method", "path", "reason", ...}` — candidates the reader saw and deliberately dropped. Flows through verbatim (carries the denominator honestly). |
| `unresolved`        | no       | list of `{"kind", "reason", ...}` — the reader's named limits. The seam stamps this entry's index as `adapter` and the free label as `kind` when the plugin omits them; any value the plugin supplies is preserved. |
| `sources`           | no       | `{relative_path: sha256}` for files the reader consumed; recorded into the inventory's `sources` and marked analysed. |

The returned `obligations` are appended, then the same generic honesty check every
built-in gets applies: a plugin that yields no `surface` obligation is itself named
under `unresolved` ("adapter declared but produced no surface obligations"). Ids
must be unique across the whole run (the existing duplicate-id invariant).

### CORE path — `adapters.load(name, plugin=...)` (for `capcov.toml [[adapters]]` parity)

```python
def reader(source_root: pathlib.Path, target: pathlib.Path, config: dict) -> dict:
    ...
```

* `source_root` — the resolved source root (`target / [capcov].source`).
* `target` — the project root (the directory holding `capcov.toml`).
* `config` — the `[[adapters]]` entry (its `plugin` string and any bespoke keys),
  or `None` for a bare invocation.

Return a **CORE adapter dict** — the same shape a built-in core adapter emits.
Build it with `capcov.adapters.build_core_dict(surface_records, excluded_surfaces,
unresolved)`, which fills the required-but-empty call-graph keys and carries
`excluded_surfaces` (`{"count", "surfaces"}`) and `unresolved` (a list) as
first-class top-level keys. `adapters.merge` folds several adapters (built-in or
plugin) into one and preserves those carriers unchanged. A duplicate surface id or
entity name across adapters is refused loudly, never silently clobbered.

`capcov.toml` wires it by naming the plugin on the entry:

```toml
[[adapters]]
name   = "deluge"                       # free label
plugin = "mycompany.capcov_deluge:read" # the bespoke reader
# ...any keys your reader reads...
```
