from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capcov.flows.cli import main
from capcov.flows.discovery import discover
from capcov.flows.model import digest, plan, reconcile


def fixture() -> tuple[dict, dict]:
    inventory = {"obligations": [{"id": "read"}, {"id": "edit"}]}
    model = {
        "version": 1,
        "scope": "fixture",
        "facts": ["signed-in", "edited"],
        "initial": [],
        "transitions": [],
    }
    for name, requires, adds in (
        ("login", [], ["signed-in"]),
        ("edit", ["signed-in"], ["edited"]),
        ("history", ["edited"], []),
    ):
        model["transitions"].append(
            {
                "id": name,
                "requires": requires,
                "adds": adds,
                "actor": "operator",
                "outcome": name,
                "evidence": [{"file": "fixture.py", "line": 1}],
                "obligations": ["edit" if name == "edit" else "read"],
                "bindings": {
                    "browser": {
                        "commands": [
                            {"op": "assert", "id": "outcome", "selector": "body", "text": name},
                        ]
                    }
                },
            }
        )
    return inventory, model


def evidence(inventory: dict, execution_plan: dict) -> dict:
    return {
        "status": "passed",
        "assurance": "test-fixture",
        "plan_sha256": digest(execution_plan),
        "inventory_sha256": digest(inventory),
        "scenarios": [
            {
                "id": s["id"],
                "status": "passed",
                "assertions": [
                    f"{i}:{step['transition']}:{c['id']}"
                    for i, step in enumerate(s["steps"])
                    for c in step["commands"]
                    if c["op"] == "assert"
                ],
            }
            for s in execution_plan["scenarios"]
        ],
    }


