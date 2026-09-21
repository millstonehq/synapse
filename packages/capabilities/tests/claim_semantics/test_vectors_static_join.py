"""``claims vectors-static``: what a recorded write and a static path say about each other.

Four properties, one per class.

1. **A divergence is refuted only under both witnesses.**  A table the candidate
   wrote that the route's *closed* store set does not contain refutes
   ``vector_store_divergence``; inject the closure test's residue and the same
   write is ``unresolved``; withhold ``index_describes_candidate`` and it is
   unresolved again.  A table the route does reach is ``reached`` and a table the
   index's entity census never declared is ``unindexed`` -- never a divergence,
   because a census that never saw a table did not say the route cannot reach it.

2. **The advisory side is licensed like any negation.**  ``static_store_unexercised``
   -- a reachable store no cell wrote -- is reported only when the replay
   producer closed what the candidate wrote: every cell recorded, every cell
   passed, every table compared.  A gap, a failed cell or an uncompared table
   withholds it, by name, and it never moves an exit code.

3. **Producers stay distinct, and the identity is checked.**  A replay row
   sourced by ``scip`` is refused by validation, and so is a reviewer witness
   sourced by the replay producer.  A ``--describes-candidate`` naming a digest
   the replay did not declare is a usage refusal, not a silently ignored flag.

4. **The kernel is the caller's choice, and it is ``vectors.claims``'.**
   ``--kernel python`` runs the Python evaluator and never the compiled one;
   ``--kernel souffle`` runs the compiled checker and never the Python one.  The
   real Souffle kernel runs only where Souffle is installed, and skips by name
   where it is not.

The fixtures are the committed go_app golden index (no indexer runs here) joined
to synthetic vectors/replay artifacts built the way ``tests/test_vectors_claims``
builds them.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from capcov.claims.differential import KernelReport, run_python
from capcov.claims.ir import canonical_dict, canonical_json
from capcov.claims.static import closure, scip_facts, join as static_bundle_join
from capcov.claims.static.combine import combine
from capcov.claims.validation import ValidationError, validate_bundle
from capcov.scip import runner
from capcov.vectors import normalize, static_join
from capcov.vectors.claims import RECORDER_PRODUCER, REPLAY_PRODUCER, artifact_digest
from capcov.vectors.recorder import (DECLARED_SOURCE_KEY, DECLARED_SOURCE_STATIC, read_vectors,
                                     record, write_vectors)
from capcov.vectors.replay import read_replay, write_replay
from capcov.vectors.schema import (Operation, ReplayArtifact, ReplayResult, StepSpec, Vector,
                                   VectorsArtifact)

try:
    from .static_rules import go_app
    from .static_rules.adapter import pack_bundle
except ImportError:  # unittest discover -s imports this directory as top-level
    from static_rules import go_app
    from static_rules.adapter import pack_bundle

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SRC = PACKAGE_ROOT / "src"

CANDIDATE = "c" * 64
OTHER_CANDIDATE = "d" * 64
PROVENANCE = {"incumbent_commit": "a" * 40}
OPERATION = "jobs.read"
RUN = "run-1"
CELL = "permitted"
VECTOR_ID = f"{OPERATION}:{CELL}"
#: The surface the go_app index declares, and the operation request that spells it.
SURFACE = go_app.SURFACE
REQUEST = {"method": "GET", "path": "/jobs/{id}"}
#: A third entity with no op site: in the index's table inventory, reached by no
#: route.  Writing it is the divergence the precheck exists to find.
UNREACHED_TABLE = "sessions"
#: The tables the one route does reach.
REACHED_TABLE = "jobs"
UNWRITTEN_TABLE = "audit_logs"
#: A table no entity declares at all -- outside the index's inventory.
UNINDEXED_TABLE = "widgets"
#: The closure test's own residue, and what it costs: no ``call_graph_closed``,
#: so no ``static_route_no_table``, so no refutation.
RESIDUE = [{"file": "internal/service/service.go", "line": 12, "callee": "h.dispatch",
            "kind": "unresolved", "reason": "untyped receiver"}]


class Authority:
    """The Shen authority verdict, stubbed: these tests judge, they do not attest."""

    ok = True

    def failed_checks(self):
        return []


def _ast(residue=()) -> dict:
    ast = go_app.ast_raw()
    ast["entities"].append({"name": UNREACHED_TABLE, "symbol": "Session", "module": "",
                            "file": "models/models.go", "line": 19})
    ast["scip_residue"] = [dict(entry) for entry in residue]
    return ast


_BUNDLES: dict[bool, static_join.StaticBundle] = {}


def static(residue: bool = False) -> static_join.StaticBundle:
    """The go_app static bundle with the closure and base packs merged, cached."""
    if residue not in _BUNDLES:
        ast = _ast(RESIDUE if residue else ())
        raw = go_app.golden_raw()
        exported = scip_facts.export_bundle(
            go_app.normalized(raw), ast_raw=ast, source_root=go_app.GO_APP, language="go",
            index_digest=go_app.json_file_digest(raw),
            index_digest_kind=runner.INDEX_DIGEST_JSON)
        assert exported.status == scip_facts.STATUS_COMPLETE, exported.messages
        bundle = combine(exported.bundle, closure.closure_bundle(exported.bundle, ast),
                         pack_bundle())
        text = canonical_json(canonical_dict(bundle)) + "\n"
        _BUNDLES[residue] = static_join.StaticBundle(
            bundle, hashlib.sha256(text.encode("utf-8")).hexdigest())
    return _BUNDLES[residue]


def operation() -> Operation:
    return Operation(OPERATION, "route", "read", "http", request=dict(REQUEST))


def artifacts(*, delta=None, informational=None, passed: bool = True, gaps=(),
              declared="*", candidate: str = CANDIDATE) -> tuple[VectorsArtifact, ReplayArtifact]:
    """One recorded cell and its replay, with whatever delta the case needs."""
    delta = {f"rows.{REACHED_TABLE}": {"inserted": []},
             f"rows.{UNREACHED_TABLE}": {"inserted": [{"id": 1}]}} if delta is None else delta
    vectors = VectorsArtifact(
        operation=OPERATION, template_version="boundary-v1", declared_stores=declared,
        provenance=PROVENANCE,
        vectors=[Vector(VECTOR_ID, CELL, "actor-1", [StepSpec(actor="actor-1", role="permitted")],
                        {"steps": [{"status": 200}], "delta": dict(delta),
                         "informational": dict(informational or {})})],
        gaps=[dict(item) for item in gaps],
        required_cells=[CELL, *[item["cell"] for item in gaps]])
    replay = ReplayArtifact(
        operation=OPERATION, mutant=None, vectors_recorded=1, vectors_passing=int(passed),
        gaps_recorded=len(vectors.gaps), candidate_sha256=candidate,
        vectors_provenance=PROVENANCE, comparison_policy=normalize.comparison_policy_identity(),
        vectors_sha256=artifact_digest(vectors), run_id=RUN,
        results=[ReplayResult(VECTOR_ID, CELL, passed,
                              None if passed else "/steps[0]/status: expected 200 got 500")])
    return vectors, replay


def pair(**kwargs) -> static_join.OperationPair:
    vectors, replay = artifacts(**kwargs)
    surface, reason = static_join.operation_surface(operation().to_json())
    return static_join.OperationPair(OPERATION, vectors, replay, surface, reason)


def judged(pairs, bundle, *, describes=CANDIDATE, kernel: str = "python", **kwargs):
    judgment = static_join.judge(pairs, bundle, describes_candidate=describes, kernel=kernel,
                                 authority_runner=lambda _bundle: Authority(), **kwargs)
    return judgment, static_join.document(judgment, pairs, bundle,
                                          describes_candidate=describes, kernel=kernel)


def rows(judgment, relation: str) -> list[tuple]:
    return sorted(tuple(row) for name, values in judgment.report.relations
                  if name == relation for row in values)


def divergence_verdicts(judgment) -> set[str]:
    return {verdict["semantic"] for key, verdict in judgment.verdicts().items()
            if key.startswith("vector-store-divergence:")}


class ADivergenceNeedsBothWitnessesTests(unittest.TestCase):
    def test_a_write_outside_the_closed_store_set_refutes_the_claim(self) -> None:
        judgment, report = judged([pair()], static())
        entry = report["operations"][OPERATION]
        self.assertEqual(entry[static_join.DIVERGENCE_RELATION], [UNREACHED_TABLE])
        self.assertEqual(entry["stores"][UNREACHED_TABLE], static_join.STORE_DIVERGENCE)
        self.assertEqual(len(report["divergence_claims_refuted"]), 1)
        self.assertIn("refuted", divergence_verdicts(judgment))

    def test_the_refutation_rests_on_the_closure_packs_own_negation(self) -> None:
        """No negation is written here: the doubt is the closure pack's row."""
        judgment, _ = judged([pair()], static())
        self.assertEqual(rows(judgment, static_join.NO_TABLE_RELATION),
                         [(static_join.index_of(static()), SURFACE, UNREACHED_TABLE)])
        self.assertEqual([row[3] for row in rows(judgment, static_join.DIVERGENCE_RELATION)],
                         [UNREACHED_TABLE])

    def test_residue_on_the_index_makes_the_same_write_unresolved(self) -> None:
        judgment, report = judged([pair()], static(residue=True))
        self.assertEqual(rows(judgment, static_join.DIVERGENCE_RELATION), [])
        self.assertEqual(report["operations"][OPERATION]["stores"][UNREACHED_TABLE],
                         static_join.STORE_UNRESOLVED)
        self.assertEqual(divergence_verdicts(judgment), {"unresolved"})
        self.assertEqual(report["divergence_claims_refuted"], [])

    def test_without_the_candidate_witness_nothing_is_derived(self) -> None:
        judgment, report = judged([pair()], static(), describes=None)
        self.assertEqual(rows(judgment, static_join.DIVERGENCE_RELATION), [])
        self.assertEqual(divergence_verdicts(judgment), {"unresolved"})
        self.assertEqual(report["join"]["status"], static_join.JOIN_UNWITNESSED)
        self.assertIn(static_join.DESCRIBES_RELATION, report["join"]["message"])

    def test_a_table_the_route_reaches_is_not_a_divergence(self) -> None:
        _judgment, report = judged([pair()], static())
        self.assertEqual(report["operations"][OPERATION]["stores"][REACHED_TABLE],
                         static_join.STORE_REACHED)

    def test_a_table_the_census_never_declared_is_unindexed_not_diverged(self) -> None:
        """An entity census that never saw a table did not say the route cannot reach it."""
        written = {f"rows.{UNINDEXED_TABLE}": {"inserted": [{"id": 2}]}}
        judgment, report = judged([pair(delta=written)], static())
        entry = report["operations"][OPERATION]
        self.assertEqual(entry["stores"], {UNINDEXED_TABLE: static_join.STORE_UNINDEXED})
        self.assertEqual(entry[static_join.DIVERGENCE_RELATION], [])
        self.assertEqual(rows(judgment, static_join.DIVERGENCE_RELATION), [])

    def test_a_failed_cell_claims_no_write_at_all(self) -> None:
        """A failure may be the delta itself, so the recording's tables are not the candidate's."""
        judgment, report = judged([pair(passed=False)], static())
        self.assertEqual(rows(judgment, static_join.STORE_CHANGED_RELATION), [])
        self.assertEqual(report["operations"][OPERATION]["cells_failed"], [VECTOR_ID])
        self.assertEqual(report["operations"][OPERATION]["stores"], {})
        self.assertEqual(divergence_verdicts(judgment), set())


