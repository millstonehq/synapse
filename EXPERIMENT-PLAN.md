# Build an experimental capcov branch from the research

## Workspace handoff

- Repository: `https://github.com/millstonehq/synapse.git` (capcov lives in `packages/capabilities`).
- Local clone: `/Users/reuben/projects/capcov`.
- Experimental branch: `experiment/claim-semantics`.
- Initial main revision: `780173269246f02a7c219b6bd086d1dd93948783`.
- Research archive beside this plan: `capcov-research-2026-09-14.zip`.
- The research inspected PR #45 at `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765`. It is not the initial main revision; inspect current upstream and PR state before choosing the implementation base.
- Setup only: no experimental engine implementation has been started by this handoff.

The remainder is the implementation prompt. Read it together with the research archive.

## 1. Objective

You are developing an experimental branch of capcov. The attached ZIP contains seven independent research reviews and a cross-review synthesis.

Your task is to turn the strongest ideas into a coherent, runnable experiment that demonstrates additional reasoning and testing capabilities. Do not merely add research references, configuration fields, or another reporting layer.

This experiment is explicitly authorized to explore substantial architectural changes. Preserve the existing production engine and consumer behavior while developing the experimental path. Do not merge or deploy the experiment without a separate decision.

Build an executable system of scoped claims that can answer:

1. What exactly is being claimed?
2. Which observations justify it?
3. Which rules and assumptions connect those observations?
4. Is there contrary evidence, or simply missing evidence?
5. Which conclusions lose support when an assumption changes?
6. What observation or experiment would distinguish the remaining explanations?
7. Can the fixed claim semantics and application model be specialized into a smaller executable checker without losing these distinctions?

The central experiment is:

```text
reviewed claim semantics
    + application model
    + immutable observations
    + explicit assumptions
    ↓
scoped verdicts and replayable derivations
    ↓
explanations, invalidation, and experiment proposals
    ↓
specialized executable checker
```

The architectural hypothesis is that one explicit representation of claim rules can support checking, explanation, support maintenance, experiment proposals, and specialization with less semantic duplication than separate handwritten implementations.

Treat that as a hypothesis to test, not a conclusion to defend.

## 2. Read the materials and inspect current reality

Extract and read:

- `synthesis.md`
- `shen.md`
- `futamura.md`
- `truth-maintenance.md`
- `datalog.md`
- `lineage-faults.md`
- `automata-learning.md`
- `egglog.md`

Begin with the synthesis, Shen, and Futamura reports. Use the other reports to challenge the design.

The research inspected PR #45 at:

```text
d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765
```

That is a historical research baseline. Inspect current upstream main and PR state before choosing the experimental base. Identify which findings remain applicable, which have already been fixed, and which interfaces changed.

Pay particular attention to:

- entity-level aggregation in reconciliation;
- HTTP-verb-to-CRUD projection;
- assertion information lost during projection;
- duplicate obligation identities across producers;
- source, run, and scope provenance;
- unresolved and excluded observations;
- existing outcome-level evidence, which may already be stronger than the structural summary.

Do not redesign a component merely because the report discusses it.

Use the isolated experimental branch with an explicitly recorded base revision. Use this maintained experiment document, updating it as the design changes. Avoid a hierarchy of subordinate planning documents.

## 3. Architectural decisions

### Preserve Python's legitimate role

Capcov is already Python. Continue using Python where it is the simplest implementation choice. This is not a request to rewrite capcov in Go or eliminate Python.

However:

- Do not implement notification business behavior in Python.
- Existing Go/PHP applications and fixtures remain the systems under examination.
- Do not create a parallel deployment or orchestration framework.
- Reuse existing process execution, artifact, provenance, and test infrastructure where suitable.

### Build one semantic contract

Define one canonical, versioned claim-rule representation.

A JSON-serializable typed IR is a reasonable starting point. Prefer explicit relation schemas and rule forms over unconstrained generic triples or arbitrary embedded code.

The architecture should contain:

1. Immutable evidence records.
2. Scoped claim instances.
3. Versioned rules and assumptions.
4. Explicit support and refutation.
5. Ground derivation certificates.
6. A small deterministic certificate checker.
7. An interpreter/reference evaluator.
8. A Shen experimental elaboration/search path.
9. An application-specific specialization path.
10. A bounded experiment-proposal mechanism.

These are responsibilities, not ten services.

Do not introduce a separate authoritative gate for every engine. During research, implementations are compared against independently reviewed expected results. If they disagree, neither wins merely because it is older, faster, or implemented in a preferred language.

### Select tools by role

Use the research as follows:

- **Datalog:** relational semantics, explicit joins, bounded recursion, and principled treatment of negation. Soufflé is not a mandatory dependency unless it materially improves the experiment.
- **Truth maintenance:** shared support structures, eligibility changes, alternative derivations, and bounded support/conflict queries.
- **Shen:** rule elaboration, derivation search, authority checks over rule forms, and missing-premise reasoning.
- **Futamura/partial evaluation:** specialize a genuine interpreter over fixed rules and application expectations.
- **Lineage and active learning:** generate targeted challenges and distinguishing experiments.
- **Egglog:** reserve a narrowly defined optional experiment for equivalent descriptions or proof plans. Do not globally equate declarations, routes, handlers, and observations.

The mandatory core is the claim semantics, support maintenance, checked derivations, Shen path, specialization path, and one concrete experiment-generation result.

Do not make full ATMS materialization, self-applicable compiler generators, whole-application automata learning, or egglog integration prerequisites for completing that core.

## 4. Semantic requirements

### Separate records from conclusions

Distinguish:

```text
producer reported X
record passed admissibility checks
record supports a particular proposition
proposition participates in a valid derivation
claim is justified under stated assumptions
gate policy permits a particular decision
```

A hash or signature can authenticate a record without proving that its account of application behavior is correct.

An HTTP POST observation must never establish database creation solely through a method-to-CRUD convention.

### Preserve context and causal identity

Claims and evidence must retain the fields necessary to prevent invalid joins, including as applicable:

- candidate and reference build roles;
- environment and configuration;
- tenant and actor;
- run and observation interval;
- request, event, notification, recipient, and attempt identities;
- outcome and quantifier;
- producer, validator, rule, and schema versions.

Do not require naive equality across entire contexts. PHP and Go intentionally have different build identities. Define explicit compatibility witnesses for legitimate comparisons.

Conversely, omitting a field must not silently authorize aggregation across its values. Represent deliberate quantification or aggregation explicitly.

### Distinguish uncertainty from contradiction

Represent at least:

- supported;
- refuted;
- unresolved;
- conflicting evidence.

Keep operational failures such as invalid evidence, unsupported constructs, and resource exhaustion distinguishable from these semantic states.

Define how support/refutation statuses relate to the possible-histories semantics described in the research. Do not assume they are automatically identical.

An inconsistent assumption set must not establish arbitrary claims through vacuous reasoning.

### Make absence require a completeness premise

Negation over a complete authored inventory is different from negation over incomplete telemetry.

“No SMTP observation exists” must not mean “no SMTP attempt occurred” unless a scoped observation-completeness premise justifies that inference.

Completeness premises must identify their actual scope and limits. They are not universal certificates of truthful instrumentation.

### Preserve claim strength

Keep these separate:

- this request was observed;
- this effect was committed;
- this message was accepted;
- this bounded replay produced no second acceptance;
- all executions satisfy a safety property.

A finite successful run must not automatically establish a universal capability claim.

### Preserve historical evidence

Changes to builds, rules, assumptions, or collector validity may change whether evidence supports a current claim. They must not rewrite or erase the original observations.

### Separate kinds of dependency

Do not collapse:

- static possible calls;
- dependencies observed in one execution;
- counterfactual causal dependencies;
- logical derivation dependencies;
- evidence provenance.

Removing a receipt changes knowledge. Injecting a provider failure changes application behavior. Report them as different experiment classes.

## 5. Implementation sequence

For each stage, produce runnable code, meaningful tests, a concise result, and explicit remaining limits.

