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

Runtime-only tables remain visible even when the consumer records an exact,
dated exemption explaining their origin (for example a migration framework's
version table). A valid exemption accounts for the corresponding test observation
once; it does not mark the table statically discovered or waive an unknown entry
point. Missing reasons, changed cells and obsolete exemptions still fail. The
legacy `orphan_tests` report key means a test observed an undeclared entity; one
inventory cannot prove that the entity was deleted. Do not infer historical
removal from that label or treat an accounted gap as a demonstrated business outcome.

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

Assertions use `mode: "text"` by default and require visible matching text. A
negative assertion can instead require that its selector match nothing:

```json
{"op": "assert", "mode": "absent", "id": "no-privileged-control", "selector": "form[data-privileged]"}
```

An absence assertion carries no `text` field. Unknown or contradictory modes
fail planning. Its unique assertion ID is still mandatory execution evidence in
every applicable step; declaring absence in the model is not a passing result.
Consumer runners must implement zero matches (including hidden elements for a
browser), not merely invisibility, and record the ID only after the check passes.
Existing text assertions retain their current contract.

A consumer may support bounded refresh while awaiting an asynchronous outcome:

```json
{"op": "assert", "id": "review-ready", "selector": "main", "text": "Ready for review", "refresh_timeout_ms": 20000}
```

`refresh_timeout_ms` is an integer from 1 through 60000, valid only on assertions.
It requests repeated reads of the current view until the assertion succeeds,
under one total deadline covering refreshes, checks and delays. It must never
repeat earlier action commands or resubmit a mutation. Browser consumers must
restrict refresh to a reviewed, same-application GET view and fail if navigation
leaves that view or origin. Consumers that cannot honor this contract must reject
the option. A timeout or unsuccessful refresh supplies no assertion evidence;
planning itself performs no waiting, browser work or network requests.

Browser consumers can select a native option by its exact value and attach one
or more fixture files:

```json
{"op": "select", "selector": "select[name=vendor]", "value": "fixture-vendor"}
{"op": "upload", "selector": "input[type=file]", "files": ["fixtures/invoice.png"]}
```

`select.value` must be a string (including an empty option value). `upload.files`
is a nonempty list of repository-relative POSIX paths, without absolute paths,
drive prefixes, backslashes, empty/dot/parent components or NULs. Both commands
require a selector and retain their exact inputs in the plan. Neither is an
assertion: a binding still needs a separate observable outcome assertion.

Planning does not read or upload files. A consumer must resolve each file within
its declared repository root, reject escaping symlinks, and require its content
hash in the run's source inventory before transfer. Uploads belong to the intended
application origin; redirecting to authentication must not change the destination
of fixture data. Unsupported consumer operations fail execution rather than being
silently ignored. The model does not invent upload contents or vendor/store values.

Missing adapters, unconfirmed meaning, absent bindings, unreachable states,
unmapped obligations, and insufficient evidence remain gaps. A baseline can
permit reviewed gaps without calling them covered. A passing browser navigation
does not prove persistence, authorization, external delivery, or product parity.

Python branch and exception candidates retain their parent HTTP surface. A mapped
candidate requires that parent request in the same execution step, together with
the declared outcome assertions; observing the route in another step is not
enough. Missing or invalid parent references fail reconciliation. The candidate
ID is a source obligation, never a URL the runner should fabricate. HTTP presence
alone does not distinguish which branch ran: consumer-reviewed assertions still
have to establish the intended outcome.

Separate `python-routes` adapters can declare different router prefixes, including
multiple mounts of the same source. Each mount keeps its own surface and branch
obligations. The four Python discovery limits apply once to the combined
inventory; mounted-route confirmation must account for every discovered mount.
Overlapping declarations of the same HTTP surface remain an error.

## OpenAPI operation inventory

An HTTP service in any language can supply a local OpenAPI JSON document:

```json
{
  "scope": "Declared API operations; runtime and business behavior unconfirmed",
  "root": ".",
  "adapters": [
    {"kind": "openapi-json", "document": "openapi.json", "prefix": "/v1"}
  ]
}
```

