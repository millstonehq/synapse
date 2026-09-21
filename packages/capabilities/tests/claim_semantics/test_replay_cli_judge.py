"""`capcov gate --judge claims` really judges: the live path, souffle present.

The host-side suite (tests/test_cli_judge.py) pins what happens when nobody asks
and when the toolchain is absent.  This one is the other half: with the Souffle
interpreter on PATH, the CLI's claims branch runs the same judge the cross-repo
``scripts/compiled_checker.py`` runs, over the committed receipt fixtures, and
its answers are the documented ones.

Two receipts, two answers, and the difference between them is the point:

* the **synthetic** receipt carries a Stage D typed-checker certificate (every
  fact in it is made up, which is exactly why it is the only fixture that can
  exercise the positive path while the checker does not exist) -> ``supported``,
  CLI exit 0;
* the **real** target-go receipt does not -> ``pending-premise``, judge exit 5,
  CLI exit 1.  The CLI collapses the judge's six exit codes to a gate's one
  question, so this test also pins that the collapse is lossless *on paper*:
  judge.json still carries ``exit_code: 5`` and names the pending premise.

Every gate here but one passes ``--exemptions``, because ``--judge claims`` adds
a verdict and never replaces the coverage artifact's: the golden artifact fails
the four-cell gate, so without the exemptions file the exit code would be 1 for
a reason that has nothing to do with the receipt.  The one exception is
``test_a_supported_receipt_does_not_speak_for_the_coverage_artifact``, which
pins exactly that.

These are the *asked-for* kernels: the CLI is invoked with ``--evaluator all``,
so in the devShell three kernels judge and the differential runs.  The default
(python alone, no tool at all) is pinned host-side in tests/test_cli_judge.py,
and that the two agree on every verdict is pinned in test_evaluator_selection.py.
Outside the devShell this class skips, because an absent interpreter is pinned
elsewhere.
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

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
COVERAGE = FIXTURES / "upstream_golden" / "python_app" / "coverage.json"
#: Explains every unexplained row in COVERAGE, so the four-cell gate over it
#: passes and the exit code is the claims judge's verdict alone.  `--judge
#: claims` ADDS a verdict, so without this every gate below is exit 1 whatever
#: the receipt says -- which is its own test, right at the top of the class.
EXEMPTIONS = FIXTURES / "python_app_exemptions.toml"
SYNTHETIC = FIXTURES / "replay_receipt_min"
QUALIFIED = FIXTURES / "replay_receipt_target_go_qualified"


@unittest.skipIf(shutil.which("souffle") is None,
                 "the live claims judge needs the souffle interpreter: run inside `nix develop`")
class ClaimsJudgeCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-cli-judge-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _gate(self, receipt: Path, out: str, evaluator: str = "all", *extra: str):
        proc = subprocess.run(
            [sys.executable, "-m", "capcov", "gate", str(COVERAGE), "--judge", "claims",
             "--exemptions", str(EXEMPTIONS),
             "--receipt", str(receipt), "--judge-out", str(self.tmp / out),
             "--evaluator", evaluator, *extra],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(PACKAGE_ROOT / "src")})
        document = json.loads((self.tmp / out / "judge.json").read_text())
        return proc, document

    def test_a_supported_receipt_does_not_speak_for_the_coverage_artifact(self) -> None:
        """The same receipt, the same verdict, no --exemptions: the gate still fails.

        The four-cell gate over COVERAGE fails (4 unexplained), and `--judge
        claims` adds a verdict rather than replacing it, so the artifact's own
        judge still decides.  Without this the positional argument would be
        decorative: any supported receipt would turn any artifact green.
        """
        proc = subprocess.run(
            [sys.executable, "-m", "capcov", "gate", str(COVERAGE), "--judge", "claims",
             "--receipt", str(SYNTHETIC), "--judge-out", str(self.tmp / "unexempted"),
             "--evaluator", "all"],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(PACKAGE_ROOT / "src")})
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        document = json.loads((self.tmp / "unexempted" / "judge.json").read_text())
        self.assertEqual(document["verdict"], "supported")
        self.assertEqual(document["gated_artifact"]["four_cell"], "fail")
        self.assertEqual(document["gated_artifact"]["four_cell_unexplained"], 4)

    def test_the_synthetic_receipt_is_supported_and_the_gate_passes(self) -> None:
        proc, document = self._gate(SYNTHETIC, "synthetic")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(document["verdict"], "supported")
        self.assertEqual(document["exit_code"], 0)
        self.assertTrue(document["differential_report"]["matched"])
        # `all` in the devShell is every evaluator whose tool is here: all three
        self.assertEqual(document["kernels"], ["python", "souffle", "souffle-compiled"])
        self.assertEqual(document["differential"], "ran")
        self.assertIsNotNone(document["compiled"], "the compiled kernel records its binary")
        self.assertTrue(document["differential_report"]["closure_digest_equal"])
        self.assertIn("supported", proc.stdout)

    def test_the_pairwise_ask_runs_exactly_the_two_kernels_named(self) -> None:
        """`--evaluator` is a list, not a level: naming two runs two, and no binary is built."""
        proc, document = self._gate(SYNTHETIC, "pairwise", evaluator="python,souffle")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(document["kernels"], ["python", "souffle"])
        self.assertEqual(document["differential"], "ran")
        self.assertIsNone(document["compiled"])
        self.assertNotIn("compiled_digest", document["differential_report"])

    def test_the_default_ask_runs_the_python_kernel_alone_even_here(self) -> None:
        """souffle is on PATH and is still not used: the evaluator is chosen, never detected."""
        proc, document = self._gate(SYNTHETIC, "defaulted", evaluator="python")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(document["kernels"], ["python"])
        self.assertEqual(document["differential"], "not-run (single evaluator)")
        self.assertEqual(document["verdict"], "supported")

    def test_the_real_receipt_is_pending_the_checker_and_the_gate_fails(self) -> None:
        proc, document = self._gate(QUALIFIED, "qualified")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(document["verdict"], "pending-premise")
        # the gate answers 0/1; the distinction the producer repo gates on survives here
        self.assertEqual(document["exit_code"], 5)
        self.assertTrue(document["pending_ops"])
        self.assertIn("pending", proc.stderr + proc.stdout)

    def test_the_gated_artifact_is_named_in_judge_json(self) -> None:
        """Three kernels agreeing about a receipt still say nothing about a tree."""
        _, document = self._gate(SYNTHETIC, "bound")
        gated = document["gated_artifact"]
        self.assertEqual(gated["four_cell"], "pass")
        self.assertEqual(gated["sha256"], hashlib.sha256(COVERAGE.read_bytes()).hexdigest())
        self.assertEqual(gated["source_snapshot"],
                         json.loads(COVERAGE.read_text())["derived_from"]["source_snapshot"])

    def test_the_judge_writes_its_certificates_beside_judge_json(self) -> None:
        _, _ = self._gate(SYNTHETIC, "artifacts")
        written = {path.name for path in (self.tmp / "artifacts").rglob("*") if path.is_file()}
        self.assertIn("judge.json", written)
        self.assertGreater(len(written), 1, "the judge writes certificates, not just a verdict")

    def test_a_malformed_receipt_is_a_named_contract_finding_not_a_traceback(self) -> None:
        broken = self.tmp / "broken-receipt"
        shutil.copytree(SYNTHETIC, broken)
        (broken / "receipt.json").write_text("{not json")
        proc = subprocess.run(
            [sys.executable, "-m", "capcov", "gate", str(COVERAGE), "--judge", "claims",
             "--exemptions", str(EXEMPTIONS),
             "--receipt", str(broken), "--judge-out", str(self.tmp / "broken-out")],
            text=True, capture_output=True,
            env={**os.environ, "PYTHONPATH": str(PACKAGE_ROOT / "src")})
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("contract finding", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_no_artifact_carries_a_local_path(self) -> None:
        """The public-repo rule: digests, counts and verdicts, never a producing path."""
        self._gate(SYNTHETIC, "paths")
        for path in (self.tmp / "paths").rglob("*"):
            if path.is_file():
                with self.subTest(path.name):
                    self.assertNotIn(str(PACKAGE_ROOT), path.read_text())


if __name__ == "__main__":
    unittest.main()