### Stage A — Establish the adversarial semantic corpus

Before choosing engine machinery, create a small corpus with reviewed expected verdicts.

Include:

1. A correctly correlated positive notification execution.
2. Static evidence from route A and runtime evidence from route B touching the same entity.
3. Successful POST without demonstrated creation.
4. A passing authorization path alongside a failing denial.
5. An accepted email belonging to a different event.
6. Cross-tenant or cross-run evidence contamination.
7. Two producers repeating one mistaken assumption.
8. Explicit rejection versus missing observation.
9. Support and refutation for the same scoped attempt.
10. A revoked assumption with an independent surviving derivation.
11. Empty and mixed compatible-history sets in a bounded model.
12. An unexpected runtime surface absent from the application model.
13. Provider acceptance followed by failed SQL acknowledgment.
14. A bounded no-resend observation incorrectly promoted to indefinite safety.

Label synthetic histories and seeded faults clearly. Do not claim these are demonstrated defects in the current production engine unless you actually reproduce them.

The existing implementation is a regression comparator, not the source of the expected semantics.

### Stage B — Implement typed claims and multiple producers

Implement the canonical evidence, claim, rule, and context structures.

Allow multiple producers to make separately attributable statements about one subject. Preserve disagreement and shared provenance.

Implement a deterministic reference evaluator for the deliberately restricted rule language. Define supported recursion, negation, aggregation, and termination/resource behavior.

Keep the initial language small enough that its semantics can be written clearly and tested exhaustively on bounded domains.

Expose the experimental path through existing CLI conventions where practical. Preserve legacy behavior unless an explicit experimental mode is selected.

### Stage C — Add proof certificates and bounded support maintenance

Make successful derivations explicit objects.

A certificate should identify:

- the exact conclusion;
- rule applications;
- evidence leaves;
- assumptions;
- context compatibility witnesses;
- relevant rule/model versions.

Implement a ground certificate checker that does not perform unbounded search, launch processes, or collect evidence.

Add shared AND/OR support structures and queries for:

- why a claim is supported;
- which premise is missing;
- which assumptions every support path shares;
- which conclusions depend on a changed premise;
- whether alternative support survives;
- small conflict or support-cut explanations.

Bound expensive enumeration and report incomplete explanations honestly.

Do not eagerly enumerate every hypothetical context merely to call the result an ATMS.

### Stage D — Implement the Shen semantic-workbench experiment

Implement a real Shen path, not a placeholder or a document describing one.

Use the canonical rule representation to:

1. Elaborate a restricted rule pack.
2. Check selected structural authority constraints.
3. Search for a notification derivation.
4. Emit an explicit derivation certificate.
5. Produce a bounded missing-premise explanation.
6. Replay the certificate through the independent checker.

Investigate authority checks that reject:

- ungrounded conclusion variables;
- lost tenant/run/causal indices;
- unsupported scope widening;
- negative conclusions without completeness premises;
- demonstrated effects derived only from declarations;
- unapproved effectful side conditions.

Keep the distinction clear:

> Rejecting invalid rule forms is useful, but does not prove arbitrary domain rules sound.

Freeze and identify the expanded rule representation. Avoid runtime mutation of the accepted rule pack.

Do not assume Shen's native typechecker emits portable proof certificates. Do not mistake Shen's `specialise` function for a partial evaluator.

If tooling blocks execution, diagnose that concrete issue and report it. Do not substitute a mocked Shen result and call the milestone complete.

### Stage E — Implement first-projection specialization

Define an interpreter with an explicit boundary, for example:

```text
interpret(rule_program, application_model, fresh_evidence)
    → verdicts + derivations + missing premises + discrepancies
```

Specialize on the rule program and application model.

Produce:

- an executable residual checker;
- an explicit dynamic evidence interface;
- an assumption/validity manifest;
- retained derivation information;
- context checks;
- handling of relevant contradictions and unexpected observations.

Be precise about whether the implementation is partial evaluation, staged interpretation, or ordinary compilation. Explain the relationship to the first Futamura projection. Generating JSON plans alone does not satisfy this stage.

Preserve semantics for unsuccessful inputs too:

- malformed;
- incomplete;
- contradictory;
- stale;
- out of scope;
- unexpectedly extended.

The evidence interface may be conservatively sufficient; do not claim it is minimal without proving that.

Compare interpreter and specialized results on the adversarial corpus and bounded generated inputs. Compare meaningful verdicts and explanation content, not only a Boolean exit status.

Introduce a controlled specializer defect—such as dropping an identity check or unexpected-surface path—and demonstrate that validation catches it.

Do not implement the second or third projections in this stage. Explain what demonstrated semantic duplication would justify them later.

### Stage F — Generate one useful experiment from an explanation

Implement a bounded experiment catalog using existing fixture/executor infrastructure.

Demonstrate at least:

- a missing-premise query producing a concrete observation request;
- a shared-assumption support cut producing a checker challenge;
- two histories with the same coarse summary producing a distinguishing experiment.

Use the held-notification case where practical:

```text
no provider contact
provider accepted but response was lost
provider accepted but SQL acknowledgment failed
```

Show what the available observations can and cannot distinguish.

Distinguish evidence perturbations from application fault injection. Only the latter can demonstrate application resilience behavior.

The planner may propose actions from an explicit catalog. It must not invent shell commands or treat arbitrary generated actions as safe and executable.

Execute at least one generated proposal in an isolated fixture, capture fresh results, and feed those results back into claim evaluation.

A planner that merely prints “add a test” does not satisfy this stage.

### Stage G — Integrate one actual Go notification execution

Consume an existing Go-produced execution receipt or extend its observation interface minimally where a demonstrated missing correlation requires it.

Do not reimplement grouping, rendering, authorization, retry, or scheduling.

Demonstrate:

```text
real execution
→ admitted observations
→ scoped claim
→ Shen-produced derivation
→ independent certificate validation
→ specialized checker agreement
→ useful explanation
```

Also execute a relevant negative control.

Preserve the distinction between synthetic semantic fixtures, disposable integration runs, deployed evidence, and whole-program acceptance.

### Stage H — Evaluate and report

Evaluate at least:

- semantic correctness against the reviewed corpus;
- valid and invalid certificate handling;
- multiple-producer behavior;
- context isolation and compatibility;
- preservation of unknown and conflicting states;
- support invalidation precision;
- explanation usefulness;
- interpreter/specializer agreement;
- detection of seeded checker/compiler defects;
- one generated experiment's actual result;
- runtime, startup/compilation cost, memory, and artifact size;
- dependency and maintenance burden.

Report failures and architectural discoveries, not just successes.

## 6. Optional bounded extensions

Only after the mandatory core is working, select at most one additional experiment based on the evidence gathered.

Candidates:

- A Soufflé evaluator for comparison with the canonical relational semantics.
- Egglog for equivalent pure descriptions or proof-plan terms.
- Active learning over a small claim-relative state space.
- A constrained hitting-set planner for an already enumerated fault catalog.
- A second-projection experiment if a real interpreter/compiler duplication has emerged.

State the hypothesis and falsifier before implementing it.

Do not silently broaden this into seven mandatory toolchains.

## 7. Working discipline

Use bounded parallel work where it genuinely helps. Give each agent explicit file ownership and a shared semantic interface. Assign an independent reviewer to attack the claim semantics and trust boundary.

Keep one integrator responsible for:

- the canonical IR;
- expected verdicts;
- interface changes;
- conflict resolution;
- final experimental results.

Do not let several agents independently invent incompatible claim schemas.

Maintain a runnable path throughout development. At coherent checkpoints, record:

- exact revision;
- completed behavior;
- commands and results;
- observed failure or limitation;
- the next experiment that resolves a real uncertainty.

Keep routine run artifacts out of version control. Commit stable semantic fixtures, code, tests, and concise reproducible result summaries.

Do not alter the full FacilityGrid acceptance denominator, adopt experimental results as production coverage, or automatically upgrade the production consumer.

## 8. Required deliverables

Deliver:

