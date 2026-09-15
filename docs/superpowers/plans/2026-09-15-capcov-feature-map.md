# capcov Feature Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get from "capcov discovers N route surfaces" to "a per-feature Harvey ball with an honest denominator and provenance", for the Nexa portco product-roadmap template, with a Laravel reader that composes group prefixes and a probe that harvests runtime evidence from existing E2E runs.

**Architecture:** Four independent engine additions land on `feat/capcov-feature-map` in `packages/capabilities`: (1) `capcov features map` projects discovered surfaces onto a FODA feature tree and writes the obligations file `features coverage` already consumes, plus the unassigned/contested remainder; (2) three discovery fixes: OpenAPI templated-path collisions become a recorded boundary instead of a crash, OpenAPI `tags`/`summary` ride onto surfaces, and a `mount` key composes a route prefix; (3) a `capcov_contrib.laravel_routes` plugin reader (via the existing plugin seam) that walks `Route::group` nesting; (5) a `har` probe that projects requests from HAR files onto static surfaces as runtime bindings. Then (6) a `features report` renderer with Harvey glyphs, and (4) per-portco seed files outside this repo. Everything except the tree-sitter parse stays stdlib-only, matching the package's rule that `gate` never takes a skip path.

**Tech Stack:** Python 3.12, stdlib `unittest`, optional `tree-sitter` + `tree-sitter-language-pack` extra (already the pattern for `treesitter-routes`), `uv` for the venv.

**Worktree:** `~/git/synapse-capcov-featuremap` (branch `feat/capcov-feature-map`, from `origin/main` at `3eca23f`). Package dir: `packages/capabilities`. Venv: `packages/capabilities/.venv` (installed with `.[treesitter,probe-python]`).

**Run tests:** from `packages/capabilities`:
```sh
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -t .
```
Baseline: 500 tests, 8 skipped, **1 pre-existing failure** (`tests.test_cli_engine.ObservePytestBackCompatTests.test_default_probe_env_matches_origin_main` compares two fresh random nonces; unrelated to this work, leave it).

**Conventions observed in this package:** module docstrings explain *why*; tests are `unittest.TestCase` classes, one behaviour per test, `tempfile.TemporaryDirectory()` for fixtures; tree-sitter tests guard with `@unittest.skipUnless(_HAVE_TS, "treesitter extra not installed")`; honest-denominator carriers (`excluded_surfaces`, `unresolved`) are never dropped; every limit becomes a named entry, never a silent skip. Commit messages: `feat(capcov): ...` / `fix(capcov): ...` / `test(capcov): ...`, imperative, with a body explaining the reason. End commit bodies with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.

---

## File map

| File | Responsibility |
|---|---|
| `src/capcov/features/mapping.py` (new) | Project surfaces onto features: matching rules, obligation counts, unassigned/contested, assurance label. Pure functions. |
| `src/capcov/features/cli.py` (modify) | Add the `map` and `report` verbs. |
| `src/capcov/features/report.py` (new) | Render a completeness vector as Markdown or CSV rows with Harvey glyphs. |
| `src/capcov/flows/structured_spec.py` (modify) | `_shape_dedupe` records a boundary instead of raising; `_emit_surface` carries `tags`/`summary`. |
| `src/capcov/flows/discovery.py` (modify) | `mount` key on `treesitter-routes` adapter entries composes into the route path. |
| `src/capcov/adapters/__init__.py` (modify) | `build_core_dict` forwards `tags`/`summary` onto surface records. |
| `src/capcov/adapters/structured_spec.py`, `src/capcov/adapters/treesitter_routes.py` (modify) | Bridges forward `tags`/`summary` from obligations to records. |
| `src/capcov_contrib/__init__.py`, `src/capcov_contrib/laravel_routes.py` (new) | Laravel route reader plugin: group-prefix composition, both handler styles, `resource`/`apiResource`, dynamic-path and dynamic-prefix boundaries, duplicate reporting. |
| `src/capcov/probes/har_probe.py` (new), `src/capcov/probes/probe_registry.py` (modify) | `har` probe: HAR entries → runtime bindings against static surface templates. |
| `tests/test_feature_map.py`, `tests/test_feature_report.py`, `tests/test_structured_spec_tags.py`, `tests/test_treesitter_mount.py`, `tests/test_laravel_routes.py`, `tests/test_har_probe.py` (new) | One test module per task. |

Tasks 1, 2, 3 and 5 touch disjoint files and can run in parallel (separate worktrees branched from `feat/capcov-feature-map`, merged back). Task 6 depends on Task 1. Task 4 depends on 1, 2, 3 and lives in `~/git/cpb-synapse`, not here.

---

### Task 1: `capcov features map`

**Files:**
- Create: `src/capcov/features/mapping.py`
- Modify: `src/capcov/features/cli.py`
- Test: `tests/test_feature_map.py`

- [ ] **Step 1: Write the failing tests**

```python
"""`capcov features map`: surfaces -> feature obligations, with the remainder named.

The FODA layer consumes `{feature_id: {covered, total}}`. Nothing produced that map
until now; it was hand-written. `map` derives it from a static inventory
(capabilities.json) and, optionally, a reconciliation (coverage.json), and keeps
the honest remainder visible: surfaces no feature claims, surfaces several
features claim, and discovery's own excluded/unresolved counts. Static-only runs
say so: `covered` is zero everywhere and `assurance` is "static-only".
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from capcov.features.cli import main
from capcov.features.mapping import project, validate_mapping
from capcov.features.model import example


def _surface(sid: str, **extra: object) -> dict:
    method, path = sid.split(" ", 1)
    return {"id": sid, "kind": "http", "method": method[len("http:"):], "path": path,
            "file": "routes.php", "line": 1, **extra}


CAPS = {
    "surfaces": [
        _surface("http:GET /contacts"),
        _surface("http:POST /contacts"),
        _surface("http:GET /contacts/{id}"),
        _surface("http:GET /invoices", tags=["Billing"]),
        _surface("http:GET /health"),
    ],
    "excluded_surfaces": {"count": 2, "surfaces": []},
    "unresolved": [{"adapter": "x", "kind": "boundary", "reason": "r"}],
}

MODEL = {
    "version": 1,
    "root": "crm",
    "features": [
        {"id": "crm", "name": "CRM", "parent": None, "decomposition": None, "group": None},
        {"id": "contacts", "name": "Contacts", "parent": "crm",
         "decomposition": "mandatory", "group": None},
        {"id": "billing", "name": "Billing", "parent": "crm",
         "decomposition": "optional", "group": None},
    ],
    "constraints": [],
}

MAPPING = {
    "version": 1,
    "features": {
        "contacts": {"surfaces": ["http:* /contacts", "http:* /contacts/*"]},
        "billing": {"tags": ["Billing"]},
    },
}

COVERAGE = {
    "rows": [
        {"entity": "http:GET /contacts", "cell": "both",
         "runtime_surfaces": ["http:GET /contacts"]},
        {"entity": "http:GET /invoices", "cell": "both",
         "runtime_surfaces": ["http:GET /invoices"]},
    ]
}


class ProjectTests(unittest.TestCase):
    def test_glob_and_tag_rules_assign_surfaces(self) -> None:
        result = project(MODEL, MAPPING, CAPS)
        self.assertEqual(result["obligations"]["contacts"], {"covered": 0, "total": 3})
        self.assertEqual(result["obligations"]["billing"], {"covered": 0, "total": 1})

    def test_unassigned_surfaces_are_named_not_dropped(self) -> None:
        result = project(MODEL, MAPPING, CAPS)
        self.assertEqual(result["unassigned"], ["http:GET /health"])
        self.assertEqual(result["surfaces_total"], 5)
        self.assertEqual(result["assigned"], 4)

    def test_static_only_run_is_labelled_and_covers_nothing(self) -> None:
        result = project(MODEL, MAPPING, CAPS)
        self.assertEqual(result["assurance"], "static-only")
        self.assertTrue(all(v["covered"] == 0 for v in result["obligations"].values()))

    def test_coverage_rows_mark_exercised_surfaces_covered(self) -> None:
        result = project(MODEL, MAPPING, CAPS, COVERAGE)
        self.assertEqual(result["assurance"], "static+runtime")
        self.assertEqual(result["obligations"]["contacts"], {"covered": 1, "total": 3})
        self.assertEqual(result["obligations"]["billing"], {"covered": 1, "total": 1})

    def test_contested_surfaces_are_counted_for_each_claimant_and_reported(self) -> None:
        mapping = {"version": 1, "features": {
            "contacts": {"surfaces": ["http:GET /*"]},
            "billing": {"surfaces": ["http:GET /invoices"]},
        }}
        result = project(MODEL, mapping, CAPS)
        self.assertEqual(result["contested"], {"http:GET /invoices": ["billing", "contacts"]})
        self.assertEqual(result["obligations"]["billing"]["total"], 1)
        self.assertIn("http:GET /invoices", [s for s in CAPS["surfaces"][3]["id"].split(",")])

    def test_discovery_carriers_are_forwarded(self) -> None:
        result = project(MODEL, MAPPING, CAPS)
        self.assertEqual(result["excluded_surfaces"], 2)
        self.assertEqual(result["unresolved"], 1)

    def test_empty_inventory_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            project(MODEL, MAPPING, {"surfaces": []})

    def test_unknown_feature_in_mapping_is_refused(self) -> None:
        bad = {"version": 1, "features": {"ghost": {"surfaces": ["*"]}}}
        with self.assertRaises(ValueError):
            validate_mapping(bad, MODEL)

    def test_rule_that_claims_nothing_is_refused(self) -> None:
        bad = {"version": 1, "features": {"contacts": {}}}
        with self.assertRaises(ValueError):
            validate_mapping(bad, MODEL)


class MapVerbTests(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    def test_map_writes_obligations_that_coverage_consumes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            (d / "model.json").write_text(json.dumps(MODEL))
            (d / "mapping.json").write_text(json.dumps(MAPPING))
            (d / "caps.json").write_text(json.dumps(CAPS))
            (d / "cov.json").write_text(json.dumps(COVERAGE))
            code, out = self._run([
                "map", str(d / "model.json"), str(d / "mapping.json"), str(d / "caps.json"),
                "--coverage", str(d / "cov.json"),
                "--out", str(d / "obligations.json"), "--report", str(d / "report.json"),
            ])
            self.assertEqual(code, 0, out)
            self.assertIn("5 surfaces", out)
            self.assertIn("1 unassigned", out)
            self.assertIn("static+runtime", out)
            obligations = json.loads((d / "obligations.json").read_text())
            self.assertEqual(obligations, {"contacts": {"covered": 1, "total": 3},
                                           "billing": {"covered": 1, "total": 1}})
            report = json.loads((d / "report.json").read_text())
            self.assertEqual(report["unassigned"], ["http:GET /health"])
            code, out = self._run(["coverage", str(d / "model.json"), str(d / "obligations.json")])
            self.assertEqual(code, 0, out)
            self.assertIn("mandatory 1/3", out)
```

