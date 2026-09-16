"""The compiled Souffle checker as a third kernel over both corpora (live binary).

Like the adversarial suites this never skips: souffle is a precondition, and
``souffle-compile.py`` plus a C++ toolchain are too.  One compile per pack
(replay, static) is shared by every case through a class-level cache -- the
cache directory is ``CAPCOV_SOUFFLE_CACHE_DIR`` when set, so a warm CI cache
skips the ~50 s compile; otherwise a temp dir compiles once.

Per case the three kernels must agree completely: no operational failure
anywhere, identical relations, identical claim verdict/status/basis/missing
premises, one canonical digest, and ``compare_three`` admitting the bundle.
The rejected replay cases check the other side of the contract: an invalid
bundle is refused by the compiled kernel under exactly the interpreter's
failure name, and is still non-admissible.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from capcov.claims import souffle
from capcov.claims.differential import (CompiledKernelMismatch, DifferentialMismatch,
                                        compare_three, reports_match, run_python,
                                        run_souffle, run_souffle_compiled)
from capcov.claims.souffle import compile as compiled
from capcov.claims.static.certificate import certify, claim_conclusions, recheck

try:
    from .replay_rules import adapter as replay_adapter
    from .static_rules import adapter as static_adapter
    from .target_go import replay_join
except ImportError:  # unittest discover -s imports this directory as top-level
    from replay_rules import adapter as replay_adapter
    from static_rules import adapter as static_adapter
    from target_go import replay_join

HEX64 = r"^[0-9a-f]{64}$"
CACHE_ENV = "CAPCOV_SOUFFLE_CACHE_DIR"


def cache_dir() -> Path:
    """The shared compiled-checker cache: ``CAPCOV_SOUFFLE_CACHE_DIR`` or a temp dir."""
    configured = os.environ.get(CACHE_ENV)
    if configured:
        path = Path(configured)
        path.mkdir(parents=True, exist_ok=True)
        return path
    return Path(tempfile.mkdtemp(prefix="capcov-compiled-cache-"))


class SouffleCompiledCorpusTests(unittest.TestCase):
    """Every reviewed case of both packs, in python, interpreted and compiled Souffle."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cache = cache_dir()
        cls.owns_cache = not os.environ.get(CACHE_ENV)
        cls.replay_root = tempfile.mkdtemp(prefix="capcov-compiled-differential-")
        cls.checkers: dict[str, compiled.CompiledChecker] = {}
        cls.cases: dict[str, dict[str, object]] = {}
        cls.compile_error: str | None = None
        if shutil.which("souffle") is None:
            return
        replay_pack = replay_adapter.load_pack()
        static_pack = static_adapter.load_pack()
        cls.cases = {
            "replay": {p.stem: replay_adapter.load_case(p, replay_pack)
                       for p in replay_adapter.case_paths()},
            "static": {p.stem: static_adapter.load_case(p, static_pack)
                       for p in static_adapter.case_paths()},
        }
        cls.rejected = {p.stem: replay_adapter.load_case(p, replay_pack, validate=False)
                        for p in replay_adapter.case_paths(replay_adapter.REJECTED_DIR)}
        try:
            for pack, cases in cls.cases.items():
                program = souffle.program_for_pack(next(iter(cases.values())))
                cls.checkers[pack] = compiled.compile_program(program, cache_dir=cls.cache)
        except (compiled.CompileError, souffle.SouffleUnavailable) as exc:
            cls.compile_error = f"{type(exc).__name__}: {exc}"

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.owns_cache:
            shutil.rmtree(cls.cache, ignore_errors=True)
        shutil.rmtree(cls.replay_root, ignore_errors=True)

    def setUp(self) -> None:
        self.assertIsNotNone(shutil.which("souffle"),
                             "souffle must be on PATH: run inside the nix devShell")
        self.assertIsNone(self.compile_error, self.compile_error)

    def test_one_compile_per_pack_serves_every_case_of_that_pack(self) -> None:
        self.assertEqual(sorted(self.checkers), ["replay", "static"])
        self.assertNotEqual(self.checkers["replay"].compile_key,
                            self.checkers["static"].compile_key)
        for pack, checker in sorted(self.checkers.items()):
            self.assertRegex(checker.binary_sha256, HEX64)
            self.assertRegex(checker.program_digest, HEX64)
            self.assertGreaterEqual(len(self.cases[pack]), 10)
            for stem, bundle in sorted(self.cases[pack].items()):
                with self.subTest(pack=pack, case=stem):
                    self.assertEqual(souffle.program_for_pack(bundle).program_digest,
                                     checker.program_digest)
            entry = Path(checker.binary_path).parent
            self.assertEqual(entry.name, f"compiled-{checker.compile_key}")
            # a second request is a cache hit: the binary is not rebuilt
            again = compiled.compile_program(souffle.program_for_pack(
                next(iter(self.cases[pack].values()))), cache_dir=self.cache)
            self.assertEqual(again.binary_sha256, checker.binary_sha256)
            self.assertEqual(again.binary_path, checker.binary_path)

    def test_three_kernels_agree_on_every_reviewed_case(self) -> None:
        for pack, cases in sorted(self.cases.items()):
            checker = self.checkers[pack]
            for stem, bundle in sorted(cases.items()):
                with self.subTest(pack=pack, case=stem):
                    python = run_python(bundle)
                    interpreted = run_souffle(bundle)
                    native = run_souffle_compiled(bundle, checker=checker)
                    for report in (python, interpreted, native):
                        self.assertIsNone(report.operational_failure,
                                          f"{report.backend}: {report.message[:400]}")
                    self.assertEqual(interpreted.relations, native.relations)
                    self.assertEqual(python.relations, native.relations)
                    self.assertEqual(interpreted.claims, native.claims)
                    self.assertEqual(python.claims, native.claims)
                    self.assertEqual(len({python.canonical_digest, interpreted.canonical_digest,
                                          native.canonical_digest}), 1)
                    self.assertEqual(interpreted.closure_digest, native.closure_digest)
                    self.assertTrue(reports_match(interpreted, native))
                    result = compare_three(bundle, checker=checker,
                                           replay_root=self.replay_root)
                    self.assertTrue(result.matched)
                    self.assertTrue(result.closure_digest_equal)
                    self.assertEqual(result.compiled.backend, "souffle-compiled")

    def test_the_rejected_cases_fail_the_same_way_in_both_souffle_kernels(self) -> None:
        checker = self.checkers["replay"]
        self.assertTrue(self.rejected, "the replay pack ships at least one rejected case")
        for stem, bundle in sorted(self.rejected.items()):
            with self.subTest(case=stem):
                interpreted = run_souffle(bundle)
                native = run_souffle_compiled(bundle, checker=checker)
                self.assertEqual(interpreted.operational_failure, "invalid-input")
                self.assertEqual(native.operational_failure, interpreted.operational_failure)
                # an identical failure name is still not admissible
                self.assertFalse(reports_match(interpreted, native))
                with self.assertRaises((DifferentialMismatch, CompiledKernelMismatch)):
                    compare_three(bundle, checker=checker, replay_root=self.replay_root)