class TheAdvisorySideIsLicensedTests(unittest.TestCase):
    def test_a_reachable_store_no_cell_wrote_is_reported_under_the_closure(self) -> None:
        _judgment, report = judged([pair()], static())
        entry = report["operations"][OPERATION]
        self.assertTrue(entry["stores_closed"])
        self.assertEqual(entry[static_join.UNEXERCISED_RELATION], [UNWRITTEN_TABLE])
        self.assertEqual(entry["unexercised_withheld"], [])

    def test_a_recording_gap_withholds_it_and_says_so(self) -> None:
        gapped = pair(gaps=({"cell": "anonymous", "reason": "manifest has no anonymous actor"},))
        judgment, report = judged([gapped], static())
        entry = report["operations"][OPERATION]
        self.assertFalse(entry["stores_closed"])
        self.assertIsNone(entry[static_join.UNEXERCISED_RELATION])
        self.assertEqual(rows(judgment, static_join.UNEXERCISED_RELATION), [])
        self.assertTrue(any("gap" in reason for reason in entry["unexercised_withheld"]),
                        entry["unexercised_withheld"])

    def test_an_uncompared_change_withholds_it_and_is_enumerated(self) -> None:
        uncompared = pair(informational={f"rows.{UNWRITTEN_TABLE}": {"inserted": [{"id": 3}]}})
        judgment, report = judged([uncompared], static())
        entry = report["operations"][OPERATION]
        self.assertEqual(entry["stores_uncompared"], [UNWRITTEN_TABLE])
        self.assertEqual(rows(judgment, static_join.STORE_UNCOMPARED_RELATION),
                         [(RUN, OPERATION, CELL, UNWRITTEN_TABLE)])
        self.assertIsNone(entry[static_join.UNEXERCISED_RELATION])
        self.assertTrue(any("uncompared" in reason for reason in entry["unexercised_withheld"]))

    def test_a_declared_subset_withholds_it(self) -> None:
        """A recording that compared a subset cannot close what the candidate wrote."""
        subset = pair(declared={"tables": [REACHED_TABLE, UNREACHED_TABLE]})
        _judgment, report = judged([subset], static())
        entry = report["operations"][OPERATION]
        self.assertIsNone(entry[static_join.UNEXERCISED_RELATION])
        self.assertTrue(any("subset" in reason for reason in entry["unexercised_withheld"]))
        # the divergence side is unaffected: a positive write is still a write
        self.assertEqual(entry[static_join.DIVERGENCE_RELATION], [UNREACHED_TABLE])

    def test_the_advisory_row_never_moves_the_exit_code(self) -> None:
        """The only thing that does is a refuted divergence claim."""
        clean = pair(delta={f"rows.{REACHED_TABLE}": {"inserted": []}})
        _judgment, report = judged([clean], static())
        self.assertEqual(report["operations"][OPERATION][static_join.UNEXERCISED_RELATION],
                         [UNWRITTEN_TABLE])
        self.assertEqual(report["divergence_claims_refuted"], [])