Note on `test_contested_surfaces...`: delete the last `assertIn` line (it is a no-op left from drafting); keep the two assertions above it.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_feature_map -v`
Expected: `ImportError: cannot import name 'project' from 'capcov.features.mapping'` (module missing).

- [ ] **Step 3: Write `src/capcov/features/mapping.py`**

```python
"""Project discovered surfaces onto a FODA feature tree.

`capcov features map` is the bridge the feature layer lacked: the tree records
what a system CAN do as user-recognisable nouns, discovery records what the code
DECLARES as routes, and nothing joined them. This module joins them by rule -- a
feature claims surfaces by id glob (fnmatch over ``"http:METHOD path"``) or by
tag (carried from an OpenAPI operation) -- and emits the ``{id: {covered, total}}``
map ``features coverage`` consumes.

Three refusals keep the projection honest, in the package's usual style:

* A surface no feature claims is NOT silently outside the product. It is listed
  under ``unassigned`` (the global-denominator property: every surface discovery
  can see is assigned or named).
* A surface several features claim counts toward each and is listed under
  ``contested`` so a human resolves the overlap rather than the tool guessing.
* Without a reconciliation, nothing is covered. ``assurance`` says
  ``"static-only"`` and every ``covered`` is zero. Declared is not exercised.
"""

from __future__ import annotations

import fnmatch

from . import model as model_mod


def validate_mapping(mapping: dict, model: dict) -> None:
    """Structural validity of a mapping against its feature model.

    A rule is ``{"surfaces": [glob, ...], "tags": [tag, ...]}``; either list may be
    absent, not both. Feature ids must exist in the model.
    """
    if not isinstance(mapping, dict) or mapping.get("version") != 1:
        raise ValueError("mapping version must be 1")
    features = mapping.get("features")
    if not isinstance(features, dict) or not features:
        raise ValueError("mapping needs a nonempty 'features' map")
    known = {f["id"] for f in model["features"]}
    unknown = sorted(set(features) - known)
    if unknown:
        raise ValueError(f"mapping names unknown features: {unknown}")
    for fid, rule in features.items():
        if not isinstance(rule, dict):
            raise ValueError(f"{fid}: rule must be an object")
        patterns = rule.get("surfaces", [])
        tags = rule.get("tags", [])
        if not isinstance(patterns, list) or not isinstance(tags, list):
            raise ValueError(f"{fid}: 'surfaces' and 'tags' must be lists")
        if not all(isinstance(p, str) and p for p in patterns + tags):
            raise ValueError(f"{fid}: patterns and tags must be nonempty strings")
        if not patterns and not tags:
            raise ValueError(f"{fid}: rule claims nothing (no surfaces, no tags)")


def _matches(surface: dict, rule: dict) -> bool:
    sid = surface["id"]
    if any(fnmatch.fnmatchcase(sid, pattern) for pattern in rule.get("surfaces", [])):
        return True
    wanted = set(rule.get("tags", []))
    return bool(wanted) and bool(wanted & set(surface.get("tags") or []))


def exercised_surfaces(coverage: dict) -> set[str]:
    """Every surface a reconciliation saw reached at runtime, across all rows."""
    seen: set[str] = set()
    for row in coverage.get("rows", []):
        seen.update(row.get("runtime_surfaces", []))
    return seen


def project(
    model: dict,
    mapping: dict,
    capabilities: dict,
    coverage: dict | None = None,
) -> dict:
    """Surfaces -> per-feature obligations plus the named remainder.

    Returns ``{version, assurance, obligations, surfaces_total, assigned,
    unassigned, contested, excluded_surfaces, unresolved}``. ``obligations`` is
    exactly the map ``features.coverage.rollup`` takes.
    """
    model_mod.validate(model)
    validate_mapping(mapping, model)
    surfaces = capabilities.get("surfaces", [])
    if not surfaces:
        raise ValueError(
            "discovery inventory has no surfaces; refusing to map an empty denominator"
        )
    exercised = exercised_surfaces(coverage) if coverage is not None else set()
    rules = mapping["features"]
    obligations = {fid: {"covered": 0, "total": 0} for fid in rules}
    claims: dict[str, list[str]] = {}
    for surface in surfaces:
        sid = surface["id"]
        owners = sorted(fid for fid, rule in rules.items() if _matches(surface, rule))
        claims[sid] = owners
        for fid in owners:
            obligations[fid]["total"] += 1
            if sid in exercised:
                obligations[fid]["covered"] += 1
    unassigned = sorted(sid for sid, owners in claims.items() if not owners)
    contested = {sid: owners for sid, owners in sorted(claims.items()) if len(owners) > 1}
    excluded = capabilities.get("excluded_surfaces") or {}
    return {
        "version": 1,
        "assurance": "static+runtime" if coverage is not None else "static-only",
        "obligations": obligations,
        "surfaces_total": len(surfaces),
        "assigned": len(surfaces) - len(unassigned),
        "unassigned": unassigned,
        "contested": contested,
        "excluded_surfaces": int(excluded.get("count", 0)),
        "unresolved": len(capabilities.get("unresolved") or []),
    }
```

- [ ] **Step 4: Add the `map` verb to `src/capcov/features/cli.py`**

In the module docstring add a line:
```
    capcov features map       model.json mapping.json capabilities.json
                              [--coverage coverage.json] --out obligations.json
                              [--report report.json]
                                                surfaces -> feature obligations
```

Add the import at the top with the others:
```python
from . import mapping as mapping_mod
```

In `main`, after the `co = sub.add_parser("coverage", ...)` block, add:
```python
    mp = sub.add_parser("map", help="project discovered surfaces onto features")
    mp.add_argument("model")
    mp.add_argument("mapping", help="JSON: {version: 1, features: {id: {surfaces: [glob], tags: [tag]}}}")
    mp.add_argument("capabilities", help="capcov discover artifact (capabilities.json)")
    mp.add_argument("--coverage", default=None, help="capcov reconcile artifact; without it nothing is covered")
    mp.add_argument("--out", required=True, help="write the {id: {covered, total}} obligations map here")
    mp.add_argument("--report", default=None, help="write the full projection (unassigned, contested, assurance) here")
```

In the `try:` block, before `model = json.loads(Path(args.model).read_text())` is fine to leave as is; add after the `if args.command == "coverage":` block:
```python
        if args.command == "map":
            mapping = json.loads(Path(args.mapping).read_text())
            capabilities = json.loads(Path(args.capabilities).read_text())
            coverage = None if args.coverage is None else json.loads(Path(args.coverage).read_text())
            result = mapping_mod.project(model, mapping, capabilities, coverage)
            Path(args.out).write_text(json.dumps(result["obligations"], indent=2, sort_keys=True) + "\n")
            if args.report:
                Path(args.report).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
            print(
                "capcov features map: "
                f"{result['surfaces_total']} surfaces, {result['assigned']} assigned to "
                f"{len(result['obligations'])} features, {len(result['unassigned'])} unassigned, "
                f"{len(result['contested'])} contested; assurance {result['assurance']}; "
                f"discovery excluded {result['excluded_surfaces']}, unresolved {result['unresolved']}"
            )
            return 0
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_feature_map -v`
Expected: all tests `ok`. Then the full suite: same count as baseline plus these, the one pre-existing failure only.

- [ ] **Step 6: Document in `src/capcov/features/README.md`**

Append a section:
```markdown
## Deriving the obligations map: `capcov features map`

`features coverage` consumes `{feature_id: {covered, total}}`. `features map`
derives it from discovery instead of a hand-written file:

    capcov features map model.json mapping.json capabilities.json \
        [--coverage coverage.json] --out obligations.json [--report report.json]

`mapping.json` says which surfaces each feature claims, by id glob or by tag:

    {"version": 1, "features": {
       "contacts": {"surfaces": ["http:* /contacts", "http:* /contacts/*"]},
       "billing":  {"tags": ["Billing"]}}}

`total` is the number of discovered surfaces a feature claims. `covered` is how
many of those a reconciliation saw reached at runtime; **without `--coverage`
every `covered` is zero and the report says `assurance: static-only`** -- a
declared route is not an exercised one. The report also lists `unassigned`
surfaces (no feature claims them: assign or name why not) and `contested`
surfaces (several features claim them: resolve the overlap), and forwards
discovery's `excluded_surfaces` and `unresolved` counts so the denominator is
never read narrower than it is.
```

- [ ] **Step 7: Commit**

```bash
git add src/capcov/features/mapping.py src/capcov/features/cli.py src/capcov/features/README.md tests/test_feature_map.py
git commit -m "feat(capcov): features map -- project discovered surfaces onto the feature tree

The FODA layer consumed a hand-written {id: {covered, total}} map; nothing
derived it. 'features map' joins discovery to the tree by id glob or OpenAPI
tag, counts declared surfaces as total and runtime-reached surfaces as covered,
and names the remainder: unassigned surfaces, contested surfaces, and
discovery's excluded/unresolved counts. A run with no reconciliation covers
nothing and says assurance=static-only.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: Discovery fixes — OpenAPI collision as boundary, tags/summary carried, `mount`

