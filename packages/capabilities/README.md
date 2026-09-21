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

The experimental claim-semantics workbench also includes a Jev advisory path
for ranking a mechanically bounded candidate set before acquiring evidence:

```sh
JEV_API_KEY=... capcov experiment claims jev assess --request request.json
```

Its content-addressed output is explicitly an assumption: it may prioritize a
runtime probe or human review, but cannot establish a fact, compatibility,
completeness, coverage, or claim qualification. See
`experiments/claim-semantics/jev/README.md`.

## Foundations

Each mechanism has a lineage in testing and program-analysis literature.
`ADR-0001-capcov-literature-foundations` (in the Synapse vault under
`content/90_Architecture/ADRs/`) records the full map and the resolver decision;
the anchors in brief:

- **Flow model = model-based testing.** Facts + guarded transitions form an
  EFSM/STRIPS model; `plan()` emits one shortest-prerequisite scenario per
  transition ("all-transitions" generation). — Chow 1978; Utting & Legeard 2007;
  Lee & Yannakakis 1996.
- **Obligations = test requirements.** The obligation set is the denominator, and
  each branch outcome is a separate obligation, never collapsed. — Ammann & Offutt
  (2008/2016).
- **Reachability + soundy resolution.** The backward-reachability fixpoint closes
  over *resolved* edges; the adapter resolves what it can syntactically and
  *enumerates* its blind spots rather than guessing. — Livshits et al. 2015
  (soundiness); Shivers 1991 (k-CFA); Samhi et al. 2024; Néron et al. 2015;
  Creager & van Antwerpen 2023 (stack graphs: scale, no precision/recall figure).
- **Static-vs-runtime reconciliation = a Software Reflexion Model.** Declared vs
  observed maps convergence/divergence/absence onto `covered` / `runtime-only` /
  `dead`. — Murphy, Notkin & Sullivan 1995.
- **Capability nouns descend from FODA.** Capabilities as a facet tree; adopting
  its variability structure is a future option. — Kang et al. 1990.

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

### Optional SCIP resolver (`--resolver scip`)

`capcov discover` resolves its call graph with a stdlib-only AST pass by default.
`--resolver scip` sources that graph from a SCIP indexer instead — type-aware,
cross-file and multi-language, which recovers call chains (and so entity
bindings) the AST pass cannot follow across module and interface boundaries:

```sh
capcov discover --target . --resolver scip --out capabilities.json
```

This is a hybrid, not a replacement. The AST pass still runs and stays the
enumerator of blind spots (`getattr`/`eval`/dynamic import) and the fallback,
because SCIP is a black box about its own gaps: it reports the edges it resolved
and says nothing about the sites it could not. capcov recovers that silence by
subtraction, so the artifact carries **both** halves — `scip_resolved_edges` and
the `scip_residue` of call sites SCIP left unresolved, each named with a file and
a line (an untyped `session.add(job)`, a computed `getattr`). Coverage therefore
reports resolved-by-SCIP plus unresolved-enumerated, never a bare number, and the
"name unresolved, do not drop" property holds through the SCIP path. These fields
flow through `reconcile` into `coverage.json` alongside the existing cells.

The resolver depends on **external command-line tools**, not Python packages, so
it is opt-in and there is no pip extra for it. `capcov` and its non-SCIP tests
run with none of them installed; `--resolver scip` fails with a named, actionable
error when a tool is absent. Install, per target language:

- a SCIP indexer — Python: `npm install -g @sourcegraph/scip-python`; Go:
  `go install github.com/scip-code/scip-go/cmd/scip-go@latest`;
- the `scip` CLI (reads an index as JSON) —
  `git clone --depth 1 https://github.com/sourcegraph/scip.git && cd scip && go build -o scip ./cmd/scip`.

capcov finds the indexer on `PATH` and locates the `scip` CLI via `$SCIP_CLI`, a
binary dropped at `src/capcov/scip/vendor/scip`, or `PATH`.

### Optional profiles (`--judge claims`)

`capcov reconcile` and `capcov gate` judge with the four-cell reconcile. That is
the default, it is stdlib-only, and it is what runs in CI. `--judge claims`
**adds** an experimental **replay judge** beside it: as well as asking whether
each capability was both derived and exercised, it judges a *replay receipt* — a
recorded run of two systems against the same requests — with the claim kernels
you name, certifies every claim row from every closure, and refuses to answer at
all if they disagree.

It adds a verdict; it does not replace the artifact's. A receipt names a run of
the system under test and a coverage artifact names a source tree, and nothing in
either names the other, so `gate` runs the four-cell gate too and passes only
when **both** pass, and `judge.json` records the artifact it was handed
(`gated_artifact`: its sha256, its source snapshot and its four-cell verdict).
`--judge-out` must be outside `--receipt` — the judge writes a `receipt.json` of
its own — and is refused by name when it is not.