class TargetGoReceiptThreeKernelsTests(unittest.TestCase):
    """Both committed receipt fixtures judged by python, interpreted and compiled Souffle."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cache = cache_dir()
        cls.owns_cache = not os.environ.get(CACHE_ENV)
        cls.replay_root = tempfile.mkdtemp(prefix="capcov-compiled-join-")
        cls.joins: dict[str, object] = {}
        cls.error: str | None = None
        if shutil.which("souffle") is None:
            return
        try:
            for label, directory in (("qualified", replay_join.COMMITTED_RECEIPT_DIR),
                                     ("unqualified", replay_join.UNQUALIFIED_RECEIPT_DIR)):
                join = replay_join.build(directory)
                cls.joins[label] = replay_join.evaluate_join(
                    join, cls.replay_root, kernels="three", cache_dir=cls.cache)
        except (compiled.CompileError, souffle.SouffleUnavailable) as exc:
            cls.error = f"{type(exc).__name__}: {exc}"

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.owns_cache:
            shutil.rmtree(cls.cache, ignore_errors=True)
        shutil.rmtree(cls.replay_root, ignore_errors=True)

    def setUp(self) -> None:
        self.assertIsNotNone(shutil.which("souffle"),
                             "souffle must be on PATH: run inside the nix devShell")
        self.assertIsNone(self.error, self.error)
        self.assertEqual(sorted(self.joins), ["qualified", "unqualified"])

    def _join(self, label: str):
        join = self.joins[label]
        self.assertIsNone(join.mismatch, f"{label}: kernels disagree")
        self.assertEqual(join.contract_findings, [])
        self.assertEqual(join.kernels, "three")
        return join

    def test_all_three_kernels_judge_both_fixtures_identically(self) -> None:
        for label in ("qualified", "unqualified"):
            with self.subTest(fixture=label):
                join = self._join(label)
                closures = join.closures()
                self.assertEqual([report.backend for report in closures],
                                 ["python", "souffle", "souffle-compiled"])
                self.assertTrue(join.result.matched)
                self.assertTrue(join.result.closure_digest_equal)
                self.assertEqual(len({report.canonical_digest for report in closures}), 1)
                self.assertEqual(replay_join.summary(join)["kernels"],
                                 ["python", "souffle", "souffle-compiled"])

    def test_the_qualified_receipt_is_supported_and_complete_in_all_three(self) -> None:
        join = self._join("qualified")
        self.assertEqual(join.ops, ("delete-issue",))
        claim_id = join.claim_id("qualified", "delete-issue")
        self.assertEqual(claim_id, "claim-qualified-delete-issue")
        for report in join.closures():
            claim = next(c for c in report.claims if c.key == claim_id)
            with self.subTest(kernel=report.backend):
                self.assertEqual(claim.semantic, "supported")
                self.assertEqual(claim.operational, "complete")
                self.assertEqual(claim.missing_premises, ())
        entry = replay_join.summary(join)["delete-issue"]
        self.assertEqual(entry["op_qualified"], "supported")
        self.assertTrue(entry["corpus_constrains"])
        self.assertEqual(entry["exclusions_applied"],
                         ["authentication", "go_issue_outbox", "jobs_statuses", "redis"])

    def test_the_unqualified_receipt_is_unresolved_on_model_writes_in_all_three(self) -> None:
        join = self._join("unqualified")
        claim_id = join.claim_id("qualified", "delete-issue")
        for report in join.closures():
            claim = next(c for c in report.claims if c.key == claim_id)
            with self.subTest(kernel=report.backend):
                self.assertEqual(claim.semantic, "unresolved")
                self.assertEqual([json.loads(item)["relation"] for item in claim.missing_premises
                                  if item.startswith("{")], ["model_writes"])
        entry = replay_join.summary(join)["delete-issue"]
        self.assertEqual(entry["missing_premise"], ["model_writes"])
        self.assertEqual(entry["blocking_premise"], {"relation": "undeclared_any", "holds": True})

    def test_certificates_are_one_document_across_the_three_closures(self) -> None:
        for label in ("qualified", "unqualified"):
            join = self._join(label)
            self.assertTrue(join.row_certificates)
            for claim in join.bundle.claims:
                rows = claim_conclusions(join.bundle, join.closures()[0].relations, claim)
                for report in join.closures():
                    with self.subTest(fixture=label, claim=claim.id, kernel=report.backend):
                        self.assertEqual(claim_conclusions(join.bundle, report.relations, claim), rows)
                        for row in rows:
                            certificate = certify(join.bundle, report.relations, claim.relation, row)
                            self.assertEqual(certificate, certify(
                                join.bundle, join.closures()[0].relations, claim.relation, row))
                            self.assertTrue(recheck(join.bundle, certificate, report.relations).ok)

    def test_write_artifacts_records_the_compiled_provenance(self) -> None:
        join = self._join("qualified")
        out = Path(tempfile.mkdtemp(prefix="capcov-compiled-artifacts-"))
        self.addCleanup(shutil.rmtree, out, True)
        document = replay_join.write_artifacts(join, out)
        provenance = document["compiled"]
        self.assertEqual(set(provenance), compiled.PROVENANCE_KEYS)
        self.assertEqual(provenance["schema"], "capcov-souffle-compiled-v1")
        for field in ("compile_key", "program_digest", "binary_sha256", "souffle_sha256"):
            self.assertRegex(provenance[field], HEX64, field)
        self.assertEqual(provenance["compile_flags"], ["--no-preprocessor", "-j1", "-o"])
        self.assertEqual(provenance, join.checker.provenance())
        # one name for the compiled closure digest in every artifact of a run
        self.assertEqual(document["kernels"]["compiled_digest"],
                         join.result.compiled.canonical_digest)
        self.assertTrue(document["kernels"]["closure_digest_equal"])
        # the cached provenance.json on disk is the same document
        entry = Path(join.checker.binary_path).parent
        self.assertEqual(json.loads((entry / "provenance.json").read_text()), provenance)
        # the toolchain path is recorded provenance; the judge's own working
        # paths (cache entry, receipt directory) never leak into the artifact
        serialized = json.dumps(document, sort_keys=True)
        self.assertNotIn(join.checker.binary_path, serialized)
        self.assertNotIn(str(entry), serialized)
        self.assertNotIn(str(join.receipt_dir), serialized)
        self.assertNotIn(str(out), serialized)


if __name__ == "__main__":
    unittest.main()
