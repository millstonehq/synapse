# Synapse capabilities

Standalone capability engine, developed and released from the Synapse monorepo.

The canonical implementation lives in `packages/capabilities` in
[Synapse](https://github.com/millstonehq/synapse). Consumers pin a commit
or release and retain only their models, recipes, adapters specific to their own
application, and evidence. Do not vendor another independently edited engine.

Optional, standalone capability discovery and model-based testing engine. The
Python import package and `capcov` command preserve the existing consumer
interface; the distribution is `synapse-capabilities`.

The engine owns discovery, finite fact-state planning, evidence reconciliation,
coverage gates, and reports. Consumer repositories own reviewed behavior models,
source scope, identities, startup/reset recipes, runtime fixtures, and target
bindings. It works without a Synapse vault or a hosted service.

## Install and test

Requires Python 3.12 or newer. From `packages/capabilities`:

```sh
uv tool install .
capcov --help
capcov flows --help

PYTHONPATH=src uv run --python 3.12 python -m unittest discover -s tests -t .
```

Both `capcov` and `synapse-capabilities` invoke the same entry point. Static
discovery, planning, reconciliation, and gates use the Python standard library.
The optional `probe-python` extra supplies SQLAlchemy/pytest integration; browser
execution uses the consumer's runner and browser installation.

## Two evidence pipelines

Entity coverage compares static discovery with runtime observations:

```sh
capcov discover --target . --out capabilities.json
capcov observe --target . --out observed.json -- pytest -q
capcov reconcile capabilities.json observed.json --out coverage.json
capcov gate coverage.json --exemptions capcov.exemptions.toml
capcov report coverage.json
```

Flow coverage retains the source obligation denominator and checks observed
outcomes against a reviewed behavior model:

```sh
capcov flows discover discovery.json --out inventory.json
capcov flows catalog inventory.json --out catalog.json --report catalog.md
capcov flows plan model.json --target local --out plan.json
capcov flows run plan.json --inventory inventory.json --config discovery.json --out run.json -- node runner.mjs
capcov flows coverage inventory.json model.json plan.json --run run.json --out coverage.json
capcov flows report coverage.json plan.json --out report.md
capcov flows gate coverage.json
```

Missing adapters, unconfirmed meaning, absent bindings, unreachable states,
unmapped obligations, and insufficient evidence remain gaps. A baseline can
permit reviewed gaps without calling them covered. A passing browser navigation
does not prove persistence, authorization, external delivery, or product parity.

## Current support

- Python/FastAPI/SQLAlchemy entity discovery and runtime probes.
- Python route source obligations and Zoho Creator export discovery.
- Required/forbidden fact-state planning with explicit blocked transitions.
- Consumer execution commands with fresh run nonces and source/model/plan hashes.
- Exact scenario/assertion reconciliation, per-step HTTP evidence, and gap gates.

Go/React discovery, a general-purpose browser exploration agent, and automatic
semantic inference are not implemented. Synapse documentation validation does
not run this engine. Optional document projection and `synapse capabilities`
CLI integration are follow-up work.

## Development and releases

The existing Synapse CI workflow tests this package, builds its wheel and source
distribution, and verifies installation from the wheel. No npm workspace wrapper
or Node installation is required to use the engine. Package versions are
independent of the npm packages and `scripts/bump-version.js`.

To release, update `version` in `pyproject.toml` and `src/capcov/__init__.py`,
refresh `uv.lock`, and merge the reviewed change. Push a tag
`capabilities-v<version>` at that commit. Synapse CI checks the tag against the
package version and publishes the tested wheel and source distribution as GitHub
release assets. Tags are immutable; use a new version for a correction. PyPI
publishing is not configured.

Consumers can pin a public Git revision with uv:

```toml
[tool.uv.sources]
synapse-capabilities = { git = "https://github.com/millstonehq/synapse.git", rev = "<full-commit-sha>", subdirectory = "packages/capabilities" }
```

Keep engine changes and regression tests here. Application models, source exports,
identities, startup recipes, and execution evidence belong in the consuming
repository. Conformance tests use synthetic fixtures; do not add private source
or real credentials. Run the unittest suite and build/install checks before a PR.
The engine is distributed under the repository's MIT license, included in both
Python distribution formats.

## Scoped outcome coverage with pytest

Use `capcov outcomes` to keep business outcomes separate from entity reachability.
The consumer owns a JSON map of stable capability/outcome IDs to **exact pytest
node IDs**, including parameter IDs. Every mapped case must pass setup, call, and
teardown; unrelated passing cases cannot satisfy an outcome. Skips and expected
failures are inconclusive. An unresolved product rule remains unresolved even
when its characterization test passes.

This initial integration supports pytest directly. It does not define a general
harness API or require pytest in the core engine's environment. The target Python
interpreter must have pytest and the application's test dependencies installed.

```json
{
  "version": 1,
  "scope": "orders/cancellation/local-api",
  "environment": {"database": "temporary SQLite", "client": "API test client"},
  "limitations": ["No production database concurrency or external delivery evidence"],
  "inputs": ["src", "tests", "pyproject.toml", "uv.lock"],
  "outcomes": [{
    "id": "cancel.ownership",
    "capability": "orders.cancel",
    "description": "Another account cannot cancel or mutate this order",
    "source_refs": ["POST /orders/{order_id}/cancel"],
    "policy": "required",
    "tests": ["tests/test_cancel.py::test_other_account"]
  }]
}
```

`source_refs` must exist in the supplied discovery inventory. This is an authored
semantic mapping: the engine checks identities and execution results, not whether
the assertion correctly expresses the business requirement. Review test meaning
and fixture limitations with the map. An outcome can have an empty `tests` list;
it will remain missing. Use `policy: "unresolved"` with a `reason` for pending
product decisions. There are no exemptions which turn such outcomes into passes.

Run from the consumer project:

```sh
capcov discover --target . --out .capcov/inventory.json
capcov outcomes run capcov.outcomes.json --inventory .capcov/inventory.json \
  --python .venv/bin/python --out .capcov/outcomes-run.json
capcov outcomes coverage capcov.outcomes.json --inventory .capcov/inventory.json \
  --run .capcov/outcomes-run.json --out .capcov/outcomes-coverage.json
capcov outcomes gate capcov.outcomes.json --inventory .capcov/inventory.json \
  --run .capcov/outcomes-run.json
```

A failed pytest run still writes evidence for reporting; arrange CI to run coverage
and gate after that failure. `run` returns 1 for unsuccessful/incomplete execution;
`coverage` returns 0 when a valid report is produced, even with gaps; `gate` returns
1 unless all scoped outcomes are demonstrated and the session is clean. Invalid
or stale evidence returns 2. Commands after `--` on `run` are pytest selections or
options; otherwise it runs the union of mapped node IDs.

The report distinguishes `demonstrated`, `failed`, `missing`, `unresolved`, and
`inconclusive`. It is complete only **within the authored scope and environment**;
it does not close unmapped source obligations, discovery blind spots, or the
separate entity/flow gates. A missing test file can cause pytest collection to
abort; all outcomes without executed evidence then remain missing.

Runs use a private result path and fresh nonce. Source inventory, map, declared
input files (including mapped tests), and engine code are hashed; coverage/gate
recompute them against the current checkout. Include fixtures, test configuration,
dependency locks, and other assertion inputs in `inputs`. These checks prevent
accidental stale evidence reuse; the runner/test code is trusted, and this is not
cryptographic attestation of an external service or proof of the deployed build.
Execution/reset/cleanup remain the consumer fixture's responsibility. A timeout
fails the run; consumers must own cleanup for subprocesses their fixtures start.