```sh
capcov gate coverage.json --judge claims --receipt <evidence>/receipt-dir --judge-out judge/
capcov reconcile capabilities.json observed.json --out coverage.json \
    --judge claims --receipt <evidence>/receipt-dir
```

It can also be selected from `capcov.toml`, read from the working directory the
artifact paths are relative to:

```toml
[judge]
engine = "claims"        # "four-cell" (the default) or "claims"
evaluator = "python"     # "python" (the default), "souffle", "souffle-compiled",
                         # a comma list, or "all"
model = "shen:model/"    # unset by default; PROFILE:DIR, see below
```

#### Which kernels judge (`--evaluator`)

`--evaluator` names the kernels, and the default is `python` — the evaluator in
this package, standard library only. It needs no external tool, which is why
`--judge claims` works in any checkout:

```sh
capcov gate coverage.json --judge claims --receipt <evidence>/receipt-dir     # python alone
capcov gate coverage.json --judge claims --receipt <evidence>/receipt-dir \
    --evaluator python,souffle                                               # the differential
capcov gate coverage.json --judge claims --receipt <evidence>/receipt-dir \
    --evaluator all                        # every evaluator whose tool is present
```

**The differential runs only when two or more evaluators were asked for.** With
one, there is nothing to compare, and `judge.json` says so rather than reporting
an agreement: `"kernels": ["python"]`, `"differential": "not-run (single
evaluator)"`. With two or more it is fail-closed exactly as before — any
disagreement on the closure, on a claim row, on a certificate or on a recheck
blocks the judgement and persists the bundle for replay. `all` means every
evaluator whose tool is *here*, so it is the one spelling that never fails for a
missing binary; naming `souffle` or `souffle-compiled` explicitly always does.

#### Which model the judge binds to (`--model shen:DIR`)

The replay judge signs a qualified verdict against a *model digest* and requires,
as a positive premise, that the model at that digest is well formed
(`model_well_formed`). Where that premise comes from is the caller's choice:

* **no flag** — the default — the judge reads whatever `model_*` files the
  receipt already carries. A receipt with none is *judged*, not refused: its ops
  come out semantically `unresolved` with the model premises named as missing,
  which is the honest answer to "was this model checked?". Nothing under
  `capcov.claims.modelcheck` is imported.
* **`--model shen:<model dir>`** runs Stage D's typed checker over that
  directory *before* judging — the same run `capcov experiment claims modelcheck
  --model DIR --out <receipt>/` performs — and writes
  `modelcheck-certificate.json`, the transcript and, for a well-formed model
  only, the `model_well_formed.json` the judge then reads:

```sh
capcov gate coverage.json --judge claims --receipt <evidence>/receipt-dir \
    --model shen:<evidence>/model
```

An ill-formed model does not stop the run — the certificate says so, no fact is
written, any stale one is removed, and the judge reports the premise as missing.
A checker that reaches *no* verdict does stop it (exit 2): judging on could read
a previous run's certificate and call it this model's. A certificate for a model
the receipt does not name is a contract finding, never a premise.

The profile needs the pinned `shen-go` runtime through the `bifrost` launcher
(`$BIFROST_SHEN_GO`, `$SHEN_GO`, or `shen-go` on `PATH`). Asking for it where
that is absent is refused before any work, in the `--resolver scip` shape:

```
capcov gate --judge claims: --model shen needs shen-go and the bifrost launcher is
not on PATH; the shen-go binary is not on PATH, $SHEN_GO or $BIFROST_SHEN_GO.
Install it with: enter the pinned devShell with `nix develop` (it pins shen-go) and
put the bifrost launcher on PATH, or name the binary in $SHEN_GO; or drop --model
and judge the model_* files the receipt already carries
```

#### The static producer profile (`--static scip`)

```sh
capcov experiment claims static --static scip --target <tree> --language go \
    --out bundle.json
```

`--static scip` is the static half of the same idea. It indexes the tree with
upstream's resolver (`capcov.scip.runner` + `resolve.hybrid_raw` +
`blindspots.enumerate_blind_spots`), exports the bundle
with `capcov.claims.static.scip_facts` exactly as before, and **additionally**
emits two relations beside that export:

The complete call-site census is read from the target tree. `--ast-raw` is an
optional input for adapter AST facts; it does not supply or suppress the census.
For Go and PHP, install the parser dependency with `pip install .[treesitter]`.
The profile checks that parser before starting the SCIP indexer and exits with
`census-unavailable` if the optional extra is missing. Python census uses only
the standard library. The indexer and `scip` CLI remain separate external tools
as described in the SCIP resolver section above.

* `static_unresolved_call_site(index, file, line, symbol)` — the resolver's
  enumerated `scip_residue` as rows rather than a count. `symbol` is the callee
  as the source spells it, because an unresolved call site has no SCIP symbol.
