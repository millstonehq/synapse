"""Bounded command measurements stay useful without exposing argv or paths."""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "measure_qualification.py"


@unittest.skipUnless(os.name == "posix" and SCRIPT.exists(), "POSIX only")
class MeasureQualificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="capcov-measure-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        subprocess.run(["git", "-C", str(self.source), "config", "user.email", "measure@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(self.source), "config", "user.name", "Measurement Test"], check=True)
        (self.source / "source.txt").write_text("pinned test source\n")
        subprocess.run(["git", "-C", str(self.source), "add", "source.txt"], check=True)
        subprocess.run(["git", "-C", str(self.source), "commit", "-q", "-m", "fixture"], check=True)

    def _run(self, *, all_skip: bool = False) -> tuple[subprocess.CompletedProcess, dict, Path]:
        receipt = self.root / "receipt"
        receipt.mkdir(exist_ok=True)
        (receipt / "receipt.json").write_text('{"schema":1}\n')
        cache = self.root / "native-cache"
        out1, out2 = self.root / "out-cold", self.root / "out-warm"
        logs, report = self.root / "logs", self.root / "report.json"
        if all_skip:
            code = (
                "import json; print(json.dumps({'available':['shen-go'], 'cases': "
                "{'fib': {'detail':'SKIPPED: no buildable targets available', "
                "'impls': {'shen-go': {'status':'SKIP'}}}}}))"
            )
            samples = [{"id": "go-shake", "phase": "native-shake", "sample_kind": "single",
                        "require_go_target": True, "shake_case": "fib", "source_root": str(self.source),
                        "command": [sys.executable, "-c", code], "timeout_seconds": 5}]
        else:
            code = (
                "import os; from pathlib import Path; "
                "Path(os.environ['OUT'], 'judge.json').write_text('{\"result\":\"same\"}\\n'); "
                "Path(os.environ['CACHE']).mkdir(parents=True, exist_ok=True); "
                "Path(os.environ['CACHE'], 'checker').write_text('native identity'); "
                "print(os.environ['SECRET']); print('/tmp/private-example')"
            )
            samples = []
            for name, kind, output in (("cold", "cold", out1), ("warm", "warm", out2)):
                samples.append({"id": name, "phase": "replay-judge", "sample_kind": kind,
                                "comparison_group": "replay", "cache_state": kind,
                                "toolchain": {"nixpkgs_rev": "34ab99075ac4f7e40cf037eef32cb1c360bb85e9"},
                                "toolchain_binaries": {"python": sys.executable},
                                "source_root": str(self.source), "input_root": str(receipt),
                                "output_root": str(output), "cache_dir": str(cache),
                                "command": [sys.executable, "-c", code], "timeout_seconds": 5,
                                "env": {"OUT": str(output), "CACHE": str(cache),
                                        "SECRET": "unguessable-private-value"}})
        manifest = self.root / "manifest.json"
        manifest.write_text(json.dumps({"schema": "capcov-qualification-measurement-v1", "samples": samples}))
        command = [sys.executable, str(SCRIPT), str(manifest), "--report", str(report),
                   "--logs", str(logs), "--lock", str(self.root / "heavy.lock"),
                   "--command-timeout", "10"]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result, json.loads(report.read_text()), logs

    def test_cold_warm_report_compares_identities_and_keeps_private_tails(self) -> None:
        result, report, logs = self._run()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(report["sample_count"], 2)
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["samples"][0]["cache_state"], "cold")
        self.assertEqual(report["samples"][1]["cache_state"], "warm")
        self.assertTrue(report["samples"][0]["lock_acquired"])
        self.assertGreaterEqual(report["samples"][0]["exec_seconds"], 0)
        self.assertTrue(report["cold_warm_comparisons"][0]["output_identity_matches"])
        serialized = json.dumps(report)
        self.assertNotIn("unguessable-private-value", serialized)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn(sys.executable, serialized)
        self.assertNotIn("command", report["samples"][0])
        self.assertEqual(report["samples"][0]["resolved_toolchain_binaries"]["python"]["bytes"],
                         Path(sys.executable).stat().st_size)
        self.assertEqual(report["samples"][0]["resolved_toolchain_binaries"]["python"]["sha256"],
                         hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest())
        tail = (logs / "cold.stdout.tail").read_text()
        self.assertNotIn("unguessable-private-value", tail)
        self.assertNotIn("/tmp/private-example", tail)
        self.assertEqual((logs / "cold.stdout.tail").stat().st_mode & 0o777, 0o600)
        self.assertEqual(report["samples"][0]["native_cache_before"]["files"], 0)
        self.assertEqual(report["samples"][1]["native_cache_before"]["files"], 1)

    def test_incomplete_output_hashes_never_claim_identity_match(self) -> None:
        sys.path.insert(0, str(SCRIPT.parent))
        try:
            from measure_qualification import _comparisons, _source_identity
        finally:
            sys.path.pop(0)
        pair = [{"comparison_group": "large", "sample_kind": kind,
                 "output_identity": {"sha256": None}} for kind in ("cold", "warm")]
        self.assertFalse(_comparisons(pair)[0]["output_identity_matches"])
        before = _source_identity(str(self.source))
        (self.source / "untracked.txt").write_text("included in the source identity\n")
        after = _source_identity(str(self.source))
        self.assertTrue(after["dirty"])
        self.assertEqual(after["untracked_files"], 1)
        self.assertNotEqual(before["working_tree_sha256"], after["working_tree_sha256"])

    def test_timeout_kills_grandchildren_in_owned_process_group(self) -> None:
        marker = self.root / "grandchild-survived"
        child = (
            "import pathlib,signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); "
            "time.sleep(1.5); pathlib.Path(" + repr(str(marker)) + ").write_text('alive')"
        )
        parent = (
            "import subprocess,sys,time; subprocess.Popen([sys.executable, '-c', "
            + repr(child) + "]); time.sleep(10)"
        )
        manifest = self.root / "timeout-manifest.json"
        report_path = self.root / "timeout-report.json"
        logs = self.root / "timeout-logs"
        manifest.write_text(json.dumps({
            "schema": "capcov-qualification-measurement-v1",
            "samples": [{"id": "timeout", "phase": "process-cleanup",
                         "source_root": str(self.source), "timeout_seconds": 1,
                         "toolchain_binaries": {"python": sys.executable},
                         "command": [sys.executable, "-c", parent]}],
        }))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(manifest), "--report", str(report_path),
             "--logs", str(logs), "--lock", str(self.root / "timeout.lock"),
             "--command-timeout", "5"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        report = json.loads(report_path.read_text())
        self.assertTrue(report["samples"][0]["timed_out"])
        time.sleep(1.7)
        self.assertFalse(marker.exists(), "timed-out sample left a grandchild running")

    def test_native_shake_zero_target_pass_is_refused(self) -> None:
        result, report, _ = self._run(all_skip=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["samples"][0]["required_go_target"]["ran"])


if __name__ == "__main__":
    unittest.main()
