"""``gate --judge claims --static BUNDLE.json``: what a static account adds, and what binds it.

Four properties, one per class.

1. **What binds a bundle to a run is the witness, and only the witness.**  The
   static producer emits ``index_describes_run(index, run)`` for the runs it was
   told its index describes.  A bundle that carries it for the receipt's run is
   ``bound`` and read; the same bundle exported for another run is ``stale``,
   says so in its own words on stderr and in judge.json, and not one of its rows
   is reported beside this run's verdict; a bundle that carries no such row at
   all is ``unbound``, which is a different sentence and a different message.

2. **What is read is the bundle's own derived rows.**  The routes
   ``static_capability_op`` binds, the reflexion cell per capability, the dead
   and blocked entities -- re-derived here by the stdlib kernel, which the
   section names, because one kernel is not a differential.  With the closure
   test's residue injected, ``dead`` empties and ``blocked`` names the symbol the
   unresolved call site sits on, exactly as the pack derives it.  A bundle
   without ``rules-static-v1`` merged derives none of them and says so in
   ``underived`` rather than reporting empty lists.

3. **``static_only`` is a negation, and is licensed like one.**  A surface the
   index binds that the run never requested is only a fact when the run's request
   set is closed by the replay producer's own witness.  Closed and unrequested ->
   reported; closed and requested -> not; requests present but not closed ->
   ``runtime: unclosed`` and ``static_only: null``; no request at all ->
   ``runtime: absent`` and ``null`` again.

4. **Asking for it wrongly is exit 2, and not asking changes nothing.**  A
   ``--static`` that is missing, is not JSON or is not a claim bundle is a named
   exit 2 before any judging, with no judge.json written; ``--static`` without
   ``--judge claims`` is the refusal every other judge flag gets; and without the
   flag judge.json has no ``static`` key at all.

The CLI cases run the stdlib kernel alone -- no souffle, no scip: the bundles are
built from the committed go_app golden index the way
``test_static_reflexion`` builds them.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from capcov.claims.ir import canonical_dict, canonical_json
from capcov.claims.static import closure, join as static_join, reflexion, scip_facts

try:
    from .static_rules import go_app
    from .static_rules.adapter import pack_bundle, read_json
except ImportError:  # unittest discover -s imports this directory as top-level
    from static_rules import go_app
    from static_rules.adapter import pack_bundle, read_json

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SRC = PACKAGE_ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
RECEIPT = FIXTURES / "replay_receipt_min"
#: A second committed receipt, whose ``replay_request`` rows spell their route
#: with no method at all -- the shape disagreement this repository already has.
QUALIFIED_RECEIPT = FIXTURES / "replay_receipt_target_go_qualified"
QUALIFIED_RUN = "eca6e7930af3"
COVERAGE = FIXTURES / "upstream_golden" / "python_app" / "coverage.json"
#: Explains every unexplained row in COVERAGE, so the gate's exit code is the
#: claims judge's verdict alone -- `--judge claims` adds a verdict, never replaces one.
EXEMPTIONS = FIXTURES / "python_app_exemptions.toml"
PILOT = PACKAGE_ROOT / "experiments" / "claim-semantics" / "static" / "reflexion-pilot"

#: The run the committed receipt fixture is for, and one it is not.
RUN = "run-fixture-1"
OTHER_RUN = "run-elsewhere"
#: The routes that receipt requested; the go_app surface is in none of them.
OBSERVED_ROUTES = frozenset({"POST /api/issues", "POST /api/issues/{id}/close",
                             "DELETE /api/issues/{id}"})
SURFACE = go_app.SURFACE
ROUTE_OF_SURFACE = SURFACE[len("http:"):]
UNREACHED_ENTITY = "sessions"
#: The closure test's own residue and the symbol it sits on.
RESIDUE = [{"file": "internal/service/service.go", "line": 12, "callee": "h.dispatch",
            "kind": "unresolved", "reason": "untyped receiver"}]
VIA = ("scip-go gomod github.com/example/jobsvc . "
       "`github.com/example/jobsvc/internal/service`/Service#Fetch().")

BINDS = [[SURFACE, "audit_logs", "create"], [SURFACE, "jobs", "read"]]


def _ast(residue=()) -> dict:
    ast = go_app.ast_raw()
    ast["entities"].append({"name": UNREACHED_ENTITY, "symbol": "Session", "module": "",
                            "file": "models/models.go", "line": 19})
    ast["scip_residue"] = [dict(entry) for entry in residue]
    return ast


def _model(edges_closed: bool = True) -> reflexion.CapabilityModel:
    """The pilot's reviewer model; ``edges_closed=False`` is a reviewer who did
    not say their edge model is complete."""
    return reflexion.model_from_documents(
        dict(read_json(PILOT / "capability-map.json"), closed=True),
        dict(read_json(PILOT / "capability-edges.json"), closed=edges_closed))


def _bundle_text(*, describes: str | None = RUN, residue=(), base_pack: bool = True,
                 edges_closed: bool = True) -> str:
    """A static bundle as ``claims static --out`` writes one, for a chosen run.

    ``describes`` is the run the static producer vouches this index describes
    (``scip_facts.export_bundle``'s ``describes_runs``); ``None`` exports a
    bundle that vouches for no run at all.  ``base_pack=False`` leaves
    ``rules-static-v1`` out, which is the bundle the profile writes on its own;
    ``edges_closed=False`` leaves ``capability_edge_closed`` unemitted, which is
    the reviewer declining to say their edge model is complete.
    """
    from capcov.scip import runner

    ast = _ast(residue)
    raw = go_app.golden_raw()
    exported = scip_facts.export_bundle(
        go_app.normalized(raw), ast_raw=ast, source_root=go_app.GO_APP, language="go",
        index_digest=go_app.json_file_digest(raw), index_digest_kind=runner.INDEX_DIGEST_JSON,
        describes_runs=[describes] if describes else [])
    assert exported.status == scip_facts.STATUS_COMPLETE, exported.messages
    extra = (closure.closure_bundle(exported.bundle, ast),)
    if base_pack:
        extra += (pack_bundle(),)
    bundle = reflexion.attach(
        exported.bundle, _model(edges_closed), *extra,
        tree_digest=dict(dict(exported.bundle.metadata)["tree"])["digest"])
    return canonical_json(canonical_dict(bundle)) + "\n"


class _Bundles:
    """The bundles every class below reads, exported once per process."""

    _cache: dict[tuple, Path] = {}
    _dir: Path | None = None

    @classmethod
    def path(cls, name: str, **kwargs) -> Path:
        if cls._dir is None:
            cls._dir = Path(tempfile.mkdtemp(prefix="capcov-static-join-bundles-"))
        key = (name,)
        if key not in cls._cache:
            path = cls._dir / f"{name}.json"
            path.write_text(_bundle_text(**kwargs), encoding="utf-8")
            cls._cache[key] = path
        return cls._cache[key]


def _loaded(name: str, **kwargs) -> static_join.StaticBundle:
    return static_join.load(_Bundles.path(name, **kwargs))


def _section(name: str, *, run: str = RUN, routes=OBSERVED_ROUTES,
             routes_closed: bool = True, **kwargs) -> dict:
    return static_join.section(_loaded(name, **kwargs), run=run, routes=routes,
                               routes_closed=routes_closed)


class _CliTestCase(unittest.TestCase):
    """A real ``capcov gate --judge claims`` run, stdlib kernel, no optional tool."""

    def setUp(self) -> None:
        self.out = Path(tempfile.mkdtemp(prefix="capcov-static-join-"))
        self.addCleanup(_rmtree, self.out)

    def gate(self, *extra: str, receipt: Path = RECEIPT):
        proc = subprocess.run(
            [sys.executable, "-m", "capcov", "gate", str(COVERAGE), "--judge", "claims",
             "--exemptions", str(EXEMPTIONS), "--receipt", str(receipt),
             "--judge-out", str(self.out / "judge"), *extra],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(SRC)})
        document_path = self.out / "judge" / "judge.json"
        document = (json.loads(document_path.read_text(encoding="utf-8"))
                    if document_path.is_file() else None)
        return proc, document


def _rmtree(path: Path) -> None:
    import shutil

    shutil.rmtree(path, ignore_errors=True)


class TheWitnessIsWhatBindsTests(_CliTestCase):
    def test_a_bundle_that_describes_the_run_is_bound_and_read(self) -> None:
        proc, document = self.gate("--static", str(_Bundles.path("bound")))
        self.assertIsNotNone(document, proc.stdout + proc.stderr)
        section = document["static"]
        self.assertEqual(section["join"]["status"], static_join.JOIN_BOUND)
        self.assertEqual(section["join"]["run"], RUN)
        self.assertEqual(section["join"]["describes_runs"], [RUN])
        self.assertEqual(sorted(section["routes"]), [SURFACE])
        self.assertIn(static_join.DESCRIBES_RELATION, section["join"]["message"])

    def test_a_bundle_exported_for_another_run_is_stale_and_reports_no_row(self) -> None:
        """The whole point: an index for another run is not this run's evidence."""
        proc, document = self.gate("--static", str(_Bundles.path("other", describes=OTHER_RUN)))
        section = document["static"]
        self.assertEqual(section["join"]["status"], static_join.JOIN_STALE)
        self.assertEqual(section["join"]["describes_runs"], [OTHER_RUN])
        for key in ("routes", "capabilities", "dead", "blocked", "unresolved",
                    "static_only", "underived"):
            with self.subTest(key=key):
                self.assertIsNone(section[key], "a stale bundle reports nothing at all")
        self.assertIn(OTHER_RUN, section["join"]["message"])
        self.assertIn(RUN, section["join"]["message"])

    def test_the_stale_join_is_said_on_stderr_and_not_only_in_the_document(self) -> None:
        proc, _ = self.gate("--static", str(_Bundles.path("other", describes=OTHER_RUN)))
        self.assertIn("static bundle not joined", proc.stderr)
        self.assertIn(OTHER_RUN, proc.stderr)

    def test_a_bundle_that_vouches_for_no_run_is_unbound_not_stale(self) -> None:
        section = _section("unvouched", describes=None)
        self.assertEqual(section["join"]["status"], static_join.JOIN_UNBOUND)
        self.assertEqual(section["join"]["describes_runs"], [])
        self.assertIsNone(section["routes"])
        self.assertIn("no index_describes_run row", section["join"]["message"])

    def test_the_section_names_the_bundle_by_digest_and_carries_no_path(self) -> None:
        """judge artifacts are publishable: the bundle is bytes, not a place."""
        bundle = _Bundles.path("bound")
        proc, document = self.gate("--static", str(bundle))
        text = (self.out / "judge" / "judge.json").read_text(encoding="utf-8")
        self.assertNotIn(str(bundle), text, proc.stdout)
        self.assertNotIn(str(PACKAGE_ROOT), text)
        self.assertEqual(document["static"]["bundle"]["sha256"],
                         hashlib.sha256(bundle.read_bytes()).hexdigest())

    def test_the_join_never_moves_the_verdict_or_the_exit_code(self) -> None:
        """A static account is not an outcome: the receipt's verdict is unchanged."""
        plain_proc, plain = self.gate()
        joined_proc, joined = self.gate("--static", str(_Bundles.path("bound")))
        self.assertEqual(plain["verdict"], joined["verdict"])
        self.assertEqual(plain["exit_code"], joined["exit_code"])
        self.assertEqual(plain_proc.returncode, joined_proc.returncode)
        self.assertNotIn("static", plain, "no flag, no section")


class WhatTheBoundBundleSaysTests(unittest.TestCase):
    def test_the_routes_are_the_bundles_own_capability_ops(self) -> None:
        section = _section("bound")
        self.assertEqual(section["routes"], {SURFACE: [["audit_logs", "create"],
                                                       ["jobs", "read"]]})
        self.assertEqual(section["kernel"], static_join.KERNEL)

    def test_each_capability_carries_its_reflexion_cell(self) -> None:
        cells = _section("bound")["capabilities"]
        self.assertEqual(cells["jobs_api"],
                         {static_join.CONVERGENCE_RELATION: ["jobs_service"],
                          static_join.DIVERGENCE_RELATION: [],
                          static_join.ABSENCE_RELATION: ["metrics"],
                          static_join.ABSENCE_UNRESOLVED_RELATION: []})
        self.assertEqual(cells["bootstrap"][static_join.DIVERGENCE_RELATION], ["jobs_api"])
        self.assertEqual(cells["bootstrap"][static_join.CONVERGENCE_RELATION], [])

    def test_a_closed_index_reports_the_unreached_entity_as_dead(self) -> None:
        section = _section("bound")
        self.assertEqual(section["dead"], [[SURFACE, UNREACHED_ENTITY]])
        self.assertEqual(section["blocked"], [])
        self.assertEqual(section["underived"], [])

    def test_one_unresolved_call_site_turns_dead_into_blocked_via_its_symbol(self) -> None:
        """The pack's own answer, carried through the join unchanged.

        One unresolved call site withholds ``call_graph_closed``, so the two
        negations it licenses are withheld with it: ``dead`` is ``null`` and
        named in ``withheld``, not an empty list, because "nothing is dead" and
        "the call graph is not closed, so we cannot tell" are different
        sentences.  ``blocked`` is positive and says which symbol the doubt
        goes through.
        """
        section = _section("residue", residue=RESIDUE)
        self.assertIsNone(section["dead"])
        self.assertEqual(section["withheld"][static_join.DEAD_RELATION],
                         [static_join.CALL_GRAPH_CLOSED_RELATION])
        self.assertEqual(
            section["closure_witnesses"][static_join.CALL_GRAPH_CLOSED_RELATION], [])
        self.assertEqual(section["blocked"], [[SURFACE, UNREACHED_ENTITY, VIA]])
        self.assertIsNone(section["capabilities"]["jobs_api"][static_join.ABSENCE_RELATION])
        self.assertEqual(section["withheld"][static_join.ABSENCE_RELATION],
                         [static_join.CALL_GRAPH_CLOSED_RELATION])
        self.assertEqual(
            section["capabilities"]["jobs_api"][static_join.ABSENCE_UNRESOLVED_RELATION],
            ["metrics"])

    def test_a_bundle_without_the_base_pack_names_what_it_cannot_derive(self) -> None:
        """An empty ``routes`` from a bundle with no rule for it is not "it binds nothing".

        ``rules-static-v1`` is what heads ``static_capability_op`` *and*
        ``static_edge``; the profile's own bundle declares both and derives
        neither.  Reported as empty they would read as an index that binds no
        route and a model every edge of which the code is missing -- the second
        is the worse one, because ``static_absence`` is a negation licensed by
        ``call_graph_closed``, which here certifies the completeness of a
        relation this bundle cannot derive at all.  So derivability is
        transitive: every reported relation whose premises this bundle cannot
        populate is named and withheld, and the negations over them with it.
        """
        section = _section("no_base_pack", base_pack=False)
        self.assertEqual(section["join"]["status"], static_join.JOIN_BOUND)
        self.assertEqual(sorted(section["underived"]),
                         sorted(static_join.REPORTED_RELATIONS),
                         "static_edge is ruleless, so nothing that reads it is derivable")
        self.assertEqual(section["withheld"],
                         {name: [static_join.UNDERIVED_REASON]
                          for name in static_join.REPORTED_RELATIONS})
        for key in ("routes", "dead", "blocked", "unresolved", "static_only"):
            with self.subTest(key=key):
                self.assertIsNone(section[key])
        self.assertEqual(
            section["capabilities"]["jobs_api"],
            {relation: None for relation in static_join.CELL_RELATIONS},
            "every model edge would otherwise be 'absent' from a ruleless static_edge")
        self.assertIsNone(section["static_only"],
                          "nothing binds, so nothing is bound-but-unobserved")

    def test_an_unclosed_edge_model_withholds_divergence_and_names_the_witness(self) -> None:
        """A reviewer who did not close their edge model licenses no divergence.

        ``static_divergence`` negates ``capability_edge`` under
        ``capability_edge_closed``.  Without that witness the kernel derives
        nothing -- and an empty list would read exactly like the closed model's
        agreement.  The section says which witnesses the index carries instead,
        and nulls what the missing one licensed; ``static_convergence``, which
        negates nothing, is unaffected.
        """
        section = _section("edges_unclosed", edges_closed=False)
        cells = section["capabilities"]
        self.assertIsNone(cells["bootstrap"][static_join.DIVERGENCE_RELATION])
        self.assertEqual(section["withheld"][static_join.DIVERGENCE_RELATION],
                         [static_join.EDGE_CLOSED_RELATION])
        self.assertEqual(
            section["closure_witnesses"][static_join.EDGE_CLOSED_RELATION], [])
        self.assertEqual(section["closure_witnesses"][static_join.CALL_GRAPH_CLOSED_RELATION],
                         section["join"]["indexes"])
        self.assertEqual(cells["jobs_api"][static_join.CONVERGENCE_RELATION], ["jobs_service"])
        self.assertEqual(_section("bound")["capabilities"]["bootstrap"]
                         [static_join.DIVERGENCE_RELATION], ["jobs_api"],
                         "the closed model is what an empty list would have looked like")


class StaticOnlyIsLicensedByTheRuntimeWitnessTests(unittest.TestCase):
    def test_a_closed_run_that_never_requested_the_surface_gives_static_only(self) -> None:
        section = _section("bound")
        self.assertEqual(section["runtime"], static_join.RUNTIME_OBSERVED)
        self.assertEqual(section["runtime_routes"], len(OBSERVED_ROUTES))
        self.assertEqual(section["static_only"], BINDS)
        self.assertEqual(section["static_only_licensed_by"],
                         static_join.REQUESTS_CLOSED_RELATION)
        self.assertEqual(section["surfaces_not_comparable"], [])

    def test_a_surface_the_run_did_request_is_not_static_only(self) -> None:
        section = _section("bound", routes=OBSERVED_ROUTES | {ROUTE_OF_SURFACE})
        self.assertEqual(section["static_only"], [])
        self.assertEqual(section["routes"], {SURFACE: [["audit_logs", "create"],
                                                       ["jobs", "read"]]})

    def test_an_unclosed_request_set_licenses_no_negation(self) -> None:
        section = _section("bound", routes_closed=False)
        self.assertEqual(section["runtime"], static_join.RUNTIME_UNCLOSED)
        self.assertIsNone(section["static_only"])
        self.assertIsNone(section["static_only_licensed_by"],
                          "an unlicensed negation names no witness either")

    def test_a_run_with_no_request_row_is_absent_not_empty(self) -> None:
        section = _section("bound", routes=(), routes_closed=True)
        self.assertEqual(section["runtime"], static_join.RUNTIME_ABSENT)
        self.assertEqual(section["runtime_routes"], 0)
        self.assertIsNone(section["static_only"])

    def test_a_request_set_not_spelled_like_a_surface_licenses_no_negation(self) -> None:
        """Closed licenses "complete"; it does not license "spelled the same way".

        ``static_only`` compares a surface id with a route by equality, and
        ``schema_replay_v1`` mandates no shape for a route.  Handed a closed
        request set that is not ``<METHOD> <path>``, every statically bound
        surface would compare unequal to every request and be reported as bound
        but never requested -- a negation from a naming difference.  The routes
        that cannot be compared are named instead, and the negation withheld.
        """
        section = _section("bound", routes={ROUTE_OF_SURFACE.split(" ", 1)[1]},
                           routes_closed=True)
        self.assertEqual(section["runtime"], static_join.RUNTIME_OBSERVED)
        self.assertIsNone(section["static_only"])
        self.assertIsNone(section["static_only_licensed_by"])
        self.assertEqual(section["runtime_routes_not_comparable"],
                         [ROUTE_OF_SURFACE.split(" ", 1)[1]])
        comparable = _section("bound", routes={ROUTE_OF_SURFACE}, routes_closed=True)
        self.assertEqual(comparable["runtime_routes_not_comparable"], [])
        self.assertEqual(comparable["static_only"], [],
                         "the same route, spelled comparably, was requested")

    def test_a_committed_receipt_that_omits_the_method_is_named_not_negated(self) -> None:
        """Not a hand-made shape: a receipt fixture this repository already has."""
        from capcov.claims.replay import replay_facts

        exported = replay_facts.export_bundle(QUALIFIED_RECEIPT, run=QUALIFIED_RUN)
        self.assertEqual(exported.status, replay_facts.STATUS_COMPLETE, exported.messages)
        side = static_join.runtime_side(exported, QUALIFIED_RUN)
        self.assertTrue(side["routes_closed"], "closed, and still not comparable")
        self.assertEqual(sorted(side["routes"]),
                         ["/api/cloud/project/{project}/issues/{issue}"])
        section = static_join.section(_loaded("bound"), run=RUN, routes=side["routes"],
                                      routes_closed=side["routes_closed"])
        self.assertIsNone(section["static_only"])
        self.assertIsNone(section["static_only_licensed_by"])
        self.assertEqual(section["runtime_routes_not_comparable"], sorted(side["routes"]))

    def test_the_receipts_own_requests_are_what_the_cli_compares_against(self) -> None:
        """Not a hand-made route set: the routes the exporter read out of the receipt."""
        from capcov.claims.replay import replay_facts

        exported = replay_facts.export_bundle(RECEIPT, run=RUN)
        self.assertEqual(exported.status, replay_facts.STATUS_COMPLETE, exported.messages)
        side = static_join.runtime_side(exported, RUN)
        self.assertEqual(side["routes"], OBSERVED_ROUTES)
        self.assertTrue(side["routes_closed"])


class AskingForItWronglyIsExitTwoTests(_CliTestCase):
    def test_a_static_bundle_that_is_not_there_is_named_exit_two(self) -> None:
        proc, document = self.gate("--static", str(self.out / "absent.json"))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot read the static bundle", proc.stderr)
        self.assertIsNone(document, "nothing was judged, so nothing was written")

    def test_a_static_bundle_that_is_not_json_is_named_exit_two(self) -> None:
        path = self.out / "not.json"
        path.write_text("{not json", encoding="utf-8")
        proc, document = self.gate("--static", str(path))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("is not JSON", proc.stderr)
        self.assertIsNone(document)

    def test_json_that_is_not_a_claim_bundle_is_named_exit_two(self) -> None:
        """The coverage artifact handed to --static: JSON, and not this kind of JSON."""
        proc, document = self.gate("--static", str(COVERAGE))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("is not a claim bundle", proc.stderr)
        self.assertIsNone(document)

    def test_static_without_the_claims_judge_is_refused_not_ignored(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "capcov", "gate", str(COVERAGE), "--exemptions",
             str(EXEMPTIONS), "--static", str(_Bundles.path("bound"))],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(SRC)})
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--static is only meaningful with --judge claims", proc.stderr)


