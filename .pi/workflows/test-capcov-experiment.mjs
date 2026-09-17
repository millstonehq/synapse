import assert from "node:assert/strict";
import fs from "node:fs";

const config = JSON.parse(fs.readFileSync(new URL("./capcov-experiment.json", import.meta.url), "utf8"));
const byId = new Map(config.tasks.map((task) => [task.id, task]));
const waveById = new Map(config.waves.map((wave) => [wave.id, wave]));
const modern = ["semantic-contract", "datalog-corpus", "python-reference", "souffle-kernel", "kernel-closure", "differential-closure", "kernel-closure-finalize", "scip-toolchain", "scip-fact-export", "static-rule-pack", "scip-datalog-differential", "datalog-certificates", "scip-target-go-pilot", "datalog-target-go", "datalog-evaluation"];

assert.deepEqual(modern.map((id) => byId.get(id)?.id), modern);
for (const id of modern) assert.ok(waveById.has(byId.get(id).wave), `${id} has a declared wave`);
for (const task of config.tasks.filter((task) => task.role === "parallel")) {
  assert.ok(task.worktree, `${task.id} has an isolated worktree`);
  assert.ok(!task.writeSet.some((pattern) => pattern.includes("EXPERIMENT-PLAN.md")), `${task.id} does not own the reducer plan`);
}
const kernel = config.tasks.filter((task) => task.wave === "datalog-kernel-closure");
assert.deepEqual(kernel.find((task) => task.role === "reducer")?.dependsOn.sort(), ["differential-closure", "kernel-closure"]);
assert.ok(!byId.has("datalog-differential") && !byId.has("kernel-closure-integrate"), "exhausted reducers are retired, not reset again");
const scip = config.tasks.filter((task) => task.wave === "scip-datalog");
assert.deepEqual(scip.find((task) => task.role === "reducer")?.dependsOn.sort(), ["scip-fact-export", "static-rule-pack"]);
assert.equal(byId.get("scip-toolchain").dependsOn[0], "kernel-closure-finalize");
assert.equal(byId.get("scip-fact-export").dependsOn[0], "scip-toolchain", "fan-out workers cut worktrees after the toolchain checkpoint");
assert.equal(byId.get("datalog-certificates").dependsOn[0], "scip-datalog-differential", "certificates replay static proofs");
assert.ok(byId.get("scip-target-go-pilot").mayBlock && byId.get("scip-target-go-pilot").externalPrerequisites.includes("CAPCOV_GO_FIXTURE_ROOT"));
assert.equal(config.mismatchRepairCap, 3);
assert.equal(config.legacyTaskAliases.toolchain, "semantic-contract");
console.log(`workflow config ok: ${modern.length} Datalog tasks, ${kernel.filter((task) => task.role === "parallel").length} parallel kernels, ${scip.filter((task) => task.role === "parallel").length} parallel SCIP workers`);
