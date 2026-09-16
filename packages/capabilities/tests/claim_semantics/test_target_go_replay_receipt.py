"""Judge a real target-go replay receipt with rules-replay-v1 (Phase 4, judge side, runtime half).

Three parts.  ``NonconformingReceiptExample`` is the documented negative
example: the first receipt the target-go runner produced
(``.work/receipts/target-go-8177366-nomodel``) used array rows under a ``columns``
key, carried the extra top-level keys ``relations`` / ``producers`` and named
an empty ``model``; the strict exporter refuses each of those, and the test
pins the exact ingestion error for each by peeling them off a synthesized
copy one at a time (and checks the on-disk directory when it is present).
``FixtureJoinTest`` proves the join logic on the checked-in fixture receipt
without any environment.  ``RealReceiptTest`` runs the positive path against
the corrected, model-backed receipt named by ``CAPCOV_REPLAY_RECEIPT_DIR``
(the gate wrapper treats a skip as not-evidence): the exporter must accept it,
``corpus_constrains`` must be supported for every replayed op in both kernels
with identical certificates, and ``op_qualified`` must be supported/complete
with leaves spanning every producer class.  Artifacts (digests, counts,
verdicts, certificates) go to ``CAPCOV_TARGET_GO_REPLAY_OUT``.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from capcov.claims import canonical_json, validate_bundle
from capcov.claims.evaluator import evaluate
from capcov.claims.replay import replay_facts

try:
    from .target_go import replay_join
    from .replay_rules import cases as fixture_cases
except ImportError:  # unittest discover -s imports this directory as top-level
    from target_go import replay_join
    from replay_rules import cases as fixture_cases

RECEIPT_DIR = replay_join.receipt_dir()
REPO_ROOT = Path(__file__).resolve().parents[3]
NONCONFORMING_DIR = Path(os.environ.get("CAPCOV_REPLAY_NONCONFORMING_RECEIPT_DIR")
                         or REPO_ROOT / ".work" / "receipts" / "target-go-8177366-nomodel")
PRODUCER_CLASSES = {"replay", "php", "go", "shen", "mut", "reviewer"}


def _nonconforming(document_dir: Path) -> None:
    """Rewrite a conforming receipt copy into the runner's first dialect."""
    receipt = json.loads((document_dir / "receipt.json").read_text())
    receipt["model"] = ""
    receipt["closed"]["model_admissible"] = False
    receipt["model_writes_closed"] = []
    receipt["mutants_closed"] = [{"model": "", "op": entry["op"]} for entry in receipt["mutants_closed"]]
    receipt["relations"] = {}
    receipt["producers"] = {}
    for name in replay_facts.OBSERVATION_FILES:
        path = document_dir / f"{name}.json"
        if not path.exists():
            continue
        document = json.loads(path.read_text())
        receipt["relations"][name] = len(document["rows"])
        if "producer" in document:
            receipt["producers"][name] = document["producer"]
        columns = list(document["rows"][0]) if document["rows"] else []
        document = {**document, "columns": columns,
                    "rows": [[("" if c == "model" else row[c]) for c in columns] for row in document["rows"]]}
        path.write_text(json.dumps(document, indent=1))
    (document_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))