class ProducersStayDistinctTests(unittest.TestCase):
    def _fragment(self, describes=CANDIDATE):
        one = pair()
        from capcov.vectors import claims as vector_claims

        bundles = {OPERATION: vector_claims.build_bundle(one.vectors, one.replay)}
        return static_join.fragment([one], bundles, index=static_join.index_of(static()),
                                    borrowed=static_join.borrow(static()),
                                    describes_candidate=describes)

    def _resourced(self, relation: str, source: str):
        from dataclasses import replace

        fragment = self._fragment()
        evidence = tuple(replace(record, source=source)
                         if record.atom.relation == relation else record
                         for record in fragment.evidence)
        return replace(fragment, evidence=evidence)

    def test_a_replay_row_cannot_claim_the_scip_producer(self) -> None:
        issues = validate_bundle(self._resourced(static_join.STORE_CHANGED_RELATION, "scip go 1"))
        self.assertTrue(any(issue.code == "evidence-producer" for issue in issues), issues)

    def test_the_candidate_witness_cannot_be_claimed_by_the_replay_producer(self) -> None:
        """An index describes a binary because a reviewer says so, not because a replay ran."""
        issues = validate_bundle(
            self._resourced(static_join.DESCRIBES_RELATION, f"{REPLAY_PRODUCER} x"))
        self.assertTrue(any(issue.code == "evidence-producer" for issue in issues), issues)

    def test_the_rows_each_side_owns_are_the_ones_it_could_know(self) -> None:
        fragment = self._fragment()
        classes = {record.atom.relation: record.source.split(" ", 1)[0]
                   for record in fragment.evidence}
        self.assertEqual(classes[static_join.STORE_CHANGED_RELATION], REPLAY_PRODUCER)
        self.assertEqual(classes[static_join.STORES_CLOSED_RELATION], REPLAY_PRODUCER)
        self.assertEqual(classes[static_join.OPERATION_SURFACE_RELATION], RECORDER_PRODUCER)
        self.assertEqual(classes[static_join.DESCRIBES_RELATION], static_join.REVIEWER_PRODUCER)

    def test_every_written_store_row_depends_on_the_replay_pass_that_licensed_it(self) -> None:
        fragment = self._fragment()
        for record in fragment.evidence:
            if record.atom.relation == static_join.STORE_CHANGED_RELATION:
                self.assertTrue(record.depends_on, record)

    def test_a_witness_naming_another_candidate_is_refused(self) -> None:
        with self.assertRaisesRegex(static_join.VectorStaticError, "another binary"):
            static_join.build_bundle([pair()], static(), describes_candidate=OTHER_CANDIDATE)

    def test_a_bundle_without_the_closure_pack_is_refused_by_name(self) -> None:
        exported = scip_facts.export_bundle(
            go_app.normalized(go_app.golden_raw()), ast_raw=_ast(), source_root=go_app.GO_APP,
            language="go", index_digest=go_app.json_file_digest(),
            index_digest_kind=runner.INDEX_DIGEST_JSON)
        bare = static_join.StaticBundle(exported.bundle, "0" * 64)
        with self.assertRaisesRegex(static_join.VectorStaticError,
                                    static_join.NO_TABLE_RELATION):
            static_join.build_bundle([pair()], bare, describes_candidate=CANDIDATE)


