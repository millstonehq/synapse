from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest

from capcov.claims import (Atom, Bundle, Claim, Column, Constant, Evidence,
                           RelationDecl, Rule, Variable, bundle_from_json, digest)
from capcov.claims.differential import DifferentialMismatch, KernelReport, compare, reports_match, run_python, run_souffle
from capcov.claims.shrinker import ReplayPersistenceError, _difference_shape


def defective_souffle(bundle: Bundle) -> KernelReport:
    report = run_souffle(bundle)
    trigger_rows = dict(report.relations).get("trigger", ())
    if not trigger_rows or not report.claims: return report
    claim = report.claims[0]
    changed = replace(claim, semantic="refuted" if claim.semantic != "refuted" else "supported")
    return replace(report, claims=(changed, *report.claims[1:]))


@unittest.skipUnless(shutil.which("souffle"), "souffle runtime is unavailable")
class ShrinkerTests(unittest.TestCase):
    def bundle(self) -> Bundle:
        trigger = RelationDecl("trigger", (Column("x", "symbol"),))
        noise = RelationDecl("noise", (Column("x", "symbol"),))
        result = RelationDecl("result", (Column("x", "symbol"),), modality="claim", primitive=False)
        facts = (Atom("trigger", (Constant("bug"),)),
                 *(Atom("noise", (Constant(f"n{i}"),)) for i in range(7)))
        evidence = tuple(Evidence(f"e{i}", fact, source="fixture") for i, fact in enumerate(facts))
        return Bundle((trigger, noise, result), facts=facts, evidence=evidence,
                      rules=(Rule(Atom("result", (Variable("x"),)),
                                  (Atom("trigger", (Variable("x"),)),), "derive"),),
                      claims=(Claim("result", (Constant("bug"),), id="claim"),))

    def test_mismatch_is_minimized_persisted_reloaded_and_blocks(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DifferentialMismatch) as caught:
                compare(self.bundle(), souffle_runner=defective_souffle,
                        replay_root=directory, max_steps=200)
            result = caught.exception.result
            self.assertIsNotNone(result.replay_path)
            replay = Path(result.replay_path)
            self.assertTrue(replay.is_file())
            minimized = bundle_from_json(replay.read_text(encoding="utf-8"), validate=True)
            self.assertLessEqual(len(minimized.facts), 3)
            self.assertLessEqual(result.shrink_steps, 200)
            self.assertTrue(result.replay_reproduced)
            self.assertFalse(reports_match(run_python(minimized), defective_souffle(minimized)))

    def test_individual_duplicate_evidence_producers_are_one_minimized(self):
        original = self.bundle()
        trigger = next(fact for fact in original.facts if fact.relation == "trigger")
        duplicate = Evidence("duplicate-trigger-producer", trigger, source="fixture")
        original = replace(original, evidence=(*original.evidence, duplicate))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DifferentialMismatch) as caught:
                compare(original, souffle_runner=defective_souffle,
                        replay_root=directory, max_steps=200)
            result = caught.exception.result
            replay = bundle_from_json(Path(result.replay_path).read_text(), validate=True)
            self.assertFalse(result.shrink_truncated)
            self.assertEqual(len(replay.facts), 1)
            self.assertEqual(len(replay.evidence), 1)
            self.assertEqual(Path(result.replay_path).name, f"{digest(replay)}.json")

    def test_right_only_relation_is_part_of_mismatch_shape(self):
        left = KernelReport("python", (), ())
        right = KernelReport("souffle", (("right_only", (("v",),)),), ())
        self.assertEqual(_difference_shape(left, right),
                         ("semantic", ("right_only",), ()))

    def test_unwritable_replay_root_is_a_named_blocking_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            not_a_directory = Path(directory) / "file"
            not_a_directory.write_text("occupied", encoding="utf-8")
            with self.assertRaises(ReplayPersistenceError):
                compare(self.bundle(), souffle_runner=defective_souffle,
                        replay_root=not_a_directory, max_steps=200)

    def test_operational_failures_are_not_accepted_as_smaller_semantic_mismatches(self):
        original = self.bundle()

        def fails_when_small(bundle):
            if len(bundle.facts) < len(original.facts):
                return KernelReport("souffle", (), (), "resource-exhausted", "injected")
            return defective_souffle(bundle)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DifferentialMismatch) as caught:
                compare(original, souffle_runner=fails_when_small,
                        replay_root=directory, max_steps=50)
            replay = bundle_from_json(Path(caught.exception.result.replay_path).read_text(), validate=True)
            self.assertEqual(len(replay.facts), len(original.facts))
            self.assertIsNone(fails_when_small(replay).operational_failure)

    def test_one_sided_resource_failure_is_minimized_and_reloadable(self):
        def exhausted(bundle):
            return KernelReport("souffle", (), (), "resource-exhausted", "injected")

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DifferentialMismatch) as caught:
                compare(self.bundle(), souffle_runner=exhausted, replay_root=directory)
            result = caught.exception.result
            self.assertEqual(result.souffle.operational_failure, "resource-exhausted")
            replay = Path(result.replay_path)
            self.assertTrue(replay.is_file())
            minimized = bundle_from_json(replay.read_text(), validate=True)
            self.assertEqual(len(minimized.facts), 0)
            self.assertFalse(result.shrink_truncated)

    def test_operational_failure_above_fact_threshold_ddmins_to_boundary(self):
        threshold = 4

        def threshold_runner(bundle):
            if len(bundle.facts) >= threshold:
                return KernelReport("souffle", (), (), "resource-exhausted", "threshold")
            healthy = run_python(bundle)
            return replace(healthy, backend="souffle")

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DifferentialMismatch) as caught:
                compare(self.bundle(), souffle_runner=threshold_runner,
                        replay_root=directory, max_steps=200)
            result = caught.exception.result
            minimized = bundle_from_json(Path(result.replay_path).read_text(), validate=True)
            self.assertEqual(len(minimized.facts), threshold)
            self.assertFalse(result.shrink_truncated)
            for fact in minimized.facts:
                reduced = replace(minimized, facts=tuple(item for item in minimized.facts if item != fact),
                                  evidence=tuple(record for record in minimized.evidence
                                                 if record.atom != fact))
                self.assertIsNone(threshold_runner(reduced).operational_failure)

    def test_transient_initial_mismatch_persists_original_without_claiming_reproduction(self):
        original = self.bundle()
        calls = 0

        def one_shot(bundle):
            nonlocal calls
            calls += 1
            return defective_souffle(bundle) if calls == 1 else run_souffle(bundle)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DifferentialMismatch) as caught:
                compare(original, souffle_runner=one_shot,
                        replay_root=directory, max_steps=20)
            result = caught.exception.result
            replay = bundle_from_json(Path(result.replay_path).read_text(), validate=True)
            self.assertEqual(digest(replay), digest(original))
            self.assertFalse(result.replay_reproduced)
            self.assertTrue(result.shrink_truncated)

    def test_hard_two_hundred_step_ceiling_rejects_larger_configuration(self):
        with self.assertRaisesRegex(ValueError, "between 1 and 200"):
            compare(self.bundle(), souffle_runner=defective_souffle,
                    max_steps=201)

    def test_two_step_bound_is_enforced_and_reported_in_comparison_units(self):
        python_calls = 0
        souffle_calls = 0

        def counted_python(bundle):
            nonlocal python_calls
            python_calls += 1
            return run_python(bundle)

        def counted_souffle(bundle):
            nonlocal souffle_calls
            souffle_calls += 1
            return defective_souffle(bundle)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(DifferentialMismatch) as caught:
                compare(self.bundle(), python_runner=counted_python,
                        souffle_runner=counted_souffle,
                        replay_root=directory, max_steps=2)
            result = caught.exception.result
            self.assertEqual(result.shrink_steps, 2)
            self.assertTrue(result.shrink_truncated)
            self.assertTrue(result.replay_reproduced)
            # The original compare is outside shrink_steps; each shrink step
            # invokes both kernels exactly once.
            self.assertEqual(python_calls, 1 + result.shrink_steps)
            self.assertEqual(souffle_calls, 1 + result.shrink_steps)


if __name__ == "__main__": unittest.main()
