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