1. An experimental branch with a recorded base revision.
2. A concise architecture and semantic specification.
3. The canonical typed claim/rule/evidence representation.
4. The adversarial corpus and reviewed expected results.
5. The reference evaluator.
6. Explicit derivation certificates and an independent ground checker.
7. Bounded support, invalidation, why, and why-not queries.
8. An executable Shen implementation of the selected semantic-workbench functions.
9. A genuine specialization implementation and executable residual checker.
10. One generated experiment that was actually executed.
11. One real Go notification execution consumed through the experimental path.
12. A reproducible evaluation report.
13. A clear recommendation: retain as research, revise, or propose specific pieces for production adoption.

Include exact reproduction commands and identify required tools. Where dependency-free replay is feasible, make retained evidence and certificates checkable without rerunning the application.

## 9. Definition of success

The experiment succeeds if it demonstrates useful capabilities that current entity-level accounting cannot express reliably, while preserving the trust and scope boundaries.

In particular, it must demonstrate that:

- unrelated evidence cannot manufacture a matching behavioral claim;
- multiple producers can corroborate without overwriting or manufacturing independence;
- missing evidence and contrary evidence remain different;
- conclusions carry replayable justification;
- changing an assumption invalidates the correct support paths;
- specialization preserves uncertainty and relevant surprises;
- one explanation leads to a useful executed experiment;
- Shen and specialization contribute measurable clarity, generative capability, or assurance—not merely additional syntax.

A negative result is valuable if it clearly identifies why the architecture fails or which simpler approach achieves the same capability.

Do not declare success because the tools run, the examples are attractive, or every implementation agrees. Declare success only when the reviewed semantics, adversarial controls, and real execution evidence support it.

---

# Detailed implementation plan

## 10. Current-reality findings

This implementation plan was formulated after reading this document and all eight reports in `capcov-research-2026-09-14.zip`.

### Repository and branch state

- Current branch: `experiment/claim-semantics`.
- Current checkout and upstream `main`: `780173269246f02a7c219b6bd086d1dd93948783`.
- PR #45 is open, non-draft, and mergeable. Its head is `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765`, based directly on `7801732` with 16 additional commits.
- The current-main capability suite passes 300 tests with 21 skips under the locally available Python 3.14. The supported version remains Python 3.12 or newer.
- `uv` is not available outside Nix in the present environment.
- A local Shen Go/KL executable exists, but it is a dirty, non-reproducible build and must not be treated as the experiment dependency.
- No FacilityGrid Go/PHP checkout or real notification execution fixture is present in this repository. That external integration is an explicit dependency, not something to replace with synthetic Python notification behavior.

### Research findings that remain applicable

PR #45 does not resolve the central semantic issues:

- `core/reconcile.py` still aggregates by entity before assigning `both`.
- The route adapter and browser probe still share the `POST -> create` convention.
- Browser assertion detail is flattened into whether a route binding is emitted.
- Multi-adapter discovery rejects duplicate obligation identities rather than retaining statements from multiple producers.
- Request, event, notification, recipient, attempt, tenant, and run correlation are not part of the core coverage identity.
- The production four-cell result cannot represent support and refutation for the same precise claim.

### Existing improvements to reuse

PR #45 adds infrastructure that should be reused rather than rebuilt:

- unified adapter and probe interfaces;
- browser evidence with nonce and source freshness checks;
- runtime mount census and namespaced outcome evidence;
- propagation of `excluded_surfaces` and `unresolved` through reconciliation and gate;
- generic tree-sitter and structured-spec discovery;
- Go/PHP static recognizers and deeper SCIP handling;
- explicit diagnostic execution scope.

Current main also has a stronger independent outcome lane in `outcomes.py`: exact pytest IDs, source/input hashes, a fresh nonce, and differentiated statuses. Preserve and reuse those patterns.

## 11. Base and branch strategy

Fast-forward the experimental branch to the exact reviewed PR #45 head:

```sh
git merge --ff-only d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765
```

Record both revisions at every experiment checkpoint:

```text
production baseline: 780173269246f02a7c219b6bd086d1dd93948783
experimental integration base: d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765
PR #45 state when selected: open, mergeable
```

This is appropriate because `d1550e4` is a direct descendant of current main, the research reviewed that exact revision, and it supplies probe/provenance/Go/PHP infrastructure needed by later stages. All claim behavior remains under a new experimental CLI namespace; production reconciliation and gates remain unchanged.

Do not silently rebase if PR #45 changes. A later update requires a separately recorded base-refresh decision and full differential testing.

## 12. Target architecture

```text
Existing adapters, probes, and receipts
        |
        v
Producer-specific boundary validation
        |
        v
Immutable typed observations + explicit assumptions
        |
        v
Canonical claim/rule/model IR
        |
        +--> deterministic Python reference evaluator
        |        +--> signed support/refutation
        |        +--> derivation certificates
        |        +--> missing premises and discrepancies
        |
        +--> bounded AND/OR support maintenance
        |
        +--> Shen elaboration and proof search
        |        +--> authority diagnostics
        |        +--> certificate
        |        +--> bounded why-not result
        |
        +--> first-projection specializer
                 +--> executable residual checker
                 +--> evidence ABI
                 +--> assumption manifest
                 +--> novelty/contradiction sentinel
                 +--> certificates for independent replay

Missing premises and support cuts
        |
        v
Bounded catalog-based experiment planner
        |
        v
Existing isolated fixture executor
        |
        v
Fresh observations fed back to evaluation
```

### Trust boundaries

- Existing applications remain responsible for notification business behavior.
- Producers report records; they do not award claims.
- Boundary validators establish record admissibility, not real-world truth.
- Rules define permitted inference and are versioned and reviewed.
- Python and Shen search are certificate producers, not self-authorizing gates.
- A small Python ground checker validates certificates without search, collection, or subprocess execution.
- Corpus expectations are independently reviewed. Neither evaluator wins disagreements by precedence.
- Gate policy remains downstream and separate from semantic verdicts.

## 13. Canonical semantic model

Create this package structure:

```text
packages/capabilities/src/capcov/claims/
  __init__.py
  ir.py
  validation.py
  evaluator.py
  verdicts.py
  certificates.py
  support.py
  shen.py
  specialize.py
  residual.py
  experiments.py
  go_receipt.py
  cli.py
```

Responsibilities:

- `ir.py`: typed records and canonical serialization.
- `validation.py`: schema, authority, and context checks.
- `evaluator.py`: deterministic reference interpreter.
- `verdicts.py`: semantic and operational result algebra.
- `certificates.py`: certificate model and ground checker.
- `support.py`: shared AND/OR graph and bounded queries.
- `shen.py`: pinned runtime adapter and deterministic data transport.
- `specialize.py`: partial evaluator over the executable interpreter representation.
- `residual.py`: generated artifact loading and execution support.
- `experiments.py`: closed proposal catalog and planner.
- `go_receipt.py`: Go receipt admission adapter.
- `cli.py`: experimental CLI integration.

### Canonical bundle

Use a versioned JSON-serializable document containing:

- relation declarations;
- immutable contexts;
- scoped claims;
- observations;
- assumptions;
- compatibility witnesses;
- completeness premises;
- application-model facts;
- rules and explicit refutation rules;
- producer and validator metadata;
- schema, rule, and model digests.

Avoid unconstrained triples. Each relation declaration specifies its name, arity, typed columns, semantic modality, polarity, binding time, accepted producer classes, required context indices, and whether it is primitive or derived.

### Identity and context

Preserve, where applicable:

- candidate/reference role and build identity;
- source, model, and configuration digest;
- environment;
- tenant and actor;
- run and observation interval;
- request, event, notification, recipient, message, and attempt identities;
- producer, validator, rule, and schema versions;
- outcome scope and quantifier.

Exact equality is the default within one rule. Cross-context joins require a typed compatibility witness such as `ComparableRuns(reference, candidate, scenario)`. Omitting a dimension must not imply aggregation. Universal and multi-context claims must explicitly quantify over a closed domain.

### Restricted rule fragment

Support initially:

