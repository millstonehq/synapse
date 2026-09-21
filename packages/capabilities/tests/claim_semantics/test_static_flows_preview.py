"""``flows plan --static BUNDLE.json``: what the index says about a planned transition.

Four properties, one per class.

1. **What the index says, it says per surface.**  On the go_app golden with a
   second, storeless route added to the tree-sitter side, the planned
   transitions come back annotated: the jobs route ``bound`` with the store set
   ``static_capability_op`` binds and a closed store set; the health route
   ``dead``, because it is declared, binds nothing, and
   ``static_route_reaches_table_closed`` closes its store set; a surface the
   inventory does not declare ``undeclared`` under
   ``static_route_inventory_closed``; and an obligation of a kind this index
   declares no surface of compared with nothing at all.

2. **A dead surface is flagged, never pruned.**  The plan is the plan: the same
   scenarios, the same ``model_sha256``, the same ``states_explored``, with one
   key added.  The dead transition is still planned and still executable, and
   the flag carries the witness that licensed the word "dead", so the model
   reviewer can check the claim rather than take it.

3. **Doubt is named, and is not a flag.**  With the closure test's residue
   injected, the jobs route is ``blocked`` and ``via`` names the symbol the
   unresolved call site sits on; its store set is the same list, now marked a
   lower bound; and the dead verdict becomes ``unresolved`` -- nothing closed,
   so nothing claimed.  A bundle without the rule packs derives no route
   inventory, and every obligation is ``unresolved`` naming the relation it has
   no rule for, rather than ``undeclared`` against an inventory that does not
   exist.

4. **Default byte-identical.**  ``flows plan`` with no ``--static`` writes the
   bytes it wrote before this flag existed, and ``flows report`` over such a
   plan writes the report it wrote before.  A ``--static`` that is not a bundle
   is a named failure with no plan written.

Every case runs the stdlib kernel alone -- no souffle, no scip: the bundles are
built from the committed go_app golden index the way ``test_static_judge_join``
builds them.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from capcov.claims.ir import canonical_dict, canonical_json
from capcov.claims.static import closure, reflexion, scip_facts
from capcov.flows import static_preview
from capcov.flows.cli import main as flows_main
from capcov.flows.model import plan as plan_model

try:
    from .static_rules import go_app
    from .static_rules.adapter import pack_bundle, read_json
except ImportError:  # unittest discover -s imports this directory as top-level
    from static_rules import go_app
    from static_rules.adapter import pack_bundle, read_json

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PILOT = PACKAGE_ROOT / "experiments" / "claim-semantics" / "static" / "reflexion-pilot"

#: The go_app route, and a second one added to the tree-sitter side of the same
#: golden index: ``handle`` is a real symbol in ``api/jobs.go`` (line 20) that
#: calls nothing at all, so a route mounted on it reaches no store -- which is
#: what makes it the dead surface this file needs and the fixture has no other.
SURFACE = go_app.SURFACE
DEAD_SURFACE = "http:GET /health"
HANDLE_NODE = f"{go_app.MODULE}/api:handle"
HANDLE_LINE = 20
#: A surface of a declared kind that the inventory does not declare, and an
#: obligation of a kind it declares no surface of.
UNDECLARED_SURFACE = go_app.UNDECLARED_SURFACE
NON_SURFACE_OBLIGATION = "read"
UNREACHED_ENTITY = "sessions"

#: The closure test's own residue and the symbol it sits on.
RESIDUE = [{"file": "internal/service/service.go", "line": 12, "callee": "h.dispatch",
            "kind": "unresolved", "reason": "untyped receiver"}]
VIA = ("scip-go gomod github.com/example/jobsvc . "
       "`github.com/example/jobsvc/internal/service`/Service#Fetch().")

STORES = ["audit_logs", "jobs"]
OPERATIONS = [["audit_logs", "create"], ["jobs", "read"]]

TARGET = "browser"


def _ast(residue=()) -> dict:
    ast = go_app.ast_raw()
    ast["entities"].append({"name": UNREACHED_ENTITY, "symbol": "Session", "module": "",
                            "file": "models/models.go", "line": 19})
    ast["surfaces"].append({
        "id": DEAD_SURFACE, "kind": "http", "method": "GET", "path": "/health",
        "handler": HANDLE_NODE, "handler_symbol": "handle",
        "file": "api/jobs.go", "line": go_app.ROUTE_LINE, "mounted": True,
    })
    ast["_node_locations"][HANDLE_NODE] = ["api/jobs.go", HANDLE_LINE]
    ast["scip_residue"] = [dict(entry) for entry in residue]
    return ast


def _bundle_text(*, residue=(), packs: bool = True) -> str:
    """A static bundle as ``claims static --out`` writes one.

    ``packs=False`` leaves ``rules-static-v1`` out, which is the bundle the
    profile writes on its own: it declares ``static_edge`` and has no rule that
    heads it, so nothing downstream of it is derivable.
    """
    from capcov.scip import runner

    ast = _ast(residue)
    raw = go_app.golden_raw()
    exported = scip_facts.export_bundle(
        go_app.normalized(raw), ast_raw=ast, source_root=go_app.GO_APP, language="go",
        index_digest=go_app.json_file_digest(raw), index_digest_kind=runner.INDEX_DIGEST_JSON,
        describes_runs=[])
    assert exported.status == scip_facts.STATUS_COMPLETE, exported.messages
    model = reflexion.model_from_documents(
        dict(read_json(PILOT / "capability-map.json"), closed=True),
        dict(read_json(PILOT / "capability-edges.json"), closed=True))
    extra = (closure.closure_bundle(exported.bundle, ast),)
    if packs:
        extra += (pack_bundle(),)
    bundle = reflexion.attach(
        exported.bundle, model, *extra,
        tree_digest=dict(dict(exported.bundle.metadata)["tree"])["digest"])
    return canonical_json(canonical_dict(bundle)) + "\n"


class _Bundles:
    """The bundles every class below reads, exported once per process."""

    _cache: dict[str, Path] = {}
    _dir: Path | None = None

    @classmethod
    def path(cls, name: str, **kwargs) -> Path:
        if cls._dir is None:
            cls._dir = Path(tempfile.mkdtemp(prefix="capcov-flows-static-bundles-"))
        if name not in cls._cache:
            path = cls._dir / f"{name}.json"
            path.write_text(_bundle_text(**kwargs), encoding="utf-8")
            cls._cache[name] = path
        return cls._cache[name]


def _transition(name: str, obligation: str, *, requires=(), adds=()) -> dict:
    return {
        "id": name, "requires": list(requires), "adds": list(adds),
        "actor": "operator", "outcome": name,
        "evidence": [{"file": "api/jobs.go", "line": go_app.ROUTE_LINE}],
        "obligations": [obligation],
        "bindings": {TARGET: {"commands": [
            {"op": "assert", "id": "outcome", "selector": "body", "text": name}]}},
    }


def _model() -> dict:
    """A flow model over the go_app surfaces: one transition per obligation kind."""
    return {
        "version": 1, "scope": "go-app-flows", "facts": ["fetched"], "initial": [],
        "transitions": [
            _transition("fetch-job", SURFACE, adds=["fetched"]),
            _transition("check-health", DEAD_SURFACE),
            _transition("create-job", UNDECLARED_SURFACE, requires=["fetched"]),
            _transition("read-something", NON_SURFACE_OBLIGATION),
        ],
    }


def _annotation(name: str, **kwargs) -> dict:
    return static_preview.annotate(
        static_preview.load(_Bundles.path(name, **kwargs)), _model())


class WhatTheIndexSaysPerSurfaceTests(unittest.TestCase):
    """The clean bundle: one status per obligation surface, each with its licence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.annotation = _annotation("clean")

    def surface(self, surface: str) -> dict:
        return self.annotation["surfaces"][surface]

    def test_a_bound_surface_carries_the_store_set_the_index_binds(self) -> None:
        entry = self.surface(SURFACE)
        self.assertEqual(entry["status"], static_preview.STATUS_BOUND)
        self.assertEqual(entry["stores"], STORES)
        self.assertEqual(entry["operations"], OPERATIONS)
        self.assertEqual(self.annotation["transitions"]["fetch-job"]["stores"], STORES)

    def test_a_bound_surfaces_store_set_is_closed_and_says_by_what(self) -> None:
        entry = self.surface(SURFACE)
        self.assertTrue(entry["stores_closed"])
        self.assertEqual(entry["stores_closed_witness"],
                         static_preview.STORES_CLOSED_RELATION)
        self.assertEqual(entry["via"], [])

    def test_a_declared_storeless_surface_is_dead_under_its_closure_witness(self) -> None:
        entry = self.surface(DEAD_SURFACE)
        self.assertEqual(entry["status"], static_preview.STATUS_DEAD)
        self.assertEqual(entry["stores"], [])
        self.assertTrue(entry["stores_closed"])
        self.assertIn(static_preview.STORES_CLOSED_RELATION, entry["reason"])

    def test_a_surface_the_inventory_does_not_declare_is_undeclared_under_its_witness(self) -> None:
        entry = self.surface(UNDECLARED_SURFACE)
        self.assertEqual(entry["status"], static_preview.STATUS_UNDECLARED)
        self.assertIn(static_preview.INVENTORY_CLOSED_RELATION, entry["reason"])
        self.assertTrue(self.annotation["route_inventory_closed"])

    def test_an_obligation_of_an_undeclared_kind_is_compared_with_nothing(self) -> None:
        """A route inventory that could not have carried it says nothing about it."""
        self.assertNotIn(NON_SURFACE_OBLIGATION, self.annotation["surfaces"])
        self.assertEqual(self.annotation["not_comparable"], [NON_SURFACE_OBLIGATION])
        transition = self.annotation["transitions"]["read-something"]
        self.assertEqual(transition["surfaces"], {})
        self.assertEqual(transition["not_comparable"], [NON_SURFACE_OBLIGATION])
        self.assertEqual(transition["flags"], [])

    def test_an_authz_sink_is_reported_three_valued_and_is_never_an_outcome(self) -> None:
        """go_app has no authz symbol and a closed index: that is a gap, not a refusal."""
        authorization = self.surface(SURFACE)["authorization"]
        self.assertEqual(authorization["status"], static_preview.AUTHZ_GAP)
        self.assertEqual(authorization["licensed_by"], static_preview.AUTHZ_CLOSED_RELATION)

    def test_the_annotation_names_the_bundle_by_digest_and_the_index_it_read(self) -> None:
        self.assertEqual(self.annotation["kernel"], static_preview.KERNEL)
        self.assertEqual(self.annotation["join"], static_preview.JOIN_KEY)
        self.assertEqual(len(self.annotation["bundle"]["sha256"]), 64)
        self.assertEqual(self.annotation["underived"], [])


