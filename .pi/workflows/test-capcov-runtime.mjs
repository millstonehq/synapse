import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";

const root = fs.mkdtempSync(path.join(os.tmpdir(), "capcov-workflow-"));
const run = (args, cwd = root) => execFileSync("git", args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
run(["init", "-q"]);
run(["config", "user.email", "test@example.invalid"]);
run(["config", "user.name", "capcov-test"]);
fs.writeFileSync(path.join(root, "base.txt"), "base\n");
run(["add", "base.txt"]);
run(["commit", "-qm", "base"]);
const worker = fs.mkdtempSync(path.join(os.tmpdir(), "capcov-worker-"));
fs.rmSync(worker, { recursive: true, force: true });
run(["worktree", "add", "--detach", worker, "HEAD"]);
fs.writeFileSync(path.join(worker, "kernel.txt"), "souffle\n");
let patch = "";
try { patch = run(["diff", "--binary", "HEAD"], worker); } catch (error) { patch = error.stdout ?? ""; }
try { patch += run(["diff", "--no-index", "--binary", "/dev/null", "kernel.txt"], worker); } catch (error) { patch += error.stdout ?? ""; }
assert.match(patch, /kernel\.txt/);
assert.notEqual(run(["status", "--porcelain"], worker).trim(), "", "worker change is visible in isolated worktree");
assert.equal(run(["status", "--porcelain"], root).trim(), "", "root remains clean before reducer fan-in");
run(["worktree", "remove", "--force", worker]);
assert.equal(fs.existsSync(worker), false, "worker worktree is removed after capture");
const harness = execFileSync("node", [".pi/workflows/datalog-runtime-harness.mjs", "--task", "semantic-contract", "--dry-run"], { cwd: process.cwd(), encoding: "utf8" });
assert.match(harness, /semantic-contract/);
const source = fs.readFileSync(new URL("../extensions/capcov-experiment.ts", import.meta.url), "utf8");
for (const marker of ["task-fanout-completed", "fanout-patch-applied", "wave-checkpoint", "latestSmoke", "wave-repair", "manifest-checkpoint", "human-checkpoint"]) assert.match(source, new RegExp(marker));
assert.match(source, /function nextTask[\s\S]*return undefined;/);
const config = JSON.parse(fs.readFileSync(new URL("./capcov-experiment.json", import.meta.url), "utf8"));
const modern = config.tasks.filter((task) => !config.legacyTaskIds.includes(task.id));
assert.ok(modern.every((task) => task.gates.every((gate) => gate.failureKind)), "modern gates classify failures in the manifest");
assert.ok(modern.every((task) => task.gates.every((gate) => gate.command.slice(0, 2).join(" ") === "nix develop")), "modern gates use the pinned Nix environment");
assert.match(config.tasks.find((task) => task.id === "souffle-kernel").gates[0].command.join(" "), /command -v souffle/);
assert.match(config.tasks.find((task) => task.id === "kernel-closure-finalize").gates[0].command.join(" "), /test_differential/);
const scipDifferential = config.tasks.find((task) => task.id === "scip-datalog-differential");
assert.equal(scipDifferential.gates[0].failureKind, "differential-mismatch");
assert.match(scipDifferential.gates[0].command.join(" "), /test_differential_static/);
assert.match(config.tasks.find((task) => task.id === "scip-toolchain").gates.map((gate) => gate.command.join(" ")).join("\n"), /scip-go/);
assert.match(config.tasks.find((task) => task.id === "scip-target-go-pilot").gates[0].command.join(" "), /CAPCOV_GO_FIXTURE_ROOT/);
for (const id of ["souffle-kernel", "kernel-closure", "differential-closure", "kernel-closure-finalize", "scip-datalog-differential", "scip-fact-export", "scip-target-go-pilot"]) {
  const joined = config.tasks.find((task) => task.id === id).gates.map((gate) => gate.command.join(" ")).join("\n");
  assert.match(joined, /skipped/, `${id} gates reject skipped tests instead of passing on them`);
}
assert.equal(config.legacyTaskAliases["reference-evaluator"], undefined, "legacy evidence cannot satisfy the dual-kernel wave");
assert.equal(config.tasks.filter((task) => !config.legacyTaskIds.includes(task.id) && task.legacy).length, 0, "modern tasks are not legacy");
assert.ok(config.tasks.filter((task) => task.role === "parallel").every((task) => task.worktree), "parallel failure/retry has isolated worktree metadata");
console.log("runtime workflow seam ok: worktree, patch capture, removal, fan-in, checkpoint, smoke and repair paths");
