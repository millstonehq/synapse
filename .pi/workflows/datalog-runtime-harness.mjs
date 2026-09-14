import assert from "node:assert/strict";
import fs from "node:fs";
import { spawnSync } from "node:child_process";

const index = process.argv.indexOf("--task");
const task = index >= 0 ? process.argv[index + 1] : undefined;
const dryRun = process.argv.includes("--dry-run");
assert.ok(task, "--task is required");
const expected = new Set(["semantic-contract", "datalog-corpus", "python-reference", "souffle-kernel", "datalog-differential", "datalog-certificates", "datalog-target-go", "datalog-evaluation"]);
assert.ok(expected.has(task), `unknown Datalog gate task: ${task}`);
assert.ok(fs.existsSync(".pi/workflows/capcov-experiment.json"), "workflow manifest is present");
const artifacts = {
  "semantic-contract": ["packages/capabilities/src/capcov/claims"],
  "datalog-corpus": ["packages/capabilities/tests/claim_semantics", "packages/capabilities/experiments/claim-semantics"],
  "python-reference": ["packages/capabilities/src/capcov/claims/python"],
  "souffle-kernel": ["packages/capabilities/experiments/claim-semantics/souffle"],
  "datalog-differential": ["packages/capabilities/tests/claim_semantics", "packages/capabilities/experiments/claim-semantics"],
  "datalog-certificates": ["packages/capabilities/src/capcov/claims", "packages/capabilities/tests/claim_semantics"],
  "datalog-target-go": ["packages/capabilities/experiments/claim-semantics"],
  "datalog-evaluation": ["packages/capabilities/experiments/claim-semantics"],
};
if (!dryRun) assert.ok(artifacts[task].some((candidate) => fs.existsSync(candidate)), `task-specific Datalog artifact is missing for ${task}`);
if (task === "souffle-kernel") {
  const result = spawnSync("souffle", ["--version"], { encoding: "utf8" });
  assert.equal(result.status, 0, `real Souffle is required: ${result.stderr || result.stdout}`);
}
if (task === "datalog-target-go") assert.ok(process.env.CAPCOV_GO_FIXTURE_ROOT, "CAPCOV_GO_FIXTURE_ROOT is required");
console.log(`datalog runtime gate passed: ${task}`);