class NonconformingReceiptExample(unittest.TestCase):
    """The strict exporter names each nonconformance of the runner's first receipt."""

    def _export(self, directory: Path):
        run = json.loads((directory / "receipt.json").read_text())["run"]
        return replay_facts.export_bundle(directory, run=run)

    def test_each_nonconformance_is_refused_with_its_own_error(self) -> None:
        with tempfile.TemporaryDirectory(prefix="capcov-nonconforming-") as tmp:
            root = Path(tmp) / "receipt"
            shutil.copytree(fixture_cases.FIXTURE, root)
            _nonconforming(root)
            # 1. extra top-level keys
            result = self._export(root)
            self.assertEqual(result.status, replay_facts.STATUS_INVALID_INPUT)
            self.assertEqual(result.messages, ("receipt.json: unknown keys ['producers', 'relations']",))
            receipt = json.loads((root / "receipt.json").read_text())
            for key in ("producers", "relations"):
                receipt.pop(key)
            (root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))
            # 2. an empty model digest (the header is checked before any row file is read)
            result = self._export(root)
            self.assertEqual(result.status, replay_facts.STATUS_INVALID_INPUT)
            self.assertEqual(result.messages, ("receipt.json: 'model' must be a non-empty string",))
            model = json.loads((fixture_cases.FIXTURE / "receipt.json").read_text())["model"]
            receipt["model"] = model
            receipt["mutants_closed"] = [{"model": model, "op": entry["op"]} for entry in receipt["mutants_closed"]]
            (root / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True))
            for name in replay_facts.OBSERVATION_FILES:
                path = root / f"{name}.json"
                if path.exists():
                    document = json.loads(path.read_text())
                    if "model" in document["columns"]:
                        position = document["columns"].index("model")
                        for row in document["rows"]:
                            row[position] = model
                        path.write_text(json.dumps(document, indent=1))
            # 3. array rows under a columns key
            result = self._export(root)
            self.assertEqual(result.status, replay_facts.STATUS_INVALID_INPUT)
            self.assertEqual(result.messages, ("replay_request.json: must be {rows, producer?}",))
            for name in replay_facts.OBSERVATION_FILES:
                path = root / f"{name}.json"
                if not path.exists():
                    continue
                document = json.loads(path.read_text())
                columns = document.pop("columns")
                document["rows"] = [dict(zip(columns, row)) for row in document["rows"]]
                path.write_text(json.dumps(document, indent=1))
            # with the three nonconformances removed the copy is the fixture again
            # (minus the model-scoped rows this dialect could not carry)
            result = self._export(root)
            self.assertEqual(result.status, replay_facts.STATUS_COMPLETE, result.messages)

    def test_the_on_disk_first_receipt_is_refused_on_its_extra_keys(self) -> None:
        if not (NONCONFORMING_DIR / "receipt.json").is_file():
            return  # the negative example above stands on its own; the directory is optional
        result = self._export(NONCONFORMING_DIR)
        self.assertEqual(result.status, replay_facts.STATUS_INVALID_INPUT)
        self.assertEqual(result.messages, ("receipt.json: unknown keys ['producers', 'relations']",))
        receipt = json.loads((NONCONFORMING_DIR / "receipt.json").read_text())
        self.assertEqual(receipt["model"], "")
        self.assertIn("columns", json.loads((NONCONFORMING_DIR / "replay_request.json").read_text()))
        join = replay_join.build(NONCONFORMING_DIR)
        self.assertIsNone(join.bundle)
        self.assertEqual(replay_join.summary(join)["status"], "blocked")
        self.assertTrue(replay_join.summary(join)["contract_findings"])