- finite typed domains;
- positive Horn-style bodies;
- positive recursion only;
- stratified negation;
- no function symbols;
- deterministic equality, ordering, and bounded arithmetic built-ins;
- explicit finite aggregation;
- explicit evaluation limits.

A negated telemetry predicate requires a scoped completeness premise in the same derivation. Aggregation requires a named finite domain, a closure witness, and a non-empty domain for universal conclusions. Unsupported recursion, recursive negation, unsafe variables, arbitrary embedded code, and effectful side conditions fail validation.

### Verdict model

Represent positive support and refutation independently:

| Support | Refutation | Semantic verdict |
|---|---|---|
| yes | no | `supported` |
| no | yes | `refuted` |
| no | no | `unresolved` |
| yes | yes | `conflicting` |

Keep operational state separate:

```text
complete
invalid-input
inconsistent-premises
resource-exhausted
unsupported-construct
stale
out-of-scope
```

An empty compatible-history set yields `inconsistent-premises` and no semantic success. It is not the same as conflicting evidence.

Possible-histories classification is a separate evaluation basis: `derivational`, `bounded-history-model`, or `finite-basis-with-certificate`. Do not claim derivational support is automatically equivalent to truth in all compatible histories.

## 14. Stage 0 — Reproducible Nix toolchain

The root `flake.nix` and generated `flake.lock` now provide the Stage 0 toolchain. This does not change production capcov behavior or add claim behavior.

### Stage 0 pinned inputs

- Repository HEAD tested: `ba3d729f452b017b2f99e2d22d548863b97dd1de`; required integration ancestor: `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765` (verified with `git merge-base --is-ancestor`, exit 0).
- nixpkgs: `34ab99075ac4f7e40cf037eef32cb1c360bb85e9`, lock `narHash` `sha256-hn1oU2rue2SYK8dAr8+WNZWtbsz1S2W5mnHlSEuh3bo=`. The generated lock file SHA-256 was `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac` before and after frozen checks.
- shen-go: clean upstream commit `610ba423795b38e58dde3515a0583a109411433c` (2026-09-09), fetched with source hash `sha256-nhJdMOcSFY5Kfd695pTGGRfrtnqBdFuy5ZLoa9tfT5Y=` and `buildGoModule` vendor hash `sha256-iTtlmSlY0qbH/1waOlfRMc1qAkBacQxI6pohRPni/so=`. The only built subpackage is `cmd/shen`, producing the actual executable `bin/shen`. No version-only shim or local executable is used: normal calls, `--version`, and `eval` all execute that packaged binary. Its standard library is embedded upstream. `GOTOOLCHAIN=local` prevents Go's automatic toolchain download.
- Advertised systems: `aarch64-darwin`, `aarch64-linux`, and `x86_64-linux`. `x86_64-darwin` is intentionally excluded because this nixpkgs revision does not support it. All advertised outputs evaluated with `--all-systems --no-build`; only `aarch64-darwin` was built and executed in this run.
- Host: `aarch64-darwin`, Darwin kernel `25.5.0`; Nix reported `nix (Determinate Nix 3.21.5) 2.34.8`.
- Observed shell tools: Python `3.12.14`, uv `0.12.5`, Go `1.27.0`, Git `2.55.0`, jq `1.8.2`, and hyperfine `1.20.0`. Every resolved executable path was under `/nix/store`. The development shell sets `UV_PYTHON_DOWNLOADS=never`, `UV_PYTHON_PREFERENCE=only-system`, and `UV_PYTHON` to Nix Python; `uv python find` and `uv run --no-project python` both resolved `/nix/store/...python3-3.12.14/bin/python`. A small Nix `bash` launcher suppresses macOS login-profile `path_helper`, which otherwise put `/usr/bin/git` and `/usr/bin/jq` ahead of the pinned tools for the workflow's `bash -lc` form.

### Stage 0 commands and observed results

```sh
nix flake check --no-update-lock-file
```

Exit 0. On `aarch64-darwin` this built/checked the shen-go package, ran a real evaluator smoke (including malformed-input rejection), and ran the regression check in a writable source copy. The check's regression run reported `Ran 490 tests in 27.665s`, `OK (skipped=69)` during the uncached build. A final frozen invocation also exited 0. Nix warned that Linux checks were omitted on this host.

```sh
nix develop --command bash -lc '
  set -eu
  python -c "import sys; assert sys.version_info[:2] == (3, 12); print(sys.executable, sys.version)"
  uv --version
  go version
  git --version
  jq --version
  hyperfine --version
  for command in python uv go git jq hyperfine shen; do
    path=$(command -v "$command")
    case "$path" in /nix/store/*) ;; *) exit 1;; esac
  done
  command -v shen
  shen --version
'
```

Exit 0 after correcting macOS login-shell PATH handling. The resolved Shen path was `/nix/store/m6vdgvc4g4djhm9ld1s16jrd39k001lm-shen-go-0-unstable-2026-09-09/bin/shen`; `shen --version` printed `42 (port ("Go" "1.0.0-rc1") implementation ("AOT+interpreter" "go1.27.0"))`. The upstream CLI reports the Shen language/runtime information rather than its Git revision, so the immutable revision is recorded above and in `flake.nix`.

```sh
nix develop --command bash -lc \
  'cd packages/capabilities &&
   PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 490 tests in 3.347s`, `OK (skipped=67)`, no failures or errors. This exact development-shell run has two fewer skips than the Python-only Nix check because the full shell provides pinned Go and Git.

```sh
nix develop --command bash -lc \
  'set -eu; output=$(shen eval -e "(+ 20 22)");
   printf "%s\n" "$output"; test "$output" = 42;
   ! shen eval -e "(+ 1" >/dev/null 2>&1'
```

Exit 0; evaluator output was exactly `42`, and malformed input exited nonzero. This is execution evidence; the weaker `--version` result is not treated as an evaluator smoke.

```sh
out=$(nix build .#shen-go --no-link --print-out-paths --no-update-lock-file)
nix path-info -Sh "$out"
"$out/bin/shen" --version
"$out/bin/shen" eval -e '(+ 20 22)'
```

Exit 0. The independently built output was the store path above, closure size was `22.2 MiB`, and evaluation printed `42`.

```sh
nix flake check --all-systems --no-build --no-update-lock-file
```

Exit 0 and evaluated all advertised package, shell, and check derivations; it did not build or execute Linux derivations.

Attempt 3 re-verified the frozen result with:

```sh
nix flake check --no-update-lock-file
nix flake check --all-systems --no-build --no-update-lock-file
nix develop --no-update-lock-file --command bash -lc '
  set -eu
  python -c "import sys; assert sys.version_info[:2] == (3,12); print(sys.version)"
  uv --version; go version; git --version; jq --version; hyperfine --version
  output=$(shen eval -e "(+ 20 22)"); test "$output" = 42
  cd packages/capabilities
  PYTHONPATH=src python -m unittest discover -s tests -t .
'
```

All three commands exited 0. The two flake checks evaluated the current frozen outputs (the host checks were already present in the Nix store); all-system evaluation remained build-free. The development-shell run observed the same tool versions listed above, evaluated Shen to `42`, and reported `Ran 490 tests in 2.510s`, `OK (skipped=67)`. `shasum -a 256 flake.lock` still reported `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac` after these commands.

An initial `nix flake check` attempt failed because `-buildvcs=false` was incorrectly supplied as a linker flag; that flag was removed and is not present in the final derivation. The successful package build used the fixed vendor derivation and then passed upstream `cmd/shen` checks. No external prerequisite or host Shen executable was used.

**Limit:** this run cannot honestly establish the clean-checkout exit criterion: the new flake and lock were necessarily uncommitted while being tested, and Linux was evaluation-only. The frozen lock, fixed source/vendor hashes, sandboxed checks, and Nix-store command paths provide reproducibility controls, but a driver-owned commit followed by a fresh clean-checkout build (and Linux execution) remains to be demonstrated.

### Workflow toolchain re-verification (attempt 1, 2026-09-14)