* `call_graph_closed(index, scope)` — the completeness witness for `static_edge`
  over one scope, emitted **only** when the census was taken and that scope's
  residue is empty. `scope` is a token of the export's own scope declaration:
  `"*"` for every in-scope document, a package prefix, or one document path.

`rules-static-closure-v1.json` (package data beside the frozen schema) layers on
`rules-static-v1` and is what makes a *negative* static claim answerable: "route
R does not reach table T" is **supported** when the call graph is closed and R
reaches no such table, **refuted** when R does reach it (one positive reach is a
counterexample and needs no completeness), and **unresolved** whenever the
residue is not empty. The rows are attributed to producer class `scip`, and the
export's own identity and bundle digest are untouched — the closure is a
separate fragment merged with `combine`, so turning the profile on renumbers no
existing evidence id. Where the SCIP toolchain is absent the profile refuses in
`capcov discover --resolver scip`'s own words.

#### Class-hierarchy dispatch (`--dispatch cha`)

```sh
capcov experiment claims static --static scip --target <tree> --language go \
    --dispatch cha --out bundle.json
```

A SCIP index resolves a call through an interface to the *interface's* member,
not to the implementations that could run, so the site lands in the residue and
`call_graph_closed` is withheld. `--dispatch cha` merges a fourth fragment
(`rules-static-cha-v1`, `capcov.claims.static.cha`) that expands each such site
through the index's own `is_implementation` relationships.

**Measured, not assumed.** scip-go 0.2.7 does emit implementation relationships
for Go interfaces — for the method (`SQL#Fetch().` → `Repo#Fetch.`) and for the
type (`SQL#` → `Repo#`) — measured on `tests/fixtures/go_iface_app`, whose
index is committed as `tests/fixtures/scip_go_iface_app_index.json`. The same
measurement is why the caller side needs a relation of its own: scip-go types an
interface member `MethodSpecification`, which `scip.map` classifies as a *term*,
so the dispatch site never reaches `scip_may_reference`. An indexer no
measurement covers (scip-python, scip-php today) is refused with
`dispatch-unsupported` and exit 3 — "never measured" is not "emits none", and
only one of those is a fact.

* `static_interface_dispatch_site(index, caller, interface_symbol, path, line)`
  — the call the index could not pin down, attributed to its innermost enclosing
  definition by the same rule `scip_may_reference` uses.
* `static_cha_unexpanded_site(index, path, line, interface_symbol, reason)` —
  every site the expansion could not cover (`caller_unattributed`,
  `no_implementation_in_index`, `implementation_out_of_scope`), enumerated,
  never dropped.
* `static_edge_cha(index, src, dst, via_interface)` — the expansion, and
  `static_reaches_cha` the reachability over the resolved graph plus it.
  `static_edge` is **never** widened: it is what `call_graph_closed` completes.
* `static_edge_cha_closed(index)` — the expansion's own witness, emitted only
  when nothing was enumerated as unexpanded *and* the scope is the whole index
  (a slice does not export the relationship rows of the documents it drops, so
  it cannot see the implementation it is missing).
* `call_graph_closed_cha(index, scope)` — the call graph *with* the expansion:
  emitted when that witness holds, the census was taken and every unresolved
  call site in the scope is discharged by an expansion of that exact site. A
  residue row that is not a dispatch site is never discharged.

A CHA edge is a **may**-edge: the expansion over-approximates on the positive
side and is only stronger on the negative one. So every verdict read off it is a
separate row — `static_capability_op_cha`, `static_entity_dead_cha`,
`static_entity_blocked_cha`, `static_convergence_cha`, `static_divergence_cha`,
`static_absence_cha` — and nothing is merged into the relation it twins. Without
the flag not one CHA row is emitted and the bundle is byte-for-byte what it was.

#### The advisory profile (`capcov experiment claims jev`)

`jev` is registered like the others and imported like the others — only when it
is named. It is *advisory*: it asks a network service (`$JEV_API_KEY`) for
patterns a reader weighs, and no claim, premise or verdict is derived from it, so
a checkout without the module, the key or the network judges exactly the same.
Naming it where it is not available answers with `profile-unavailable` and exit
3, never an ImportError.

`reconcile` still writes `coverage.json` either way — it is the producer of that
artifact, and `--judge claims` changes who decides, not what is produced. The
judge writes `judge.json` plus the per-row certificates into `--judge-out`
(default `capcov-judge/`); that document names the kernels that ran (`kernels`),
whether a differential ran (`differential`), and carries the judge's own six
exit codes (0 qualified, 1 unsupported, 2 kernels disagree, 3 the receipt breaks the
exporter's contract, 4 toolchain unavailable, 5 pending a premise nothing can
satisfy yet), while the CLI itself answers the one question a gate asks: 0 when
every op the verdict turns on is qualified, 1 otherwise.