The adapter supports OpenAPI 3.0.x and 3.1.x JSON and inventories all eight inline
HTTP operation methods. Each surface retains the document hash and JSON pointer;
line 1 identifies the document, not an inferred operation line. The optional
prefix defaults to empty and must be reviewed against the deployment. Server URLs
are never fetched or selected. Export the contract locally using the application's
own recipe; this adapter performs no network requests and adds no dependencies.

This is an operation inventory, not a full OpenAPI validator. It does not resolve
Path Item references or invent methods for empty/filtered paths: each stays an
explicit gap. It also retains boundaries for runtime/omitted routes, business
outcomes, authorization/configurations, schema/reference behavior, server bindings,
and callbacks/webhooks/extensions. Descriptions, examples, operation IDs and server
values are not copied into reports. Duplicate JSON members, unsupported versions,
invalid path/operation shapes and equivalent templated paths fail discovery.
The supported method and Path Item rules come from the
[OpenAPI 3.1 specification](https://spec.openapis.org/oas/v3.1.0.html#path-item-object).

Run the existing `flows discover` and `flows catalog` commands on this config.
Operations become candidate flow families with missing outcomes, fixtures and
bindings. Whole-document declaration accounting, reference resolution and behavioral
completeness remain false. A fresh exported contract hashes the snapshot; it does not prove the
snapshot belongs to the running build. The consumer must bind export, build and
execution provenance in its local recipe.

Keep contract and source inventories separate when comparing them: overlapping
HTTP surfaces still fail if configured in one inventory. Agreement does not prove
completeness, and differences need investigation. In a local Storekeeper probe,
the contract exposed 60 operations versus 25 in the selected source-flow scope:
all 25 matched, while 35 additional operations mostly belonged to inherited
administration and portal/auth code. None received coverage merely from discovery.

## Current support

- Python/FastAPI/SQLAlchemy entity discovery and runtime probes.
- Opt-in literal SQLite table declarations, with unbound query diagnostics.
- Python route source obligations, OpenAPI JSON operations, and Zoho Creator export discovery.
- Required/forbidden fact-state planning with explicit blocked transitions.
- Consumer execution commands with fresh run nonces and source/model/plan hashes.
- Exact scenario/assertion reconciliation, per-step HTTP evidence, and gap gates.

Go/React discovery, a general-purpose browser exploration agent, and automatic
semantic inference are not implemented. Synapse documentation validation does
not run this engine. Optional document projection and `synapse capabilities`
CLI integration are follow-up work.

### Direct SQLite declarations

For a Python target using direct SQLite calls, add to `capcov.toml`:

```toml
[capcov]
adapter = "python-fastapi-sqlalchemy"
source = "src"
sqlite_ddl = true
```

This adds literal `CREATE [TEMP] TABLE [IF NOT EXISTS] name (...)` declarations
inside `execute`, `executemany`, and `executescript` calls to the entity inventory.
It reads Python/SQL tokens without importing or running the application. Comments
and string contents cannot create table declarations. Declaration records carry
file/line evidence and `declaration_kind = "sqlite_literal_ddl"`; duplicate table
names retain their first declaration (an existing ORM declaration takes priority).

Opting in asserts these SQL-shaped method calls are relevant to the target; this
pass does not infer the receiver's runtime type. It deliberately creates no CRUD
or route binding. Every candidate call stays in `blind_spots`: literal statements
as `literal_sql_unbound`, computed SQL or ORM expressions as
`computed_sql_or_expression`. Parameter values and SQL text are not emitted.
Unsupported declarations (virtual tables, `AS SELECT`, single-quoted names),
external SQL files, and connections outside the source scope remain outside this
declaration subset. Schema qualifications are retained, but entity keys do not
distinguish separate databases with identical table names.

The runtime probe still observes SQLAlchemy, not direct `sqlite3` operations.
New declarations with neither route bindings nor runtime evidence correctly stay
in the `neither` cell. This feature expands the denominator; it does not establish
SQLite coverage or solve query/receiver analysis.

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


A download can itself be an observable assertion against a reviewed expected file:

```json
{"op": "assert", "mode": "download", "id": "export-bytes", "selector": "a.export", "file": "fixtures/expected.csv"}
```

The expected file uses a canonical repository-relative POSIX path, with the same
confinement and enrolled-byte requirements as upload fixtures. The consumer must
perform the selected download, require successful completion and compare its
complete bytes with the checked expected bytes before emitting the assertion ID.
A link, filename, prefix match, or successful HTTP response alone is insufficient.
`text` and `refresh_timeout_ms` are invalid for this mode; download actions are
never automatically retried. The consumer owns origin restrictions and bounded
transfer/size handling, and must reject the mode if it cannot honor that contract.
Planning neither reads the expected file nor downloads anything.


A journey can retain a runtime-created resource path and revisit it after an
identity change:

```json
{"op": "remember-path", "name": "invoice"}
{"op": "visit-path", "name": "invoice", "expect_status": 404}
```

Names match `[a-z][a-z0-9_-]{0,63}`. `visit-path` requires an integer expected HTTP
status from 200 through 599. Both are actions; a binding still needs a separate
observable assertion. They accept no alternate path, selector or value.

Consumers must scope saved paths to one scenario, reject missing names and
redefinitions, retain only a reviewed same-application path (no credentials, query
or fragment), and revisit it with a bounded GET. The final URL must remain the
saved resource and the final response must match `expect_status`; a login redirect
is not a resource-access refusal. Invalid captures and unresolved names fail,
without a guessed/default path. Models must describe the capture prerequisites
and identity changes. Planning does not invent a resource URL or perform requests.


A reviewed direct HTTP response can be an assertion, including a denied mutation:

```json
{"op":"assert","mode":"http","id":"price-refused","method":"POST","path":"/items/1/base","form":{"price":"4.99"},"expect_status":403,"text":"not permitted"}
```

This initial contract supports GET and form-encoded POST on literal application
paths composed of letters, digits, underscores, hyphens and single slashes. It
excludes queries, fragments, encoded paths, alternate origins, arbitrary headers
and raw bodies. GET has no form. Form keys/values are strings with bounded sizes.
Expected statuses are 200–299 or 400–599; response text must be nonempty.

Consumers must use the scenario's current authenticated session, confine the
request to a reviewed application endpoint, send it once, reject redirects, and
bound both transfer time and complete response bytes. They must verify exact
response URL/status and the declared body text before recording assertion
evidence, and record the actual request for route reconciliation. A DOM assertion
elsewhere is not response evidence. No retries or refresh are permitted, including
for writes. The planner performs no requests. An expected denial alone does not
prove absence of side effects; model follow-up state checks where required.


Planning defaults to 10,000 reachable fact states. For larger reviewed models,
use `capcov flows plan model.json --target local --max-states 20000 --out plan.json`.
The positive integer limit bounds exploration; exhaustion still fails without
emitting a complete plan. Non-default limits are recorded in the plan and used
when coverage independently re-derives its scenarios. Raising this budget adds
no coverage and does not waive unreachable targets or missing evidence. Default
plans retain their existing artifact shape.


A click may declare a native browser confirmation explicitly:

```json
{"op":"click","selector":"button.delete","confirmation":{"message":"Delete this sample?","action":"dismiss"}}
```

The contract requires an exact nonempty message of at most 1024 characters and
an `accept` or `dismiss` action. It is valid only on `click`; extra confirmation
keys are rejected. The declaration is preserved in the plan and bound to run
evidence. It does not itself grant coverage or replace subsequent outcome
assertions. A browser consumer must wait for a native `confirm` dialog caused by
that click, match the message exactly, apply the declared action, and fail on a
missing or mismatched dialog within a bounded deadline. It must not silently
accept prompts, alerts or arbitrary confirmation messages. Planning does not
open or answer a browser dialog.