**Files:**
- Modify: `src/capcov/flows/structured_spec.py` (`_shape_dedupe`, `_emit_surface`, `_descend`)
- Modify: `src/capcov/adapters/structured_spec.py:75-85`, `src/capcov/adapters/treesitter_routes.py:118-134`, `src/capcov/adapters/__init__.py:187-200`
- Modify: `src/capcov/flows/discovery.py` (route emit, ~line 462)
- Test: `tests/test_structured_spec_tags.py`, `tests/test_treesitter_mount.py`

- [ ] **Step 1: Write the failing tests for the OpenAPI changes**

```python
"""Two OpenAPI reader changes for real-world documents.

Leap Crew's committed openapi.json (692 paths) has four templated-path
collisions ("/{id}" beside "/{optionId}"). The reader raised and produced
nothing -- a hard failure on a spec quirk, against the package's own rule that a
limit becomes a named entry. It now records a boundary and keeps every surface.
Operations also carry `tags` and `summary` onto the surface so `features map`
can claim by tag and a tree can be seeded from the document's own grouping.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from capcov.adapters import load
from capcov.flows.openapi import derive


DOC = {
    "openapi": "3.0.0",
    "paths": {
        "/{id}": {"get": {"tags": ["Options"], "summary": "Get one"}},
        "/{optionId}": {"delete": {"tags": ["Options"]}},
        "/jobs": {"get": {"tags": ["Jobs", "Core"], "summary": "List jobs"}},
    },
}


class CollisionBecomesBoundaryTests(unittest.TestCase):
    def test_equivalent_templated_paths_record_a_boundary_and_keep_surfaces(self) -> None:
        obligations = derive(json.dumps(DOC), "openapi.json")
        surfaces = {o["id"] for o in obligations if o["kind"] == "surface"}
        self.assertEqual(surfaces, {"http:GET /{id}", "http:DELETE /{optionId}", "http:GET /jobs"})
        boundaries = [o for o in obligations if o["kind"] == "unresolved"
                      and "path-shape-collision" in o["id"]]
        self.assertEqual(len(boundaries), 1)
        self.assertIn("/{optionId}", boundaries[0]["reason"])
        self.assertIn("/{id}", boundaries[0]["reason"])


class TagsAndSummaryTests(unittest.TestCase):
    def test_surface_obligations_carry_tags_and_summary(self) -> None:
        by_id = {o["id"]: o for o in derive(json.dumps(DOC), "openapi.json")}
        self.assertEqual(by_id["http:GET /jobs"]["tags"], ["Jobs", "Core"])
        self.assertEqual(by_id["http:GET /jobs"]["summary"], "List jobs")
        self.assertEqual(by_id["http:DELETE /{optionId}"]["tags"], ["Options"])
        self.assertNotIn("summary", by_id["http:DELETE /{optionId}"])

    def test_core_bridge_forwards_tags_and_summary_onto_surfaces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "openapi.json").write_text(json.dumps(DOC))
            module = load("structured-spec")
            core = module.discover(root, root, config={"document": "openapi.json"})
        by_id = {s["id"]: s for s in core["surfaces"]}
        self.assertEqual(by_id["http:GET /jobs"]["tags"], ["Jobs", "Core"])
        self.assertEqual(by_id["http:GET /jobs"]["summary"], "List jobs")
        self.assertEqual(by_id["http:DELETE /{optionId}"].get("tags"), ["Options"])
```

If `capcov.flows.openapi.derive` has a different signature, read `src/capcov/flows/openapi.py` (it is a thin delegate to `structured_spec.derive_document` with `OPENAPI_SPEC`) and call whichever public function takes `(text, relative)`; adjust the test to that name. If the core bridge `discover` signature differs from `(source_root, target, config=...)`, match `src/capcov/adapters/structured_spec.py`'s `discover` exactly.

- [ ] **Step 2: Run to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_structured_spec_tags -v`
Expected: `ValueError: equivalent templated OpenAPI paths` on the first, `KeyError: 'tags'` on the others.

- [ ] **Step 3: Change `_shape_dedupe` to record instead of raise**

In `src/capcov/flows/structured_spec.py` replace `_shape_dedupe`:
```python
def _shape_dedupe(key: str, level: dict, level_index: int, bindings: dict,
                  pointer: str, state: dict) -> None:
    """A second path with the same template shape is recorded, not refused.

    "/{id}" and "/{optionId}" are one shape to a router and two to a reader; the
    document is ambiguous about which handler serves a concrete path. That is a
    limit of reading the document -- named as a boundary carrying both paths --
    not a reason to produce nothing. Both surfaces are still emitted.
    """
    rule = level.get("shape_dedupe")
    if rule is None:
        return
    shape = re.sub(rule["template_pattern"], rule["replacement"], key)
    seen = state["shapes"].setdefault(level_index, {})
    if shape in seen:
        _emit_boundary(
            {
                "category": "path-shape-collision:",
                "digest_role": "path",
                "reason": (
                    f"{rule['message']}: {key!r} has the same template shape as "
                    f"{seen[shape]!r}; the document does not say which serves a concrete path"
                ),
            },
            {**bindings, "path": key},
            pointer,
            state,
        )
        return
    seen[shape] = key
```
and update the call in `_descend`:
```python
        _shape_dedupe(str(raw_key), level, level_index, bound, child_pointer, state)
```
(move the call to after `bound` is built; `bound` is defined a few lines above the `if leaf:` branch — place the `_validate_key`/`_shape_dedupe` calls after `bound = dict(bindings)` block, keeping `_validate_key` first).

- [ ] **Step 4: Carry `tags` and `summary` from the operation record**

Change `_emit_surface` to take the operation value:
```python
def _emit_surface(bindings: dict, pointer: str, state: dict, value: object = None) -> None:
    method = bindings["method"]
    if state["method_transform"] == "upper":
        method = method.upper()
    path = state["prefix"] + bindings["path"]
    obligation = {
        "id": f"http:{method} {path}",
        "kind": "surface",
        "source": {"file": state["relative"], "line": 1, "pointer": pointer},
        "declaration": state["declaration"],
    }
    if isinstance(value, dict):
        # The document's own grouping and one-line intent, carried verbatim so a
        # feature tree can be seeded from it and `features map` can claim by tag.
        tags = value.get("tags")
        if isinstance(tags, list) and all(isinstance(t, str) for t in tags):
            obligation["tags"] = list(tags)
        summary = value.get("summary")
        if isinstance(summary, str) and summary:
            obligation["summary"] = summary
    state["obligations"].append(obligation)
    state["surface_count"] += 1
```
and in `_descend` the leaf call becomes `_emit_surface(bound, child_pointer, state, value)`.

- [ ] **Step 5: Forward through both bridges and the core builder**

`src/capcov/adapters/structured_spec.py` records (around line 75): add after `"module": ...`:
```python
                "tags": obligation.get("tags"),
                "summary": obligation.get("summary"),
```
`src/capcov/adapters/treesitter_routes.py` records (around line 127): add the same two lines.
`src/capcov/adapters/__init__.py` `build_core_dict`, in the `surfaces.append({...})` dict after `"mounted": True,`:
```python
                **({"tags": record["tags"]} if record.get("tags") else {}),
                **({"summary": record["summary"]} if record.get("summary") else {}),
```

- [ ] **Step 6: Run the tests**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_structured_spec_tags -v`
Expected: pass. Then run the full suite; if an existing structured-spec golden test pinned the raise or exact obligation dicts, update that expectation (the `shapes` state is now a dict of shape → first key, and surfaces may carry two extra keys) and say so in the commit body.

- [ ] **Step 7: Commit**