**Off unless asked, exactly like `--resolver scip`.** With no flag and no
`[judge]` key, `capcov.cli` does not import `capcov.claims` at all — not the
evaluator, not the rule packs, not the model checker — and `reconcile`/`gate`
produce byte-identical output to the version before these options existed
(pinned against upstream's own artifacts in
`tests/claim_semantics/test_upstream_golden.py`). The experimental namespace
`capcov experiment claims ...` is likewise registered lazily and never appears
on the default path.

**What fails, and how.** The `souffle` and `souffle-compiled` evaluators need
the **external** Souffle 2.5 binary (`$SOUFFLE`, else `souffle` on `PATH`) — a
binary, not a Python package, so as with the SCIP resolver there is no extra
that can install it (the `judge` and `souffle` markers in `pyproject.toml` are
empty and documentary). Asking for one that is not here never degrades to a
smaller differential; it is checked before any work and refused with a named,
actionable message:

```
capcov gate --judge claims: --evaluator souffle needs the Souffle 2.5 executable
'souffle', which is not on PATH or $SOUFFLE. Install it with: install Souffle 2.5
(https://souffle-lang.github.io/install) or enter the pinned devShell with
`nix develop`; or use --evaluator python
```

Install it from <https://souffle-lang.github.io/install>, or run `nix develop`
at the repository root — `flake.nix` pins it. Configuration mistakes are
separated from verdicts by exit code: `--judge claims` with no `--receipt`, a
`--receipt` that is not a receipt directory, an unknown `[judge] engine`, an
unknown or absent `--evaluator`, an unknown `--model` profile or a model
directory that is not there, or a `--receipt`/`--judge-out`/`--evaluator`/
`--model` passed without `--judge claims` all exit **2** with a message naming
the mistake, and judge nothing. A flag that silently did nothing is how a gate ends
up green for the wrong reason.

The same rule covers the config file. `reconcile` and `gate` never read
`capcov.toml` before these flags existed, so one that cannot be parsed still
must not turn a working default run into a failure — it is passed over, the exit
code and stdout are the ones it always had, and the defaults stand. But it is
not passed over in silence: a single line on **stderr** names the file, the
parse error and what is deciding instead, because a project that opted in with
`[judge] engine = "claims"` and later broke an unrelated line of that same file
would otherwise get the four-cell gate's usual PASS with nothing anywhere saying
the judge it believes is gating never ran. A well-formed `capcov.toml`, and no
`capcov.toml` at all, are untouched — neither reaches that branch.

`--quiet` governs the opt-in judge as it governs the rest of the command: it
suppresses the per-op summary and the closing verdict line alike, leaving stdout
exactly what it is without `--judge claims` at all. Nothing is lost by the
silence — the verdict, the kernels and the judge's own exit code are in
`judge.json`, and the process's exit code answers the gate's question either
way. Diagnostics stay on stderr, which `--quiet` has never governed.

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

Route branch and exception candidates retain their parent HTTP surface. A mapped
candidate requires that parent request in the same execution step, together with
the declared outcome assertions; observing the route in another step is not
enough. Missing or invalid parent references fail reconciliation. The candidate
ID is a source obligation, never a URL the runner should fabricate. HTTP presence
alone does not distinguish which branch ran: consumer-reviewed assertions still
have to establish the intended outcome.

Source code in any tree-sitter-supported language is read by the single
`treesitter-routes` adapter (install the `treesitter` extra). The opinion of
which calls are routes is a config-supplied tree-sitter query, so one adapter
serves Go, JavaScript, Python and the rest -- there is no per-language reader. It
sees literal string arguments in the nodes the query matches: a path built by
concatenation or held in a variable is invisible and becomes an unresolved
dynamic-route obligation. Unlike a regex it is comment- and syntax-aware, so a
commented-out call never matches. When the query captures the enclosing handler
as `@handler`, its body is walked for branch and exception candidates; the node
types that count are config-driven (`branch_nodes`, `exception_nodes`) with
per-language defaults. Four route-reading limits are emitted once for the
combined inventory.

The same source read at more than one mount point is namespaced with distinct
`id_prefix` values, which keeps each mount's surface and branch IDs separate;
overlapping declarations of the same ID remain an error. A `mount` composes a
router prefix into every path of an entry (one entry per mounted router), so the
surface id is the path the runtime serves rather than the literal in the file. An optional `methods`
allowlist records a matched, route-shaped candidate whose verb is outside the set
under `excluded_surfaces` -- the query saw it and the verb filter dropped it, so
the narrowed denominator stays legible instead of implied by absence. This is a
conservative source rule, not proof of runtime mounting or framework object
identity. Runtime reconciliation remains required.

### Static reflexion

Seven optional pieces put a *reflexion model* (Murphy/Notkin/Sullivan) over the
static account: the call graph as extracted, a reviewer's intended architecture,
and the comparison of the two -- plus the closures that let an absence be `dead`
rather than merely unobserved. Each piece is behind its own flag, each is
additive, and each leaves the relation `call_graph_closed` completes
(`static_edge`) exactly as it was. **Every one of them is off by default, and
with the flag absent the behaviour is identical to capcov main** -- no module of
the piece is even imported.