Re-ran Stage 0 gates on committed HEAD `233d1eca99a11ae24e75d77566b47749406af1f5` (ancestor of `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765` still holds). Host remained `aarch64-darwin`, Darwin kernel `25.5.0`, Nix `nix (Determinate Nix 3.21.5) 2.34.8`. `flake.nix` / `flake.lock` were not changed; `shasum -a 256 flake.lock` is still `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac`.

Pinned tools observed again through `nix develop --no-update-lock-file --command bash -lc`: Python `3.12.14`, uv `0.12.5`, Go `1.27.0`, Git `2.55.0`, jq `1.8.2`, hyperfine `1.20.0`, Shen path `/nix/store/m6vdgvc4g4djhm9ld1s16jrd39k001lm-shen-go-0-unstable-2026-09-09/bin/shen`. Every resolved executable, including the workflow `bash` wrapper, was under `/nix/store`. `uv python find` resolved the same Nix Python. `shen --version` printed `42 (port ("Go" "1.0.0-rc1") implementation ("AOT+interpreter" "go1.27.0"))`; `shen eval -e "(+ 20 22)"` printed exactly `42`; malformed `shen eval -e "(+ 1"` exited nonzero.

```sh
nix flake check --no-update-lock-file
```

Exit 0. Rebuilt `checks.aarch64-darwin.capability-regression`, `shen-evaluator-smoke`, and `shen-package`. Linux checks were omitted on this host. The sandboxed regression copies `${self}` and therefore has no `.git` history; the origin/main baseline tests skip there.

```sh
nix flake check --all-systems --no-build --no-update-lock-file
```

Exit 0. Evaluated advertised package, shell, and check derivations for `aarch64-darwin`, `aarch64-linux`, and `x86_64-linux` without building Linux.

```sh
nix develop --no-update-lock-file --command bash -lc \
  'set -eu; output=$(shen eval -e "(+ 20 22)"); test "$output" = 42; ! shen eval -e "(+ 1" >/dev/null 2>&1'
```

Exit 0.

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 1: `Ran 490 tests in 2.279s`, `FAILED (failures=1, skipped=67)`. The single failure is `tests.test_cli_engine.ObservePytestBackCompatTests.test_default_probe_env_matches_origin_main`. Isolated re-run also failed. The test prefers live `origin/main` over the recorded production baseline `780173269246f02a7c219b6bd086d1dd93948783`. Current `origin/main` is `f5775bdaa513bd155ae19166ca9693f45a07be84` (`docs(verification): require independent fixture premises`, 2026-09-14 12:12:02 -0500). That blob's `cli.py` now also sets `CAPCOV_NONCE` to `uuid.uuid4().hex`, so the baseline and current observe envs both contain a nonce and they differ. This is not a flake, Shen, or Nix-store-path defect. The toolchain write set cannot change the test or `origin/main`. The earlier Stage 0 develop-shell `OK (skipped=67)` result was recorded when `origin/main` still matched `7801732`.

**Limit:** Stage 0 pinning is unchanged and Shen smoke is still real evaluator evidence. The workflow regression gate cannot pass on this checkout until `origin/main` stops being a moving observe-env baseline or the test is pointed at the recorded experimental baseline. That change is outside this task's write set. Linux execution and a driver-owned clean-checkout rebuild remain undemonstrated. The pinned `shen-go` revision remains accepted only for the observed smoke, not for Stage D.

### Workflow toolchain re-verification (attempt 2, 2026-09-14)

Independently re-ran Stage 0 gates on the same committed HEAD `233d1eca99a11ae24e75d77566b47749406af1f5` (ancestor of `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765` still holds). Host remained `aarch64-darwin`, Darwin kernel `25.5.0`, Nix `nix (Determinate Nix 3.21.5) 2.34.8`. `flake.nix` / `flake.lock` were not changed; `shasum -a 256 flake.lock` is still `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac`. Attempt 1's uncommitted plan notes were already present, so `nix flake check` warned `Git tree '/Users/reuben/projects/capcov' has uncommitted changes`.

Pinned tools observed again through `nix develop --no-update-lock-file --command bash -lc`: Python `3.12.14` at `/nix/store/p1wfv7znig26m3hns4583cb9va3kzxkg-python3-3.12.14/bin/python`, uv `0.12.5`, Go `1.27.0`, Git `2.55.0`, jq `1.8.2`, hyperfine `1.20.0`, Shen path `/nix/store/m6vdgvc4g4djhm9ld1s16jrd39k001lm-shen-go-0-unstable-2026-09-09/bin/shen`. Every resolved executable, including the workflow `bash` wrapper, was under `/nix/store`. `uv python find` resolved the same Nix Python. `shen --version` printed `42 (port ("Go" "1.0.0-rc1") implementation ("AOT+interpreter" "go1.27.0"))`; `shen eval -e "(+ 20 22)"` printed exactly `42`; malformed `shen eval -e "(+ 1"` exited nonzero.

```sh
nix flake check --no-update-lock-file
```

Exit 0. Rebuilt `checks.aarch64-darwin.capability-regression` because the dirty Git tree changed `${self}`; `shen-evaluator-smoke` and `shen-package` were previously built. Linux checks were omitted on this host. The sandboxed regression copies `${self}` and therefore has no `.git` history; the origin/main baseline tests skip there.

```sh
nix flake check --all-systems --no-build --no-update-lock-file
```

Exit 0. Evaluated advertised package, shell, and check derivations for `aarch64-darwin`, `aarch64-linux`, and `x86_64-linux` without building Linux.

```sh
nix develop --no-update-lock-file --command bash -lc \
  'set -eu; output=$(shen eval -e "(+ 20 22)"); test "$output" = 42; ! shen eval -e "(+ 1" >/dev/null 2>&1'
```

Exit 0.

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 1: `Ran 490 tests in 4.844s`, `FAILED (failures=1, skipped=67)`. Isolated re-run of `tests.test_cli_engine.ObservePytestBackCompatTests.test_default_probe_env_matches_origin_main` also failed in 0.547s. The assertion compared two distinct `CAPCOV_NONCE` hex strings (`AssertionError: '6dace5cab8c640298ded85349b4360e4' != '209156a87b31473385cb6e24d9fc7fcd' : CAPCOV_NONCE` on the full suite; a different pair on the isolated re-run). `_origin_main_cli_source()` still prefers live `origin/main` over recorded production baseline `780173269246f02a7c219b6bd086d1dd93948783`. Current `origin/main` remains `f5775bdaa513bd155ae19166ca9693f45a07be84`. Direct `git show` of `packages/capabilities/src/capcov/cli.py` shows `uuid.uuid4` / `CAPCOV_NONCE` on `origin/main` and `HEAD`, and neither on `7801732`. This is not a flake, Shen, or Nix-store-path defect. The toolchain write set cannot change the test or `origin/main`. Making `nix develop` hide `origin/main` so the test fell back to `7801732` would be a false pass, not a toolchain pin.

**Limit:** Stage 0 pinning is unchanged and Shen smoke is still real evaluator evidence. The workflow `regression` gate (`nix develop` unittest discover) cannot pass on this checkout while `origin/main` is a moving observe-env baseline that now also emits `CAPCOV_NONCE`. Pointing that test at the recorded experimental baseline is outside this task's write set. Linux execution and a driver-owned clean-checkout rebuild remain undemonstrated. The pinned `shen-go` revision remains accepted only for the observed smoke, not for Stage D.

### Workflow toolchain re-verification (attempt 3, 2026-09-14)