```bash
git add src/capcov/flows/structured_spec.py src/capcov/adapters/structured_spec.py src/capcov/adapters/treesitter_routes.py src/capcov/adapters/__init__.py tests/test_structured_spec_tags.py
git commit -m "fix(capcov): OpenAPI shape collisions become a boundary; tags and summary ride the surface

A real 692-path document with four '/{id}' vs '/{optionId}' collisions produced
a ValueError and no artifact. A limit of reading is a named boundary, not a
crash: both surfaces are emitted and a path-shape-collision boundary carries
both paths. Operations' tags and summary are carried onto surface obligations
and through both bridges into the core dict, so a feature tree can be seeded
from the document's own grouping and features map can claim by tag.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 8: Write the failing test for `mount`**

`tests/test_treesitter_mount.py`:
```python
"""`mount` on a treesitter-routes adapter entry composes a prefix into the path.

An Express router mounted at app.use('/api/v1', router) serves '/api/v1/jobs',
not '/jobs'. The literal in the file is the second; the runtime surface is the
first. Without a mount two routers with the same literals collide, and no
runtime probe can match the id. `mount` is per adapter entry, so each mounted
router gets its own entry and its own prefix.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from capcov.flows.discovery import discover

_HAVE_TS = (
    importlib.util.find_spec("tree_sitter") is not None
    and importlib.util.find_spec("tree_sitter_language_pack") is not None
)

JS_QUERY = (
    "((call_expression function: (member_expression property: (property_identifier) @method) "
    "arguments: (arguments (string) @path)) "
    "(#match? @method \"^(get|post|put|patch|delete)$\"))"
)
SRC = "router.get('/jobs', h);\nrouter.post('/jobs/:id', h);\n"


@unittest.skipUnless(_HAVE_TS, "treesitter extra not installed")
class MountTests(unittest.TestCase):
    def _discover(self, mount: str | None) -> set[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes.js").write_text(SRC)
            entry = {"kind": "treesitter-routes", "language": "javascript",
                     "files": ["routes.js"], "query": JS_QUERY}
            if mount is not None:
                entry["mount"] = mount
            config = root / "discovery.json"
            config.write_text(json.dumps({"scope": "t", "root": ".", "adapters": [entry]}))
            inventory = discover(config)
        return {o["id"] for o in inventory["obligations"] if o["kind"] == "surface"}

    def test_mount_prefixes_every_route(self) -> None:
        self.assertEqual(self._discover("/api/v1"), {"http:/api/v1/jobs", "http:/api/v1/jobs/:id"})

    def test_mount_joins_with_a_single_slash(self) -> None:
        self.assertEqual(self._discover("/api/v1/"), {"http:/api/v1/jobs", "http:/api/v1/jobs/:id"})

    def test_no_mount_is_unchanged(self) -> None:
        self.assertEqual(self._discover(None), {"http:/jobs", "http:/jobs/:id"})
```

If the existing JS tests in `tests/test_treesitter_routes.py` show surface ids carrying the method (e.g. `http:GET /jobs`) for this query shape, match that exact id form in the expectations above.

- [ ] **Step 9: Run to verify it fails**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_treesitter_mount -v`
Expected: the two mount tests fail (ids lack the prefix).

- [ ] **Step 10: Implement `mount` in `src/capcov/flows/discovery.py`**

Where `id_prefix = adapter.get("id_prefix", "http:")` is read (~line 386) add:
```python
            mount = str(adapter.get("mount", "")).rstrip("/")
```
In the route emit loop, right after `route, verb = _route_from_literal(node.text.decode(), strip_suffixes)`, add:
```python
                    if mount:
                        route = mount + ("" if route.startswith("/") else "/") + route
```
Also add `"mount"` to `_ENGINE_KEYS` in `src/capcov/adapters/treesitter_routes.py` (the list of keys forwarded from a `capcov.toml` `[[adapters]]` entry into the flows entry) so the core path honours it too.

- [ ] **Step 11: Run the tests and the full suite; commit**

```bash
git add src/capcov/flows/discovery.py src/capcov/adapters/treesitter_routes.py tests/test_treesitter_mount.py
git commit -m "feat(capcov): mount key composes a router prefix into treesitter-routes surfaces

A router mounted at /api/v1 serves /api/v1/jobs; the file says /jobs. Without
the mount, two routers with the same literals collide on id and no runtime
probe can match. mount is per adapter entry and joins with a single slash.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Laravel route reader plugin

**Files:**
- Create: `src/capcov_contrib/__init__.py` (docstring only: "Bespoke readers brought in through the plugin seam; never special-cased into the core."), `src/capcov_contrib/laravel_routes.py`
- Test: `tests/test_laravel_routes.py`
- Modify: `src/capcov/PLUGINS.md` (append a "Shipped contrib readers" section naming `capcov_contrib.laravel_routes:discover` and its config keys)

The tree-sitter query mechanism cannot compose `Route::group` nesting; a reader can. It uses the CORE-path plugin contract from `PLUGINS.md`: `discover(source_root, target, config) -> core dict`, built with `capcov.adapters.build_core_dict`.

Config (in `capcov.toml`):
```toml
[[adapters]]
name = "laravel-routes"
plugin = "capcov_contrib.laravel_routes:discover"
globs = ["routes/**/*.php", "app/**/Routes/**/*.php"]   # default if omitted
```

- [ ] **Step 1: Write the failing tests**

```python
"""Laravel route reader: group prefixes composed, both handler styles, resources.

FacilityGrid's backend declares 592 distinct routes across 47 Route::group
prefixes. The generic tree-sitter query sees the literal path only, so 'GET /'
under /account and 'GET /' under /project collapse to one surface and the
inventory reads 323. This reader walks the nesting and composes the path a
runtime probe will actually see. It refuses to guess: a non-literal path or
prefix is an unresolved obligation, a duplicate composed route is reported under
excluded_surfaces, never silently dropped.
"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from capcov.adapters import load

_HAVE_TS = (
    importlib.util.find_spec("tree_sitter") is not None
    and importlib.util.find_spec("tree_sitter_language_pack") is not None
)

ROUTES = r"""<?php
use App\Http\Controllers\AccountController;
use Illuminate\Support\Facades\Route;

Route::group(['prefix' => 'api/v1', 'middleware' => ['auth']], function () {
    Route::get('/', [AccountController::class, 'index']);
    Route::group(['prefix' => 'account'], function () {
        Route::get('/', [AccountController::class, 'show']);
        Route::post('settings', ['uses' => 'AccountController@update']);
        Route::delete('tokens/{token_id}', 'AccountController@revoke');
    });
    Route::prefix('billing')->middleware('auth')->group(function () {
        Route::get('invoices', [AccountController::class, 'invoices']);
    });
    Route::resource('photos', PhotoController::class)->only(['index', 'store', 'destroy']);
    Route::apiResource('tags', TagController::class);
    Route::get($dynamic, [AccountController::class, 'dyn']);
    Route::group(['prefix' => $tenant], function () {
        Route::get('inside', [AccountController::class, 'inside']);
    });
    Route::get('/', [AccountController::class, 'index']);
});
\Route::get('health', fn () => 'ok');
"""


