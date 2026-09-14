import assert from "node:assert/strict";
import fs from "node:fs";

const config = JSON.parse(fs.readFileSync(new URL("./capcov-experiment.json", import.meta.url), "utf8"));
const byId = new Map(config.tasks.map((task) => [task.id, task]));
const waveById = new Map(config.waves.map((wave) => [wave.id, wave]));
const modern = ["semantic-contract", "datalog-corpus", "python-reference", "souffle-kernel", "datalog-differential", "datalog-certificates", "datalog-target-go", "datalog-evaluation"];

assert.deepEqual(modern.map((id) => byId.get(id)?.id), modern);
for (const id of modern) assert.ok(waveById.has(byId.get(id).wave), `${id} has a declared wave`);
for (const task of config.tasks.filter((task) => task.role === "parallel")) {
  assert.ok(task.worktree, `${task.id} has an isolated worktree`);
  assert.ok(!task.writeSet.some((pattern) => pattern.includes("EXPERIMENT-PLAN.md")), `${task.id} does not own the reducer plan`);
}
const kernel = config.tasks.filter((task) => task.wave === "datalog-kernels");
assert.deepEqual(kernel.find((task) => task.role === "reducer")?.dependsOn.sort(), ["python-reference", "souffle-kernel"]);
assert.equal(config.mismatchRepairCap, 3);
assert.equal(config.legacyTaskAliases.toolchain, "semantic-contract");
console.log(`workflow config ok: ${modern.length} Datalog tasks, ${kernel.filter((task) => task.role === "parallel").length} parallel kernels`);