Re-ran Stage 0 gates on committed HEAD `3edda1e335bf9d4d2df276267def14d0f1f446f3` (`fix(workflow): tolerate volatile and streamed results`, 2026-09-14 13:51:21 -0500). Required ancestor `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765` still holds (`git merge-base --is-ancestor`, exit 0). Host remained `aarch64-darwin`, Darwin kernel `25.5.0`, Nix `nix (Determinate Nix 3.21.5) 2.34.8`. The flake does not pin the host Nix CLI. `flake.nix` / `flake.lock` were not changed: no pin defect (wrong hash, wrapper bypass, unlocked input, shim binary, Go toolchain download, or uv fetching CPython) was observed. `shasum -a 256 flake.lock` is still `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac`. nixpkgs remains `34ab99075ac4f7e40cf037eef32cb1c360bb85e9` with lock `narHash` `sha256-hn1oU2rue2SYK8dAr8+WNZWtbsz1S2W5mnHlSEuh3bo=`. shen-go remains fetchFromGitHub rev `610ba423795b38e58dde3515a0583a109411433c`, source hash `sha256-nhJdMOcSFY5Kfd695pTGGRfrtnqBdFuy5ZLoa9tfT5Y=`, vendor hash `sha256-iTtlmSlY0qbH/1waOlfRMc1qAkBacQxI6pohRPni/so=`, `subPackages = [ "cmd/shen" ]`, `GOTOOLCHAIN=local`. An unchanged lock SHA does not by itself prove the Shen revision; that pin lives in `flake.nix` hashes and was left as-is.

Live `origin/main` used by git is `8994d639fe4fa56285dc083eeca22ab00d30d839` (`docs(verification): preserve shared Crossplane resources`, 2026-09-14 13:37:44 -0500) via the loose ref `.git/refs/remotes/origin/main`. `.git/packed-refs` still lists `780173269246f02a7c219b6bd086d1dd93948783 refs/remotes/origin/main`; git prefers the loose ref. `_origin_main_cli_source()` therefore loaded `8994d639:packages/capabilities/src/capcov/cli.py`. HEAD and that blob share `cli.py` git object `bb6954d7a8aad121cc928e8bb3d55e47f91f2674`. Production baseline `7801732` remains `a57f38ce1db8631199d6f111e7120c1f5c63d48d` for the same path. HEAD `packages/capabilities/tests/test_cli_engine.py` already pops `CAPCOV_NONCE` before comparing observe envs; that test edit is outside this write set and was not touched. Attempts 1–2 recorded a develop-shell failure against then-current `origin/main` `f5775bda…`; that nonce inequality is not this attempt's result.

Pinned tools observed through `nix develop --no-update-lock-file --command bash -lc` (the workflow login-shell form, not interactive `nix develop` or `bash -c`):

- Python `3.12.14` at `/nix/store/p1wfv7znig26m3hns4583cb9va3kzxkg-python3-3.12.14/bin/python` (`sys.version_info[:2] == (3, 12)`; not host 3.14)
- uv `0.12.5` at `/nix/store/71zq15rr7i4avy58y89hfgf2lhp3b7la-uv-0.12.5/bin/uv`
- Go `1.27.0` at `/nix/store/lz3qw52rpazqga73xgsqlj4qz1lgs4hg-go-1.27.0/bin/go`
- Git `2.55.0` at `/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`
- jq `1.8.2` at `/nix/store/d01nk4ck93bwlzwbnnb1qf1kv4d94a09-jq-1.8.2-bin/bin/jq`
- hyperfine `1.20.0` at `/nix/store/krcnbpwana1dpxx45a0yzqjk8hpi9ff8-hyperfine-1.20.0/bin/hyperfine`
- Shen at `/nix/store/m6vdgvc4g4djhm9ld1s16jrd39k001lm-shen-go-0-unstable-2026-09-09/bin/shen`
- workflow `bash` wrapper at `/nix/store/vvd5k6yfqss3i49flrv5a928iqzq263m-bash/bin/bash`

Every resolved executable was under `/nix/store`. `uv python find` resolved the same Nix Python. Shell env: `UV_PYTHON_DOWNLOADS=never`, `UV_PYTHON_PREFERENCE=only-system`, `UV_PYTHON` → Nix `python3.12`, `GOTOOLCHAIN=local`, `BASH_ENV` → `/nix/store/5v1hsmilsng49sxagabawls7fwms4xiz-capcov-bash-env`. `shen --version` printed `42 (port ("Go" "1.0.0-rc1") implementation ("AOT+interpreter" "go1.27.0"))`; that language version is not evaluator evidence.

```sh
nix flake check --no-update-lock-file
```

Exit 0. Built `checks.aarch64-darwin.capability-regression` (`/nix/store/094s9nvz4z1ir2hgyqn5b79f498kv0ha-capcov-capability-regression.drv`); `shen-evaluator-smoke` and `shen-package` were previously built. Nix warned Linux checks were omitted on this host. The sandboxed regression copies `${self}/packages/capabilities` with no `.git`, so origin/main baseline tests skip there. Nix log: `Ran 490 tests in 19.121s`, `OK (skipped=69)`.

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 490 tests in 27.951s`, `OK (skipped=67)`, no failures or errors. The skip gap versus the Python-only Nix check (`69`) is the documented develop-vs-check toolset split: this shell has pinned Go and Git, and the worktree `.git` is visible, so origin/main comparators run. They ran against live `origin/main` `8994d639`; remotes were not hidden or filtered to force fallback to `7801732`.

```sh
nix develop --no-update-lock-file --command bash -lc \
  'set -eu; output=$(shen eval -e "(+ 20 22)"); test "$output" = 42; ! shen eval -e "(+ 1" >/dev/null 2>&1'