class _JoinCase(unittest.TestCase):
    directory: Path
    out_dir: Path
    join: replay_join.ReplayJoin

    @classmethod
    def _setup(cls, directory: Path, out_dir: Path) -> None:
        cls.directory = directory
        cls.out_dir = out_dir
        cls.replay_root = tempfile.mkdtemp(prefix="capcov-target-go-replay-diff-")
        cls.join = replay_join.build(directory)
        if cls.join.bundle is not None and shutil.which("souffle") is not None:
            replay_join.evaluate_join(cls.join, cls.replay_root)
        cls.artifacts = replay_join.write_artifacts(cls.join, cls.out_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls, "join", None) is not None and cls.join.mismatch is None:
            shutil.rmtree(cls.replay_root, ignore_errors=True)

    def _exported(self) -> None:
        if self.join.bundle is None:
            self.fail("CONTRACT FINDING: " + "; ".join(self.join.contract_findings))

    def _evaluated(self) -> None:
        self._exported()
        self.assertIsNotNone(shutil.which("souffle"), "souffle must be on PATH: run inside the nix devShell")
        if self.join.mismatch is not None:
            self.fail(f"kernels disagree; replay bundle: {self.join.mismatch.replay_path}; "
                      f"souffle={self.join.mismatch.souffle.message[:400]}")
        self.assertIsNotNone(self.join.result)

    # -- shared assertions ------------------------------------------------------

    def check_export(self) -> None:
        self._exported()
        self.assertEqual(self.join.exported.status, replay_facts.STATUS_COMPLETE)
        self.assertEqual(validate_bundle(self.join.exported.bundle), ())
        self.assertEqual(validate_bundle(self.join.bundle), ())
        self.assertEqual(self.join.exported.counts["replay_run"], 1)
        self.assertTrue(self.join.ops)
        self.assertRegex(self.join.receipt["model"], r"^[0-9a-f]{64}$")
        for record in self.join.bundle.evidence:
            if record.kind == "assumption":
                self.assertIn(record.id, self.join.assumption_ids)
                self.assertIn(":assumed:", record.id)
                self.assertIn(record.atom.relation, {"op_declared", "index_describes_replay"})
        self.assertEqual(len(self.join.assumption_ids), 1 + len(self.join.ops))

    def check_kernels(self) -> None:
        self._evaluated()
        self.assertTrue(self.join.result.matched)
        self.assertEqual(self.join.result.python.canonical_digest, self.join.result.souffle.canonical_digest)
        self.assertIsNone(self.join.result.python.operational_failure)

    def check_corpus_constrains(self) -> None:
        self._evaluated()
        relations = dict(self.join.result.python.relations)
        for op in self.join.ops:
            claim_id = self.join.claim_id("corpus-constrains", op)
            declared = [row for row in relations["mutant"] if row[2] == op]
            killed = {row[1] for row in relations["mutant_killed_in"]}
            with self.subTest(op=op):
                self.assertTrue(declared, f"no mutant declared for {op}")
                self.assertTrue({row[1] for row in declared} <= killed, "a declared mutant was not killed")
                self.assertEqual([row for row in relations["surviving_mutant"] if row[1] == op], [])
                self.assertEqual(relations["kill_closure_gap"], ())
                for report in (self.join.result.python, self.join.result.souffle):
                    claim = next(c for c in report.claims if c.key == claim_id)
                    self.assertEqual((claim.semantic, claim.operational), ("supported", "complete"), report.backend)
                cert = self.join.certificates[claim_id]
                self.assertFalse(cert["truncated"])
                self.assertTrue({"mutant", "mutants_closed", "mutant_kills_closed", "model_describes_run"}
                                <= {leaf.split(":")[2] for leaf in cert["leaves"]})
                self.assertEqual(json.loads((self.out_dir / f"certificate-{claim_id}.json").read_text()), cert)
        report = evaluate(self.join.bundle)
        for entry in report.claims:
            if entry.claim.relation == "corpus_constrains":
                self.assertEqual(sorted(entry.result.support), self.join.certificates[entry.claim.id]["leaves"])

    def check_qualified(self) -> None:
        self._evaluated()
        by_id = {record.id: record for record in self.join.bundle.evidence}
        for op in self.join.ops:
            claim_id = self.join.claim_id("qualified", op)
            with self.subTest(op=op):
                for report in (self.join.result.python, self.join.result.souffle):
                    claim = next(c for c in report.claims if c.key == claim_id)
                    self.assertEqual((claim.semantic, claim.operational), ("supported", "complete"), report.backend)
                    self.assertEqual(claim.missing_premises, ())
                cert = self.join.certificates[claim_id]
                leaves = set(cert["leaves"])
                self.assertEqual({leaf.split(":")[0] for leaf in leaves}, PRODUCER_CLASSES)
                classes = {by_id[leaf].source.split(" ", 1)[0] for leaf in leaves}
                self.assertTrue(PRODUCER_CLASSES | {"php-census"} <= classes)
                self.assertTrue(set(self.join.assumption_ids) & leaves, "the census assumptions carry the claim")
        self.assertEqual({row[2] for row in dict(self.join.result.python.relations)["op_qualified"]}, set(self.join.ops))

    def check_artifacts(self) -> None:
        self._exported()
        written = sorted(p.name for p in self.out_dir.iterdir())
        self.assertIn("receipt.json", written)
        document = json.loads((self.out_dir / "receipt.json").read_text())
        self.assertEqual(document["join"]["run"], self.join.run)
        self.assertEqual(document["export"]["status"], "complete")
        text = "\n".join((self.out_dir / name).read_text(encoding="utf-8") for name in written)
        for needle in ("/Users/", "/home/", str(self.directory), "package ", "func ("):
            self.assertNotIn(needle, text)
        for value in self.join.receipt.get("receipts", {}).values():
            if isinstance(value, str) and value.startswith("/"):
                self.assertNotIn(value, text)
        if self.join.result is not None:
            for op in self.join.ops:
                self.assertTrue(document["join"][op]["corpus_constrains"])
                self.assertEqual(document["join"][op]["op_qualified"], "supported")


