"""``scripts/compiled_checker.py`` end to end, as a subprocess (live binary).

The script is the cross-repo contract: a producer repo runs it on an exported
receipt directory and gates its build on the exit code, so the tests drive the
real CLI rather than its functions.  Both committed receipt fixtures are
judged, the option-only invocation (no subcommand) that the producer's
`make judge-compiled` uses is asserted to be the same as ``judge``, and every
refusal path is pinned to its documented exit code.

souffle is a precondition, not a skip.  One compiled binary is shared by every
case through ``CAPCOV_SOUFFLE_CACHE_DIR``; without it a temp cache compiles
once for the whole class.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    from .target_go import replay_join
except ImportError:  # unittest discover -s imports this directory as top-level
    from target_go import replay_join

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PACKAGE_ROOT / "scripts" / "compiled_checker.py"
HEX64 = r"^[0-9a-f]{64}$"
CACHE_ENV = "CAPCOV_SOUFFLE_CACHE_DIR"
JUDGE_KEYS = {"schema", "receipt", "pack", "compiled", "kernels", "ops", "required_ops",
              "contract_findings", "verdict", "exit_code"}


class CompiledCheckerScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        configured = os.environ.get(CACHE_ENV)
        cls.owns_cache = not configured
        cls.cache = Path(configured) if configured else Path(
            tempfile.mkdtemp(prefix="capcov-script-cache-"))
        cls.cache.mkdir(parents=True, exist_ok=True)
        cls.workspace = Path(tempfile.mkdtemp(prefix="capcov-script-out-"))

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.owns_cache:
            shutil.rmtree(cls.cache, ignore_errors=True)
        shutil.rmtree(cls.workspace, ignore_errors=True)

    def setUp(self) -> None:
        self.assertIsNotNone(shutil.which("souffle"),
                             "souffle must be on PATH: run inside the nix devShell")
        self.assertTrue(SCRIPT.is_file(), SCRIPT)

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=PACKAGE_ROOT,
                              capture_output=True, text=True, check=False)

    def out(self, name: str) -> Path:
        path = self.workspace / name
        shutil.rmtree(path, ignore_errors=True)
        return path

    def judge(self, receipt: Path, name: str, *extra: str) -> tuple[subprocess.CompletedProcess, Path]:
        out = self.out(name)
        completed = self.run_script("--receipt", str(receipt), "--out", str(out),
                                    "--cache-dir", str(self.cache), "--souffle", "souffle",
                                    *extra)
        return completed, out

    def test_the_qualified_receipt_is_supported_and_exits_zero(self) -> None:
        completed, out = self.judge(replay_join.COMMITTED_RECEIPT_DIR, "qualified",
                                    "--require-supported", "delete-issue")
        self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(set(document), JUDGE_KEYS)
        self.assertEqual(document["schema"], "capcov-compiled-judge-v1")
        self.assertEqual(document["verdict"], "supported")
        self.assertEqual(document["exit_code"], 0)
        self.assertEqual(document["required_ops"], ["delete-issue"])
        self.assertEqual(document["contract_findings"], [])
        self.assertEqual(document["pack"]["id"], "rules-replay-v1")
        self.assertEqual(document["pack"]["relation_count"], 65)
        self.assertEqual(document["pack"]["rule_count"], 40)
        self.assertRegex(document["pack"]["program_digest"], HEX64)

        kernels = document["kernels"]
        self.assertTrue(kernels["matched"])
        self.assertTrue(kernels["closure_digest_equal"])
        self.assertEqual(kernels["failures"], {})
        self.assertEqual(len({kernels["python_digest"], kernels["souffle_digest"],
                              kernels["compiled_digest"]}), 1)
        for field in ("python_digest", "souffle_digest", "compiled_digest"):
            self.assertRegex(kernels[field], HEX64, field)
        for field in ("interpreter_seconds", "compiled_seconds", "python_seconds"):
            self.assertGreater(kernels[field], 0.0, field)

        entry = document["ops"]["delete-issue"]
        self.assertEqual(entry["verdict"], "supported")
        self.assertEqual(entry["op_qualified"],
                         {"semantic": "supported", "operational": "complete",
                          "missing_premises": []})
        self.assertTrue(entry["corpus_constrains"])
        self.assertIsNone(entry["blocking_premise"])
        self.assertEqual(entry["exclusions_applied"],
                         ["authentication", "go_issue_outbox", "jobs_statuses", "redis"])
        self.assertRegex(entry["certificate_sha256"], HEX64)

        self.assertRegex(document["compiled"]["binary_sha256"], HEX64)
        self.assertEqual(document["compiled"]["schema"], "capcov-souffle-compiled-v1")
        self.assertEqual(document["compiled"]["program_digest"], document["pack"]["program_digest"])

        # the judge writes the join artifacts next to judge.json
        self.assertTrue((out / "receipt.json").is_file())
        certificates = sorted(p.name for p in out.glob("certificate-*.json"))
        self.assertIn("certificate-claim-qualified-delete-issue.json", certificates)

    def test_judge_artifacts_carry_no_local_paths(self) -> None:
        completed, out = self.judge(replay_join.COMMITTED_RECEIPT_DIR, "no-paths",
                                    "--require-supported", "delete-issue")
        self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
        for path in sorted(out.glob("*.json")):
            text = path.read_text()
            with self.subTest(artifact=path.name):
                self.assertNotIn(str(out), text)
                self.assertNotIn(str(self.cache), text)
                self.assertNotIn(str(replay_join.COMMITTED_RECEIPT_DIR), text)
                self.assertNotIn(str(Path.home()), text)

    def test_the_option_only_invocation_is_the_judge_subcommand(self) -> None:
        """The producer repo's gate passes options with no subcommand word."""
        bare, bare_out = self.judge(replay_join.COMMITTED_RECEIPT_DIR, "bare",
                                    "--require-supported", "delete-issue")
        named_out = self.out("named")
        named = self.run_script("judge", "--receipt", str(replay_join.COMMITTED_RECEIPT_DIR),
                                "--out", str(named_out), "--cache-dir", str(self.cache),
                                "--souffle", "souffle", "--require-supported", "delete-issue")
        self.assertEqual((bare.returncode, named.returncode), (0, 0), named.stderr[-2000:])
        stable = ("schema", "receipt", "pack", "compiled", "ops", "required_ops", "verdict",
                  "exit_code", "contract_findings")
        left = json.loads((bare_out / "judge.json").read_text())
        right = json.loads((named_out / "judge.json").read_text())
        self.assertEqual({k: left[k] for k in stable}, {k: right[k] for k in stable})

    def test_the_unqualified_receipt_is_not_supported_and_exits_one(self) -> None:
        completed, out = self.judge(replay_join.UNQUALIFIED_RECEIPT_DIR, "unqualified",
                                    "--require-supported", "delete-issue")
        self.assertEqual(completed.returncode, 1, completed.stdout[-2000:])
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["verdict"], "not-supported")
        self.assertEqual(document["exit_code"], 1)
        self.assertEqual(document["unmet_ops"], ["delete-issue"])
        self.assertTrue(document["kernels"]["matched"], "the kernels still agree; the op does not qualify")
        entry = document["ops"]["delete-issue"]
        self.assertEqual(entry["verdict"], "not-supported")
        self.assertEqual(entry["op_qualified"]["semantic"], "unresolved")
        self.assertEqual(entry["op_qualified"]["missing_premises"], ["model_writes"])
        self.assertEqual(entry["blocking_premise"], {"relation": "undeclared_any", "holds": True})

    def test_an_unreplayed_required_op_exits_one(self) -> None:
        completed, out = self.judge(replay_join.COMMITTED_RECEIPT_DIR, "unknown-op",
                                    "--require-op", "nope")
        self.assertEqual(completed.returncode, 1, completed.stdout[-2000:])
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["verdict"], "not-supported")
        self.assertEqual(document["unmet_ops"], ["nope"])
        # the replayed op itself is still judged and still supported
        self.assertEqual(document["ops"]["delete-issue"]["op_qualified"]["semantic"], "supported")

    def test_no_required_op_derives_the_verdict_from_every_replayed_op(self) -> None:
        """A verdict over zero requirements would be vacuous; every replayed op decides it."""
        completed, out = self.judge(replay_join.UNQUALIFIED_RECEIPT_DIR, "no-requirement")
        self.assertEqual(completed.returncode, 1, completed.stderr[-2000:])
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["required_ops"], [])
        self.assertEqual(document["verdict"], "not-supported")
        self.assertEqual(document["exit_code"], 1)
        self.assertEqual(document["unmet_ops"], ["delete-issue"])
        self.assertEqual(document["ops"]["delete-issue"]["op_qualified"]["semantic"], "unresolved")
        self.assertTrue(document["kernels"]["matched"], "the kernels still agree")

        # the qualified receipt needs no requirement to be judged supported
        completed, out = self.judge(replay_join.COMMITTED_RECEIPT_DIR, "no-requirement-qualified")
        self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["required_ops"], [])
        self.assertEqual(document["verdict"], "supported")
        self.assertEqual(set(document), JUDGE_KEYS)

    def test_an_extra_receipt_key_is_a_contract_finding_and_exits_three(self) -> None:
        copy = self.workspace / "receipt-with-extra-key"
        shutil.rmtree(copy, ignore_errors=True)
        shutil.copytree(replay_join.COMMITTED_RECEIPT_DIR, copy)
        receipt = json.loads((copy / "receipt.json").read_text())
        receipt["extra_key"] = 1
        (copy / "receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
        completed, out = self.judge(copy, "contract-finding", "--require-supported", "delete-issue")
        self.assertEqual(completed.returncode, 3, completed.stderr[-2000:])
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["verdict"], "contract-finding")
        self.assertEqual(document["exit_code"], 3)
        self.assertIsNone(document["kernels"])
        self.assertIsNone(document["compiled"])
        self.assertEqual(document["ops"], {})
        self.assertEqual(len(document["contract_findings"]), 1)
        self.assertIn("extra_key", document["contract_findings"][0])

    def test_an_absent_receipt_is_a_contract_finding_and_exits_three(self) -> None:
        out = self.out("no-receipt")
        completed = self.run_script(
            "--receipt", str(self.workspace / "there-is-no-receipt-here"), "--out", str(out),
            "--cache-dir", str(self.cache), "--require-supported", "delete-issue")
        self.assertEqual(completed.returncode, 3, completed.stderr[-2000:])
        self.assertIn("contract finding", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_an_absent_souffle_is_unavailable_and_exits_four(self) -> None:
        out = self.out("unavailable")
        completed = self.run_script(
            "--receipt", str(replay_join.COMMITTED_RECEIPT_DIR), "--out", str(out),
            "--cache-dir", str(self.cache), "--souffle", "souffle-that-is-not-installed",
            "--require-supported", "delete-issue")
        self.assertEqual(completed.returncode, 4, completed.stderr[-2000:])
        self.assertIn("toolchain unavailable", completed.stderr)
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["verdict"], "unavailable")
        self.assertEqual(document["exit_code"], 4)
        self.assertIsNone(document["compiled"])

    def test_bench_scales_the_receipt_and_records_both_medians(self) -> None:
        out = self.out("bench")
        completed = self.run_script(
            "bench", "--receipt", str(replay_join.COMMITTED_RECEIPT_DIR), "--out", str(out),
            "--scale", "2", "--repeat", "2", "--cache-dir", str(self.cache))
        self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
        document = json.loads((out / "bench.json").read_text())
        self.assertEqual(document["schema"], "capcov-compiled-bench-v1")
        self.assertEqual(document["fixture"], replay_join.COMMITTED_RECEIPT_DIR.name)
        self.assertEqual(document["scale"], 2)
        self.assertEqual(document["relation_count"], 65)
        self.assertTrue(document["closures_identical"])
        self.assertRegex(document["binary_sha256"], HEX64)
        self.assertRegex(document["souffle"]["sha256"], HEX64)
        for kernel in ("interpreter", "compiled"):
            with self.subTest(kernel=kernel):
                self.assertEqual(len(document[kernel]["runs"]), 2)
                self.assertGreater(document[kernel]["median_s"], 0.0)
        # scale 2 doubles the req-keyed rows and leaves the model rows alone
        one = self.out("bench-1x")
        self.assertEqual(self.run_script(
            "bench", "--receipt", str(replay_join.COMMITTED_RECEIPT_DIR), "--out", str(one),
            "--scale", "1", "--repeat", "1", "--cache-dir", str(self.cache)).returncode, 0)
        single = json.loads((one / "bench.json").read_text())
        scaled_rows = document["rows_in"] - single["rows_in"]
        self.assertGreater(scaled_rows, 0)
        self.assertEqual(document["rows_in"], single["rows_in"] + scaled_rows)
        self.assertTrue(single["closures_identical"])

    def test_compile_prints_the_provenance_of_each_pack(self) -> None:
        digests = {}
        for pack in ("replay", "static"):
            with self.subTest(pack=pack):
                completed = self.run_script("compile", "--pack", pack,
                                            "--cache-dir", str(self.cache))
                self.assertEqual(completed.returncode, 0, completed.stderr[-4000:])
                provenance = json.loads(completed.stdout)
                self.assertEqual(provenance["pack"], pack)
                self.assertEqual(provenance["schema"], "capcov-souffle-compiled-v1")
                for field in ("compile_key", "program_digest", "binary_sha256", "souffle_sha256"):
                    self.assertRegex(provenance[field], HEX64, field)
                digests[pack] = provenance
                # a second invocation is a cache hit on the same key and binary
                again = json.loads(self.run_script(
                    "compile", "--pack", pack, "--cache-dir", str(self.cache)).stdout)
                self.assertTrue(again["cache_hit"])
                self.assertEqual(again["compile_key"], provenance["compile_key"])
                self.assertEqual(again["binary_sha256"], provenance["binary_sha256"])
        self.assertNotEqual(digests["replay"]["program_digest"], digests["static"]["program_digest"])
        self.assertNotEqual(digests["replay"]["compile_key"], digests["static"]["compile_key"])


if __name__ == "__main__":
    unittest.main()