@unittest.skipUnless(_HAVE_TS, "treesitter extra not installed")
class LaravelRoutesTests(unittest.TestCase):
    def _core(self) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "routes").mkdir()
            (root / "routes" / "api.php").write_text(ROUTES)
            module = load("laravel-routes", plugin="capcov_contrib.laravel_routes:discover")
            return module.discover(root, root, config={"globs": ["routes/**/*.php"]})

    def test_group_prefixes_compose_into_the_path(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /api/v1", ids)
        self.assertIn("http:GET /api/v1/account", ids)
        self.assertIn("http:POST /api/v1/account/settings", ids)
        self.assertIn("http:DELETE /api/v1/account/tokens/{token_id}", ids)

    def test_fluent_prefix_group_composes_too(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /api/v1/billing/invoices", ids)

    def test_both_handler_styles_are_read(self) -> None:
        by_id = {s["id"]: s for s in self._core()["surfaces"]}
        self.assertEqual(by_id["http:GET /api/v1/account"]["handler_symbol"], "AccountController@show")
        self.assertEqual(by_id["http:POST /api/v1/account/settings"]["handler_symbol"], "AccountController@update")
        self.assertEqual(by_id["http:DELETE /api/v1/account/tokens/{token_id}"]["handler_symbol"], "AccountController@revoke")
        self.assertEqual(by_id["http:GET /health"]["handler_symbol"], "closure")

    def test_resource_expands_with_only_and_api_resource_omits_forms(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /api/v1/photos", ids)
        self.assertIn("http:POST /api/v1/photos", ids)
        self.assertIn("http:DELETE /api/v1/photos/{photo}", ids)
        self.assertNotIn("http:GET /api/v1/photos/create", ids)
        self.assertNotIn("http:GET /api/v1/photos/{photo}", ids)
        for verb, path in [("GET", "/api/v1/tags"), ("POST", "/api/v1/tags"), ("GET", "/api/v1/tags/{tag}"),
                           ("PUT", "/api/v1/tags/{tag}"), ("PATCH", "/api/v1/tags/{tag}"),
                           ("DELETE", "/api/v1/tags/{tag}")]:
            self.assertIn(f"http:{verb} {path}", ids)
        self.assertNotIn("http:GET /api/v1/tags/create", ids)
        self.assertNotIn("http:GET /api/v1/tags/{tag}/edit", ids)

    def test_dynamic_path_and_dynamic_prefix_are_unresolved_not_guessed(self) -> None:
        core = self._core()
        kinds = [(u["kind"], u["reason"]) for u in core["unresolved"]]
        self.assertTrue(any(k == "dynamic-route" for k, _ in kinds), kinds)
        self.assertTrue(any(k == "dynamic-prefix" for k, _ in kinds), kinds)
        ids = {s["id"] for s in core["surfaces"]}
        self.assertFalse(any(i.endswith("/inside") for i in ids), ids)

    def test_duplicate_composed_route_is_reported_not_dropped(self) -> None:
        core = self._core()
        dup = [s for s in core["excluded_surfaces"]["surfaces"] if s["path"] == "/api/v1" and s["method"] == "GET"]
        self.assertEqual(len(dup), 1)
        self.assertIn("duplicate", dup[0]["reason"])
        self.assertEqual(core["excluded_surfaces"]["count"], len(core["excluded_surfaces"]["surfaces"]))

    def test_leading_backslash_facade_is_read(self) -> None:
        ids = {s["id"] for s in self._core()["surfaces"]}
        self.assertIn("http:GET /health", ids)

    def test_no_route_files_is_an_unresolved_entry_not_an_empty_success(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            module = load("laravel-routes", plugin="capcov_contrib.laravel_routes:discover")
            core = module.discover(root, root, config={"globs": ["routes/**/*.php"]})
        self.assertEqual(core["surfaces"], [])
        self.assertTrue(any(u["kind"] == "no-surfaces" for u in core["unresolved"]))
```

- [ ] **Step 2: Run to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_laravel_routes -v`
Expected: `ModuleNotFoundError: No module named 'capcov_contrib'`.

- [ ] **Step 3: Write `src/capcov_contrib/laravel_routes.py`**

```python
"""Laravel route reader, brought in through the plugin seam.

A tree-sitter query sees one call at a time. Laravel's route surface is the
COMPOSITION of nested `Route::group(['prefix' => ...], fn)` and fluent
`Route::prefix(...)->group(fn)` scopes around each `Route::get(...)`, so a query
that captures the literal reads '/' for every index route in the codebase and
the inventory collapses. This reader walks the syntax tree with a prefix stack
and emits the path the router serves.

What it refuses to do, in the package's usual style:

* a non-literal path (`Route::get($x, ...)`) is a `dynamic-route` unresolved entry;
* a non-literal prefix (`['prefix' => $tenant]`) makes every route beneath it a
  `dynamic-prefix` unresolved entry -- the subtree is named, not emitted with a
  guessed path;
* a second declaration of the same METHOD+path is reported under
  `excluded_surfaces` with reason "duplicate ..." -- visible, not a silent dedupe;
* no route file at all is a `no-surfaces` unresolved entry, never an empty green.

Handler styles read: `[Controller::class, 'method']`, `'Controller@method'`,
`['uses' => 'Controller@method']`, closures ("closure"). `resource` /
`apiResource` expand to Laravel's canonical action set, honouring `->only([...])`
and `->except([...])`. `match([...], path, h)` emits one surface per verb;
`any(path, h)` emits the five recognised verbs.

Plugin contract (CORE path, see capcov/PLUGINS.md):
    discover(source_root, target, config) -> core dict
"""

from __future__ import annotations

import re
from pathlib import Path

from capcov.adapters import build_core_dict

NAME = "laravel-routes"
LANGUAGE = "php"
DEFAULT_GLOBS = ["routes/**/*.php", "app/**/Routes/**/*.php"]
VERBS = ("get", "post", "put", "patch", "delete")
ROUTE_FACADES = {"Route", "\\Route", "Illuminate\\Support\\Facades\\Route"}

# Laravel's resource controller actions: name -> (verb, path suffix).
RESOURCE_ACTIONS = [
    ("index", "GET", ""),
    ("create", "GET", "/create"),
    ("store", "POST", ""),
    ("show", "GET", "/{param}"),
    ("edit", "GET", "/{param}/edit"),
    ("update", "PUT", "/{param}"),
    ("update", "PATCH", "/{param}"),
    ("destroy", "DELETE", "/{param}"),
]
API_RESOURCE_OMITS = {"create", "edit"}


def _join(prefix: str, path: str) -> str:
    parts = [p for p in (prefix.strip("/") + "/" + path.strip("/")).split("/") if p]
    return "/" + "/".join(parts)


def _singular(name: str) -> str:
    # Laravel's resource parameter is Str::singular of the last URI segment; the
    # common English cases suffice here, the rest fall through unchanged.
    last = name.strip("/").split("/")[-1]
    if last.endswith("ies"):
        return last[:-3] + "y"
    if last.endswith("ses") or last.endswith("xes"):
        return last[:-2]
    if last.endswith("s") and not last.endswith("ss"):
        return last[:-1]
    return last


class _Reader:
    def __init__(self, relative: str, source: bytes) -> None:
        self.relative = relative
        self.source = source
        self.records: list[dict] = []
        self.excluded: list[dict] = []
        self.unresolved: list[dict] = []
        self.seen: dict[str, tuple[str, int]] = {}

    # -- tree helpers -------------------------------------------------------
    def text(self, node) -> str:
        return self.source[node.start_byte:node.end_byte].decode("utf-8", "replace")

    def line(self, node) -> int:
        return node.start_point[0] + 1

    @staticmethod
    def children(node, *types: str):
        return [c for c in node.named_children if c.type in types]

    def string_literal(self, node) -> str | None:
        """The content of a single- or double-quoted literal, else None."""
        if node.type in ("string", "encapsed_string"):
            inner = [c for c in node.named_children if c.type == "string_content"]
            if node.type == "encapsed_string" and any(
                c.type != "string_content" for c in node.named_children
            ):
                return None  # interpolation: not a literal
            return inner[0] and self.text(inner[0]) if inner else ""
        return None

    def call_parts(self, node):
        """(facade_or_None, method_name, arguments_node) for a scoped call."""
        if node.type != "scoped_call_expression":
            return None
        scope = node.child_by_field_name("scope")
        name = node.child_by_field_name("name")
        args = node.child_by_field_name("arguments")
        if scope is None or name is None or args is None:
            return None
        return self.text(scope).lstrip("\\"), self.text(name), args

    def arguments(self, args_node) -> list:
        return [a.named_children[0] for a in args_node.named_children
                if a.type == "argument" and a.named_children]

    # -- handlers -----------------------------------------------------------
    def handler(self, node) -> str:
        if node is None:
            return "closure"
        if node.type in ("anonymous_function", "anonymous_function_creation_expression",
                         "arrow_function"):
            return "closure"
        literal = self.string_literal(node)
        if literal is not None:
            return literal
        if node.type == "array_creation_expression":
            elements = self.children(node, "array_element_initializer")
            # ['uses' => 'C@m']
            for element in elements:
                kids = element.named_children
                if len(kids) == 2 and self.string_literal(kids[0]) == "uses":
                    value = self.string_literal(kids[1])
                    if value is not None:
                        return value
            # [C::class, 'm']
            if len(elements) == 2:
                first, second = elements[0].named_children[-1], elements[1].named_children[-1]
                method = self.string_literal(second)
                if first.type == "class_constant_access_expression" and method is not None:
                    cls = self.text(first).rsplit("::", 1)[0].lstrip("\\").split("\\")[-1]
                    return f"{cls}@{method}"
        return self.text(node)[:80]

    # -- emission -----------------------------------------------------------
    def emit(self, verb: str, path: str, handler: str, node) -> None:
        sid = f"http:{verb} {path}"
        line = self.line(node)
        if sid in self.seen:
            first_file, first_line = self.seen[sid]
            self.excluded.append({
                "file": self.relative, "line": line, "method": verb, "path": path,
                "handler": handler,
                "reason": f"duplicate declaration of {sid}; first at {first_file}:{first_line}",
            })
            return
        self.seen[sid] = (self.relative, line)
        self.records.append({
            "id": sid, "method": verb, "path": path, "handler": handler,
            "file": self.relative, "line": line, "module": self.relative,
        })

    def unresolved_entry(self, kind: str, reason: str, node) -> None:
        self.unresolved.append({
            "adapter": NAME, "kind": kind, "reason": reason,
            "file": self.relative, "line": self.line(node),
        })

    # -- walking ------------------------------------------------------------
    def walk(self, node, prefix: str, dynamic: bool) -> None:
        handled = self.route_call(node, prefix, dynamic)
        if handled:
            return
        for child in node.children:
            self.walk(child, prefix, dynamic)

    def group_scope(self, node):
        """If `node` is a group call, return (prefix_literal_or_None, is_dynamic, body)."""
        # Route::group([...], function () {...})
        parts = self.call_parts(node)
        if parts and parts[0] in ROUTE_FACADES and parts[1] == "group":
            args = self.arguments(parts[2])
            if len(args) >= 2:
                return self.prefix_from_array(args[0]) + (args[1],)
            if len(args) == 1:
                return None, False, args[0]
        # Route::prefix('x')->middleware(...)->group(function () {...})
        if node.type == "member_call_expression":
            name = node.child_by_field_name("name")
            args_node = node.child_by_field_name("arguments")
            if name is not None and self.text(name) == "group" and args_node is not None:
                body_args = self.arguments(args_node)
                prefix, dynamic = self.prefix_from_chain(node.child_by_field_name("object"))
                if prefix is not None or dynamic:
                    return prefix, dynamic, (body_args[0] if body_args else None)
                if self.chain_root_is_route(node.child_by_field_name("object")):
                    return None, False, (body_args[0] if body_args else None)
        return None

    def chain_root_is_route(self, node) -> bool:
        while node is not None and node.type == "member_call_expression":
            node = node.child_by_field_name("object")
        parts = self.call_parts(node) if node is not None else None
        return bool(parts and parts[0] in ROUTE_FACADES)

    def prefix_from_chain(self, node):
        """Walk a fluent chain collecting prefix(...) calls down to the facade."""
        prefixes: list[str] = []
        dynamic = False
        while node is not None:
            if node.type == "member_call_expression":
                name = node.child_by_field_name("name")
                args_node = node.child_by_field_name("arguments")
                if name is not None and self.text(name) == "prefix" and args_node is not None:
                    args = self.arguments(args_node)
                    literal = self.string_literal(args[0]) if args else None
                    if literal is None:
                        dynamic = True
                    else:
                        prefixes.append(literal)
                node = node.child_by_field_name("object")
                continue
            parts = self.call_parts(node)
            if parts and parts[0] in ROUTE_FACADES:
                if parts[1] == "prefix":
                    args = self.arguments(parts[2])
                    literal = self.string_literal(args[0]) if args else None
                    if literal is None:
                        dynamic = True
                    else:
                        prefixes.append(literal)
                break
            return None, False
        if not prefixes and not dynamic:
            return None, False
        # innermost call is outermost in the chain text; compose in source order
        return "/".join(p.strip("/") for p in reversed(prefixes)), dynamic

    def prefix_from_array(self, node):
        if node.type != "array_creation_expression":
            return None, False
        for element in self.children(node, "array_element_initializer"):
            kids = element.named_children
            if len(kids) == 2 and self.string_literal(kids[0]) == "prefix":
                literal = self.string_literal(kids[1])
                return (literal, False) if literal is not None else (None, True)
        return None, False

    def route_call(self, node, prefix: str, dynamic: bool) -> bool:
        scope = self.group_scope(node)
        if scope is not None:
            group_prefix, group_dynamic, body = scope
            if group_dynamic:
                self.unresolved_entry(
                    "dynamic-prefix",
                    "Route group prefix is not a literal; routes beneath it are not emitted",
                    node,
                )
            new_prefix = _join(prefix, group_prefix) if group_prefix else prefix
            if body is not None:
                self.walk(body, new_prefix, dynamic or group_dynamic)
            return True
        parts = self.call_parts(node)
        if not parts or parts[0] not in ROUTE_FACADES:
            return False
        facade, method, args_node = parts
        args = self.arguments(args_node)
        if method in VERBS or method in ("any", "match"):
            if method == "match":
                if len(args) < 2 or args[0].type != "array_creation_expression":
                    self.unresolved_entry("dynamic-route", "Route::match verbs are not a literal array", node)
                    return True
                verbs = [v.upper() for v in (self.string_literal(e.named_children[-1]) or ""
                         for e in self.children(args[0], "array_element_initializer")) if v]
                path_node, handler_node = args[1], (args[2] if len(args) > 2 else None)
            else:
                verbs = [v.upper() for v in VERBS] if method == "any" else [method.upper()]
                path_node, handler_node = (args[0] if args else None), (args[1] if len(args) > 1 else None)
            literal = self.string_literal(path_node) if path_node is not None else None
            if literal is None:
                self.unresolved_entry("dynamic-route", "route path is not a string literal", node)
                return True
            if dynamic:
                self.unresolved_entry("dynamic-prefix", f"route {literal!r} sits under a non-literal prefix", node)
                return True
            path = _join(prefix, literal)
            handler = self.handler(handler_node)
            for verb in verbs:
                self.emit(verb, path, handler, node)
            return True
        if method in ("resource", "apiResource"):
            literal = self.string_literal(args[0]) if args else None
            if literal is None:
                self.unresolved_entry("dynamic-route", f"Route::{method} name is not a literal", node)
                return True
            if dynamic:
                self.unresolved_entry("dynamic-prefix", f"resource {literal!r} sits under a non-literal prefix", node)
                return True
            controller = self.handler(args[1]) if len(args) > 1 else "closure"
            if "@" not in controller and controller != "closure":
                controller = controller.lstrip("\\").split("\\")[-1].replace("::class", "")
            only, except_ = self.resource_filters(node)
            base = _join(prefix, literal)
            param = _singular(literal)
            for action, verb, suffix in RESOURCE_ACTIONS:
                if method == "apiResource" and action in API_RESOURCE_OMITS:
                    continue
                if only is not None and action not in only:
                    continue
                if except_ is not None and action in except_:
                    continue
                self.emit(verb, base + suffix.replace("{param}", "{" + param + "}"),
                          f"{controller}@{action}", node)
            return True
        return False

    def resource_filters(self, node):
        """->only([...]) / ->except([...]) chained onto a resource call."""
        only = except_ = None
        parent = node.parent
        while parent is not None and parent.type == "member_call_expression":
            name = parent.child_by_field_name("name")
            args_node = parent.child_by_field_name("arguments")
            if name is not None and args_node is not None:
                args = self.arguments(args_node)
                if args and args[0].type == "array_creation_expression":
                    names = {self.string_literal(e.named_children[-1])
                             for e in self.children(args[0], "array_element_initializer")}
                    if self.text(name) == "only":
                        only = names
                    elif self.text(name) == "except":
                        except_ = names
            parent = parent.parent
        return only, except_


def discover(source_root, target, config: dict | None = None) -> dict:
    """The CORE-path plugin entry point (see capcov/PLUGINS.md)."""
    try:
        import tree_sitter as ts
        from tree_sitter_language_pack import get_language
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise SystemExit(
            "laravel-routes needs the treesitter extra: pip install 'synapse-capabilities[treesitter]'"
        ) from exc
    root = Path(source_root)
    globs = list((config or {}).get("globs") or DEFAULT_GLOBS)
    parser = ts.Parser(get_language("php"))
    records: list[dict] = []
    excluded: list[dict] = []
    unresolved: list[dict] = []
    seen: dict[str, tuple[str, int]] = {}
    files = sorted({p for g in globs for p in root.glob(g) if p.is_file()})
    for path in files:
        source = path.read_bytes()
        reader = _Reader(str(path.relative_to(root)), source)
        reader.seen = seen  # duplicates are global across route files
        tree = parser.parse(source)
        reader.walk(tree.root_node, "", False)
        records.extend(reader.records)
        excluded.extend(reader.excluded)
        unresolved.extend(reader.unresolved)
    if not records:
        unresolved.append({
            "adapter": NAME, "kind": "no-surfaces",
            "reason": f"no Laravel route declarations found under {globs}",
        })
    return build_core_dict(
        records,
        {"count": len(excluded), "surfaces": excluded},
        unresolved,
    )
```

Grammar caveats to verify while making the tests pass (the installed `tree-sitter-language-pack` PHP grammar decides): the closure node type may be `anonymous_function` or `anonymous_function_creation_expression`; the leading-backslash facade may parse `scope` as `qualified_name` (handled by text comparison); `'k' => 'v'` inside an array is an `array_element_initializer` with two named children. Print `node.sexp()` on the fixture if a test disagrees, then adjust the node-type names in ONE place (the constants at the top or the `handler` method). Do not weaken the tests.

- [ ] **Step 4: Run the tests until they pass**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_laravel_routes -v`
Expected: all `ok`.

- [ ] **Step 5: Prove it on FacilityGrid**

Create `/tmp/fg-laravel/capcov.toml` with `source = "src"` (symlink `src -> /Users/cpb/git/fg-backend`) and:
```toml
[[adapters]]
name = "laravel-routes"
plugin = "capcov_contrib.laravel_routes:discover"
globs = ["app/**/Routes/**/*.php", "routes/*.php", "facility-grid/**/routes.php"]
```
Run: `PYTHONPATH=src .venv/bin/capcov discover --target /tmp/fg-laravel --out /tmp/fg-laravel/capabilities.json` and report: surfaces count (expect materially more than 323 and in the neighbourhood of the grep-derived 592 declarations minus true duplicates), `excluded_surfaces.count`, `unresolved` kinds. Record the numbers in the commit body. Do not commit anything under /tmp.

- [ ] **Step 6: Document and commit**

Append to `src/capcov/PLUGINS.md`:
```markdown
## Shipped contrib readers

`capcov_contrib` ships bespoke readers that use this seam and are NOT part of the
core. Declare them exactly like a consumer-local plugin:

    [[adapters]]
    name = "laravel-routes"
    plugin = "capcov_contrib.laravel_routes:discover"
    globs = ["routes/**/*.php", "app/**/Routes/**/*.php"]   # default

`laravel_routes` composes nested `Route::group` / `Route::prefix()->group()`
prefixes into each route's path, reads `[C::class, 'm']`, `'C@m'`,
`['uses' => 'C@m']` and closures, expands `resource`/`apiResource` (honouring
`only`/`except`), and names what it cannot read: `dynamic-route`,
`dynamic-prefix`, `no-surfaces` unresolved entries and duplicate declarations
under `excluded_surfaces`. Requires the `treesitter` extra.
```

```bash
git add src/capcov_contrib tests/test_laravel_routes.py src/capcov/PLUGINS.md
git commit -m "feat(capcov-contrib): Laravel route reader composes group prefixes

A tree-sitter query sees the literal path; Laravel's surface is the composition
of nested group prefixes around it. On FacilityGrid the query read 323 surfaces
against 592 distinct declarations because every index route collapsed to '/'.
This reader walks the nesting with a prefix stack (array and fluent forms),
reads both handler styles, expands resource controllers, and names what it
cannot read: dynamic paths and prefixes as unresolved, duplicates as excluded.
Shipped under capcov_contrib through the plugin seam, not in the core.

FacilityGrid result: <surfaces> surfaces, <excluded> excluded, <unresolved> unresolved.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: `har` probe — runtime evidence from existing E2E runs

**Files:**
- Create: `src/capcov/probes/har_probe.py`
- Modify: `src/capcov/probes/probe_registry.py` (REGISTRY), `src/capcov/cli.py` (`--probe` help string only)
- Test: `tests/test_har_probe.py`

Contract: `capcov observe --target . --probe har --out observed.json -- run1.har run2.har`. The probe reads the HAR files named after `--`, matches each request's method and URL path against the static surfaces in `<target>/capcov.capabilities.json` (override with `[capcov] har_surfaces = "path"` in `capcov.toml`), and emits bindings `{surface: sid, entity: sid, operations: [crud], tests: [har basename]}`. Requests that match no surface are grouped and reported as an `unresolved` entry with `gating: False` (a runtime-side limit, reported not gated). Optional `[capcov] har_strip_prefixes = ["/api"]` strips a leading prefix before matching.

- [ ] **Step 1: Write the failing tests**

```python
"""The `har` probe: runtime bindings harvested from an existing browser run.

FacilityGrid and Leap have no Python test suite to hook, but both already run
Playwright suites that can record a HAR. This probe projects those requests
onto the static surfaces so a route that a real session reached lands in
`both` and one nobody reached stays `static_only` -- the split that would have
caught a feature that was merged, deployed and never exercised.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from capcov.probes.har_probe import match_surface, project_har, template_regex


SURFACES = [
    {"id": "http:GET /api/jobs", "method": "GET", "path": "/api/jobs"},
    {"id": "http:GET /api/jobs/{id}", "method": "GET", "path": "/api/jobs/{id}"},
    {"id": "http:POST /api/jobs/:id/close", "method": "POST", "path": "/api/jobs/:id/close"},
    {"id": "http:DELETE /api/jobs/{id}", "method": "DELETE", "path": "/api/jobs/{id}"},
]


def _har(entries: list[tuple[str, str]]) -> dict:
    return {"log": {"entries": [
        {"request": {"method": m, "url": f"https://app.example.com{u}"},
         "response": {"status": 200}} for m, u in entries]}}


class TemplateTests(unittest.TestCase):
    def test_brace_and_colon_params_match_one_segment(self) -> None:
        self.assertTrue(template_regex("/api/jobs/{id}").fullmatch("/api/jobs/42"))
        self.assertTrue(template_regex("/api/jobs/:id/close").fullmatch("/api/jobs/42/close"))
        self.assertFalse(template_regex("/api/jobs/{id}").fullmatch("/api/jobs/42/close"))

    def test_literal_beats_template_when_both_match(self) -> None:
        surfaces = SURFACES + [{"id": "http:GET /api/jobs/new", "method": "GET", "path": "/api/jobs/new"}]
        self.assertEqual(match_surface("GET", "/api/jobs/new", surfaces), "http:GET /api/jobs/new")
        self.assertEqual(match_surface("GET", "/api/jobs/7", surfaces), "http:GET /api/jobs/{id}")

    def test_method_must_match(self) -> None:
        self.assertIsNone(match_surface("PUT", "/api/jobs/7", SURFACES))


class ProjectTests(unittest.TestCase):
    def test_requests_become_bindings_with_crud_and_test_name(self) -> None:
        har = _har([("GET", "/api/jobs"), ("GET", "/api/jobs/7?x=1"), ("DELETE", "/api/jobs/7")])
        result = project_har({"smoke.har": har}, SURFACES, strip_prefixes=[])
        by_surface = {b["surface"]: b for b in result["bindings"]}
        self.assertEqual(by_surface["http:GET /api/jobs"]["operations"], ["read"])
        self.assertEqual(by_surface["http:GET /api/jobs"]["entity"], "http:GET /api/jobs")
        self.assertEqual(by_surface["http:GET /api/jobs"]["tests"], ["smoke.har"])
        self.assertEqual(by_surface["http:DELETE /api/jobs/{id}"]["operations"], ["delete"])
        self.assertEqual(result["unresolved"], [])

    def test_unmatched_requests_are_reported_not_dropped(self) -> None:
        har = _har([("GET", "/api/jobs"), ("GET", "/static/app.js"), ("GET", "/api/ghost")])
        result = project_har({"smoke.har": har}, SURFACES, strip_prefixes=[])
        self.assertEqual(len(result["bindings"]), 1)
        self.assertEqual(len(result["unresolved"]), 1)
        entry = result["unresolved"][0]
        self.assertEqual(entry["kind"], "unmatched-requests")
        self.assertFalse(entry["gating"])
        self.assertEqual(entry["count"], 2)
        self.assertIn("GET /api/ghost", entry["samples"])

    def test_strip_prefixes_before_matching(self) -> None:
        har = _har([("GET", "/v2/api/jobs")])
        result = project_har({"a.har": har}, SURFACES, strip_prefixes=["/v2"])
        self.assertEqual([b["surface"] for b in result["bindings"]], ["http:GET /api/jobs"])

    def test_same_surface_from_two_runs_merges_tests(self) -> None:
        result = project_har(
            {"a.har": _har([("GET", "/api/jobs")]), "b.har": _har([("GET", "/api/jobs")])},
            SURFACES, strip_prefixes=[],
        )
        self.assertEqual(result["bindings"][0]["tests"], ["a.har", "b.har"])


class ObserveTests(unittest.TestCase):
    def test_observe_writes_a_valid_observed_artifact(self) -> None:
        from capcov.probes.har_probe import observe
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src").mkdir()
            (root / "src" / "app.php").write_text("<?php\n")
            (root / "capcov.capabilities.json").write_text(json.dumps({"surfaces": SURFACES}))
            (root / "run.har").write_text(json.dumps(_har([("GET", "/api/jobs")])))
            observed = observe(source_root=root / "src", target=root, out=root / "observed.json",
                               nonce="n1", har_paths=[root / "run.har"])
            written = json.loads((root / "observed.json").read_text())
        self.assertEqual(written["kind"], "observed")
        self.assertEqual(written["bindings"][0]["surface"], "http:GET /api/jobs")
        self.assertEqual(written["exercises"], 1)
        self.assertEqual(observed["bindings"], written["bindings"])
```

- [ ] **Step 2: Run to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_har_probe -v`
Expected: `ModuleNotFoundError: No module named 'capcov.probes.har_probe'`.

- [ ] **Step 3: Write `src/capcov/probes/har_probe.py`**

Read `src/capcov/probes/load_probe.py` first: its `observe()` (below the stub driver) shows the exact `FreshnessGuard`, `observed_carriers` and `artifacts.write` usage this probe must reproduce so the artifact validates. Then write:

```python
"""The `har` probe: runtime bindings harvested from an existing browser run.

Some targets have no Python test suite to hook and no planner flow models yet,
but they already run browser suites -- Playwright can record every request of a
run as a HAR file. This probe reads those HARs and projects each request onto
the static surface it reached:

    request METHOD + URL path  -> surface   (matched against the static
                                            inventory's path templates)
    the same surface           -> entity    (route readers self-bind, so the
                                            entity IS the surface id)
    HTTP verb                  -> operation (GET=read, POST=create, PUT/PATCH=
                                            update, DELETE=delete -- weak but
                                            declared, as the browser probe does)
    HAR file name              -> test      (the exercise that produced it)

Honesty: a request no static surface matches is reported as an `unresolved`
entry (`gating: False`, runtime-side, counted with samples), never dropped.
Static surfaces the run never reached are simply absent, and land in
`static_only` at reconcile -- which is the point.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from .. import artifacts
from .probe_registry import (
    ENV_NONCE,
    ENV_ONLY,
    ENV_OUT,
    ENV_SOURCE_ROOT,
    ENV_TARGET,
    FreshnessGuard,
    observed_carriers,
)

VERB_TO_OP = {"GET": "read", "HEAD": "read", "OPTIONS": "read", "POST": "create",
              "PUT": "update", "PATCH": "update", "DELETE": "delete"}
_PARAM = re.compile(r"\{[^/{}]+\}|:[A-Za-z_][A-Za-z0-9_]*")


def template_regex(path: str) -> re.Pattern[str]:
    """`/jobs/{id}` and `/jobs/:id` both match exactly one non-empty segment."""
    pattern = "".join(
        "[^/]+" if _PARAM.fullmatch(part) else re.escape(part)
        for part in _PARAM.split(path) if part is not None
        for part in ([part] if not _PARAM.fullmatch(part) else [part])
    )
    # Rebuild with the parameters substituted in place (split drops them).
    out: list[str] = []
    last = 0
    for m in _PARAM.finditer(path):
        out.append(re.escape(path[last:m.start()]))
        out.append("[^/]+")
        last = m.end()
    out.append(re.escape(path[last:]))
    return re.compile("".join(out))


def match_surface(method: str, path: str, surfaces: list[dict]) -> str | None:
    """The surface id a request reached: a literal path wins over a template."""
    literal = None
    templated = None
    for surface in surfaces:
        if (surface.get("method") or "").upper() != method.upper():
            continue
        spath = surface.get("path") or ""
        if not spath.startswith("/"):
            spath = "/" + spath
        if spath == path:
            literal = surface["id"]
            break
        if _PARAM.search(spath) and templated is None and template_regex(spath).fullmatch(path):
            templated = surface["id"]
    return literal or templated


def _request_path(url: str, strip_prefixes: list[str]) -> str:
    path = urlsplit(url).path or "/"
    for prefix in strip_prefixes:
        prefix = prefix.rstrip("/")
        if prefix and path.startswith(prefix + "/"):
            path = path[len(prefix):]
            break
    return path if path.startswith("/") else "/" + path


def project_har(hars: dict[str, dict], surfaces: list[dict], strip_prefixes: list[str]) -> dict:
    """`{name: har_document}` -> `{bindings, unresolved, requests}`."""
    rows: dict[str, dict] = {}
    unmatched: list[str] = []
    requests = 0
    for name in sorted(hars):
        for entry in hars[name].get("log", {}).get("entries", []):
            request = entry.get("request") or {}
            method = str(request.get("method", "")).upper()
            path = _request_path(str(request.get("url", "")), strip_prefixes)
            requests += 1
            sid = match_surface(method, path, surfaces)
            if sid is None:
                unmatched.append(f"{method} {path}")
                continue
            row = rows.setdefault(sid, {"operations": set(), "tests": set()})
            row["operations"].add(VERB_TO_OP.get(method, method.lower()))
            row["tests"].add(name)
    bindings = [
        {"surface": sid, "entity": sid, "operations": sorted(r["operations"]),
         "tests": sorted(r["tests"])}
        for sid, r in sorted(rows.items())
    ]
    unresolved = []
    if unmatched:
        distinct = sorted(set(unmatched))
        unresolved.append({
            "adapter": "har", "kind": "unmatched-requests", "gating": False,
            "count": len(distinct),
            "samples": distinct[:25],
            "reason": "requests in the run matched no static surface (assets, third-party, or routes discovery missed)",
        })
    return {"bindings": bindings, "unresolved": unresolved, "requests": requests}


def _surfaces_path(target: Path) -> Path:
    config = target / "capcov.toml"
    if config.exists():
        import tomllib
        block = tomllib.loads(config.read_text()).get("capcov", {})
        if block.get("har_surfaces"):
            return target / block["har_surfaces"]
    return target / "capcov.capabilities.json"


def _strip_prefixes(target: Path) -> list[str]:
    config = target / "capcov.toml"
    if config.exists():
        import tomllib
        return list(tomllib.loads(config.read_text()).get("capcov", {}).get("har_strip_prefixes", []))
    return []


def observe(*, source_root, out, target, har_paths: list, nonce: str | None = None,
            only: str | None = None) -> dict:
    """Project the named HAR files and write the `observed` artifact."""
    source_root = Path(source_root)
    target = Path(target)
    out = Path(out)
    surfaces_file = _surfaces_path(target)
    if not surfaces_file.exists():
        raise SystemExit(
            f"har probe: no static inventory at {surfaces_file}; run `capcov discover` first "
            "or set [capcov] har_surfaces in capcov.toml"
        )
    surfaces = json.loads(surfaces_file.read_text()).get("surfaces", [])
    if not har_paths:
        raise SystemExit("har probe: name at least one .har file after `--`")
    hars = {Path(p).name: json.loads(Path(p).read_text()) for p in har_paths}
    guard = FreshnessGuard(source_root, out, nonce)
    guard.before()
    result = project_har(hars, surfaces, _strip_prefixes(target))
    guard.after()
    tree_hash, files = artifacts.tree_sha256(source_root)
    doc = artifacts.write(
        out, "observed",
        artifacts.derived_from(source_root.name, tree_hash, "capcov har-probe", files),
        {
            "bindings": result["bindings"],
            "exercises": len(hars),
            "requests": result["requests"],
            **observed_carriers(excluded_surfaces=[], unresolved=result["unresolved"]),
        },
    )
    return doc


def main(argv: list[str]) -> int:
    import os
    har_paths = [Path(a) for a in argv]
    observe(
        source_root=os.environ[ENV_SOURCE_ROOT], out=os.environ[ENV_OUT],
        target=os.environ[ENV_TARGET], har_paths=har_paths,
        nonce=os.environ.get(ENV_NONCE), only=os.environ.get(ENV_ONLY),
    )
    return 0
```

Fix `template_regex`: delete the first `pattern = "".join(...)` expression entirely (it is dead code left from drafting); keep the `out`/`finditer` build. Match the exact names and signatures of `FreshnessGuard`, `observed_carriers`, `artifacts.write` and `artifacts.derived_from` as `load_probe.py` and `artifacts.py` define them (read them; the calls above are the intended shape, the real signatures win).

- [ ] **Step 4: Register the probe**

In `src/capcov/probes/probe_registry.py` `REGISTRY` add `"har": "capcov.probes.har_probe",`. In `src/capcov/cli.py` the `--probe` help string, add `| 'har'`. Confirm `cmd_observe` already routes non-pytest probes to `probe.main(list(args.command or []))` (it does, per the in-process branch) so `-- a.har b.har` reaches `main`.

- [ ] **Step 5: Run the tests, then the full suite; commit**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_har_probe -v` → all `ok`.

```bash
git add src/capcov/probes/har_probe.py src/capcov/probes/probe_registry.py src/capcov/cli.py tests/test_har_probe.py
git commit -m "feat(capcov): har probe -- runtime bindings from an existing browser run

PHP and TypeScript targets have no Python suite to hook and no flow models
yet, but they already run Playwright suites that can record a HAR. The probe
projects each request onto the static surface it reached (literal beats
template; method must match), emits surface==entity bindings with verb->CRUD
and the HAR name as the exercise, and reports unmatched requests as a
non-gating unresolved entry with samples. Surfaces no run reached stay
static_only at reconcile -- the split that catches merged-deployed-never-run.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: `capcov features report` — Harvey glyphs as Markdown or CSV

**Files:**
- Create: `src/capcov/features/report.py`
- Modify: `src/capcov/features/cli.py`
- Test: `tests/test_feature_report.py`

Depends on Task 1 (uses `coverage.rollup` rows; no new inputs).

- [ ] **Step 1: Write the failing tests**

```python
"""`features report`: the completeness vector as a table people can paste.

A Harvey ball is a rolled (covered, total) pair drawn as a glyph. The glyph is
computed from the ratio and NEVER from a bare percentage across the tree: a
feature with total 0 renders as unassessed ('?'), not as full.
"""

from __future__ import annotations

import unittest

from capcov.features.coverage import rollup
from capcov.features.model import example
from capcov.features.report import glyph, render


OBL = {"auth": {"covered": 1, "total": 1}, "password": {"covered": 2, "total": 4},
       "mfa": {"covered": 0, "total": 3}}


class GlyphTests(unittest.TestCase):
    def test_glyphs_follow_quarters(self) -> None:
        self.assertEqual(glyph(0, 0), "?")
        self.assertEqual(glyph(0, 4), "○")
        self.assertEqual(glyph(1, 4), "◔")
        self.assertEqual(glyph(2, 4), "◑")
        self.assertEqual(glyph(3, 4), "◕")
        self.assertEqual(glyph(4, 4), "●")
        self.assertEqual(glyph(1, 3), "◔")
        self.assertEqual(glyph(2, 3), "◕")


class RenderTests(unittest.TestCase):
    def test_markdown_has_one_row_per_feature_with_glyph_and_counts(self) -> None:
        text = render(rollup(example(), OBL, selected={"mfa"}), fmt="md")
        self.assertIn("| Authentication |", text)
        self.assertIn("| ◑ | 2/4 |", text)
        self.assertIn("| ○ | 0/3 |", text)
        self.assertIn("unassessed", text)

    def test_csv_rows_are_parseable(self) -> None:
        import csv, io
        text = render(rollup(example(), OBL), fmt="csv")
        rows = list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(rows[0]["feature"], "auth")
        self.assertEqual({"feature", "name", "parent", "kind", "status", "self_covered",
                          "self_total", "covered", "total", "glyph"}, set(rows[0]))

    def test_unknown_format_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            render(rollup(example(), OBL), fmt="xlsx")
```

- [ ] **Step 2: Run to verify they fail**

Run: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_feature_report -v`
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write `src/capcov/features/report.py`**

```python
"""Render a completeness vector as a table with Harvey-ball glyphs.

The glyph is a function of one feature's ROLLED (covered, total) pair, computed
in quarters. A feature with nothing to cover renders as '?' -- unassessed -- not
as full: an empty denominator is a question, never a green.
"""

from __future__ import annotations

import csv
import io

GLYPHS = ("○", "◔", "◑", "◕", "●")
COLUMNS = ("feature", "name", "parent", "kind", "status", "self_covered", "self_total",
           "covered", "total", "glyph")


def glyph(covered: int, total: int) -> str:
    if total <= 0:
        return "?"
    if covered >= total:
        return GLYPHS[4]
    if covered <= 0:
        return GLYPHS[0]
    quarter = int((4 * covered) // total)
    return GLYPHS[max(1, min(3, quarter if quarter > 0 else 1))]


def _rows(vector: dict) -> list[dict]:
    rows = []
    for r in vector["tree_rows"]:
        rows.append({**{k: r.get(k) for k in COLUMNS if k != "glyph"},
                     "glyph": "?" if r["status"] in ("unassessed", "deselected")
                     else glyph(r["covered"], r["total"])})
    return rows


def render(vector: dict, fmt: str = "md") -> str:
    if fmt == "csv":
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=COLUMNS)
        writer.writeheader()
        for row in _rows(vector):
            writer.writerow(row)
        return buffer.getvalue()
    if fmt != "md":
        raise ValueError(f"unknown report format {fmt!r}; use md or csv")
    lines = [
        f"mandatory {vector['mandatory_covered']}/{vector['mandatory_total']} · "
        f"optional {vector['optional_covered']}/{vector['optional_total']} "
        f"({vector['optional_assessed']} assessed, {vector['optional_unassessed']} unassessed)",
        "",
        "| Feature | Kind | Status | Ball | Rolled | Own |",
        "|---|---|---|---|---|---|",
    ]
    depth = {vector["root"]: 0}
    for row in _rows(vector):
        parent = row["parent"]
        depth[row["feature"]] = 0 if parent is None else depth.get(parent, 0) + 1
        indent = "  " * depth[row["feature"]]
        lines.append(
            f"| {indent}{row['name']} | {row['kind']} | {row['status']} | {row['glyph']} | "
            f"{row['covered']}/{row['total']} | {row['self_covered']}/{row['self_total']} |"
        )
    return "\n".join(lines) + "\n"
```

Check `glyph(1, 3)`: `4*1//3 = 1` → "◔"; `glyph(2, 3)`: `8//3 = 2` → "◑" but the test expects "◕". Use rounding to nearest quarter instead: `quarter = round(4 * covered / total)`; clamp to 1..3 for strictly-between values. Then 2/3 → round(2.67)=3 → "◕", 1/3 → round(1.33)=1 → "◔", 1/4 → 1, 2/4 → 2, 3/4 → 3. Implement with `round`, keep the clamp.

- [ ] **Step 4: Add the verb**

In `src/capcov/features/cli.py` add `from . import report as report_mod`, a parser:
```python
    rp = sub.add_parser("report", help="the completeness vector as a Markdown or CSV table with Harvey glyphs")
    rp.add_argument("model")
    rp.add_argument("obligations")
    rp.add_argument("--selected", default=None)
    rp.add_argument("--format", default="md", choices=["md", "csv"])
    rp.add_argument("--out", default=None)
```
and handling next to `coverage`:
```python
        if args.command == "report":
            obligations = json.loads(Path(args.obligations).read_text())
            selected = None if args.selected is None else _ids(args.selected)
            text = report_mod.render(coverage_mod.rollup(model, obligations, selected), fmt=args.format)
            if args.out:
                Path(args.out).write_text(text)
                print(f"capcov features: wrote {args.out}")
            else:
                sys.stdout.write(text)
            return 0
```
Add the usage line to the module docstring.

- [ ] **Step 5: Run tests, full suite, commit**

```bash
git add src/capcov/features/report.py src/capcov/features/cli.py tests/test_feature_report.py
git commit -m "feat(capcov): features report -- Harvey glyphs from the rolled vector, md or csv

The glyph is quarters of one feature's rolled (covered, total); a zero
denominator renders '?' not '●'. Markdown for a page, CSV for a workbook.

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Portco seeds (outside this repo)

Lives in `~/git/cpb-synapse/docs/capability-mapping/portcos/<company>/<product-line>/` with `capcov.toml`, `model.json`, `mapping.json`, and a `README.md` recording the run numbers. Depends on Tasks 1, 2, 3. Performed in-session after the engine tasks merge:

1. **Leap Crew**: `structured-spec` on `apps/api/openapi.json` (after Task 2 the four collisions are boundaries). Seed `model.json` from the 105 tags (tag → feature, grouped under the domains the Aug 18 matrix used: lead/contact/pipeline, estimating, documents, money, selling in the field, job & production, communications, reporting, AI, platform, interoperability). `mapping.json` claims by `tags`. Run `features map` → `features report`.
2. **FacilityGrid**: `laravel-routes` plugin over `app/**/Routes/**/*.php`, `routes/*.php`, `facility-grid/**/routes.php`. Seed features from route-file names and first path segments. Claims by surface globs.
3. **Autura**: one target per product line from the clones under `~/git/autura`: TMS (`omadi-tms` PHP → laravel-routes if Laravel, else treesitter), tow clearinghouse (`aries` Java: treesitter-routes with a Spring `@GetMapping`/`@RequestMapping` query; `unclaimed-vehicle-portal`, `impound-express` TS), marketplace (`marketplace-services` PHP, `marketplace-specs` if it holds OpenAPI), lien (`tow-lien` TS), network (`network-issc-geico-pir-api` C#: no grammar in the pack → record as unresolved in the README, do not fake it).

Each README states: adapter used, surfaces / excluded / unresolved, assurance (static-only until a HAR run exists), and the unassigned list length.

---

## Self-review notes

- Spec coverage: steps 1, 2, 3, 5, 6 of the A-to-B list map to Tasks 1, 2, 3, 5, 6; step 4 is Task 4. The "boundary names by language" item was dropped deliberately (model.reconcile credits the literal `boundary:python:mounted-route-confirmation`; renaming it is coupling for a cosmetic gain).
- Type consistency: `project()` returns `obligations` as `{id: {covered, total}}`, which is exactly `coverage.rollup`'s `feature_obligations` input; `render()` takes `rollup()`'s return value; `build_core_dict(records, excluded_dict, unresolved_list)` matches `adapters/__init__.py:151`; `match_surface` reads `surface["method"]`/`["path"]`/`["id"]`, which `build_core_dict` emits.
- Placeholders: two drafting leftovers are called out inline (a dead `assertIn` in Task 1's contested test; the dead first expression in `template_regex`) with instructions to delete them.