**1. The reviewer's model and the reflexion verdicts** (`rules-static-reflexion-v1`)

```sh
capcov experiment claims static --static scip --target <tree> --language go \
    --capability-map MAP.json [--capability-edges EDGES.json] --out bundle.json
```

`capability_map(index, symbol, capability)` and `capability_edge(index, src, dst)`
are the reviewer's, producer class `reviewer`, each closed by its own witness
(`capability_map_closed`, `capability_edge_closed`) and bound to one index by
`capability_map_describes_index`. Derived: `static_low_edge` (the lift of
`static_edge` through the map), `static_convergence`, `static_divergence` (needs
the closed edge model), `static_absence` (needs `call_graph_closed` *and* the
closed map), and the split of an entity a surface does not reach into
`static_entity_dead` (closed) / `static_entity_blocked(index, surface, entity,
via)` (an unresolved call site is reachable from the handler, and `via` names the
symbol the doubt enters through) / `static_entity_unresolved` (residue with no
owner to name).

*Tools:* a SCIP indexer and the `scip` CLI, plus the tree-sitter census extra
(`pip install .[treesitter]`). *When they are absent:* the census is checked
before the indexer is started and answers
`{"operational_failure": "census-unavailable", ...}` with exit 3; an absent
toolchain answers `{"operational_failure": "scip-tools-unavailable", ...}` with
exit 3, in `capcov discover --resolver scip`'s own words. A map naming a symbol
this index does not declare, or a *closed* map that omits a symbol the index's
edges run through, is `{"refusal": "..."}` with exit 2 -- naming the symbols is
the only safe failure. With this flag absent, behavior is identical to capcov
main.

**2. The static bundle joined to the judge**

```sh
capcov gate --judge claims --receipt <dir> --static bundle.json
```

`judge.json` gains a `static` section: the routes the index binds, each
capability's reflexion cell, `dead`, `blocked` (with its `via`), `unresolved`,
and `static_only` (a surface the index binds that the run never requested --
licensed only by the replay producer's own `replay_requests_closed`). The four
cells, the verdicts and the exit code are untouched: a static path is not an
outcome. Falls back to `[judge] static` in `capcov.toml`.

*Tools:* none beyond the bundle. *When it is absent or wrong:* a path that is
not there, is not JSON, or is not a claim bundle is
`capcov gate --judge claims: --static: cannot read the static bundle '...'` with
exit 2, before any judging; a bundle that does not carry `index_describes_run`
for this run is reported `stale` and not joined, and one that cannot derive a
reported relation names it in `underived` rather than reporting an empty list.
With this flag absent, behavior is identical to capcov main.

**3. The flow plan previewed against the static account**

```sh
capcov flows plan MODEL --target <tree> --out plan.json --static bundle.json
```

Each transition is annotated with what the bundle says about its obligation
surfaces: the store set the route can reach, `surface_status` ∈
`declared | undeclared | dead | blocked`, and whether an authz sink is on the
path. Annotation only -- the plan is planned before the bundle is read, no
scenario is pruned and `model_sha256` does not move, because a persistence
assertion is an outcome and no static account retires it.

*Tools:* none beyond the bundle. *When it is absent or wrong:* the command exits
1 with `the static bundle did not evaluate: ...`, `the static bundle carries no
scip_index and no static_route_declared_surface row`, or the multi-index
refusal -- a preview
against more than one index is more than one preview. With this flag absent,
behavior is identical to capcov main.

**4. Class-hierarchy dispatch** (`rules-static-cha-v1`)

`--dispatch cha`, documented in full above: the dispatch sites a SCIP index
resolves only to an interface member, expanded through the index's own
`is_implementation` relationships into `static_edge_cha`, with
`static_edge_cha_closed` and `call_graph_closed_cha` as its own witnesses and
every verdict as a separate `*_cha` row.

*Tools:* an indexer a measurement covers -- scip-go 0.2.7 today. *When it is
absent:* an unmeasured indexer is `{"operational_failure":
"dispatch-unsupported", ...}` with exit 3, naming what *was* measured and the
remedy (`--dispatch none` still produces the resolved bundle), because "never
measured" is not "emits none". With this flag absent, behavior is identical to
capcov main.

**5. Boundary vectors joined to the static store account**

```sh
capcov experiment claims vectors-static --vectors <dir> --replay <dir> \
    --static bundle.json [--kernel python|souffle|differential] [--out report.json]
```

The recorded/replayed vector cells beside the tables the route can statically
reach: `vector_store_divergence` (a delta in a table the route cannot reach --
refuting, under `call_graph_closed`) and `vector_store_unexercised` (a reachable
table no cell touched -- advisory, because `retry` and `invalid-input` expect no
delta). Producer classes stay apart: `scip` for the paths,
`capcov-vectors-replay-v1` for the outcomes.

*Tools:* none for `--kernel python`; the `souffle` executable for
`--kernel souffle` or `--kernel differential`. *When they are absent:* a missing
or mismatched input is `{"refusal": "..."}` with exit 2, and anything else --
an absent `souffle` under those two kernels among it -- is
`{"operational_failure": "vectors-static-failed", ...}` with exit 3, carrying
the evaluator's own message: never a silently single-kernel result reported as a
differential. With this flag absent, behavior is identical to capcov main.

**6. The incumbent's edge producer: PHPStan/Larastan** (`rules-static-phpstan-v1`,
`rules-static-parity-v1`)

