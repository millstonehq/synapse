import assert from "node:assert/strict";
import fs from "node:fs";
import { spawnSync } from "node:child_process";

const index = process.argv.indexOf("--task");
const task = index >= 0 ? process.argv[index + 1] : undefined;
const dryRun = process.argv.includes("--dry-run");
assert.ok(task, "--task is required");
const expected = new Set(["semantic-contract", "datalog-corpus", "python-reference", "souffle-kernel", "kernel-closure", "differential-closure", "kernel-closure-integrate", "scip-toolchain", "scip-fact-export", "static-rule-pack", "scip-datalog-differential", "datalog-certificates", "scip-target-go-pilot", "datalog-target-go", "datalog-evaluation"]);
assert.ok(expected.has(task), `unknown Datalog gate task: ${task}`);
assert.ok(fs.existsSync(".pi/workflows/capcov-experiment.json"), "workflow manifest is present");
const artifacts = {
  "semantic-contract": ["packages/capabilities/src/capcov/claims/ir.py"],
  "datalog-corpus": ["packages/capabilities/tests/claim_semantics/corpus"],
  "python-reference": ["packages/capabilities/src/capcov/claims/evaluator.py"],
  "souffle-kernel": ["packages/capabilities/src/capcov/claims/souffle.py"],
  "kernel-closure": ["packages/capabilities/src/capcov/claims/evaluator.py"],
  "differential-closure": ["packages/capabilities/src/capcov/claims/shrinker.py"],
  "kernel-closure-integrate": ["packages/capabilities/src/capcov/claims/differential.py"],
  "scip-toolchain": ["packages/capabilities/tests/fixtures/scip_go_app_index.json", "tests/scip/canonicalize.jq"],
  "scip-fact-export": ["packages/capabilities/src/capcov/claims/static/scip_facts.py"],
  "static-rule-pack": ["packages/capabilities/experiments/claim-semantics/static"],
  "scip-datalog-differential": ["packages/capabilities/src/capcov/claims/static/certificate.py"],
  "datalog-certificates": ["packages/capabilities/src/capcov/claims/certificates.py"],
  "scip-target-go-pilot": ["packages/capabilities/tests/claim_semantics/target_go"],
  "datalog-target-go": ["packages/capabilities/tests/claim_semantics"],
  "datalog-evaluation": ["packages/capabilities/tests/claim_semantics"],
};
if (!dryRun) assert.ok(artifacts[task].some((candidate) => fs.existsSync(candidate)), `task-specific Datalog artifact is missing for ${task}`);
if (task === "souffle-kernel") {
  const result = spawnSync("souffle", ["--version"], { encoding: "utf8" });
  assert.equal(result.status, 0, `real Souffle is required: ${result.stderr || result.stdout}`);
}
if (task === "datalog-target-go" || task === "scip-target-go-pilot") assert.ok(process.env.CAPCOV_GO_FIXTURE_ROOT, "CAPCOV_GO_FIXTURE_ROOT is required");
if (!dryRun && ["scip-toolchain", "scip-fact-export", "scip-datalog-differential", "scip-target-go-pilot"].includes(task)) {
  for (const tool of ["scip", "scip-go"]) {
    const result = spawnSync(tool, ["--version"], { encoding: "utf8" });
    assert.ok(result.status === 0 || (result.stdout || result.stderr || "").length > 0, `real ${tool} is required: ${result.error?.message || result.stderr || ""}`);
  }
}
console.log(`datalog runtime gate passed: ${task}`);