class TheKernelIsTheCallersChoiceTests(unittest.TestCase):
    def _report(self, backend: str) -> KernelReport:
        return KernelReport(backend, (), ())

    def test_python_runs_the_python_evaluator_and_not_the_compiled_one(self) -> None:
        def refuse(_bundle):
            raise AssertionError("the compiled kernel must not run for --kernel python")

        judgment = static_join.judge([pair()], static(), describes_candidate=CANDIDATE,
                                     kernel="python", authority_runner=lambda _b: Authority(),
                                     compiled_runner=refuse)
        self.assertEqual(judgment.report.backend, "python")
        self.assertEqual(dict(judgment.bundle.metadata)["claim_kernel"], "python")

    def test_souffle_runs_the_compiled_checker_and_not_the_python_one(self) -> None:
        def refuse(_bundle):
            raise AssertionError("the python kernel must not run for --kernel souffle")

        judgment = static_join.judge(
            [pair()], static(), describes_candidate=CANDIDATE, kernel="souffle",
            authority_runner=lambda _b: Authority(), python_runner=refuse,
            compiled_runner=lambda _b: self._report("souffle-compiled"))
        self.assertEqual(judgment.report.backend, "souffle-compiled")

    def test_an_unknown_kernel_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "kernel must be"):
            static_join.judge([pair()], static(), describes_candidate=CANDIDATE,
                              kernel="datalog", authority_runner=lambda _b: Authority())

    @unittest.skipIf(shutil.which("souffle") is None, "souffle is not installed")
    def test_the_real_souffle_kernel_agrees_with_the_python_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            judgment = static_join.judge(
                [pair()], static(), describes_candidate=CANDIDATE, kernel="souffle",
                authority_runner=lambda _b: Authority(), cache_dir=Path(directory))
        self.assertEqual([row[3] for row in rows(judgment, static_join.DIVERGENCE_RELATION)],
                         [UNREACHED_TABLE])