On a Laravel-shaped PHP tree every `DB::`, `Auth::` and Eloquent static forward
is `facade_magic` residue to a SCIP index, so `call_graph_closed` is never
earned. `capcov.claims.static.phpstan_facts` reads the JSON report of the
bundled collector (`phpstan/CapcovCallCollector.php`) and emits the *same*
static schema with producer class `phpstan` -- never `scip`, because Larastan's
resolution is itself an assumption about framework behaviour, and a PHPStan
"call on mixed" *is* the residue, named at its site.
`capcov.claims.static.parity` then compares two indexes in one bundle under a
reviewer's `op_maps`: `static_parity`, `parity_static_only_incumbent` (a store
the incumbent reaches and the candidate cannot -- a missing capability found
before anything is run), `parity_blocked`, `parity_unresolved`.

*Flag:* none on the command line today -- this piece is a library entry point,
and nothing imports it unless a caller names it. *Tools:* PHP, PHPStan and
Larastan, run against the incumbent tree with the bundled collector. *When they
are absent:* there is no report to read, and reading a document that is not one
is a named `ReportInputError` about the fact or kind at fault, never a partial
index. With this flag absent, behavior is identical to capcov main.

**7. Framework assumption rows** (`rules-static-framework-v1`)

```sh
capcov experiment claims static --static scip --target <tree> --language go \
    --assumptions ASSUMPTIONS.json --out bundle.json
```

The edges a *framework* makes out of data, which no indexer can see: a `net/http`
handler registered into a package-level registry by an `init()` and invoked by a
loop at startup, a Laravel container `bind`/`singleton` or facade accessor
Larastan cannot type (one it *can* type is a `larastan-container` edge of piece 6
and must not be re-declared here), a FastAPI `Depends`. The document is
reviewer-signed and looks like this:

```json
{
  "schema_version": 1,
  "reviewer": "who reviewed it",
  "commit": "<the commit the review was signed against>",
  "expires": "2026-12-31",
  "closed": true,
  "assumptions": [
    {"src": "<caller symbol>", "dst": "<callee symbol>", "framework": "net/http",
     "mechanism": "init-registry", "path": "api/jobs.go", "line": 20}
  ]
}
```

* `framework_edge(index, src, dst, framework, mechanism, path, line)` — producer
  class `framework-assumption`, its own class: not `scip` (what an index said),
  not `phpstan` (what an analyser typed), not `reviewer` (intent over symbols).
  `(framework, mechanism)` is an enumerated vocabulary, so a reader can ask
  whether the claim is true of that framework; anything else is refused.
* `framework_assumption_unapplied(index, path, line, src, dst, reason)` — every
  row the producer could not apply, enumerated, never dropped:
  `co_located_residue` (the census gives that line a second unresolved callee,
  and discharge is a `(path, line)` join, so the row is applied not at all),
  `no_unresolved_site`, `document_out_of_scope`.
* `static_edge_assumed(index, src, dst, framework)` and `static_reaches_assumed`
  — the assumed account. `static_edge` is **never** widened.
* `assumptions_closed(index, assumptions)` — the reviewer's own closure, emitted
  only when the document says `closed`, every row was applied, and the scope is
  the whole index. `call_graph_closed_assumed(index, scope)` — that, a census,
  and every unresolved call site in the scope discharged by a row for that exact
  site.
* Every verdict over the assumed graph is a separate row:
  `static_capability_op_assumed`, `static_entity_dead_assumed`,
  `static_entity_blocked_assumed`, `static_convergence_assumed`,
  `static_divergence_assumed`, `static_absence_assumed`.

Each reviewed row is `Evidence.kind == "assumption"`, so
`capcov experiment claims assumptions registry|invalidate` gives it a
run-independent `asm:` id, lists the claims it carries, and can withdraw it:
withdrawing the registry row takes `call_graph_closed_assumed` with it (a witness
that says every site is covered rests on the rows that cover them), leaves the
reviewer's closure standing, and re-derives `static_entity_blocked_assumed`
naming the dispatcher the doubt re-enters through.

