import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from capcov.artifacts import tree_sha256
from capcov.outcomes import execute, provenance, reconcile, validate
from capcov.probes import outcomes_probe


class OutcomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "src/app.py").write_text("value = 1\n")
        (self.root / "tests").mkdir()
        (self.root / "tests/test_app.py").write_text("def test_owner(): pass\n")
        self.inventory = {
            "schema_version": 1,
            "kind": "capabilities",
            "surfaces": [{"id": "POST /cancel"}],
            "derived_from": {
                "artifact": "src",
                "artifact_sha256": tree_sha256(self.root / "src")[0],
            },
        }
        self.test = "tests/test_app.py::test_owner"
        self.mapping = {
            "version": 1,
            "scope": "cancel",
            "environment": "local sqlite",
            "limitations": ["no external delivery"],
            "inputs": ["src", "tests"],
            "outcomes": [
                {
                    "id": "ownership",
                    "capability": "cancel",
                    "description": "Other owners cannot cancel",
                    "source_refs": ["POST /cancel"],
                    "policy": "required",
                    "tests": [self.test],
                }
            ],
        }
        self.current = provenance(self.root, self.mapping, self.inventory)
        self.run = {
            "version": 1,
            "provenance": self.current,
            "finished": True,
            "exit_code": 0,
            "errors": [],
            "tests": {self.test: "passed"},
        }

    def coverage(self):
        return reconcile(
            self.mapping,
            self.inventory,
            self.run,
            provenance(self.root, self.mapping, self.inventory),
        )

    def test_exact_case_demonstrates_obligation(self):
        self.assertTrue(self.coverage()["complete"])

    def test_unrelated_pass_does_not_fill_missing_case(self):
        self.run["tests"] = {"tests/test_other.py::test_ok": "passed"}
        self.assertEqual(self.coverage()["rows"][0]["status"], "missing")
        self.assertFalse(self.coverage()["complete"])

    def test_failure_is_not_missing(self):
        self.run["tests"][self.test] = "failed"
        self.run["exit_code"] = 1
        self.assertEqual(self.coverage()["rows"][0]["status"], "failed")

    def test_all_mapped_cases_required(self):
        self.mapping["outcomes"][0]["tests"].append("tests/test_app.py::test_second")
        self.run["provenance"] = provenance(self.root, self.mapping, self.inventory)
        self.assertEqual(self.coverage()["rows"][0]["status"], "missing")

    def test_policy_remains_unresolved_despite_pass(self):
        self.mapping["outcomes"][0].update(
            policy="unresolved", reason="owner decision needed"
        )
        self.run["provenance"] = provenance(self.root, self.mapping, self.inventory)
        self.assertEqual(self.coverage()["rows"][0]["status"], "unresolved")
        self.assertFalse(self.coverage()["complete"])

    def test_changed_tests_reject_old_evidence(self):
        (self.root / "tests/test_app.py").write_text("def test_owner(): assert False\n")
        with self.assertRaisesRegex(ValueError, "current map"):
            self.coverage()

    def test_changed_source_rejects_inventory(self):
        (self.root / "src/app.py").write_text("value = 2\n")
        with self.assertRaisesRegex(ValueError, "stale"):
            self.coverage()

    def test_unknown_surface_is_rejected(self):
        self.mapping["outcomes"][0]["source_refs"] = ["POST /invented"]
        with self.assertRaisesRegex(ValueError, "unknown source"):
            validate(self.mapping, self.inventory)

    def test_duplicate_or_empty_outcomes_rejected(self):
        self.mapping["outcomes"] *= 2
        with self.assertRaises(ValueError):
            validate(self.mapping, self.inventory)
        self.mapping["outcomes"] = []
        with self.assertRaises(ValueError):
            validate(self.mapping, self.inventory)

    def test_unfinished_or_collection_error_cannot_complete(self):
        self.run["finished"] = False
        self.assertEqual(self.coverage()["rows"][0]["status"], "inconclusive")
        self.run["finished"] = True
        self.run["errors"] = ["collection failure"]
        self.assertFalse(self.coverage()["complete"])

    def test_fresh_nonce_required(self):
        def runner(command, **kwargs):
            Path(kwargs["env"]["CAPCOV_OUTCOME_OUT"]).write_text(
                json.dumps(
                    {"nonce": "old", "finished": True, "tests": {}, "errors": []}
                )
            )
            return SimpleNamespace(returncode=0)

        with (
            patch("capcov.outcomes.subprocess.run", runner),
            self.assertRaisesRegex(ValueError, "nonce"),
        ):
            execute(self.root, self.mapping, self.inventory, "python", [], 5)

    def test_source_change_during_execution_rejected(self):
        def runner(command, **kwargs):
            (self.root / "src/app.py").write_text("value = 3\n")
            return SimpleNamespace(returncode=0)

        with (
            patch("capcov.outcomes.subprocess.run", runner),
            self.assertRaises(ValueError),
        ):
            execute(self.root, self.mapping, self.inventory, "python", [], 5)

    def test_successful_command_without_plugin_is_not_evidence(self):
        with patch(
            "capcov.outcomes.subprocess.run", return_value=SimpleNamespace(returncode=0)
        ):
            run = execute(self.root, self.mapping, self.inventory, "python", [], 5)
        self.assertFalse(
            reconcile(self.mapping, self.inventory, run, self.current)["complete"]
        )

    def test_pytest_requires_all_phases_and_rejects_xfail(self):
        cases = {
            "ok": ("passed", "passed", "passed"),
            "teardown-fails": ("passed", "passed", "failed"),
            "skip": ("skipped",),
            "xfail": ("passed", "skipped", "passed"),
        }
        outcomes_probe.pytest_configure(None)
        for node, values in cases.items():
            for phase, result in zip(("setup", "call", "teardown"), values):
                report = SimpleNamespace(nodeid=node, when=phase, outcome=result)
                if node == "xfail" and phase == "call":
                    report.wasxfail = "known bug"
                outcomes_probe.pytest_runtest_logreport(report)
        out = self.root / "plugin.json"
        with patch.dict(
            "os.environ",
            {"CAPCOV_OUTCOME_OUT": str(out), "CAPCOV_OUTCOME_NONCE": "fresh"},
        ):
            outcomes_probe.pytest_sessionfinish(None, 1)
        self.assertEqual(
            json.loads(out.read_text())["tests"],
            {
                "ok": "passed",
                "teardown-fails": "failed",
                "skip": "inconclusive",
                "xfail": "inconclusive",
            },
        )