class TheRecorderCanTakeTheStaticListTests(unittest.TestCase):
    def test_a_closed_store_set_becomes_a_declared_list(self) -> None:
        declared = static_join.declared_stores(static(), SURFACE)
        self.assertEqual(declared["declared"], {"tables": [UNWRITTEN_TABLE, REACHED_TABLE]})
        self.assertIn("closes", declared["reason"])

    def test_an_open_store_set_declares_nothing(self) -> None:
        """A lower bound used as the compared list stops observing what the index missed."""
        declared = static_join.declared_stores(static(residue=True), SURFACE)
        self.assertIsNone(declared["declared"])
        self.assertIn("lower bound", declared["reason"])
        self.assertEqual(declared["tables"], [UNWRITTEN_TABLE, REACHED_TABLE])

    def _record(self, static_declared=None) -> VectorsArtifact:
        op = Operation("sync", "command", "command", "shell",
                       request={"mode": "command", "target": "sync"})

        class Fixture:
            def snapshot(self): return "snapshot"
            def restore(self, token): pass
            def inspect(self): return {"rows": {}, "collections": {}, "queues": {}, "redis_keys": []}
            def drain(self): pass

        class Endpoint:
            candidate_sha256 = CANDIDATE
            base_url = None
            def run_shell(self, request): return 0, {"ok": True}

        with tempfile.TemporaryDirectory() as directory:
            record([op], Fixture(), Endpoint(), {}, {}, Path(directory),
                   provenance=PROVENANCE, static_declared=static_declared)
            return read_vectors(Path(directory) / "sync" / "vectors.json")

    def test_without_the_opt_in_the_recording_is_what_it_was(self) -> None:
        artifact = self._record()
        self.assertEqual(artifact.declared_stores, "*")
        self.assertNotIn(DECLARED_SOURCE_KEY, artifact.provenance)

    def test_the_opt_in_records_against_the_static_list_and_says_so(self) -> None:
        artifact = self._record({"sync": {"tables": [REACHED_TABLE]}})
        self.assertEqual(artifact.declared_stores, {"tables": [REACHED_TABLE]})
        self.assertEqual(artifact.provenance[DECLARED_SOURCE_KEY], DECLARED_SOURCE_STATIC)

    def test_an_operation_the_map_does_not_name_is_untouched(self) -> None:
        artifact = self._record({"other.operation": {"tables": [REACHED_TABLE]}})
        self.assertEqual(artifact.declared_stores, "*")
        self.assertNotIn(DECLARED_SOURCE_KEY, artifact.provenance)