*Tools:* none beyond the static profile's own. *When the document is wrong:* an
expired review, a document signed against another commit than the index was
taken at, an unenumerated framework or mechanism, a symbol this index does not
declare, and a closed capability map that omits a symbol an assumed edge runs
through are each `{"refusal": "..."}` with exit 2; anything else is
`{"operational_failure": "static-assumptions-failed", ...}` with exit 3. An
expired document is refused rather than used: an expired assumption is not a
weaker assumption, it is one nobody has looked at since. With this flag absent,
behavior is identical to capcov main.

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
and invalid path/operation shapes fail discovery. Equivalent templated paths
(`/{id}` beside `/{optionId}`) do not: every operation is still inventoried and
the collision is recorded as a `path-shape-collision` boundary carrying both paths,
since the document does not say which serves a concrete path.
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
completeness, and differences need investigation. A contract may expose inherited
administration and authentication operations outside the selected source-flow
scope. Those additional operations receive no coverage merely from discovery.

## Current support

- Python/FastAPI/SQLAlchemy entity discovery and runtime probes.
- Opt-in literal and shared-constant SQLite declarations, with unbound query diagnostics.
- Tree-sitter route source obligations in any supported language, and OpenAPI JSON operations (one config of the generic structured-spec reader).
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

A direct module-level string assignment or annotated string assignment can also
supply the SQL argument. These declarations carry `sqlite_constant_ddl` and their
calls retain `constant_sql_unbound` diagnostics. Resolution requires one binding
with no reassignment, deletion, import or lexical shadow anywhere in that module.
Even shadowing in an unrelated function leaves the name unresolved. Conditional
initialization, aliases, imported constants, string computation and SQL wrappers
remain outside this conservative subset. This is static lexical resolution, not
proof that runtime monkeypatching or dynamic code cannot replace a value.

Literal module mappings of tuples are also supported when a `for` loop unpacks
`SCHEMAS.values()` and its first statement passes a string tuple element directly
to a SQLite execution call. Other reads of the mapping, aliases, mutations,
shadowing, computed entries, duplicate keys and ambiguous unpacking remain
unresolved. This pattern also retains `constant_sql_unbound`; no query or route
binding is inferred from the declaration.

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

At the repository root, `direnv allow` enters the pinned `flake.nix` shell. It
provides Python, uv, Go, jq, and git; uv still resolves capcov itself from the
checked-in lockfile. To exercise capcov against a real non-Python process, run:

```sh
nix develop --command sh -c \
  'cd packages/capabilities && uv run --frozen --extra treesitter sh scripts/check-real-go-flow.sh'
```

That check uses tree-sitter to discover two routes in a Go HTTP server, plans a
save followed by its prerequisite-bound read, executes each scenario against a
fresh server process, reconciles the observations, and gates the result. It then
changes the server to acknowledge without retaining the write and requires the
gate to name `required-flow-failed: read-saved-note`. The example exemptions
record the static-analysis boundaries outside this bounded claim.

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

The bounded qualification measurement runner records command and lock timing,
cache state, and output identities without persisting argv, environment values,
or host paths. Its limits and manifest format are documented in
[`experiments/claim-semantics/qualification-measurement.md`](experiments/claim-semantics/qualification-measurement.md).

## Many worktrees, many agents, one machine

Every artifact binds to a source snapshot: sha256 over a sorted manifest of per-file
hashes. Two caches make that cheap without making it weaker.

- **Per-root manifest** (`~/.cache/capcov/tree-manifests-v1`): a file's digest is reused
  while its size, times, inode and mode are unchanged. Cold for every new checkout.
- **Shared blob index** (`~/.cache/capcov/blob-sha256-v1`): keyed by git blob id. For a
  tracked file that git itself judges byte-identical to its index entry (`git diff-files`,
  the judgement `git commit` relies on), the digest is a fact about the blob, so a fresh
  `git worktree add` of a known commit hashes nothing it has seen in any other checkout.
  Only read-only git plumbing is used. Files git would convert on checkout (filters,
  CRLF, `ident`, working-tree encodings), symlinks, submodules, unmerged, skip-worktree
  and assume-unchanged entries are never keyed by blob; untracked files are hashed.

Both caches are off under `CAPCOV_NO_CACHE=1` and for every verification walk, and any
reuse makes the snapshot inexact (`source_snapshot.verification: cached`). When the two
caches disagree about a file, the bytes are read. The digest formula is unchanged, so no
recorded identity moves. `snapshot_tree(...).verification` reports `files_reused_by_blob`,
`blobs_learned` and a `blob_index` status (`hit`, `learned`, `ready`, `not-a-repo`,
`disabled: core.autocrlf`, ...).

When several agents run indexers, `nix develop` builds, full-tree snapshots or full test
suites on one disk at the same time, none of them finishes. Serialize the heavy steps:

```sh
scripts/with-heavy-lock.py --label "regression" -- \
  nix develop --command bash -lc 'PYTHONPATH="$PWD/src" python -m unittest discover -s tests -t .'
```