class FlowTests(unittest.TestCase):
    def test_every_declared_outcome_requires_its_own_evidence(self) -> None:
        inventory, model = fixture()
        inventory["obligations"][0]["outcomes"] = ["allowed", "denied"]
        execution_plan = plan(model, "browser")
        result = reconcile(inventory, model, execution_plan, evidence(inventory, execution_plan))
        self.assertFalse(result["complete"])
        model["transitions"][0]["covers_outcomes"] = {"read": ["allowed"]}
        execution_plan = plan(model, "browser")
        self.assertFalse(
            reconcile(inventory, model, execution_plan, evidence(inventory, execution_plan))[
                "complete"
            ]
        )
        model["transitions"][2]["covers_outcomes"] = {"read": ["denied"]}
        execution_plan = plan(model, "browser")
        self.assertTrue(
            reconcile(inventory, model, execution_plan, evidence(inventory, execution_plan))[
                "complete"
            ]
        )

    def test_mapping_an_unknown_boundary_to_an_assertion_cannot_close_it(self) -> None:
        inventory, model = fixture()
        inventory["obligations"][0]["kind"] = "unresolved"
        execution_plan = plan(model, "browser")
        self.assertFalse(
            reconcile(inventory, model, execution_plan, evidence(inventory, execution_plan))[
                "complete"
            ]
        )

    def test_http_claim_requires_observation_in_the_same_step(self) -> None:
        inventory, model = fixture()
        inventory["obligations"].append({"id": "http:POST /edit", "kind": "surface"})
        model["transitions"][1]["obligations"].append("http:POST /edit")
        execution_plan = plan(model, "browser")
        run = evidence(inventory, execution_plan)
        self.assertFalse(reconcile(inventory, model, execution_plan, run)["complete"])
        for scenario, result in zip(execution_plan["scenarios"], run["scenarios"], strict=True):
            result["observed_requests"] = [
                {"step": f"{i}:{step['transition']}", "surface": "http:POST /edit"}
                for i, step in enumerate(scenario["steps"])
                if step["transition"] == "edit"
            ]
        self.assertTrue(reconcile(inventory, model, execution_plan, run)["complete"])
        run["mounted_surfaces"] = ["http:POST /edit", "http:DELETE /new"]
        self.assertIn(
            "runtime-only surface: http:DELETE /new",
            reconcile(inventory, model, execution_plan, run)["failures"],
        )

    def test_baseline_never_hides_new_or_obsolete_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            coverage, baseline = root / "coverage.json", root / "baseline.json"
            coverage.write_text(json.dumps({"complete": False, "failures": ["unmapped: old"]}))
            baseline.write_text(json.dumps({"unmapped: old": "Existing screen; awaiting a flow"}))
            args = ["gate", str(coverage), "--baseline", str(baseline)]
            with patch("builtins.print"):
                self.assertEqual(main(args), 0)
                coverage.write_text(
                    json.dumps(
                        {
                            "complete": False,
                            "failures": [
                                "unmapped: old",
                                "unmapped: new",
                            ],
                        }
                    )
                )
                self.assertEqual(main(args), 1)
                coverage.write_text(json.dumps({"complete": True, "failures": []}))
                self.assertEqual(main(args), 1)

    def test_run_rejects_success_without_fresh_evidence(self) -> None:
        inventory, model = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / f"{name}.json" for name in ("inventory", "plan", "out")}
            paths["inventory"].write_text(json.dumps(inventory))
            paths["plan"].write_text(json.dumps(plan(model, "browser")))
            # Even an apparently successful previous output must not be read.
            paths["out"].write_text(json.dumps({"status": "passed"}))
            args = [
                "run",
                str(paths["plan"]),
                "--inventory",
                str(paths["inventory"]),
                "--config",
                "unused.json",
                "--out",
                str(paths["out"]),
                "--",
                "runner",
            ]
            with (
                patch("capcov.flows.cli.discover", return_value=inventory),
                patch("capcov.flows.cli.subprocess.run") as command,
                patch("builtins.print"),
            ):
                command.return_value.returncode = 0
                self.assertEqual(main(args), 1)
                self.assertFalse(paths["out"].exists())

    def test_empty_inventory_is_not_complete(self) -> None:
        _, model = fixture()
        with self.assertRaisesRegex(ValueError, "empty inventory"):
            reconcile({"obligations": []}, model, plan(model, "browser"), None)

    def test_duplicate_scenarios_are_rejected(self) -> None:
        inventory, model = fixture()
        execution_plan = plan(model, "browser")
        run = evidence(inventory, execution_plan)
        run["scenarios"].append(copy.deepcopy(run["scenarios"][0]))
        self.assertFalse(reconcile(inventory, model, execution_plan, run)["complete"])

    def test_history_requires_login_and_edit_in_order(self) -> None:
        _, model = fixture()
        result = plan(model, "browser")
        history = next(s for s in result["scenarios"] if s["id"] == "history")
        self.assertEqual([s["transition"] for s in history["steps"]], ["login", "edit", "history"])

    def test_missing_dependency_is_blocked_not_skipped(self) -> None:
        _, model = fixture()
        model["transitions"][0]["bindings"] = {}
        result = plan(model, "browser")
        self.assertEqual(len(result["blocked"]), 3)
        self.assertEqual(result["scenarios"], [])

    def test_forbidden_state_forces_another_path(self) -> None:
        _, model = fixture()
        model["transitions"][2]["forbids"] = ["signed-in"]
        self.assertIn("history", [b["transition"] for b in plan(model, "browser")["blocked"]])
        model["transitions"][1]["removes"] = ["signed-in"]
        self.assertEqual(plan(model, "browser")["blocked"], [])

    def test_state_explosion_fails_loudly(self) -> None:
        _, model = fixture()
        with self.assertRaisesRegex(ValueError, "budget"):
            plan(model, "browser", max_states=1)

    def test_action_without_assertion_is_not_a_test(self) -> None:
        _, model = fixture()
        model["transitions"][0]["bindings"]["browser"]["commands"] = [{"op": "goto", "path": "/"}]
        with self.assertRaisesRegex(ValueError, "assertion"):
            plan(model, "browser")

    def test_duplicate_transition_is_rejected(self) -> None:
        _, model = fixture()
        model["transitions"].append(copy.deepcopy(model["transitions"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            plan(model, "browser")

    def test_complete_requires_exact_outcome_evidence(self) -> None:
        inventory, model = fixture()
        execution_plan = plan(model, "browser")
        run = evidence(inventory, execution_plan)
        self.assertTrue(reconcile(inventory, model, execution_plan, run)["complete"])
        run["scenarios"][0]["assertions"] = []
        self.assertFalse(reconcile(inventory, model, execution_plan, run)["complete"])

    def test_new_capability_cannot_hide_behind_existing_entity(self) -> None:
        inventory, model = fixture()
        execution_plan = plan(model, "browser")
        inventory["obligations"].append({"id": "delete"})
        result = reconcile(inventory, model, execution_plan, evidence(inventory, execution_plan))
        self.assertIn("unmapped: delete", result["failures"])

    def test_no_execution_means_no_coverage(self) -> None:
        inventory, model = fixture()
        result = reconcile(inventory, model, plan(model, "browser"), None)
        self.assertEqual(result["summary"]["covered"], 0)

    def test_stale_model_inventory_or_plan_cannot_pass(self) -> None:
        inventory, model = fixture()
        execution_plan = plan(model, "browser")
        run = evidence(inventory, execution_plan)
        for altered in ("inventory", "model", "plan"):
            i, m, p = copy.deepcopy((inventory, model, execution_plan))
            if altered == "inventory":
                i["obligations"].append({"id": "new"})
            elif altered == "model":
                m["scope"] = "changed"
            else:
                p["scenarios"].pop()
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                reconcile(i, m, p, run)

    def test_failed_or_skipped_run_cannot_cover_anything(self) -> None:
        inventory, model = fixture()
        execution_plan = plan(model, "browser")
        run = evidence(inventory, execution_plan)
        run["status"] = "failed"
        self.assertEqual(reconcile(inventory, model, execution_plan, run)["summary"]["covered"], 0)
        run["status"] = "passed"
        run["scenarios"].pop()
        self.assertFalse(reconcile(inventory, model, execution_plan, run)["complete"])

    def test_discovery_retains_branches_exceptions_and_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            route = root / "routes.py"
            route.write_text(
                '@router.post("/edit")\ndef edit():\n'
                "    if authenticated:\n        return save()\n"
                "    try:\n        reject()\n    except Error:\n        return False\n"
            )
            config = root / "discovery.json"
            config.write_text(
                json.dumps(
                    {
                        "scope": "fixture",
                        "root": ".",
                        "adapters": [
                            {"kind": "python-routes", "files": ["routes.py"], "prefix": "/portal"},
                        ],
                    }
                )
            )
            inventory = discover(config)
            kinds = [o["kind"] for o in inventory["obligations"]]
            self.assertEqual(kinds.count("branch-candidate"), 2)
            self.assertEqual(kinds.count("exception-candidate"), 1)
            self.assertIn("unresolved", kinds)
            route.write_text('@router.get("/new")\ndef new():\n    return 1\n')
            self.assertNotEqual(inventory, discover(config))

    def test_unknown_adapter_does_not_produce_empty_green(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "discovery.json"
            config.write_text(json.dumps({"root": ".", "adapters": [{"kind": "magic"}]}))
            with self.assertRaisesRegex(ValueError, "unsupported"):
                discover(config)