```

Exit 0. Direct observation of the same `bash -lc` form: `shen eval -e '(+ 20 22)'` printed exactly `42`; malformed `shen eval -e '(+ 1'` printed `ERROR: syntax error here: 40 43 32 49` and exited 1. `--version` was not treated as this smoke.

```sh
nix flake check --all-systems --no-build --no-update-lock-file
```

Exit 0. Evaluated advertised package, shell, and check derivations for `aarch64-darwin`, `aarch64-linux`, and `x86_64-linux` without building Linux. This is evaluation-only for Linux; no Linux execution is claimed. `x86_64-darwin` remains absent.

Independent extra evidence, not a substitute for the four gates:

```sh
out=$(nix build .#shen-go --no-link --print-out-paths --no-update-lock-file)
nix path-info -Sh "$out"
"$out/bin/shen" eval -e '(+ 20 22)'
```

Exit 0. Output path `/nix/store/m6vdgvc4g4djhm9ld1s16jrd39k001lm-shen-go-0-unstable-2026-09-09`, closure `22.2 MiB`, eval printed `42`. Same binary rejected malformed `(+ 1` with exit 1. This is `cmd/shen`, not a host or shim `bin/shen`.

**Limit:** pins are unchanged, not tightened. This run still cannot honestly establish a clean-checkout rebuild: the driver owns the commit, and appending this subsection dirties `EXPERIMENT-PLAN.md`, which changes `${self}` and will rebuild `capability-regression` with a dirty-tree warning. Linux remains evaluation-only. Host Nix is unpinned. The skip gap (`69` in the Python-only check vs `67` in develop) is documented and was not equalized by copying `.git` into the sandbox. The pinned `shen-go` revision remains accepted only for the observed smoke, not for Stage D (`pyrex41/Shen-Backpressure@6b9dde09` is prior art only). Live `origin/main` can still drift after this recording; this attempt's develop regression passed against `8994d639` with identical `cli.py` blobs.

## 15. Stage A — Adversarial semantic corpus

Add:

```text
packages/capabilities/tests/claim_semantics/
  corpus/
    01-correlated-positive.json
    02-surface-mismatch.json
    03-post-without-creation.json
    04-authorization-polarity.json
    05-wrong-event-email.json
    06-context-contamination.json
    07-shared-mistaken-assumption.json
    08-rejection-versus-missing.json
    09-support-and-refutation.json
    10-revoked-assumption-alternative.json
    11-compatible-history-sets.json
    12-unexpected-runtime-surface.json
    13-acceptance-sql-ack-failure.json
    14-bounded-no-resend.json
  expected.json
  test_corpus_schema.py
  test_expected_semantics.py
```

Every fixture identifies whether it is synthetic or real, any seeded fault, its exact claims, evidence and assumptions, expected semantic verdict, expected operational state, required/forbidden derivation leaves, and expected discrepancies or missing premises.

Expected distinctions:

1. Correlated positive execution is supported.
2. Route A static plus route B runtime leaves the effect claim unresolved.
3. POST without commit evidence supports the request, not creation.
4. Allow and deny behavior are separate claims; a failing denial does not disappear behind a passing allow path.
5. An accepted email for another event does not support the intended claim.
6. Cross-run or cross-tenant evidence produces context discrepancies, not support.
7. Two producers sharing one false assumption do not manufacture independent support.
8. Explicit rejection is refutation; a missing record is unresolved.
9. Support and refutation for one scoped attempt is conflicting.
10. Revoking one assumption leaves a claim supported when an independent path survives.
11. An empty history set is inconsistent; a mixed set is unresolved.
12. An unknown runtime surface remains an explicit discrepancy and blocks whole-model completeness.
13. Provider acceptance and failed SQL acknowledgement support different claims; stronger terminal completion is not inferred.
14. Bounded no-resend can be supported while indefinite safety remains unresolved.

Capture legacy comparator output where useful, clearly labeled non-authoritative.

**Exit criterion:** reviewers can determine expected semantics without executing any evaluator.

## 16. Stage B — Typed IR and reference evaluator

Implement strict JSON validation, frozen typed value objects, canonical ordering and hashing, immutable evidence IDs, relation schemas, context compatibility, deterministic fixed-point evaluation, independent support/refutation derivation, and explicit resource accounting.

Expose:

```sh
capcov experiment claims validate BUNDLE
capcov experiment claims evaluate RULES MODEL EVIDENCE --out RESULT
```

The `experiment` namespace preserves all existing commands and artifacts.

Test:

- malformed records and relation arity/type errors;
- duplicate evidence IDs without overwrite;
- multiple producers addressing one proposition;
- unsafe rule variables;
- positive recursion and termination;
- recursive-negation rejection;
- closure-gated negation;
- finite aggregation and empty-domain behavior;
- deterministic output under shuffled JSON input;
- context contamination mutants;
- rule/model/evidence digest changes.

**Exit criterion:** all corpus cases match reviewed expectations and existing CLI behavior remains unchanged.

## 17. Stage C — Certificates and support maintenance

### Ground certificates

A certificate contains:

- exact signed conclusion;
- rule, model, and schema digests;
- ground rule applications;
- evidence and assumption leaves;
- compatibility and completeness witnesses;
- child certificate references;
- producer and validator versions.

The checker performs no proof search, process launch, or evidence collection. It validates supplied ground steps, recomputes side conditions, requires exact conclusions, and rejects stale digests or scope widening.

Expose:

```sh
capcov experiment claims check \
  --rules RULES --model MODEL --evidence EVIDENCE CERTIFICATE
```

### Shared support graph

Use hash-consed `EvidenceLeaf`, `AssumptionLeaf`, `CompatibilityLeaf`, `AND`, `OR`, and signed-claim nodes. Implement bounded:

- `why`;
- `why-not`;
- changed-premise impact;
- alternative-support survival;
- assumptions shared by every support path;
- minimal support cuts;
- localized conflict explanations.

Start with exhaustive/minimal-set algorithms for small neighborhoods. Every query accepts node, result, and time limits and emits `truncated: true` when incomplete.

Tests include malformed and cyclic certificates, substituted evidence IDs, removed context checks, wrong digests, exact reverse-impact scope, alternative support, and minimal-set comparison against brute force for small fixtures.

**Exit criterion:** every supported corpus claim has a replayable certificate, all seeded invalid certificates fail, and invalidation affects only dependent paths.

## 18. Stage D — Executable Shen workbench

Add:

```text
packages/capabilities/shen/
  claim-workbench.shen
  rule-authority.shen
  certificate-output.shen
```

Python may translate validated canonical IR into deterministic Shen data, but must not precompute the semantic answer.

The Shen path must:

1. load the canonical normalized rule pack;
2. elaborate rules into executable proof-search predicates;
3. run structural authority checks;
4. search for positive and negative derivations;
5. emit an explicit certificate;
6. emit bounded missing-premise alternatives;
7. replay the certificate through the independent Python checker.

Authority checks reject:

- conclusion variables not grounded by premises or explicit constructors;
- loss of run, tenant, scope, or causal indices;
- unsupported context widening;
- negative conclusions without completeness;
- source declarations or HTTP conventions promoted directly to demonstrated effects;
- unapproved effectful side conditions;
- mutation of the accepted rule pack after freeze.

Record hashes of canonical JSON, generated Shen representation, Shen runtime, and frozen elaborated representation.

Expose:

```sh
capcov experiment claims shen evaluate ...
capcov experiment claims shen why-not ...
```

**Exit criterion:** Shen performs real elaboration and search, emits a portable certificate, and the independent checker catches planted invalid certificates. Concrete tooling failure is reported as a failed milestone, never mocked.

## 19. Stage E — First-projection specialization

Define the reference interpreter as an executable expression/relational-plan AST:

```text
interpret(rule_program, application_model, fresh_evidence)
  -> verdicts, derivations, missing premises, discrepancies
```

Implement an online partial evaluator that fixes the rule program, application model, expected context relationships, and claim inventory. Fold static schema/model lookups and fixed rule dispatch while residualizing:

- dynamic evidence reads;
- actual build/configuration validation;
- identity and correlation checks;
- completeness checks;
- contradiction handling;
- malformed, stale, and out-of-scope paths;
- unknown evidence and unexpected surfaces;
- certificate construction.

Generate:

```text
checker.py
evidence-schema.json
assumption-manifest.json
proof-skeletons.json
specialization-report.json
```

The residual checker runs with Python stdlib alone:

```sh
python checker.py evidence.json --out result.json
```

This counts as a first projection only if the checker is produced by specializing the executable interpreter representation, not by a separate template that restates the rule semantics.

Retain a general novelty/contradiction sentinel so unexpected evidence remains representable.

Validation must compare interpreter and residual verdicts, explanations, discrepancies, and normalized certificates across the corpus and exhaustively generated bounded inputs. Introduce controlled defects that drop an attempt/run check and ignore unexpected surfaces; require differential validation or certificate replay to detect both.

Record generation time, runtime, memory, code size, ABI size, and review complexity.

**Exit criterion:** residual and interpreter agree on successful and unsuccessful inputs, and both controlled defects are detected.

## 20. Stage F — Bounded experiment proposals

Define a closed experiment catalog. Each entry names:

- the predicate or assumption it can observe or challenge;
- a catalog action ID and executor binding;
- required context;
- expected observation types;
- cost and timeout;
- isolation, reset, and cleanup requirements;
- side effects;
- whether it is an evidence perturbation, observation experiment, or application fault.

The planner selects parameterized catalog actions and never generates shell commands.

Demonstrate:

1. A missing terminal SQL premise generates a bounded SQL observation tied to the known message/attempt.
2. A shared-assumption support cut generates an independent SQL-correlated checker challenge rather than another POST-derived opinion.
3. Two coarse-equivalent held histories select provider-side acceptance as the distinguishing observation.

Cover these explanations:

```text
no provider contact
provider accepted but response was lost
provider accepted but SQL acknowledgment failed
```

Execute at least one generated proposal through a consumer-owned isolated fixture command. Capture a fresh nonce, build/source identity, action activation receipt, observations, and cleanup status, then feed the observations back into evaluation.

If the application fixture is unavailable, this stage remains blocked rather than substituting Python notification behavior.

**Exit criterion:** an executed generated proposal changes a claim from unresolved to supported, refuted, or conflicting using fresh evidence, with its experiment class explicit.

## 21. Stage G — Real Go notification execution

Resolve this dependency early:

- identify and pin the external Go application revision;
- identify its existing notification fixture or receipt command;
- document database and SMTP requirements;
- expose the checkout through a path such as `CAPCOV_GO_FIXTURE_ROOT`;
- use the fixture's existing reset and execution machinery.

Do not commit private source or implement notification behavior in Python.

The Go receipt adapter should require:

- exact candidate build/source identity;
- run nonce;
- tenant and actor;
- save/request ID;
- committed event ID;
- notification, recipient, message, and attempt IDs;
- SMTP acceptance or rejection;
- SQL terminal state and ordering;
- process exits;
- observation completeness/loss metadata;
- fixture cleanup.

Retain a sanitized real receipt and resulting certificate where policy permits dependency-free replay.

Required pipeline:

```text
real Go execution
-> receipt admission
-> scoped claim
-> Shen derivation
-> Python certificate replay
-> specialized checker agreement
-> useful why/why-not result
```

Run a negative control with a wrong event/attempt correlation or accepted-but-SQL-acknowledgement failure. It must not receive the positive completion verdict.

**Exit criterion:** one actual Go-produced execution and one negative control traverse the complete experimental path. Synthetic Go fixtures do not satisfy this milestone.

## 22. Stage H — Evaluation and recommendation

Evaluate:

- all corpus verdicts;
- valid and invalid certificates;
- producer multiplicity and shared dependencies;
- context isolation and explicit compatibility;
- missing versus contrary evidence;
- conflicting evidence;
- exact invalidation and surviving alternatives;
- explanation usefulness and size;
- Shen/reference agreement;
- interpreter/specialized agreement;
- specializer mutation detection;
- generated experiment results;
- real Go execution;
- startup, runtime, generation cost, memory, and artifact size;
- Nix closure and maintenance burden.

Record exact revisions, commands, environment, failures, limitations, and results in this document. Include whether Shen caught anything the Python path did not, whether specialization reduced semantic duplication, and whether the generated experiment was operationally useful.

Conclude with one recommendation: retain as research, revise, or propose named components for production adoption.

## 23. Reproduction commands

Target workflow:

```sh
# Enter the pinned environment.
nix develop

# Existing regression suite.
cd packages/capabilities
PYTHONPATH=src python -m unittest discover -s tests -t .

# Semantic corpus.
PYTHONPATH=src python -m unittest \
  discover -s tests/claim_semantics -t .

# Reference evaluation.
capcov experiment claims evaluate \
  experiments/claim-semantics/rules-v1.json \
  experiments/claim-semantics/model.json \
  tests/claim_semantics/corpus/01-correlated-positive.json \
  --out result.json

# Independent certificate validation.
capcov experiment claims check \
  --rules experiments/claim-semantics/rules-v1.json \
  --model experiments/claim-semantics/model.json \
  --evidence tests/claim_semantics/corpus/01-correlated-positive.json \
  result.certificate.json

# Shen differential path.
capcov experiment claims shen evaluate ...

# Specialization and residual execution.
capcov experiment claims specialize ... --out-dir .capcov/generated
python .capcov/generated/checker.py evidence.json --out residual-result.json

# Complete pinned check.
nix flake check
```

Routine generated output belongs under ignored `.capcov/`. Commit stable corpus fixtures, sanitized retained evidence, certificates, necessary generated-checker golden files, code, tests, and concise results only.

## 24. Implementation checkpoints

Recommended coherent commit sequence:

1. Pin PR #45 base and add the Nix flake.
2. Add the semantic specification and reviewed corpus.
3. Add typed IR and validation.
4. Add the reference evaluator and verdict algebra.
5. Add certificates and the ground checker.
6. Add support maintenance and bounded explanations.
7. Add Shen elaboration/search and differential tests.
8. Add the partial evaluator and residual checker.
9. Add specializer mutation validation.
10. Add the experiment catalog and planner.
11. Integrate and retain the real Go execution.
12. Add benchmarks, final results, and recommendation.

Each checkpoint must leave existing CLI behavior and tests runnable.

## 25. Risks and stop conditions

Stop or revise if:

- a claim cannot be stated without accepting producer-authored business verdicts;
- context joins remain ambiguous;
- Shen cannot emit a stable certificate independently replayable in Python;
- Shen duplicates Python semantics without improving authority checks, search, or why-not output;
- specialization becomes JSON plan generation or separately handwritten code generation;
- the residual checker cannot receive unexpected evidence;
- explanations routinely exceed bounds or hide truncation;
- the experiment planner only prints generic advice;
- the Go fixture cannot supply required correlation identities;
- a real execution is replaced with a synthetic claim of completion;
- the toolchain cannot be reproduced through Nix.

Even if the broader experiment is negative, the typed claim/evidence schema, strict context compatibility, ground certificates, and bounded support/invalidation queries may be independently production-worthy. Shen and specialization must earn adoption separately.

## 26. Pi execution workflow

A project-local Pi driver is defined by:

- `.pi/extensions/capcov-experiment.ts` — orchestration, journal replay, subprocess agents, gates, review, and checkpoint ownership;
- `.pi/workflows/capcov-experiment.json` — the authoritative task DAG, write sets, acceptance statements, and executable gates;
- `.pi/workflows/README.md` — operating and trust-model documentation.

The driver deliberately runs one writer at a time because the semantic IR has one integrator and the stages are substantially ordered. It parallelizes only independent read-only scouts and skeptical reviewers. Each task is accepted only after write-set enforcement, manifest-authored gates, and two independent approvals; an implementer's completion claim is never authoritative. Gate and review failures become backpressure for the next bounded attempt. Events and review patches are retained under ignored `.capcov/pi-workflow/`, and successful tasks receive driver-owned git checkpoint commits.

Use `/capcov-workflow start` from a clean checkout descending from `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765`. The default executes at most one completed task; `/capcov-workflow resume --tasks N` opts into a larger bounded run. `/capcov-workflow status`, `stop`, and `retry TASK` provide lifecycle control. The Go stage stops as blocked when its real external fixture is unavailable; the workflow cannot waive or mock that requirement.

### 2026-09-14 harness diagnosis and repair

The stopped run's exact subprocess failure is **UNKNOWN**, because the old driver discarded
raw stdout whenever it could not find a completed assistant `message_end`, retained no exit
or event diagnostics in the journal, and never wrote `driver.log`. That reduction explains
the observed empty structured result; it does not prove why each child ended without a
parseable final object. A direct current Pi JSON invocation succeeded, so the command shape
itself is not disproven.

The repaired driver accepts the installed Pi event envelope (`message_end`, `turn_end`,
stream `text_end`, and final `agent_end` fallback), validates the implementer result shape,
persists bounded agent diagnostics and gate/reviewer results as structured events, and writes
timestamped phase/exit/byte-count lines to `driver.log`. It also uses an atomic lock, prevents
retry races and exhausted-budget resets, and checks resume HEAD plus the next task's write set.
Only the harness commits; read-only scouts/reviewers may fan out while semantic writing remains
sequential.

Cheap end-to-end smoke, run interactively after project resources are loaded:

```text
/capcov-workflow smoke
```

Observed result: **PASS twice** on Pi `0.84.1`, including after the lock/race repair. The
latest bounded child exited `0` in about 5 seconds, wrote 13,300 stdout bytes and 0 stderr
bytes, parsed the exact requested object, appended `smoke-result` event sequence 10, released
its atomic lock, and left actionable entries in `driver.log`. This proves the repaired
subprocess/parser/event/log/lock path, not the long workflow or any semantic stage.

Stage 0's authoritative gates are now: frozen `nix flake check`; the full legacy regression
suite in `nix develop`; a real Shen evaluation returning `42` plus malformed-input rejection;
and frozen all-system derivation evaluation without builds. The fuller manual evidence above
also checks every tool's Nix-store path, versions, the independently built Shen closure, and
host-versus-Linux scope.

`pyrex41/Shen-Backpressure` was inspected at `6b9dde09b3a98ee5d20d0a6556acceacad4657d8`.
Its useful harness pattern is fail-closed, bounded Shen execution with an explicit runtime
override. It has no Nix flake to reuse. It also warns that `shen-go` has memory-allocation
crashes and moved its own Gate 4 to `shen-sbcl`; therefore the pinned `shen-go` runtime here is
accepted only for the observed Stage 0 smoke, not presumed safe for Stage D. Before Stage D,
run a bounded representative stress probe and either retain it with evidence or revise the
pinned runtime. This is an explicit unresolved toolchain risk, not a passed semantic gate.