class _OnDisk(unittest.TestCase):
    """The artifacts as the recorder and the replay actually write them."""

    def layout(self, *, replay_elsewhere: bool = False, drop_replay: bool = False):
        directory = Path(tempfile.mkdtemp(prefix="capcov-vectors-static-"))
        self.addCleanup(shutil.rmtree, directory, True)
        vectors_dir = directory / "vectors"
        replay_dir = directory / ("replay" if replay_elsewhere else "vectors")
        vectors, replay = artifacts()
        op = operation()
        write_vectors(vectors_dir, op, vectors)
        if not drop_replay:
            write_replay(replay_dir, op, replay, normalize.freeze_comparison_policy())
        bundle_path = directory / "static.json"
        bundle_path.write_text(
            canonical_json(canonical_dict(static().bundle)) + "\n", encoding="utf-8")
        return vectors_dir, replay_dir, bundle_path


class ReadingTheArtifactsTests(_OnDisk):
    def test_the_surface_comes_from_the_recorders_own_operation_record(self) -> None:
        vectors_dir, replay_dir, _bundle = self.layout()
        pairs = static_join.read_pairs(vectors_dir, replay_dir)
        self.assertEqual([one.surface for one in pairs], [SURFACE])
        self.assertEqual([one.run for one in pairs], [RUN])

    def test_a_recording_nothing_replayed_is_named_not_skipped(self) -> None:
        vectors_dir, replay_dir, _bundle = self.layout(replay_elsewhere=True, drop_replay=True)
        replay_dir.mkdir(parents=True, exist_ok=True)
        with self.assertRaisesRegex(static_join.VectorStaticError, "not replayed"):
            static_join.read_pairs(vectors_dir, replay_dir)

    def test_an_operation_that_is_not_a_route_has_no_surface_and_says_why(self) -> None:
        surface, reason = static_join.operation_surface(
            {"id": "sync", "kind": "command", "driver": "shell",
             "request": {"mode": "command", "target": "sync"}})
        self.assertIsNone(surface)
        self.assertIn(static_join.HTTP_DRIVER, reason)


class TheCommandTests(_OnDisk):
    def run_cli(self, *extra: str, vectors=None, replay=None, bundle=None):
        vectors_dir, replay_dir, bundle_path = self.layout(replay_elsewhere=True)
        proc = subprocess.run(
            [sys.executable, "-m", "capcov.claims.cli", "claims", "vectors-static",
             "--vectors", str(vectors if vectors else vectors_dir),
             "--replay", str(replay if replay else replay_dir),
             "--static", str(bundle if bundle else bundle_path), "--kernel", "python", *extra],
            text=True, capture_output=True, env={**os.environ, "PYTHONPATH": str(SRC)})
        document = json.loads(proc.stdout) if proc.stdout.strip() else None
        return proc, document

    def test_an_unreadable_static_bundle_is_a_named_exit_two(self) -> None:
        proc, document = self.run_cli(bundle=Path("/nonexistent/bundle.json"))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot read the static bundle", document["refusal"])

    def test_a_vectors_directory_with_no_artifact_is_a_named_exit_two(self) -> None:
        empty = Path(tempfile.mkdtemp(prefix="capcov-vectors-empty-"))
        self.addCleanup(shutil.rmtree, empty, True)
        proc, document = self.run_cli(vectors=empty)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("vectors.json", document["refusal"])

    def test_a_candidate_the_replay_did_not_declare_is_a_named_exit_two(self) -> None:
        proc, document = self.run_cli("--describes-candidate", OTHER_CANDIDATE)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("another binary", document["refusal"])

    def test_the_divergence_is_the_exit_code_and_the_advisory_is_not(self) -> None:
        from capcov.claims import shen

        try:
            shen.authority(rules={"relations": [], "rules": []})
        except shen.ShenUnavailable as exc:
            self.skipTest(f"the Shen authority runtime is unavailable: {exc}")
        except shen.ShenFailure:
            pass
        proc, document = self.run_cli("--describes-candidate", CANDIDATE)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(document["operations"][OPERATION][static_join.DIVERGENCE_RELATION],
                         [UNREACHED_TABLE])
        self.assertEqual(document["operations"][OPERATION][static_join.UNEXERCISED_RELATION],
                         [UNWRITTEN_TABLE])
        self.assertIn("store divergence", proc.stderr)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