class ADeadSurfaceIsFlaggedNeverPrunedTests(unittest.TestCase):
    """The reviewer decides; the planner does not decide by deleting the evidence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.annotation = _annotation("clean")

    def test_the_dead_transition_is_flagged_with_the_closure_evidence(self) -> None:
        flags = self.annotation["transitions"]["check-health"]["flags"]
        self.assertEqual(len(flags), 1, flags)
        self.assertIn(static_preview.STATUS_DEAD, flags[0])
        self.assertIn(DEAD_SURFACE, flags[0])
        self.assertIn(static_preview.STORES_CLOSED_RELATION, flags[0])

    def test_the_flagged_list_is_the_dead_and_undeclared_transitions_and_no_other(self) -> None:
        self.assertEqual(self.annotation["flagged"], ["check-health", "create-job"])

    def test_every_transition_is_still_annotated_including_the_flagged_ones(self) -> None:
        self.assertEqual(sorted(self.annotation["transitions"]),
                         ["check-health", "create-job", "fetch-job", "read-something"])

    def test_the_plan_under_the_flag_is_the_plan_without_it_plus_one_key(self) -> None:
        """Annotation, not planning: the scenarios and the budget do not move."""
        model = _model()
        bare = plan_model(model, TARGET)
        annotated = dict(bare, **{static_preview.KEY: self.annotation})
        self.assertEqual(set(annotated) - set(bare), {static_preview.KEY})
        for key in ("scenarios", "blocked", "unreachable", "model_sha256", "states_explored"):
            with self.subTest(key=key):
                self.assertEqual(annotated[key], bare[key])
        self.assertIn("check-health", [s["id"] for s in bare["scenarios"]],
                      "the dead-surface transition is still planned")


class DoubtIsNamedAndIsNotAFlagTests(unittest.TestCase):
    """Residue, and a bundle with no rule pack: what is not claimed, and why."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.residue = _annotation("residue", residue=RESIDUE)
        cls.unpacked = _annotation("unpacked", packs=False)

    def test_an_unresolved_site_on_the_path_makes_the_surface_blocked_and_names_it(self) -> None:
        entry = self.residue["surfaces"][SURFACE]
        self.assertEqual(entry["status"], static_preview.STATUS_BLOCKED)
        self.assertEqual(entry["via"], [VIA])
        self.assertEqual(entry["via_total"], 1)
        self.assertIn(static_preview.UNRESOLVED_ON_RELATION, entry["reason"])

    def test_a_blocked_surfaces_store_set_is_the_same_list_marked_a_lower_bound(self) -> None:
        entry = self.residue["surfaces"][SURFACE]
        self.assertEqual(entry["stores"], STORES)
        self.assertFalse(entry["stores_closed"])
        self.assertFalse(self.residue["transitions"]["fetch-job"]["stores_closed"])

    def test_without_the_closure_witness_dead_becomes_unresolved_and_is_not_flagged(self) -> None:
        entry = self.residue["surfaces"][DEAD_SURFACE]
        self.assertEqual(entry["status"], static_preview.STATUS_UNRESOLVED)
        self.assertNotIn("check-health", self.residue["flagged"])
        self.assertIn(static_preview.STORES_CLOSED_RELATION, entry["reason"])

    def test_a_blocked_transition_is_not_flagged_because_doubt_is_not_a_verdict(self) -> None:
        self.assertEqual(self.residue["transitions"]["fetch-job"]["flags"], [])

    def test_a_bundle_with_no_route_inventory_resolves_nothing_and_says_which_relation(self) -> None:
        self.assertIn(static_preview.DECLARED_RELATION, self.unpacked["underived"])
        self.assertFalse(self.unpacked["route_inventory_closed"])
        for surface, entry in self.unpacked["surfaces"].items():
            with self.subTest(surface=surface):
                self.assertEqual(entry["status"], static_preview.STATUS_UNRESOLVED)
                self.assertIn(static_preview.DECLARED_RELATION, entry["reason"])

    def test_such_a_bundle_never_calls_a_surface_undeclared_or_flags_a_transition(self) -> None:
        """A completeness witness over a relation with no rule closes a silence."""
        self.assertEqual(self.unpacked["flagged"], [])
        self.assertNotIn(static_preview.STATUS_UNDECLARED,
                         {entry["status"] for entry in self.unpacked["surfaces"].values()})