One advisory lock per machine (`$CAPCOV_HEAVY_LOCK`, else `~/.cache/capcov/heavy.lock`);
the waiter says who holds it; the child's exit status passes through; `--timeout 0`
fails fast with status 75 instead of waiting. It changes when a step runs, never what it
does.

## Scoped outcome coverage with pytest

### Test capcov's own advancement gate

From `packages/capabilities`, run:

```sh
uv run --frozen --with pytest sh scripts/check-backpressure.sh
```

The checked-in `capcov.toml` and `capcov.outcomes.json` bind a small set of capcov's
own acceptance behaviors to exact tests. The script discovers the actual source
and runs `outcomes check` in disposable copies. Its host creates an `advanced`
marker only on exit zero. It verifies three executions: a passing baseline, an
omitted required check, and a source mutant that suppresses required browser-flow
failures. The negative cases must return 1 and name the intended missing/failed
outcome; an unrelated error is not a successful fault control. The script verifies
cleanup and fails if any expectation is unmet. The existing package CI job runs
this same command before building release artifacts.

This establishes local host enforcement for these capcov obligations. It does not
qualify every capcov feature, prove resistance to an agent rewriting its protected
tests/host, or measure autonomous repair/convergence. Ordinary runs retain no JSON
receipts in the repository; CI retains the terminal command output.

### Bind consumer outcomes

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

For an advancement gate, use the single fresh execution-and-check command:

```sh
capcov outcomes check capcov.outcomes.json --inventory .capcov/inventory.json \
  --python .venv/bin/python --timeout 180 --out .capcov/outcomes-run.json
```

First generate the inventory with `capcov discover` as below. `check` always runs
the union of mapped test IDs, accepts no selection arguments, and returns zero
only when **every authored outcome is demonstrated** with a clean session. Missing
bindings, skips, unresolved outcomes, failures, and timeouts prevent acceptance.
Even an inherited pytest filter that runs a passing subset cannot discharge the
missing cases. The output is the usual run receipt, suitable for `coverage`.
Invalid/stale inputs return 2; valid but unqualified execution returns 1.

Have the existing CI/agent host advance only on exit zero. A host that ignores the
exit code is not enforcing this gate. Keep the accepted map, checker, dependencies,
and invocation under the host's existing trusted revision/review controls; a
candidate that can rewrite those controls can bypass them. This command prevents
accidental old-receipt reuse by executing afresh; it does not sandbox hostile tests
or authenticate their external observations. It has one bounded execution, not
an autonomous retry loop. The caller must bound any retries across invocations.

For diagnostic selection or separate report generation, the existing commands remain:

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

`run` success is execution success, not acceptance: a passing selection can still
leave required outcomes missing. Use `check`, or explicitly invoke `gate` after
`run`, before advancing. Printed success messages from tests do not override the
pytest setup/call/teardown results collected by the probe.

The browser path now also preserves required scenario failures through
`observe --probe browser` → `reconcile` → `gate`. A passing scenario on a shared
route cannot hide a failed/missing scenario. Structural exemptions cannot waive
these failures. Duplicate scenario IDs and nonzero runner exits are rejected;
empty, blocked, assertionless, diagnostic, and `--only` executions cannot qualify
the full plan. Author a separate bounded model to qualify a smaller capability.
Older browser observation files without required-flow results must be regenerated.
Browser runners remain trusted assertion observers; this is not proof that an
arbitrary runner truthfully reports SQL, SMTP, or browser effects.

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


Run evidence may declare `execution_scope: "diagnostic"` when a consumer selects
only one journey for debugging. Such a run can have `status: "passed"`, meaning
the selected execution succeeded, but reconciliation awards **zero coverage**,
does not resolve runtime-mount boundaries, and remains incomplete. This applies
even if the diagnostic happens to execute every planned scenario. Missing scope
defaults to `"full"` for existing runners; an explicit scope must be `"full"` or
`"diagnostic"`, otherwise reconciliation rejects it. Consumers must preserve the
full plan and its digest when selecting diagnostic scenarios and retain all steps
of a selected journey. This flag neither selects scenarios nor supplies their
prerequisites; selection remains a consumer runner responsibility. Plan, source
identity, assertion and request-evidence checks still apply.

An element-relative mouse drag is explicit as well:

```json
{"op":"drag","selector":"#drawing","from":[0.1,0.2],"to":[0.8,0.7]}
```

Coordinates are numeric x/y fractions of the rendered element bounds, from zero
to one. Both pairs are required and must differ; booleans, non-finite values and
out-of-bounds coordinates are rejected. Consumers must resolve the element,
bring it into view, verify that both endpoints can be hit within it, and perform
an actual mouse press/move/release. They must release the button on failure and
must not replace the gesture with direct application-state mutation. Subsequent
assertions still establish the outcome; declaring a drag grants no coverage.