class FixtureJoinTest(_JoinCase):
    """The join logic on the checked-in fixture receipt (no environment needed)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._setup(fixture_cases.FIXTURE, Path(tempfile.mkdtemp(prefix="capcov-fixture-replay-out-")))

    def test_export(self) -> None:
        self.check_export()
        self.assertEqual(self.join.ops, (fixture_cases.CLOSE, fixture_cases.CREATE))

    def test_kernels(self) -> None:
        self.check_kernels()

    def test_corpus_constrains(self) -> None:
        self.check_corpus_constrains()

    def test_qualified(self) -> None:
        self.check_qualified()

    def test_artifacts(self) -> None:
        self.check_artifacts()

    def test_a_missing_model_witness_leaves_qualification_unresolved_naming_it(self) -> None:
        # the same join without the reviewer's model_observed row: the why-not names it
        self._evaluated()
        bundle = self.join.bundle
        dropped = next(record for record in bundle.evidence if record.atom.relation == "model_observed")
        from dataclasses import replace
        variant = replace(bundle, facts=tuple(f for f in bundle.facts if f != dropped.atom),
                          evidence=tuple(r for r in bundle.evidence if r.id != dropped.id),
                          outputs=tuple(replace(o, excludes_evidence=tuple(e for e in o.excludes_evidence if e != dropped.id))
                                        for o in bundle.outputs))
        report = evaluate(variant)
        self.assertEqual(report.status.value, "complete", report.message)
        for entry in report.claims:
            if entry.claim.relation == "op_qualified":
                self.assertEqual(entry.result.semantic.value, "unresolved")
                self.assertEqual([item["relation"] for item in entry.result.missing_premises], ["model_observed"])
            else:
                self.assertEqual(entry.result.semantic.value, "supported")


@unittest.skipUnless(RECEIPT_DIR is not None, f"needs {replay_join.RECEIPT_DIR_ENV}")
class RealReceiptTest(_JoinCase):
    """The corrected, model-backed target-go receipt."""

    @classmethod
    def setUpClass(cls) -> None:
        out_dir = Path(os.environ.get(replay_join.OUT_ENV) or tempfile.mkdtemp(prefix="capcov-target-go-replay-out-"))
        cls._setup(RECEIPT_DIR, out_dir)
        print(f"\ntarget-go replay artifacts: {out_dir}")

    def test_exporter_accepts_the_receipt(self) -> None:
        self.check_export()
        counts = self.join.exported.counts
        self.assertIn("delete-issue", self.join.ops)
        self.assertGreaterEqual(counts.get("mutant", 0), 1)

    def test_kernels_agree_on_the_real_receipt(self) -> None:
        self.check_kernels()

    def test_the_corpus_constrains_every_replayed_op_in_both_kernels(self) -> None:
        self.check_corpus_constrains()

    def test_delete_issue_is_qualified_with_leaves_from_every_producer(self) -> None:
        self.check_qualified()

    def test_artifacts_carry_digests_and_verdicts_only(self) -> None:
        self.check_artifacts()


if __name__ == "__main__":
    unittest.main()