class TheJoinThatWillNotEvaluateTests(_CliTestCase):
    """A bound bundle the kernel cannot close: named, counted as nothing, not a traceback.

    ``evaluate`` returns ``RESOURCE_EXHAUSTED``/``UNSUPPORTED_CONSTRUCT`` rather
    than raising, and its defaults are finite (10k iterations, 100k derived
    rows, 100k provenance nodes, 30 s), so this path is reachable on a big
    enough bundle.  It is driven here by evaluating the same bundle under a
    one-row bound, which is the same failure with a smaller number in it.  The
    clamp is on this module's own limits, so the claims judge's evaluation of
    the receipt -- the verdict and exit code asserted below -- is untouched.
    """

    def _clamped(self):
        from capcov.claims import evaluator

        return mock.patch.object(static_join, "LIMITS",
                                 evaluator.ResourceLimits(max_derived_rows=1))

    def _in_process(self, *extra: str):
        """The gate, in this process, so the clamp reaches the join and nothing else."""
        from capcov import cli

        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(["gate", str(COVERAGE), "--judge", "claims", "--exemptions",
                             str(EXEMPTIONS), "--receipt", str(RECEIPT),
                             "--judge-out", str(self.out / "judge"), *extra])
        document_path = self.out / "judge" / "judge.json"
        document = (json.loads(document_path.read_text(encoding="utf-8"))
                    if document_path.is_file() else None)
        return code, out.getvalue(), document

    def test_the_section_names_the_failure_and_reports_no_row(self) -> None:
        with self._clamped():
            section = _section("bound")
        self.assertEqual(section["join"]["status"], static_join.JOIN_BOUND)
        self.assertIn("did not evaluate", section["error"])
        for key in ("routes", "capabilities", "dead", "blocked", "unresolved",
                    "static_only", "underived", "withheld", "closure_witnesses"):
            with self.subTest(key=key):
                self.assertIsNone(section[key], "an unevaluated bundle reports nothing")

    def test_the_summary_line_says_it_instead_of_counting_what_is_not_there(self) -> None:
        with self._clamped():
            section = _section("bound")
        line = static_join.summary_line(section)
        self.assertIn("no rows read", line)
        self.assertIn(section["error"], line)

    def test_the_cli_names_it_and_still_exits_with_the_judges_own_code(self) -> None:
        """The line is printed after judge.json is written: it may not replace a verdict."""
        plain_code, _, plain = self._in_process()
        with self._clamped():
            code, out, document = self._in_process("--static", str(_Bundles.path("bound")))
        self.assertEqual(code, plain_code)
        self.assertEqual(document["verdict"], plain["verdict"])
        self.assertEqual(document["exit_code"], plain["exit_code"])
        self.assertIn("no rows read", out)
        self.assertIn("did not evaluate", document["static"]["error"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