class TheDefaultPathIsUnchangedTests(unittest.TestCase):
    """With no flag: the bytes upstream wrote, and a named failure when asked wrongly."""

    def setUp(self) -> None:
        self.work = Path(tempfile.mkdtemp(prefix="capcov-flows-static-"))
        self.addCleanup(_rmtree, self.work)
        self.model_path = self.work / "model.json"
        self.model_path.write_text(json.dumps(_model()), encoding="utf-8")

    def run_plan(self, *extra: str) -> tuple[int, Path]:
        out = self.work / f"plan{len(extra)}.json"
        code = flows_main(["plan", str(self.model_path), "--target", TARGET,
                           "--out", str(out), *extra])
        return code, out

    def test_plan_without_the_flag_writes_the_bytes_it_always_wrote(self) -> None:
        code, out = self.run_plan()
        self.assertEqual(code, 0)
        expected = json.dumps(plan_model(_model(), TARGET), indent=2, sort_keys=True) + "\n"
        self.assertEqual(out.read_text(encoding="utf-8"), expected)
        self.assertNotIn(static_preview.KEY, json.loads(out.read_text(encoding="utf-8")))

    def test_plan_with_the_flag_adds_the_annotation_and_moves_nothing_else(self) -> None:
        bare_code, bare = self.run_plan()
        code, out = self.run_plan("--static", str(_Bundles.path("clean")))
        self.assertEqual((bare_code, code), (0, 0))
        annotated = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(set(annotated) - set(json.loads(bare.read_text(encoding="utf-8"))),
                         {static_preview.KEY})
        self.assertEqual(annotated[static_preview.KEY]["surfaces"][DEAD_SURFACE]["status"],
                         static_preview.STATUS_DEAD)
        del annotated[static_preview.KEY]
        self.assertEqual(json.dumps(annotated, indent=2, sort_keys=True) + "\n",
                         bare.read_text(encoding="utf-8"))

    def test_a_static_argument_that_is_not_a_bundle_is_named_and_writes_no_plan(self) -> None:
        bad = self.work / "not-a-bundle.json"
        bad.write_text("{}", encoding="utf-8")
        out = self.work / "refused.json"
        code = flows_main(["plan", str(self.model_path), "--target", TARGET,
                           "--out", str(out), "--static", str(bad)])
        self.assertEqual(code, 1)
        self.assertFalse(out.exists())

    def test_report_over_an_unannotated_plan_is_the_report_it_always_was(self) -> None:
        _, bare = self.run_plan()
        _, annotated = self.run_plan("--static", str(_Bundles.path("clean")))
        coverage = _coverage()
        (self.work / "coverage.json").write_text(json.dumps(coverage), encoding="utf-8")
        bare_report, annotated_report = self.work / "bare.md", self.work / "annotated.md"
        for source, target in ((bare, bare_report), (annotated, annotated_report)):
            self.assertEqual(flows_main(["report", str(self.work / "coverage.json"), str(source),
                                         "--out", str(target)]), 0)
        bare_text = bare_report.read_text(encoding="utf-8")
        self.assertNotIn("Static preview", bare_text)
        self.assertTrue(annotated_report.read_text(encoding="utf-8").startswith(
            bare_text.split("## Blocked flows")[0]),
            "the static preview is added to the report, never woven through it")

    def test_report_over_an_annotated_plan_previews_the_surfaces_in_a_table(self) -> None:
        _, annotated = self.run_plan("--static", str(_Bundles.path("clean")))
        (self.work / "coverage.json").write_text(json.dumps(_coverage()), encoding="utf-8")
        out = self.work / "report.md"
        self.assertEqual(flows_main(["report", str(self.work / "coverage.json"), str(annotated),
                                     "--out", str(out)]), 0)
        text = out.read_text(encoding="utf-8")
        self.assertIn("## Static preview", text)
        self.assertIn(f"| check-health | {DEAD_SURFACE} | {static_preview.STATUS_DEAD} |", text)
        self.assertIn(f"| fetch-job | {SURFACE} | {static_preview.STATUS_BOUND} | "
                      f"{', '.join(STORES)} | closed |", text)
        self.assertIn("Flagged for review: check-health, create-job.", text)
        self.assertIn(f"Not comparable with this index: {NON_SURFACE_OBLIGATION}.", text)


def _coverage() -> dict:
    """The smallest coverage document ``flows report`` reads."""
    return {"scope": "go-app-flows", "target": TARGET, "assurance": "none", "complete": False,
            "summary": {"covered": 0}, "blocked": [], "rows": []}


def _rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
