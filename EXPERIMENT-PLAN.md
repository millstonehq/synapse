# Build an experimental capcov branch from the research

## Workspace handoff

- Repository: `https://github.com/millstonehq/synapse.git` (capcov lives in `packages/capabilities`).
- Local clone: `/Users/dev/projects/capcov`.
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

Do not alter the full the target system acceptance denominator, adopt experimental results as production coverage, or automatically upgrade the production consumer.

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
- No the target system Go/PHP checkout or real notification execution fixture is present in this repository. That external integration is an explicit dependency, not something to replace with synthetic Python notification behavior.

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

Independently re-ran Stage 0 gates on the same committed HEAD `233d1eca99a11ae24e75d77566b47749406af1f5` (ancestor of `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765` still holds). Host remained `aarch64-darwin`, Darwin kernel `25.5.0`, Nix `nix (Determinate Nix 3.21.5) 2.34.8`. `flake.nix` / `flake.lock` were not changed; `shasum -a 256 flake.lock` is still `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac`. Attempt 1's uncommitted plan notes were already present, so `nix flake check` warned `Git tree '/Users/dev/projects/capcov' has uncommitted changes`.

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

### Stage 0 addendum — Shen runtime for Stage D (2026-09-15)

Decision (repository owner): Stage D uses the shen-go that `pyrex41/bifrost` drives, not the
flake's `shen-go` pin (`610ba42`), matching the target-go model work in the `shen1` session. The two
pins are recorded as different on purpose; the flake pin stays for the Stage 0 smoke until it is
repointed. Runtime provenance: `pyrex41/shen-go` `c12933d89d7312d5d25a951bbe20d1511c3dfbea`
(2026-09-14, checkout clean apart from an untracked `.worktrees/`), built with the pinned Go into
`.capcov/shen-go-c12933d/shen-go`, sha256
`05cac13837e0a78ca207030540721468e13d910979692cb9c1c4b9280f72a29d`; driven by `pyrex41/bifrost`
`3027741` via `BIFROST_SHEN_GO` (`bifrost eval --impl shen-go -e …`, `bifrost run --impl shen-go
FILE`; the launcher's own subcommands are `script FILE` and `eval`). `bifrost eval -e '(+ 20 22)'`
printed `42`; malformed `(+ 1` exited 1.

Bounded stress probe (the plan's precondition for Stage D, prompted by Shen-Backpressure's
"known memory allocation crash bugs and hangs during cold bootstrap" warning; record in
`.capcov/shen-go-c12933d/stress-probe.json`): cold bootstrap ×3 [0.964, 0.981, 1.015] s;
300 sequential `bifrost eval` calls with a 30 s per-call timeout: 0
failures, 0 timeouts, p50 1.009 s, max
2.304 s, children peak RSS 76.1 MB; a
200,000-element list build plus 20,000-deep recursive sum: 1.33 s,
peak RSS 127.5 MB; a 400-definition program:
1.48 s, peak RSS 83.1 MB. No
crash or hang was observed. The warning stays on the record; the mitigation Stage D must keep
is a hard per-call timeout, closed stdin, and captured output, with timeouts reported as named
operational failures. Note: `sum` is a reserved kernel name in this Shen.

### Stage 0 repin — `shen-go` flake pin moved to the bifrost revision (2026-09-15)

Worktree `capcov-shen-repin`, branch `agent/shen-go-repin`, parent commit
`8803f17a9a6fce6fad8770d2e5718596cb89d360`. This closes the "two pins recorded as different on
purpose" state from the addendum above: the flake's `shen-go` now points at the same upstream
revision that bifrost drives. Only `flake.nix` and this file changed; `flake.lock` is untouched
(`shasum -a 256 flake.lock` = `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac`
before and after — the shen-go pin lives in `flake.nix` hashes, not in the lock). Host
`aarch64-darwin`, Darwin `25.5.0`, `nix (Determinate Nix 3.21.5) 2.34.8`, nixpkgs still
`34ab99075ac4f7e40cf037eef32cb1c360bb85e9` with `go_1_27`.

| | old pin | new pin |
|---|---|---|
| `pyrex41/shen-go` rev | `610ba423795b38e58dde3515a0583a109411433c` (2026-09-09) | `c12933d89d7312d5d25a951bbe20d1511c3dfbea` (2026-09-14, `build(nix): bound interpreter package tests`) |
| `fetchFromGitHub` `hash` | `sha256-nhJdMOcSFY5Kfd695pTGGRfrtnqBdFuy5ZLoa9tfT5Y=` | `sha256-He6LoA/M6IjuV25KK7d2DO5dW8yccloK37KRSj5jKTA=` |
| `buildGoModule` `vendorHash` | `sha256-iTtlmSlY0qbH/1waOlfRMc1qAkBacQxI6pohRPni/so=` | `sha256-iTtlmSlY0qbH/1waOlfRMc1qAkBacQxI6pohRPni/so=` (unchanged) |
| package `version` | `0-unstable-2026-09-09` | `0-unstable-2026-09-14` |
| output store path | `/nix/store/m6vdgvc4g4djhm9ld1s16jrd39k001lm-shen-go-0-unstable-2026-09-09` | `/nix/store/xc7f80vh6gb5j6ar0452sflfs8jm1xxm-shen-go-0-unstable-2026-09-14` |
| `nix path-info -Sh` closure | `22.2 MiB` | `22.2 MiB` |

`subPackages = [ "cmd/shen" ]`, `nativeBuildInputs = [ git ]`, `env.GOTOOLCHAIN = "local"`, and the
`shen-evaluator-smoke` check are unchanged. Upstream `git diff 610ba42..c12933d` (one commit) touches
only `docs/NIX.md` and upstream `flake.nix` (adds `checkFlags = [ "-timeout=5m" ]` to its own
package); `go.mod`, `go.sum`, and `cmd/shen/` are byte-identical between the two revisions, which
is why the vendor hash did not change and why the launcher subcommands (`script FILE`, `eval -e
EXPR`) are the same ones the existing smoke exercises. No smoke or subcommand adjustment was needed.
The downstream flake does not add upstream's `checkFlags`; `buildGoModule`'s default check phase
already ran the upstream `cmd/shen` suite (`ok github.com/pyrex41/shen-go/cmd/shen 115.784s`).

Hashes were obtained the honest way, in order:

```sh
# 1. rev → c12933d…, hash → pkgs.lib.fakeHash, vendorHash → pkgs.lib.fakeHash
nix build --no-update-lock-file --no-link .#shen-go
#   error: hash mismatch in fixed-output derivation '/nix/store/4ahm85vh3w0hcbp1z5wrvbn9g5x1xaxl-source.drv'
#            got:    sha256-He6LoA/M6IjuV25KK7d2DO5dW8yccloK37KRSj5jKTA=
# 2. paste source hash, vendorHash still fake
nix build --no-update-lock-file --no-link .#shen-go
#   error: hash mismatch in fixed-output derivation '/nix/store/ihzwwrgya82i68wyj882zshkic8hq2cb-shen-go-0-unstable-2026-09-14-go-modules.drv'
#            got:    sha256-iTtlmSlY0qbH/1waOlfRMc1qAkBacQxI6pohRPni/so=
# 3. paste vendor hash
nix build --no-update-lock-file --no-link --print-out-paths -L .#shen-go
#   exit 0 → /nix/store/xc7f80vh6gb5j6ar0452sflfs8jm1xxm-shen-go-0-unstable-2026-09-14
#   buildPhase 1m08s ("Building subPackage ./cmd/shen"); checkPhase 2m42s, upstream cmd/shen tests ok
```

Direct evidence from the built output (not through the shell): `bin/shen` sha256
`17580d4498dc3535e4ab2ea3dc67a288e3b87c20c8a799a33541440dd764c8c3` (20,223,296 bytes, stripped);
`shen --version` → `42 (port ("Go" "1.0.0-rc1") implementation ("AOT+interpreter" "go1.27.0"))`
(same string as the old pin — upstream reports the Shen language/runtime version, not its Git
revision, so `passthru.revision` and this record carry the rev); `shen eval -e '(+ 20 22)'` → `42`;
`shen eval -e '(+ 1'` → exit 1, stderr `ERROR: syntax error here: 40 43 32 49`.

Workflow gates, each run as `nix develop --no-update-lock-file --command bash -lc '…'` from the
worktree root:

```sh
nix flake check --no-update-lock-file
```

Exit 0. Built `capcov-bash-env`, the workflow `bash` wrapper, and the dev-shell env (all changed
because `shenGo` changed), then `checks.aarch64-darwin.{capability-regression, scip-go-index-smoke,
shen-evaluator-smoke, souffle-recursive-typed-smoke}`; `shen-package` was already realised by the
build above. Nix warned about the dirty Git tree (`flake.nix` uncommitted while under test) and that
`aarch64-linux`/`x86_64-linux` checks were omitted on this host. The `shen-evaluator-smoke` output
(`/nix/store/ry1mi503kd5l2ddrhqppfx4si5kk2xic-shen-evaluator-smoke`) recorded `version.txt` =
the `--version` string above, `evaluation.txt` = `42`, `malformed.stderr` = `ERROR: syntax error
here: 40 43 32 49`. The sandboxed regression check's `nix log` reported `Ran 1053 tests in
202.234s`, `OK (skipped=145)`.

```sh
set -eu; output=$(shen eval -e '(+ 20 22)'); test "$output" = 42; ! shen eval -e '(+ 1' >/dev/null 2>&1
```

Exit 0 (the manifest's `shen-smoke` gate, verbatim). Inside the same shell form: `command -v shen`
→ `/nix/store/xc7f80vh6gb5j6ar0452sflfs8jm1xxm-shen-go-0-unstable-2026-09-14/bin/shen`;
`shen --version` → the string above; workflow `bash` →
`/nix/store/wc30aj1ysqgqpkiv1vpbl7kacjlbr07a-bash/bin/bash`; `python`, `uv`, `go`, `git`, `jq`,
`hyperfine`, `shen` all resolved under `/nix/store`; `go version go1.27.0 darwin/arm64`;
`Python 3.12.14`.

```sh
nix flake check --all-systems --no-build --no-update-lock-file
```

Exit 0. Evaluated every advertised package, shell, and check derivation for `aarch64-darwin`,
`aarch64-linux`, and `x86_64-linux` (including `checks.{aarch64,x86_64}-linux.shen-package` and
`shen-evaluator-smoke`) without building Linux.

```sh
cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -t .
```

Exit 0: `Ran 1053 tests in 134.263s`, `OK (skipped=135)`, no failures or errors. The skip gap
against the sandboxed check (`145`) is the documented develop-vs-check toolset split (pinned Go and
Git, visible `.git`), not a regression.

Behavioural comparison, Nix build vs the bifrost/host-Go build
(`/Users/dev/projects/capcov/.capcov/shen-go-c12933d/shen-go`, sha256
`05cac13837e0a78ca207030540721468e13d910979692cb9c1c4b9280f72a29d`, 27,158,402 bytes, unstripped;
read-only, not modified). The binaries are different builds of the same source revision, so byte
equality was not expected and does not hold (`17580d44…` vs `05cac138…`). Behavioural equality was
checked on the same inputs, both binaries invoked directly:

| input | bifrost build | Nix build | comparison |
|---|---|---|---|
| `--version` | `42 (port ("Go" "1.0.0-rc1") implementation ("AOT+interpreter" "go1.27.0"))` | same | identical |
| `eval -e '(+ 20 22)'` | `42`, exit 0 | `42`, exit 0 | identical |
| `eval -e '(+ 1'` | exit 1, `ERROR: syntax error here: 40 43 32 49` | exit 1, same stderr | identical |
| `script smoke.shen` | exit 0, stdout `3628800` / `[1 4 9]` (16 B, sha256 `8c9be2f4…`) | exit 0, same | stdout+stderr byte-identical |
| `script alloc.shen` | exit 0, stdout `200010000` / `200000` (17 B, sha256 `e7c4dd65…`) | exit 0, same | stdout+stderr byte-identical |
| `script big.shen` | exit 0, stdout `400` (4 B, sha256 `e4df891c…`) | exit 0, same | stdout+stderr byte-identical |

Result: no behavioural difference observed on the smoke, the malformed case, or the three
stress-probe scripts. Stage D may therefore use either the flake's `shen` (through `nix develop`)
or the bifrost-driven binary and get the same source revision; the flake path is the reproducible
one.

**Limits.** Linux remains evaluation-only (`--all-systems --no-build`); no Linux build or execution
of the new pin is claimed. Host Nix is unpinned. The comparison above covers only the listed inputs,
not the full upstream suite (which the Nix check phase ran only for the Nix build). The
`shen-go` pin is fixed by `flake.nix` hashes; an unchanged `flake.lock` SHA does not by itself
prove the Shen revision. As before, the commit was made after the gates ran on the uncommitted
`flake.nix`, so a fresh clean-checkout rebuild from the recorded commit is still the driver's to
demonstrate.

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
  corpus/expected.json
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

### 2026-09-17 Stage D built: `capcov experiment claims modelcheck` (branch `agent/modelcheck`)

Delivered against shen1's contract (section 26, 2026-09-17): `claims/modelcheck.py`,
`shen/modelcheck/prelude.shen` (untyped reification), `shen/modelcheck/types/*.shen` (one datatype or
one judgement per file), the CLI, `tests/claim_semantics/test_modelcheck.py` with the
labelled-synthetic `fixtures/model_min` and eight ill-formed mutants, each failing exactly the
judgement its defect breaks. Checker `capcov-modelcheck` version `1.0.0`, producer class
`modelcheck`; the fact and certificate files are what `replay_facts` reads.

How the type checker is actually used, with the facts that were measured first (shen-go `c12933d`
and shen-cl agree on every one): Shen decides once, when a `load` begins, whether that file is
typechecked, so a `(tc +)` inside a script never applies to the script's own forms — the driver's
top level runs untyped and only its nested loads after `(tc +)` are typed, which is exactly the
boundary wanted. A datatype side condition sees the *syntactic* term being typed (`[cons X [cons Y
[]]]`), so a whole-list predicate must walk that syntax (`tt.value`) and a condition on the head
of a `(cons X Xs)` pattern sees the literal atom; a computed predicate applied to the raw term
answers about the wrong object and never gates. Side conditions whose variables arrive through
*type parameters* (`X : (notin (cons Y Ys))`, `(ne A B)`) do not gate and provoke "changing the
type of F" warnings; structural rules with literal conclusions and pure unification do. A load
unit with two definitions, or a bare define, is declared twice and stops gating. Every predicate a
rule uses must be total, because the checker tries the rule against unrelated terms during search.

The judgements (`prelude.shen` computes the literal; `types/` decides): `writes:<op>` — the
declared write-set is a distinct string list, every table is one the effect vocabulary can write
for the op, and it equals as a set the tables the as-is effects touch across three live witness
states; `matrix:<op>` — admissibility over {committed, aborted, unknown} × {live, non-live} is
total, disjoint and has the documented shape (committed on a non-live target refused, aborted
admits exactly the pre-state, unknown admits one or two); `atlas:<endpoint>` — both atomicity
facts and the failure policy exist with documented values; `registry:<n>:<id>` — the entry names an
indexed rule and a known endpoint and both dispatch predicates run on the witness; `registry-ids`
— distinct, none malformed. Ops without an as-is target on any live witness are reported skipped,
never presumed. The model digest is the model's own recipe (sha256 over `shen/load.shen` and the
files it loads, in order), and the run fails closed unless the loader loaded exactly those files.
The certificate binds model files, checker sources, runtime binary, driver, the exact literals
judged and the transcript; `recheck` recomputes everything but the type judgements and refuses
tampering; a stale `model_well_formed.json` is removed when a model turns ill-formed.

Results on the real models (read only, this host): the qualified receipt's model `08380c9c…f7b`
is **well-formed** — 11 judgements pass, certificate `a00a096a…a41f`, fact emitted. The
unqualified receipt's older model `8410a39b…f859` is **ill-formed**: `writes:delete-issue` fails
because it declares `["issue"]` while its as-is effects touch `["issue" "mongo:issue"]` — the
undeclared audit write the replay judge found at runtime, now refused statically from the model
alone, before any receipt exists. Certificate `d6cc68ac…9515`, no fact. Suites: modelcheck 11 OK
(live model included when `CAPCOV_MODEL_DIR` names it), Shen workbench 22 OK, assumptions 44 OK,
CLI 19 OK.

Not done and said so: the admitted row `(capcov-modelcheck, 1.0.0)` in `model_checkers.json` is
the reviewer's signature and is left for the repository owner; the two certificate files go into
shen1's fixtures as one commit after their CI fix, and shen1 flips the qualified receipt's
expectation together with the signed row. The rule-pack walker of the earlier Stage D stays in
the tree until its certificate-equality evidence is superseded. Well-formed is not "correct
against PHP": that remains the judge's and the mutants' question.

### 2026-09-16 Stage D redefined: typed well-formedness of the Shen domain model (decision, repository owner)

Verdict on the delivered workbench: it works (section 18 record, merged as `114a35a`) but its
authority checks are functions walking the elaborated rule pack — a second walker over JSON that
Python already validates — and the three `.shen` files contain no `datatype` declarations and no
use of the type checker. By the criterion agreed with shen1 ("Stage D earns its place only if its
authority checks are expressed as types of rule forms, so an ill-formed rule fails to typecheck"),
the rule-pack walker is retired as the purpose of Stage D. It stays in the tree until the
replacement lands, and its certificate-equality evidence remains valid for what it checked.

New purpose. Stage D checks the well-formedness of the Shen *domain model* (the fact producer:
admissible-state sets, effect lists, declared writes, closures, reviewer exclusions) that the
replay judge consumes and signs verdicts against. Invariants are Shen typing rules (the sequent
calculus the type system is programmed in), so an ill-formed model fails to typecheck; Prolog
gives the why-not. The typecheck emits one fact with a `capcov-static-certificate-v1`-style
certificate, signed against the model digest, which the judge takes as a premise: no
well-formedness fact at that digest, no qualification, only `unresolved`.

Invariant list proposed to shen1 (open until they reply): (1) every closure owned by a named
producer, no exclusion set closed without a signed review; (2) every declared write has an effect
and every effect a declaring operation; (3) no operation both admissible and killed in one state;
(4) admissibility total over every operation the corpus claims to constrain; (5) every assumption
signed against the model digest and a run, a stale review cannot typecheck; (6) the digest the
judge binds to is the digest of the artifact that typechecked. Constraints: every invariant
written to terminate, under the existing hard timeouts; well-formed is not "correct against PHP",
which stays with the judge and the lineage-derived mutants.

Architecture stated with the decision: Shen's types define correctness deterministically; Soufflé
does the derivation (shen1's compiled-checker item becomes the production evaluator); Python keeps
strict ingestion, IR validation, certificate extraction and recheck, and remains an oracle in the
differential gates only — it is no longer the evaluator of record, because graph walking in Python
is the slow path (section 31 numbers). Sequencing: nothing starts until shen1's five in-flight r2
worktrees land (lineage-derived mutants, assumption registry, ordering claims, compiled gate,
active learning); Stage D stays off those paths.

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

### 2026-09-15 Stage D record — executable Shen workbench

Integrated into `experiment/claim-semantics` as merge `114a35a` (2026-09-16); the go_app bundle
digest this record pins was re-pinned in `86b2fe1` because the runtime-join merge (`5c22a89`) had
changed the exported bundle after this branch was cut (rules digest unchanged). See the
2026-09-16 integration record at the end of section 26.

**Status: milestone met on the pinned runtime; no part mocked.** The Shen side
elaborates the rule pack, runs the structural authority checks, computes the
stratified closure of the bundle's ground facts, searches a bounded derivation,
emits a `capcov-static-certificate-v1` certificate that the independent Python
checker accepts unchanged, and emits bounded why-not alternatives. Python only
translates (`claims/shen.py`); `evaluator.py` is used by the tests solely as the
comparison oracle for the Python extractor's certificate, never by the adapter.

Files: `packages/capabilities/shen/claim-workbench.shen` (runtime, elaboration,
closure, derivation search, why-not), `shen/rule-authority.shen` (authority
checks, frozen elaborated pack), `shen/certificate-output.shen` (certificate and
envelope rendering); `src/capcov/claims/shen.py` (transport: `authority`,
`evaluate`, `derive`, `why_not`, `ShenUnavailable`, `ShenFailure`,
`NotDerivable`); `src/capcov/claims/cli.py` wired only through the new
top-level `experiment` pre-parse dispatch in `src/capcov/cli.py`
(`capcov experiment claims shen authority|evaluate|why-not`; production
argparse untouched, `tests/test_cli_engine.py` 19 tests OK, 1 skipped);
`tests/claim_semantics/test_shen_workbench.py`, `test_shen_transport.py`.

Runtime provenance (recorded by every run in `provenance.runtime`):

- shen-go built from `pyrex41/shen-go` `c12933d`, binary
  `/Users/dev/projects/capcov/.capcov/shen-go-c12933d/shen-go`, sha256
  `05cac13837e0a78ca207030540721468e13d910979692cb9c1c4b9280f72a29d`;
  `--version` prints `42 (port ("Go" "1.0.0-rc1") implementation ("AOT+interpreter" "go1.27.0"))`.
- launcher `pyrex41/bifrost` `3027741c6e8830f01c0c4ce23cc615134d73481b` at
  `/Users/dev/.local/bin/bifrost`; invocation form, used consistently:
  `BIFROST_SHEN_GO=<binary> bifrost run --impl shen-go --raw <driver.shen>`
  (`--raw` because the launcher otherwise trims output; result block delimited
  by whole-line markers `<<<CAPCOV-SHEN-JSON-BEGIN>>>` / `...-END>>>`).
- every call: stdin `/dev/null`, stdout/stderr captured, own process group,
  hard timeout (default 60 s, `CAPCOV_SHEN_TIMEOUT` / `timeout=` override),
  `SIGKILL` to the whole group on expiry, one fresh temp directory per call.
  Timeout, non-zero exit, missing/duplicate/unparsable result block and Shen
  side `capcov-*` errors are named `ShenFailure` kinds; a missing launcher or
  binary is `ShenUnavailable`. Nothing falls back.
- The devShell's own `shen` (flake pin `610ba42`) was not used.

Recorded hashes for the go_app run (fixture digest
`50e642610e13c00fc06eefbfe9c507897fed049da9c9532f5a8b0a1614f1cdb7`, rules
digest `3c7c80822404fc2ef221b91edd209db7ea8e73a40122a9f9764be20398a4d36c`;
`go_app.go_app_bundle()` reproduces the handoff bundle byte-for-byte and the
tests pin both digests):

| hash | value |
|---|---|
| canonical JSON input (derive, row 0 `... api/GetJob() -> gorm/DB#Create()`) | `3ca01c34045e17cdf9f2488fa3c7a7b1d4c5d729bf5c09da7f824ad4d067fe15` |
| generated Shen driver (same run, 88,782 bytes) | `1b95687a076b2d476e7e5ac6121a9f5b3c43605fa1560cd07b6c4b8aa1b1ff88` |
| runtime binary | `05cac13837e0a78ca207030540721468e13d910979692cb9c1c4b9280f72a29d` |
| frozen elaborated pack printed back by Shen (go_app bundle: 70 relations, 29 rules) | sha256 `537bd2e0cc8d47388f97f752311fbd25c622d269b7b0278869040d112e2ffac6`, Shen checksum `ck2-666418996-496367451` |
| frozen elaborated pack, rules-static-v1 alone (73 relations, 27 rules) | sha256 `f6e865ae4e61190ba1501d8e0109451b9ee7096b6d1f5d03ab2a969adc88ce2f`, Shen checksum `ck2-2118177021-2102950502` |

Each derive run has its own input/driver hashes (rows 1-4:
`71d67798…`/`47d2211a…`, `d1ab3aee…`/`b126fe4c…`, `dbcdf58c…`/`9aff86ea…`,
`66d9fc37…`/`5091d1a3…`); the authority run over the go_app bundle recorded
input `8f81f438…`, driver `cf54f0e7…`.

Results (`test_shen*.py`, 22 tests, 46.7 s wall in the devShell, all pass):

- (a) authority: rules-static-v1 accepted, every rule passes all eight
  per-rule checks; the go_app bundle, all 14 corpus packs and two static
  review cases accepted; Shen's elaborated rule order equals the bundle's
  canonical order and Shen's canonical rendering of every rule equals
  Python's `canonical_json`; one planted bad rule per check id
  (`undeclared-relation`, `ungrounded-conclusion-variable`,
  `ungrounded-side-condition-variable`, `context-index-loss`,
  `unsupported-context-widening`, `negative-conclusion-without-completeness`,
  `declaration-promoted-to-effect`, `non-linear-recursion`) is rejected on
  exactly that rule.
- (b) derive: all 5 `static_reaches` rows yield certificates that
  `certificate.recheck` accepts (`ok=True`, no problems, nothing unchecked)
  and that equal the Python extractor's certificate **in full** (derivation,
  leaves, witnesses, absent, steps 2/2/1/1/0, nesting, and node counts
  57/55/37/37/15 — the search mirrors `certificate.py` tick for tick).
- (c) planted invalid certificates (substituted leaf, dropped evidence,
  wrong `rules_digest`, extra premise step, wrong conclusion row) are rejected.
- (d) negative control (`... -> nowhere/Missing()`): outcome `negative`, no
  certificate, why-not with 6 alternatives each naming a missing premise
  (nested one level: the missing `static_edge` is explained by its missing
  `scip_may_reference`), `truncated: false`; `derive` raises `NotDerivable`.
- (e) fake launchers: timeout (killed at 2 s, group reaped), non-zero exit,
  three malformed-output shapes, Shen error payload classification, and a
  disagreeing elaborated-pack checksum each produce the named failure;
  missing launcher/binary is `ShenUnavailable`; `max_nodes=3` yields a
  truncated certificate that recheck rejects.
- (f) frozen pack: a renamed rule and a wrong checksum are refused with
  `frozen-pack-mismatch` before any request is served.
- CLI: `capcov experiment claims shen authority --bundle` exits 0 with the
  JSON document; a missing runtime exits 3 with `operational_failure`.
- Full regression in the devShell with `BIFROST_SHEN_GO` set (the Shen tests
  included): 1075 tests, 135 skipped, OK, 132–148 s wall. With `BIFROST_SHEN_GO`
  unset the 20 runtime-backed Shen tests skip; with `CAPCOV_SHEN_REQUIRED=1`
  they error instead (verified: `FAILED (errors=2)` at import).

Timings (one bifrost + shen-go process per call, cold bootstrap ≈ 0.65 s):
authority 0.95–1.08 s (pack), 1.04 s (go_app bundle), 0.73–0.79 s (corpus);
derive 1.15–1.33 s per row (Shen work 3930–3968 ticks; inside Shen the
closure of 276 facts/29 rules takes ≈1.1 s and the search ≈0.75 s); why-not
1.26 s. Peak RSS was not re-measured here (integrator: ≈80 MB).

Fail-closed manifest line (a missing runtime is an error, never a skip):

```sh
cd packages/capabilities && CAPCOV_SHEN_REQUIRED=1 BIFROST_SHEN_GO=/Users/dev/projects/capcov/.capcov/shen-go-c12933d/shen-go PATH="$HOME/.local/bin:$PATH" nix develop --no-update-lock-file .. --command bash -lc 'PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p "test_shen*.py" -t .'
```

Runtime findings that shaped the implementation (all diagnosed on the pinned
binary, none worked around by mocking):

- Every string primitive (`pos`, `tlstr`, `explode`) is O(length) per call,
  so a byte walk over a long string is quadratic; `pr`/`output` of one
  70 KB string takes 4.7 s. The workbench renders JSON as a flat chunk list,
  prints chunk by chunk, walks only short strings, memoises string escapes and
  byte lists, and orders rows by comparing rendered values natively and
  byte-comparing only the first differing value.
- `mod` costs ≈110 µs per call even on tiny operands and is inexact near
  2^53; `div` ≈47 µs. Neither is used on any hot path: the frozen-pack
  checksum is `a ← (4a + k + 1) mod (2^31-1)`, `b ← (3b + k + 1) mod
  (2^31-19)` reduced by at most four exact subtractions (Python recomputes
  it in `pack_checksum` and refuses a disagreement). It is a change-detection
  fingerprint, not a cryptographic hash; the SHA-256 of the printed-back
  text is recorded beside it.
- `trap-error` under a deep call stack is very expensive (a per-chunk handler
  turned a 30 KB checksum into 36 s); the only handlers left are the
  top-level one and the two around the search.
- The runtime echoes the value of every top-level form it loads (including
  the marker string literal and, unwrapped, the entire fact list); data forms
  are wrapped to return `ok` and markers are matched as whole lines.
- Numbers are float64: floats and integers ≥ 2^53 are refused at translation
  (`invalid-input`) rather than transported inexactly; `str` cannot print
  pairs, so row hash keys use the JSON renderer.
- The "known memory allocation crash" warned about by Shen-Backpressure was
  not observed in the more than one hundred workbench runs made here (all bounded by the
  per-call timeout and process-group kill, which are the mitigation); the
  integrator's 300-call probe likewise saw none.

Honest limits:

- The authority checks are structural: they inspect declarations and rule
  shapes only. Compatibility-witness matching is by target-set membership
  (looser than the Python validator's typed-position matching);
  `context-index-loss` accepts a constant head context as an explicit
  constructor unless a premise binds that index to something else (the
  corpus's per-claim ground rules rely on this); the diagnostic policy is not
  consulted, so a negated premise without an exact scoped completeness
  witness always fails the check.
- Aggregation rules pass through authority (the aggregation variable counts
  as grounded) but closure/derive refuse them with `unsupported-construct`;
  non-linear recursion and unstratifiable negation are refused likewise.
- Bounds: `max_depth` 64 and `max_nodes` 10,000 (certificate parity with
  Python), a 3,000,000-tick work budget over closure and search
  (`resource-exhausted`), why-not capped at 16 alternatives and nesting depth
  2 with an explicit `truncated` flag; the certificate `nodes` count follows
  Python's tick discipline exactly.
- A row that is in the closure but that no rule application re-derives is
  reported as `inconsistent-closure`, never certified.
- Souffle is not involved in this stage; certificate parity is against the
  Python extractor over the Python kernel's closure.

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

### 2026-09-14 manifest realignment and SCIP → Datalog waves

The driver journal (`.capcov/pi-workflow/events.jsonl`) shows that only the legacy
`toolchain` task ever completed through the driver (checkpoint `6ba124e1`). Every Datalog
deliverable on this branch — the semantic contract, the adversarial corpus, the Python and
Soufflé kernels, the evidence-policy programs, and the diagnostic output templates — landed
manually from `codex/*` worktrees and was integrated by hand. The manifest's datalog gates
and write sets referenced files that were never created (`claims/python/**`,
`experiments/claim-semantics/souffle/**`, `test_evaluator_python*`, `test_differential*`,
`test_certificate*`), and Python 3.12's `unittest discover` exits 5 when a pattern matches
nothing, so those gates would have failed loudly had the driver reached them.

Realignment (this commit, human-owned; `.pi/workflows/**` is outside every task write set):

- Delivered tasks now point at delivered files: `semantic-contract` → `tests/test_claim_ir*.py`
  + `test_claim_contract_review*.py`; `datalog-corpus` → `test_corpus*.py` + `test_expected_semantics*.py`;
  `python-reference` → `claims/evaluator.py` and its two test modules; `souffle-kernel` →
  `claims/souffle.py` and its two test modules, with a fail-closed gate (Soufflé under
  `/nix/store`, `skipped` output rejected).
- `datalog-differential` is repurposed as the kernel provenance repair plus differential
  harness (section 27). `datalog-certificates` now depends on `scip-datalog-differential`.
- New waves in order: `scip-toolchain` (section 28), `scip-datalog` with parallel
  `scip-fact-export` and `static-rule-pack` reduced by `scip-datalog-differential` (section 29),
  and `scip-target-go-pilot` before `datalog-target-go` (section 30). Phantom `experiments/**` globs were
  removed from later tasks; the `static-rule-pack` worker reintroduces that directory deliberately.
- `test-capcov-experiment.mjs`, `datalog-runtime-harness.mjs`, and `test-capcov-runtime.mjs`
  assert the new ordering, delivered artifact paths, `differential-mismatch` classification of
  the static differential, and that every external-binary gate rejects `skipped`.

Journal backfill (human decision): `datalog-corpus`, `python-reference`, and `souffle-kernel`
receive `task-completed` events with `manual: true`, `checkpoint` = this realignment commit,
and `integrated_from` naming the codex worktree revisions (`codex/datalog-corpus@98dfbe7`,
`codex/datalog-python-kernel@3b36b62`, `codex/datalog-souffle-kernel@ae95676`,
`codex/datalog-semantic-contract@9a535f6`, `codex/datalog-evidence-policy@d385a81`,
`codex/datalog-diagnostic-templates@83af766`), plus a `wave-checkpoint` for `datalog-corpus`.
`semantic-contract` is already satisfied through the `toolchain` alias. These events record
integration, not review: the two-skeptic review those tasks would have received is deferred to
the `datalog-differential` reducer, whose acceptance covers the same code. Nothing in this
subsection is evidence that the kernels are correct.

Known defects carried into section 27 (verified on `026cdfb`): evaluator proof leaves are
synthesized `fact:<relation>:<row>` ids and never the bundle's `Evidence.id`; `expected.json`
support leaves have never been checked against evaluator output; the Soufflé `_claim_result`
hard-wires refutation to false and treats an empty universal domain as complete; the Soufflé
binary is resolved by bare name with no guard, so both Soufflé test modules error rather than
skip outside `nix develop` and inside the python-only `capability-regression` check.

#### 2026-09-15 first driver run of `datalog-differential`

Run `claims-20260914185300567` resumed at `0b6ec34` on model `openai-codex/gpt-5.6-sol`.
Attempt 1: both scouts finished (about 6 minutes each); the implementer was killed by the
30-minute agent timeout (exit 143) while running the regression suite, so the journaled
feedback was test noise. Attempt 2: scouts finished; the implementer was killed by a host
low-memory kill of the driver process, leaving roughly 1,000 changed lines uncommitted in
`claims/{evaluator,souffle,validation}.py`, the two Soufflé test modules, `schema-v1.json`,
and corpus fixtures 02, 07, 10 and `expected.json`. Neither attempt reached a gate or a
reviewer, so neither is semantic evidence for or against the task.

Repairs (human-owned, this commit): `agentTimeoutMinutes` 30 → 90; the driver accepts a
`manifest-checkpoint` event as the expected resume HEAD so such commits do not require a
fake task completion; the attempt counter for `datalog-differential` is reset by a
`task-reset` event naming the infrastructure causes; the implementer receives targeted
feedback (keep reviewed corpus fixtures byte-stable apart from added evidence records, do
not reformat them, and make `static-context` apply only to relations that declare an
`index` column rather than forcing `index` onto the corpus's existing static relations).
The dirty tree is left in place for attempt 3, which the driver treats as a retry.

#### 2026-09-15 second driver run of `datalog-differential` (`70077c7`, 90-minute budget)

Attempt 1 (05:11–05:52 UTC): implementer ready in 25 minutes; all three gates green under the
driver; both reviewers requested changes (Soufflé `all` compared cardinalities only; Python
claim matching ignored repeated-variable equality; the alternatives cap could discard the only
surviving producer while reporting complete; revocation was relation-global; `static-context`
enforced only when an `index` column existed; the differential shrank only when both kernels
were operationally complete). Attempt 2 (05:52–06:31): implementer ready in 23 minutes; gates
green; reviewers requested changes again (`forall` domains scoped only by context columns;
`all` collapses domain identity when the source lacks the member column; evidence mappings may
under-bind causal identities; indexless static relations bypass the static/runtime join guard;
mapping-valued JSON rows crash the Python kernel instead of yielding a report; a
`refutation`-effect diagnostic does not revoke; the Soufflé `outputs` subset can change
verdicts; replay bundles are not minimized over evidence records). Attempt 3 (06:31–07:06):
implementer ready in 27 minutes reporting all gates green locally; the driver's
`differential-tests` gate then failed 4 of 17 tests.

Attempt 3's failure was infrastructure, not semantics. The three replay bundles the failing
tests wrote (`packages/capabilities/.capcov/differential/{8b1d980e…,fbb3d3b5…,98cfaf87…}.json`)
are shrunk to zero facts, which the shrinker only produces when the Soufflé side fails
operationally for every input; the fourth failure shows Soufflé returning an empty relation
set. Rerunning the identical module in the identical tree at 07:10 UTC passed 15/15, and that
`nix develop` had to re-fetch the entire devShell closure (souffle-2.5, python3-3.12.14,
go-1.27.0, shen-go) from cache.nixos.org, so the store paths had been deleted between the
green 06:22 gate and the red 07:06 gate. `nix develop` registers no GC root, so any garbage
collection removes the closure; the initiator of that collection is UNKNOWN (`gc.lock` was
not touched; `db.sqlite` was written at 07:06:18 UTC, inside the gate window). Repair: the
devShell is now built with `--out-link .capcov/pi-workflow/devshell-gcroot` (1.9 GiB closure,
indirect root registered under `/nix/var/nix/gcroots/auto`), documented in the workflow
README. The attempt counter is reset a second time by a `task-reset` naming this cause; the
attempt-3 tree is left in place, and the human feedback restores the attempt-2 reviewer
findings that the gate-noise feedback had replaced.

#### 2026-09-15 third and fourth driver runs of `datalog-differential`; task retired

Run 3 (`62510b3`, GC root in place): attempt 1 passed all gates; both reviewers requested
changes (differential omits provenance fields; producer-class authority unenforced; generic
rules can project away causal identities; refuted universals omit domain and closure leaves;
bounded shrinking is not unconditional minimality). Several of those demands came from plan
sections 16 and 22, which the task's `planSections` still cited, and from an acceptance
sentence that promised unconditional minimality. The human stopped the run during attempt 2's
scouts, narrowed `planSections` to 27, reworded the acceptance to the bounded-shrink design,
and recorded the deferred items (commit `6fdb00b`); that aborted attempt was reset with the
reason journaled.

Run 4 (`6fdb00b`): three attempts, each ready in 13–26 minutes, each green on all three gates
under the driver, each refused by both reviewers with new, narrower, real findings — round 1:
conjunctive mappings bind claim variables independently; `EvidenceMapping.claim_relation` is
not tied to its `claim_id`; leaves still union alternative paths; corpus cases 02 and 07 had
been neutered to rules-free observation-only fixtures. Round 2: negated static atoms escape
the static/runtime join check; missing-premise templates ignore trigger conditions; Soufflé
shrinks a universal domain under revocation and returns supported where Python fails closed.
Round 3: valid positive cycles can grow proof trees to a `RecursionError`; output relevance
does not unify variable-valued claims; compatibility payload types are unchecked; the shrinker
mutates output templates. The attempt budget is exhausted (`run-stopped: attempt limit reached`).

Decision: the task is retired, not reset a third time. Its uncommitted tree (19 changed and 8
new files, about 2,600 lines; focused suites green: 26 differential, 10 shrinker, 13
provenance, 33 Soufflé; full regression green under the driver at 09:33 UTC on the same tree)
is committed as explicitly unapproved work in progress and journaled as a `human-checkpoint`
so later patches are incremental. The four round-3 findings become the specification of two
new parallel tasks, `kernel-closure` and `differential-closure`, reduced by
`kernel-closure-integrate` in wave `datalog-kernel-closure`, each with a fresh attempt budget.
The `datalog-kernels` wave keeps its delivered members and no longer names a reducer.

## 27. Kernel provenance repair and differential closure

Owner: `datalog-differential` (reducer, wave `datalog-kernels`). Write set: `claims/**`,
`packages/capabilities/tests/**`, this document.

Required changes:

1. `claims/evaluator.py` `_Engine.seed`: index `bundle.evidence` by `(relation, ground row)`
   and add one fact `Derivation(kind="fact", leaf_id=<evidence id>)` per matching evidence
   record (alternative leaves, so revoking one producer's record leaves the other path intact
   and `Derivation.signature()` distinguishes them). Facts with no evidence keep the legacy
   `fact:<relation>:<row>` id and are counted in `resources["unattributed_facts"]`. Remove the
   dead `getattr(fact, "evidence_id", ...)` probe.
2. `_match_body`: children are one canonical proof per body atom (proof lists are already
   `sort(key=repr)`), with an `alternatives` count recorded on the derivation; add
   `ResourceLimits.max_alternatives_per_row` so recursive closure over a service graph cannot
   exhaust `max_provenance`. Today `leaves` is the union over every alternative path, which
   would make a closure witness "every edge on every path".
3. `claims/souffle.py`: `_claim_result` mirrors `evaluator.evaluate_claim` — support and
   refutation by relation polarity, `verdict(support, refutation)`, `missing_premises`
   when no row matches, empty `forall` domain → `unresolved`/`inconsistent-premises`/
   `bounded-history-model`, per-instance `forall` binding by column name. `run_bundle` probes
   `shutil.which(executable)` and raises `SouffleUnavailable`; an optional `outputs` subset
   stops a large static bundle echoing every input relation (the row cap counts inputs).
4. `claims/validation.py`: `mixed-binding-join` (a body with both `binding=static` and
   `binding=runtime` positive atoms needs a compatibility atom whose targets include one of
   each and whose payload carries the static `index` and runtime `run` terms),
   `static-context` (static observation/completeness relations carry `index` unless
   explicitly context-free like `source_tree_observed`), `evidence-without-fact`.
5. `claims/differential.py`: `KernelReport`, `run_python`, `run_souffle` (maps
   `OverflowError`/`TimeoutError` → `resource-exhausted`, `SouffleUnavailable` → a named
   operational failure, never a crash), `compare` over every relation including primitives
   and every claim. `claims/shrinker.py`: bounded ddmin over facts plus matching evidence,
   `max_steps=200`, replay bundle written under `.capcov/differential/<bundle_digest>.json`.
6. `claims/static/schema_static_v1.json`: the frozen primitive static relation declarations
   from section 29, so the `scip-datalog` parallel workers consume identical names.
7. Tests: `tests/claim_semantics/test_differential_kernels.py` (all 14 corpus fixtures agree,
   shuffled facts give identical digests), `test_shrinker_bundle.py` (an injected
   comparison-side defect localizes to at most three facts), `test_provenance_leaves.py`
   (evaluator support/refutation leaves equal `expected.json` and are all `Evidence.id`s),
   and the Soufflé modules gain `skipUnless(shutil.which("souffle"))` plus one unguarded test
   that patches `which` to `None` and asserts `SouffleUnavailable`; a negative-polarity claim
   yields `refuted`; an empty `forall` domain yields `inconsistent-premises`.

Checkpoint record must include: commit, gate commands and exit codes, Soufflé version and
store path, per-fixture differential result, and which corpus fixtures (if any) changed leaf
sets under the AND-structured children change and why that is correct.

### 2026-09-15 reducer completion record

The manifest dependencies had already been integrated manually and journaled in section 26 as
`python-reference` then `souffle-kernel`, the same order as the task manifest. Their worker
worktrees were no longer present during this reducer run, so no worker commit was applied and no
worker worktree was mutated. The reducer inspected and repaired the already-integrated
`claims/evaluator.py` first, then `claims/souffle.py`, and treated both implementations as
unreviewed inputs rather than authority. Reviewed fixtures 02 and 07 and the corpus schema were
restored byte-for-byte to `70077c7`; no `index` was forced onto their tenant-keyed static
relations.

Checkpoint ownership remains with the driver. The working tree was tested from base HEAD
`70077c74713d4eeb2218d6c682de1df8e654dd66`; there is deliberately no claimed completion commit
here because the task instruction forbids the implementer from committing. The driver must add
the resulting checkpoint hash after admission. Required ancestor `d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765`
remains in the history.

Tool observation through the pinned shell:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'set -eu; p=$(command -v souffle); printf "path=%s\\n" "$p"; souffle --version 2>&1; printf "deriver=%s\\n" "$(nix-store --query --deriver "${p%/bin/souffle}")"; python --version; nix --version'
```

Exit 0. Soufflé resolved to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`; its derivation was
`/nix/store/jgyfiny19jxvqk395xlzilr9bgwzhi1x-souffle-2.5.drv`. The packaged version is 2.5.
The binary's own `--version` banner printed a blank value after `Version:` (plus 32-bit word size
and `ffi ncurses sqlite zlib`); this record does not invent a missing banner value. Python was
3.12.14 and Nix was Determinate Nix 3.21.5 / Nix 2.34.8.

The three manifest gates were run exactly through `nix develop`:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Exit 0: differential discovery ran 8 tests in 6.034s with no skips; shrinker discovery ran 4
tests in 0.688s, all passing.

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0. The five discoveries ran 1, 10, 7, 2, and 22 tests respectively; neither Soufflé
discovery reported a skip. The real Nix-store binary covered startup, recursion, aggregation,
all four verdict states, empty universal domains, claim-local revocation, and reordered domain
columns. Patched absent/permission boundaries remained unguarded and produced named
`SouffleUnavailable` failures.

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 606 tests in 12.290s`, `OK (skipped=67)`. Those 67 are the pre-existing full-suite
optional-tool/platform skips; this broad regression is not used as Soufflé evidence. The two
Soufflé gate commands above explicitly rejected any skip and observed none.

A separate `compare(load_fixture(path), shrink=False)` report over every numbered fixture
produced the following canonical Python/Soufflé agreements (all compared every declared
relation, including empty primitives):

| fixture | result | claims | canonical report digest |
|---|---|---|---|
| 01-correlated-positive | match, 50 relations | terminal-delivery supported/complete/derivational | `72f385df2c33b9eefc503c06e23c4502eeb008f4b1ffde06374107603aed96fb` |
| 02-surface-mismatch | match, 50 | effect unresolved/complete/derivational | `fbef722d99a70a0b66f46e36de877df7f6e7efcb3c7ee4c355853bd2319ad135` |
| 03-post-without-creation | match, 50 | created unresolved; request supported (both complete/derivational) | `d52d05321e47d95cccc64e9e8a81cefa81dc56b4cf97157b9cafa5dca9b4e4c8` |
| 04-authorization-polarity | match, 50 | allow supported; deny supported (complete/derivational) | `d1b0e16d3390a50c9707c34ee45dcc80819834d680b540e2dba090672059eaf5` |
| 05-wrong-event-email | match, 50 | target-mail unresolved/complete/derivational | `416484a285af3de3632137f528ba48aa102a03a4706cad739b9cf3dcd083634d` |
| 06-context-contamination | match, 50 | terminal unresolved/complete/derivational | `c28aa042f5e7bfa854b96f610b023a725f2cdbc103d73ecefe5b56787813ce57` |
| 07-shared-mistaken-assumption | match, 50 | delivered unresolved/complete/derivational | `957d06342036fb2e4ca1899e870dbab5e8f986abeb2efa0f49926933f6203926` |
| 08-rejection-versus-missing | match, 50 | explicit-denial refuted; missing-denial unresolved (complete/derivational) | `7fb25480922aedebead44f0dd84fba1b8b4b5ec56c365d305c2e563c3c837f13` |
| 09-support-and-refutation | match, 50 | terminal conflicting/complete/derivational | `10fe80267ba1e8b13b9f4be5c925d68f3e265cc1254d15c0570e0ebde37769ff` |
| 10-revoked-assumption-alternative | match, 50 | saved supported/complete/derivational | `11d72c3c860b92c10c8528727832979810f78ffb275e00ce07be560a9d2cc02e` |
| 11-compatible-history-sets | match, 51 | universal unresolved/inconsistent-premises/bounded-history-model; mixed unresolved/complete/bounded-history-model | `7525fdc6cceea21fbf1b62191bb57fee18ea6825f8526e52bc8a5b98a0c033d1` |
| 12-unexpected-runtime-surface | match, 50 | model-complete unresolved/out-of-scope/derivational | `1d4e7934ca9bb7cc67f08ca762fe8441265b91418be366b2d9a31662fe07128f` |
| 13-acceptance-sql-ack-failure | match, 50 | terminal unresolved; provider supported (complete/derivational) | `d24cb0a13e8ccf18d46bf564609cda6062c9305ea75d3efd386306b5f3ff3f40` |
| 14-bounded-no-resend | match, 50 | bounded supported; forever unresolved (complete/derivational) | `c64ed2edab993064ba43c969bf8f955a74b96538dfed4bffafeb01ceba5cc766` |

Exactly one reviewed leaf set changed. Fixture 10's supported proof is an AND application of
`sql_row_exists` and `sql_snapshot_current__accepted`; after fact leaves became Evidence IDs,
its exact canonical support tuple is
`("assumption-independent-source", "fact-independent-proof")`. The fixture-local expectation
and mirrored `expected.json` now both name those two required children. The revoked
`assumption-revoked` is not on that path. No other corpus support/refutation leaf set changed.
This is a provenance correction, not a change made merely to force kernel agreement.

The static primitive contract contains 43 declarations and has canonical JSON SHA-256
`d936ba0c35465bcded2d3a51d5d3facfdd9fe2b27991de7fa216bac252299071`.
A gate-discovered test checks every primitive name/column order and the full digest, merges the
future completeness projections, and validates both `scip_index_comparable(index_a,index_b)`
and section 29's `index_describes_run(index,run)` rule.

Limits: Soufflé independently computes full and claim-eligible relation closure, but claim
mapping, quantifier folding, and diagnostic status are normalized in Python in `souffle.py`;
therefore this is stronger independent closure evidence than independent end-to-end verdict
implementation evidence. Claim-local eligibility reruns Soufflé after excluding only fact rows
whose every evidence producer path reaches a forbidden assumption; it does not trust producer
verdict metadata. Replay shrinking preserves validation, dependency closure, mismatch shape,
and operational completeness within 200 executions. Operational and semantic failures now both
enter bounded shrinking; a replay is called minimized only when `shrink_truncated` is false. No
Shen run, SCIP execution, certificate, specialization, generated experiment, real Go receipt,
Linux execution, or section 22 final recommendation is claimed by this checkpoint.

### 2026-09-15 reviewer-gate repair (attempt 2)

This sole-root reducer started from the still-dirty attempt-1 tree at HEAD
`70077c74713d4eeb2218d6c682de1df8e654dd66`. The `python-reference` and
`souffle-kernel` artifacts were already integrated in manifest order as recorded above. No
parallel patch/commit was listed for this attempt, no `git apply` was needed, and no worker
commit or worker worktree was used. The reducer did not commit; checkpoint ownership remains
with the driver.

Prior reviewer findings were reproduced with focused controls and repaired as follows:

- Existential direct claims and evidence mappings now unify repeated variables. `pair(X,X)`
  does not match `pair("a","b")` in either kernel.
- Forbidden-assumption eligibility identifies exact diagnostic rows, constrained by the
  claim's shared constants/context and the diagnostic predicate, then blocks only those
  Evidence IDs. Tests include same-relation assumptions in another context and another row.
- The 64-alternative proof limit no longer silently evicts a potentially eligible path. The
  evaluator reports `resource-exhausted` as soon as a 65th distinct path is encountered, and
  its candidate-key set is bounded by the same limit. A differential control with 64 tainted
  producers and one late independent producer proves Python fails closed while Soufflé finds
  support; `compare` blocks admission rather than reporting false complete agreement.
- Static observation/completeness declarations without `index` are rejected except for three
  exact frozen contracts: legacy `mail_path_declared`, legacy `static_route_exists`, and
  section 29's context-free `source_tree_observed`. Renaming a legacy declaration does not
  mint an exception. Facts and evidence targeting `primitive=false` are rejected by shared
  validation.
- Soufflé `all` lowering now compares projected source keys, domain keys, and their exact
  intersection, rejects any false source row, and collapses extra source-only dimensions.
  Boolean `any`/`all` relations emit explicit false rows when the aggregate variable is in
  the head; when it is absent, false remains a guard failure. Equal-cardinality wrong-member
  and duplicate-extra-dimension controls agree with Python.
- Differential backend `ValueError`/`TypeError`/Unicode and I/O failures become named
  operational reports. A valid IR symbol containing a tab exercises the real TSV translation
  failure and produces a reloadable replay. Semantic and operational mismatch classes use
  bounded ddmin; a threshold-injected resource failure minimized from eight facts to its
  four-fact boundary,
  and a fact-independent resource failure minimized to zero facts. Strict canonical replay
  loading also works for an intentionally invalid producer input.
- The admitted differential claim contract is explicit: `semantic`, `operational`, `basis`,
  and `missing_premises`, plus every declared relation. Mutation controls cover each field.
  Support/refutation provenance, discrepancies, resources, and messages are not claimed as
  independently produced Soufflé results; exact Python leaves remain checked against the
  reviewed corpus.

The pinned runtime observation was unchanged:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'p=$(command -v souffle); printf "%s\\n" "$p"; souffle --version 2>&1'
```

Exit 0. Path:
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`.
The banner again printed a blank value after `Version:`; the Nix package path identifies 2.5.

The manifest `differential-tests` command was run exactly as authored. Exit 0: differential
discovery ran 15 tests in 6.629s (`OK`, no skips), then shrinker discovery ran 5 tests in
0.732s (`OK`). The manifest `kernel-tests` command was also run exactly. Exit 0: its five
discoveries ran 1, 10, 7, 2, and 23 tests; both Soufflé discoveries reported `OK` with no
skips. The resolved binary printed the Nix-store path above in both gates.

The manifest regression command was run exactly after the focused repairs:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Its first run exited 1 after 616 tests because the pre-existing renamed-program test renamed
`static_route_exists` and therefore correctly hit the new frozen-exception boundary. The test
was changed to retain that exact legacy relation name while continuing to rename unrelated
program/evidence identifiers. The exact regression command was rerun after the final boundary
control and exited 0: `Ran 617 tests in 13.218s`, `OK (skipped=67)`. The broad suite's optional-tool/platform skips
are not Soufflé execution evidence; the two manifest gates above rejected `skipped` and saw
none. An additional focused command over the six modified semantic modules ran 66 tests in
10.272s, all passing.

A final pinned-shell script reran `compare(load_fixture(path), shrink=False)` for all fourteen
numbered fixtures. Every fixture still matched over 50 relations (51 for fixture 11), and all
fourteen canonical digests were byte-for-byte the values in the table above. Thus this repair
changed no reviewed corpus verdict or leaf set; fixture 10 remains the sole leaf-set correction
from the original reducer work.

Limits: crossing the alternative-proof bound now fails honestly rather than computing a
verdict; this is not a claim that explanations above the bound are available. Shrinking is
bounded at 200 executions by default, and `shrink_truncated=true` explicitly means the replay
has not been proved minimal. Soufflé independently computes closure, including the new exact
aggregate-key helpers, but Python code still performs claim folding and diagnostics. The
frozen static exceptions are transitional contracts, not general permission for identity-free
static producers. Section 16's experimental CLI namespace is still absent and was not added
through a production CLI file outside this task's intended kernel scope. No Shen, certificate,
specialization, real-Go, Linux, performance, or section 22 recommendation evidence is added.

### 2026-09-15 prior-review repair (attempt 3)

This sole-root reducer continued from the attempt-2 dirty tree at base HEAD
`70077c74713d4eeb2218d6c682de1df8e654dd66`. The dependency artifacts were already integrated
in manifest order (`python-reference`, then `souffle-kernel`) as recorded in section 26. No
parallel artifact or patch was listed for this attempt, so no `git apply` was performed; no
worker commit was consumed and no worker worktree was mutated. The reducer made no commit.

The two request-changes reviews were treated as gates and repaired before re-running admission:

- `FORALL` domain selection now honors every shared named claim constant as well as context,
  so another capability in the same run cannot enlarge a claim's finite domain. Both kernels
  have a two-capability oracle.
- `all` validation now requires each domain member identity in the aggregate source with the
  same type and term. The bounded-history corpus's explicitly reviewed `outcome` label is the
  sole frozen non-key payload exception; `history` remains mandatory. A source containing only
  `(tenant, holds)` is rejected rather than collapsing all members to `tenant`.
- Support/refutation mappings cannot omit shared Stage-B causal identities (tenant, actor, run,
  request, event, notification, recipient, message, attempt, interval, environment, build and
  model/config/source identities). Mapping bindings must also preserve types. Observation-only
  mappings remain non-authorizing and may be deliberately partial.
- Every mixed static/runtime rule now requires an indexed static atom, a runtime `run`, and a
  compatibility witness whose declared payload positions include and exactly bind both
  `index` and `run`. The three frozen indexless static declarations remain valid only outside
  mixed rules. Consequently fixtures 02 and 07 had their unsafe mixed rules removed; their
  observations, mappings, expectations, verdicts, and leaf sets did not change. This is a
  trust-boundary correction, not a kernel-agreement edit.
- Mapping-valued JSON constants are hashable immutable IR values, so the Python relation set no
  longer crashes. Soufflé symbols and JSON metadata now use one reversible hexadecimal UTF-8
  encoding in rule literals, TSV facts, and decoded outputs; tabs and newlines are valid and
  compare identically instead of becoming a translation failure.
- Count binds `Aggregation.value_variable` in Python, including zero-count groups. Soufflé's
  output subset automatically emits derived claim/domain/mapping/diagnostic relations required
  for verdict folding, so omitting a derived claim relation cannot silently change the verdict.
  Direct negative evidence plus a positive mapping is explicitly tested as `conflicting`.
- Assumption diagnostics with effect `refutation`, as well as `forbidden`, now revoke dependent
  proof paths in both kernels. Fixture 10 now contains `fact-revoked-proof` depending on
  `assumption-revoked` plus the existing independent proof; removing the independent producer
  yields `unresolved/stale`, while the reviewed complete bundle remains supported by exactly
  `assumption-independent-source` and `fact-independent-proof`.
- The shrinker minimizes individual Evidence IDs as well as fact rows, preserves dependency and
  attribution closure, and performs a bounded one-deletion certification pass. Mismatch shape
  uses the union of left/right relation names. Replay filenames equal the replay bundle digest;
  persistence failure raises named `ReplayPersistenceError` and blocks comparison. A bound hit
  remains `shrink_truncated=true`, never a minimality claim.
- The provenance topology control now uses two positive body atoms with two producers each. A
  rule proof has exactly two AND children, records two discarded OR alternatives, and resolves
  to the independent producer for either revoked canonical child. `path_key()` and the bounded
  alternative failure semantics were not weakened.

Pinned runtime observation remained
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`.
The final manifest `differential-tests` command was run exactly as authored in
`.pi/workflows/capcov-experiment.json`:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Exit 0. Differential discovery ran 17 tests in 33.615s and shrinker discovery ran 8 tests in
1.958s. Both reported `OK`; the gate's skip rejection did not fire.

The final manifest `kernel-tests` command was also run exactly as authored:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0. Its five discoveries ran 1, 10, 9, 2, and 26 tests in 0.044s, 0.006s, 0.056s,
0.092s, and 2.141s respectively. Every discovery reported `OK`; the two real-Soufflé
discoveries had no skips.

The final manifest regression command was run exactly:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 630 tests in 39.736s`, `OK (skipped=67)`. Those broad-suite skips remain the
pre-existing optional-tool/platform skips and are not used as Soufflé evidence.

A final pinned-shell per-fixture script ran every numbered fixture:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python - <<"PY"
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims.differential import compare
for path in sorted(Path("tests/claim_semantics/corpus").glob("[0-9][0-9]-*.json")):
    result = compare(load_fixture(path), shrink=False)
    print(path.stem, len(result.python.relations), result.python.canonical_digest,
          ";".join(f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}"
                   for claim in result.python.claims))
PY'
```

Exit 0. All compared every declared relation and matched. Canonical digests/verdicts:

| fixture | relations | canonical report digest | claims |
|---|---:|---|---|
| 01-correlated-positive | 50 | `72f385df2c33b9eefc503c06e23c4502eeb008f4b1ffde06374107603aed96fb` | supported/complete/derivational |
| 02-surface-mismatch | 50 | `fbef722d99a70a0b66f46e36de877df7f6e7efcb3c7ee4c355853bd2319ad135` | unresolved/complete/derivational |
| 03-post-without-creation | 50 | `d52d05321e47d95cccc64e9e8a81cefa81dc56b4cf97157b9cafa5dca9b4e4c8` | created unresolved; request supported |
| 04-authorization-polarity | 50 | `d1b0e16d3390a50c9707c34ee45dcc80819834d680b540e2dba090672059eaf5` | allow supported; deny supported |
| 05-wrong-event-email | 50 | `416484a285af3de3632137f528ba48aa102a03a4706cad739b9cf3dcd083634d` | unresolved/complete/derivational |
| 06-context-contamination | 50 | `c28aa042f5e7bfa854b96f610b023a725f2cdbc103d73ecefe5b56787813ce57` | unresolved/complete/derivational |
| 07-shared-mistaken-assumption | 50 | `ec6946397ee18fb525364ad0ee7b378357c6fde07b4289aa5fadf3eb8be6523f` | unresolved/complete/derivational |
| 08-rejection-versus-missing | 50 | `7fb25480922aedebead44f0dd84fba1b8b4b5ec56c365d305c2e563c3c837f13` | explicit refuted; missing unresolved |
| 09-support-and-refutation | 50 | `10fe80267ba1e8b13b9f4be5c925d68f3e265cc1254d15c0570e0ebde37769ff` | conflicting/complete/derivational |
| 10-revoked-assumption-alternative | 50 | `9295043b384a3ec90cff0158784b1b3f1709d2a57cac2e69f5eba4007e0d7fb8` | supported/complete/derivational |
| 11-compatible-history-sets | 51 | `7525fdc6cceea21fbf1b62191bb57fee18ea6825f8526e52bc8a5b98a0c033d1` | universal inconsistent/unresolved; mixed unresolved |
| 12-unexpected-runtime-surface | 50 | `1d4e7934ca9bb7cc67f08ca762fe8441265b91418be366b2d9a31662fe07128f` | unresolved/out-of-scope/derivational |
| 13-acceptance-sql-ack-failure | 50 | `d24cb0a13e8ccf18d46bf564609cda6062c9305ea75d3efd386306b5f3ff3f40` | terminal unresolved; provider supported |
| 14-bounded-no-resend | 50 | `c64ed2edab993064ba43c969bf8f955a74b96538dfed4bffafeb01ceba5cc766` | bounded supported; forever unresolved |

Only fixture 07's report digest changed due removal of an inadmissible rule, and fixture 10's
changed due the added revoked producer. Their reviewed verdicts and leaves did not change.
Fixture 02's removed rule had never derived a row in the mismatched-surface input, so its report
digest is unchanged. Fixture 10 remains the only fixture whose expected leaf set changed in the
original provenance repair; this attempt changed no expected leaf set.

Honest limits: Soufflé still independently computes closure, not end-to-end claim policy or
provenance; Python performs claim folding and diagnostics. The IR lacks a general domain-key
annotation, so the reviewed `outcome` non-key exception is frozen by name and should be replaced
by explicit key metadata before broadening aggregation schemas. Replay one-minimality is claimed
only when the 200-execution bound completes; a truncated replay is merely a reproducer. Section
16's `capcov experiment claims validate/evaluate` production CLI dispatch remains absent because
`packages/capabilities/src/capcov/cli.py` is outside this task's declared write set; no hidden
production command was changed. Section 22's performance/memory/startup/artifact/maintenance
study and final recommendation remain future `datalog-evaluation` work. No Shen, SCIP, external
execution, receipt, certificate, specialization, real-Go, Linux execution, or driver checkpoint
commit is claimed.

### 2026-09-15 gate/reviewer closure re-verification (attempt 4)

This sole-root reducer continued from the dirty attempt-3 tree at HEAD
`62510b3b2562bd3ff4b8a4c70f533875e41bdae8` (the required ancestor
`d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765` was verified, exit 0). The manifest dependencies
were already integrated in the recorded order, `python-reference` then `souffle-kernel`. No
parallel artifact was listed for this attempt. The two retained historical reducer patches under
ignored `.capcov/pi-workflow/patches/` were not applied, no worker commit was consumed, and no
worker worktree was touched. The existing GC root
`.capcov/pi-workflow/devshell-gcroot` resolved to a live Nix shell closure before the gates.
The reducer made no commit; the driver still owns checkpoint creation.

Every attempt-2 reviewer finding remains closed by a named control:

- `test_forall_domain_is_scoped_by_shared_noncontext_constants` isolates an unrelated
  same-tenant capability; claim-level universals now additionally require a ground,
  claim-eligible whole-domain closure witness. `test_forall_support_requires_attributed_domain_closure`
  proves missing closure stays unresolved and reviewed closure/member/support Evidence IDs are
  retained in Python's universal support.
- `test_all_aggregate_requires_domain_member_identity_in_source` rejects silent member
  projection; the exact-key cross-kernel controls remain in
  `test_boolean_all_compares_exact_domain_identity_and_projects_source_dimensions`.
- `test_support_mapping_cannot_project_away_shared_causal_identities` now mutates each of
  `event`, `notification`, `recipient`, and `attempt`. Mapping types remain exact, and the
  previously dormant non-default `required` / `allow_out_of_scope` options now fail validation
  rather than being silently ignored.
- `test_frozen_indexless_static_exceptions_still_cannot_join_runtime` keeps all frozen
  indexless declarations out of mixed runtime rules; exact indexed compatibility payload tests
  remain in `test_mixed_binding_join_requires_exact_index_run_witness`.
- `test_json_metadata_runs_in_python_and_remains_replayable_on_a_defect` exercises nested
  mapping metadata through both real kernels and strict replay loading.
- `test_fixture_ten_contains_a_revoked_path_and_an_independent_survivor` uses the fixture's
  refutation-effect revocation, while the claim-local differential revocation tests cover
  independent survival and tainted-only elimination.
- `test_output_subset_keeps_omitted_derived_claim_semantics` keeps internally required derived
  outputs available for folding.
- `test_individual_duplicate_evidence_producers_are_one_minimized` proves bounded
  one-minimality over individual Evidence IDs, not only fact rows.

Additional trust-boundary controls were added in the same kernel task. Facts/evidence targeting
`modality=claim` now fail with `producer-authored-claim`; polarity tests derive claim tuples from
reviewed rules instead of seeding conclusions. A rule for one ground claim no longer suppresses
a mapping for another claim sharing the relation. Ground claim terms must equal their context
values. Supported evidence no longer masks a relevant runtime `stale`/`out-of-scope` diagnostic,
while an independent proof still survives an assumption-only revoked path. Claim-local Soufflé
reruns now share one cumulative deadline and a default 64-process cap, and equal eligible bundles
are cached. The corpus adapter rejects wrong `arg_order` and excess arguments instead of relying
on truncating `zip`.

Reviewed corpus changes remain narrowly enumerated. Attempt 3 removed unsafe mixed static/runtime
rules from fixtures 02 and 07 and added `fact-revoked-proof` to fixture 10. This attempt changed
only fixture 02's ground claim context `surface` from `route-b` to `route-a`, matching its claim
term and making the mismatch explicitly route-A claim versus route-B runtime evidence. Verdict,
status, and expected leaf sets did not change. Fixture 10's original provenance correction remains
the sole expected-leaf change: support is exactly
`("assumption-independent-source", "fact-independent-proof")`. `corpus/expected.json` is the
authoritative review table; the stale section-15 path sketch was corrected above.

Pinned tool observation and per-fixture differential command:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; p=$(command -v souffle); printf "path=%s\\n" "$p"; souffle --version 2>&1; python --version; cd packages/capabilities && PYTHONPATH=src python - <<"PY"
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims.differential import compare
for path in sorted(Path("tests/claim_semantics/corpus").glob("[0-9][0-9]-*.json")):
    result = compare(load_fixture(path), shrink=False)
    claims = ";".join(f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}" for claim in result.python.claims)
    print(path.stem, len(result.python.relations), result.python.canonical_digest, claims)
PY'
```

Exit 0. Python was 3.12.14. Soufflé resolved to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`; its own banner again
left `Version:` blank and reported 32-bit word size with `ffi ncurses sqlite zlib`, so no banner
version is invented. All fixtures matched every declared relation and admitted claim field:

| fixture | relations | canonical report digest | claims |
|---|---:|---|---|
| 01-correlated-positive | 50 | `72f385df2c33b9eefc503c06e23c4502eeb008f4b1ffde06374107603aed96fb` | terminal supported/complete/derivational |
| 02-surface-mismatch | 50 | `8e112a0638a5a123eaff537755b2233df2218e7989dc091a7b0ddbaf0cc2ad27` | effect unresolved/complete/derivational |
| 03-post-without-creation | 50 | `d52d05321e47d95cccc64e9e8a81cefa81dc56b4cf97157b9cafa5dca9b4e4c8` | created unresolved; request supported |
| 04-authorization-polarity | 50 | `d1b0e16d3390a50c9707c34ee45dcc80819834d680b540e2dba090672059eaf5` | allow supported; deny supported |
| 05-wrong-event-email | 50 | `416484a285af3de3632137f528ba48aa102a03a4706cad739b9cf3dcd083634d` | target-mail unresolved |
| 06-context-contamination | 50 | `c28aa042f5e7bfa854b96f610b023a725f2cdbc103d73ecefe5b56787813ce57` | terminal unresolved |
| 07-shared-mistaken-assumption | 50 | `ec6946397ee18fb525364ad0ee7b378357c6fde07b4289aa5fadf3eb8be6523f` | delivered unresolved |
| 08-rejection-versus-missing | 50 | `7fb25480922aedebead44f0dd84fba1b8b4b5ec56c365d305c2e563c3c837f13` | explicit denial refuted; missing denial unresolved |
| 09-support-and-refutation | 50 | `10fe80267ba1e8b13b9f4be5c925d68f3e265cc1254d15c0570e0ebde37769ff` | terminal conflicting |
| 10-revoked-assumption-alternative | 50 | `9295043b384a3ec90cff0158784b1b3f1709d2a57cac2e69f5eba4007e0d7fb8` | saved supported |
| 11-compatible-history-sets | 51 | `7525fdc6cceea21fbf1b62191bb57fee18ea6825f8526e52bc8a5b98a0c033d1` | universal unresolved/inconsistent; mixed unresolved/complete |
| 12-unexpected-runtime-surface | 50 | `1d4e7934ca9bb7cc67f08ca762fe8441265b91418be366b2d9a31662fe07128f` | model-complete unresolved/out-of-scope |
| 13-acceptance-sql-ack-failure | 50 | `d24cb0a13e8ccf18d46bf564609cda6062c9305ea75d3efd386306b5f3ff3f40` | terminal unresolved; provider supported |
| 14-bounded-no-resend | 50 | `c64ed2edab993064ba43c969bf8f955a74b96538dfed4bffafeb01ceba5cc766` | bounded supported; forever unresolved |

The exact manifest `differential-tests` command from `.pi/workflows/capcov-experiment.json`
exited 0: 18 differential tests ran in 30.229s and 8 shrinker tests ran in 2.070s; both were
`OK`, and the explicit skip rejection did not fire. The exact manifest `kernel-tests` command
exited 0: its five discoveries ran 1, 10, 9, 2, and 31 tests in 0.045s, 0.006s, 0.056s,
0.089s, and 2.921s; every discovery was `OK`, and neither real-Soufflé discovery skipped. The
exact manifest regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 640 tests in 39.269s`, `OK (skipped=67)`. These 67 broad-suite optional/platform
skips are not used as Soufflé evidence. The focused gates above resolved the pinned binary and
rejected skips. The frozen static contract still contains 43 declarations with canonical JSON
SHA-256 `d936ba0c35465bcded2d3a51d5d3facfdd9fe2b27991de7fa216bac252299071`;
the source file byte SHA-256 is `80ce00e848304953b54ab80aaa023ad0a58240f8dc3d3fc803f41973b7bbcac9`.

Honest limits: Soufflé independently computes closure, but Python in `souffle.py` still folds
claim mappings, diagnostics, and quantifiers; provenance agreement is not claimed. Generic
same-binding rules still lack an explicit authority form for intentionally omitting a context
dimension; validation closes causal-identity omission in support/refutation mappings and all
mixed static/runtime joins, but broader rule-authority work remains Stage D. The corpus's broad
fixture `context` is retained as scenario metadata while adapter Evidence context is derived
from typed relation arguments; it is not an independently authenticated producer context.
Empty `producer_classes` are not producer admission authority. The static JSON's inclusion in an
installed wheel has not been demonstrated. Row/output limits apply to each Soufflé subprocess,
while deadline and process-count limits are cumulative. Replay one-minimality remains conditional
on completing the 200-execution certification pass. Section 16's production CLI dispatch remains
absent because `capcov/cli.py` is outside this task's write set. Section 22 performance, memory,
artifact-size, maintenance, Shen, specialization, external execution, real-Go evidence, Linux
execution, final recommendation, and driver checkpoint remain unclaimed.

### Scope boundary and deferred findings for `datalog-differential`

Three driver attempts on 2026-09-15 passed every gate and were refused by both reviewers.
Several findings are in scope and must be closed here: conjunctive claim mappings that combine
indexless static support with runtime support without an `index/run` witness; a refuted
universal whose refutation leaves omit the domain-member and closure evidence; `static-context`
enforcement with an explicit allowlist rather than a silent skip. Other findings restate
decisions this plan already made or belong to later tasks; they are recorded here so a
reviewer can see the decision instead of inferring neglect:

- **Soufflé-side provenance.** Soufflé computes relational closure; claim folding, quantifier
  expansion, diagnostics, and leaf reporting are Python. This checkpoint compares closure plus
  verdict, operational status, basis, and missing premises. Engine-independent certificates
  that make provenance comparable across kernels are section 29's bounded backward-chaining
  extractor, owned by `scip-datalog-differential`, and the ground checker is `datalog-certificates`.
- **Bounded replay minimization.** The plan's discipline (sections 17 and 25) is bounded search
  with honest truncation. A replay produced after `max_steps=200` carries `shrink_truncated=true`
  and is a reproducer, not a proven one-minimal bundle. Unconditional minimality is not required.
- **Producer-class authority** (`RelationDecl.producer_classes` is declared but not enforced)
  and **causal-identity projection in generic rules** (a rule may omit a non-context causal
  column such as `event` or `attempt`) are pre-existing plan-level gaps from section 13. They
  are owned by `datalog-certificates` (authority checks over rule forms) and must be closed
  before any static/runtime correspondence claim in section 29 is admitted as evidence. The
  current manifest sequences `datalog-certificates` after `scip-datalog-differential`; therefore
  the earlier static reducer cannot admit its output as trusted correspondence until the later
  authority gate has completed. This ordering limitation is explicit rather than waived.
- **Experimental CLI** (section 16) remains with `reference-evaluator`, currently a legacy
  manifest lane; `capcov/cli.py` is outside this task's write set. **Performance evaluation**
  (section 22) is owned by `datalog-evaluation`.

The task's `planSections` were narrowed to section 27 so reviewers evaluate the task against
its own specification; the acceptance statements were reworded to match the bounded-shrink
design. The reviewers' finding lists from all three attempts are retained in the journal.

### 2026-09-15 in-scope trust-boundary closure (attempt 5)

This sole-root reducer continued from the prior dirty tree at HEAD
`6fdb00b7e9a469d33c2ef5aae8523c69b85df1d0`; `git merge-base --is-ancestor
 d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765 HEAD` exited 0. The task packet listed no
parallel artifact for this attempt. The already integrated dependency order remains
`python-reference`, then `souffle-kernel`; no patch or worker commit was applied and no worker
worktree was mutated. The reducer did not commit.

The remaining in-scope reviewer findings were closed as follows:

- Support mappings are grouped by claim id according to their actual conjunctive evaluator
  semantics. Every static/runtime source pair now requires a support mapping to a compatibility
  relation that targets both sources, declares `index` and `run` as compatibility payload, and
  binds those positions through the same claim columns as the static digest `index` and runtime
  `run`. A declaration alone, a wrong-target/payload relation, an unbound or swapped projection,
  or an observation-only witness fails `mixed-binding-join`. An exact witness mapping validates;
  without its witness fact both real kernels return `unresolved`, and with the fact both return
  `supported`. Refutation mappings remain disjunctive and are intentionally outside this check.
- The frozen indexless declarations remain exact allowlist entries, not a naming convention.
  Near-miss names and schemas fail `static-context`, and even an exact allowlisted declaration
  fails `mixed-binding-join` when combined with runtime support. The route-A mutant of fixture 02
  proves matching static/runtime payload values cannot bypass the absent index/run identity.
- A universal counterexample's Python refutation now contains the claim-eligible whole-domain
  closure proof, that counterexample's domain-member proof, and its own refutation proof. It does
  not include unrelated domain members. A conflicting one-member universal retains separately
  structured support and refutation leaf sets. No Soufflé provenance was manufactured.

The justified corpus changes are only mapping-policy narrowing. Fixture 02 removed its two
unsafe support mappings and retained its two observation mappings. Fixture 07 changed its two
unsafe support mappings to observation mappings, preserving output causality. Their file SHA-256
values are respectively `32ff7908aa39b5aba4930a92fadb3f976dbbe282ae184d3d9cc1d84523cc0520`
and `53901c0cf85e931bc20f3cf5e2ba0905db416902685ca6720b203d3037526ee2`.
Both fixtures remain `unresolved/complete/derivational`; no expected verdict or leaf set changed,
and `corpus/expected.json` was not changed in this attempt.

Pinned tool observation used:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'set -eu; p=$(command -v souffle); printf "path=%s\\n" "$p"; souffle --version 2>&1; python --version; nix --version'
```

Exit 0. Soufflé resolved to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`; its banner again left
`Version:` blank and reported 32-bit word size with `ffi ncurses sqlite zlib`. Python was 3.12.14;
Nix was Determinate Nix 3.21.5 / Nix 2.34.8.

The exact manifest `differential-tests` command was rerun after the final code/test changes:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Exit 0. Differential discovery ran 22 tests in 33.452s and shrinker discovery ran 8 tests in
3.032s. Both reported `OK`; the explicit skip rejection did not fire.

The exact manifest `kernel-tests` command was rerun:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0. Its five discoveries ran 1, 10, 11, 2, and 31 tests in 0.044s, 0.006s, 0.058s,
0.088s, and 2.678s. Every discovery reported `OK`; neither real-Soufflé discovery skipped.

The exact manifest regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 646 tests in 39.144s`, `OK (skipped=67)`. The 67 broad-suite optional/platform
skips are not Soufflé evidence; both focused gates resolved the pinned binary and rejected
skips. `git diff --check` also exited 0.

The per-fixture command was rerun through the same pinned shell:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python - <<"PY"
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims.differential import compare
for path in sorted(Path("tests/claim_semantics/corpus").glob("[0-9][0-9]-*.json")):
    result = compare(load_fixture(path), shrink=False)
    claims = ";".join(f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}" for claim in result.python.claims)
    print(path.stem, len(result.python.relations), result.python.canonical_digest, claims)
PY'
```

Exit 0. All fourteen fixtures matched every declared relation and the admitted claim fields.
Their relation counts, report digests, and verdict/status/basis output are exactly the attempt-4
table above; in particular fixture 02 remains digest `8e112a…` and fixture 07 `ec6946…` because
mapping metadata is not part of `KernelReport`. The frozen static schema remains 43 declarations,
canonical digest `d936ba0c35465bcded2d3a51d5d3facfdd9fe2b27991de7fa216bac252299071`, and source-byte digest
`80ce00e848304953b54ab80aaa023ad0a58240f8dc3d3fc803f41973b7bbcac9`.

Honest limits remain those in the scope boundary: Soufflé independently computes closure while
Python still performs claim/quantifier/diagnostic folding, so no independent end-to-end
provenance agreement is claimed. A `shrink_truncated=true` replay is a bounded reproducer, not
proved minimal. Producer-class authority and generic-rule causal projection remain owned by
`datalog-certificates`, with the manifest sequencing limitation above. The experimental CLI is
still deferred to legacy `reference-evaluator`, and section 22 to `datalog-evaluation`. No Shen,
SCIP, external execution, receipts, certificates, production CLI behavior, or driver checkpoint
is claimed here.

### 2026-09-15 trust-boundary and discriminating-corpus repair (attempt 6)

This sole-root reducer continued from the dirty attempt-5 tree at HEAD
`6fdb00b7e9a469d33c2ef5aae8523c69b85df1d0`; the required ancestor check exited 0. The task
packet listed no parallel artifact. Dependency integration remains the already-recorded
`python-reference`, then `souffle-kernel` order; no patch or worker commit was applied, no worker
worktree was used, and the reducer did not commit.

Both request-changes reviews were treated as gates. The repairs are:

- Validation now ties every `EvidenceMapping.claim_relation` to the actual relation of the Claim
  selected by `claim_id` before projection or mixed-binding checks. The decoy-relation attack
  (`actual_claim(x,event)` but a mapping declared against `decoy_claim(x)`) is
  `mapping-claim-relation`/`invalid-input` at both kernel boundaries.
- Conjunctive support mappings now backtrack over one shared claim-variable environment in both
  implementations. Static, runtime, and compatibility rows with unrelated index/run values no
  longer manufacture support; adding the exact `index_describes_run(index,run)` row supports the
  variable-valued positive control.
- Claim-level existential provenance chooses one deterministic eligible OR path. Alternative
  derivations remain retained in the provenance graph and available after revocation, but their
  leaves are no longer unioned into an apparent conjunctive certificate. A two-branch graph
  control retains both relation proofs and reports only canonical `leaf-a` for the claim.
- `source_tree_observed(tree_digest)` is now the only exact context-free static fingerprint.
  Legacy `static_route_exists` and `mail_path_declared` no longer bypass `static-context` merely
  by name. Near-miss name, column, type, and context-flag declarations fail validation.
- Corpus fixtures 02 and 07 now use indexed static observations, an explicit
  `index_describes_run` fact, and valid mixed static/runtime rules. Fixture 02 stays unresolved
  for route-A static versus route-B runtime, becomes supported when runtime is changed to route A,
  and becomes unresolved again when only the compatibility fact is removed. Fixture 07 stays
  unresolved because both path producers depend on the rejected provider assumption and becomes
  supported when those two dependencies are removed. Thus neither reviewed negative is vacuous.
  Their source SHA-256 values are `fa2179b234ee4234ef047f5d2fcc18bfcfe8d960b23591a4638deb275c976ee4`
  and `46b9d0abe5fcece46f66dc201f367e30f5c4e1018b3da5a033a389818032457c`.
- `expected.json` now freezes evaluation basis by quantifier. The corpus provenance oracle checks
  every claim's verdict, status, basis, support/refutation Evidence IDs, and structured
  missing-premise explanation. Those explanations come from reviewed missing-premise output
  declarations after evaluation, not from producer verdict metadata.
- Differential operational failure never constitutes agreement, even when both sides report the
  same failure. Shrinking rejects `max_steps > 200`; one step is one candidate comparison that
  invokes both runners, while the caller's initial mismatch is outside the counter. The final
  step executes the strictly reloaded replay. A transient initial mismatch remains blocking,
  persists the original digest-named bundle, and reports `replay_reproduced=false` and
  `shrink_truncated=true` instead of claiming minimization.

Pinned tool observation:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'set -eu; p=$(command -v souffle); printf "path=%s\\n" "$p"; souffle --version 2>&1; python --version; nix --version'
```

Exit 0. Soufflé resolved to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`; its banner again left
`Version:` blank and reported 32-bit word size with `ffi ncurses sqlite zlib`. Python was 3.12.14
and Nix was Determinate Nix 3.21.5 / Nix 2.34.8.

The exact manifest `differential-tests` command was rerun:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Exit 0. The final rerun after strengthening the equal-operational-failure control ran 25
differential tests in 33.286s and 10 shrinker tests in 4.339s. Both were `OK`; the explicit
skip rejection did not fire.

The exact manifest `kernel-tests` command was rerun:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0. Its five discoveries ran 1, 10, 12, 2, and 31 tests in 0.045s, 0.006s, 0.061s,
0.157s, and 2.653s. Every discovery was `OK`; neither real-Soufflé discovery skipped.

The exact manifest regression command was rerun:

```sh
nix develop --no-update-lock-file --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0 on the final rerun: `Ran 653 tests in 42.757s`, `OK (skipped=67)`. Those broad-suite optional/platform
skips are not Soufflé evidence. During repair, a focused evidence-policy command first exited 1
with one `KeyError: tenant` after the static context became index-only; the assertion was corrected
to check static `index` and runtime `tenant`, and its exact focused rerun passed 1 test.
`git diff --check` exited 0.

A pinned-shell per-fixture run used:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python - <<"PY"
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims.differential import compare
for path in sorted(Path("tests/claim_semantics/corpus").glob("[0-9][0-9]-*.json")):
    result = compare(load_fixture(path), shrink=False)
    claims = ";".join(f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}" for claim in result.python.claims)
    print(path.stem, len(result.python.relations), result.python.canonical_digest, claims)
PY'
```

Exit 0. It compared every declared relation and admitted claim field; all fourteen matched.
Adding the shared compatibility declaration makes the count 51 relations (52 for fixture 11).
Canonical Python/Soufflé report digests were:

| fixture | digest |
|---|---|
| 01 | `b8dff89a3a46448425fc2964ee0f687d7256797576b0e9e3338aef51b096472e` |
| 02 | `50b3d20617546a30c9d43fb8022ad9fccdbd9424ea76cef7937b107b195a07d4` |
| 03 | `dbe4b81c5c09637ca7cecda2464e67b9b2fce428b5b0cea806146fbd0d56ff5f` |
| 04 | `80909bf03217a43a5fde19c83d19a136bff799df1e49126e0ab983a06a8214c2` |
| 05 | `01027fa9dfb1d53b46e743088d7526909b08a308cb9b75dc7f4170371e86eedb` |
| 06 | `e5ab74db0791c24170b551c15250bd371662518bd924d1e86be8ba8128ada7f9` |
| 07 | `bad57767c10e8b173ececbc63bb587a62bbc6cc8470786041eb6b555324987a0` |
| 08 | `c469d3a410d11c27a03cd0e92f9142d6cff28b57f6e2a92bc8d526f2b018270b` |
| 09 | `fff1921eb4d63a325e7b9fd630e8a2e5a57360ed2909b671b72469f88a76bdd2` |
| 10 | `ce16e1617483fa669a05b8b18ce4f9f0ddd84eed972f4f205b58866069f3cc6d` |
| 11 | `7cc9b29dd5fb2efaecc92f4fab1072bbeddf92b0fcd4b5b1506926fbe41aa378` |
| 12 | `e9ea27ebf410d2103d876cdd61b7f67fef03c3b000c89a2332e1d253b18d81d0` |
| 13 | `6773e22a599444967bff3ef84c095026e68d369731bbb5c272e75c58fda66a2e` |
| 14 | `a0f542b53bcb8e66ca1001ac233c5cd10aeafbcda085145f1a809d437d0f6f91` |

No reviewed verdict or support/refutation leaf set changed. Fixture 10 remains the sole original
leaf-set correction. The section-29 static schema remains 43 declarations with canonical digest
`d936ba0c35465bcded2d3a51d5d3facfdd9fe2b27991de7fa216bac252299071` and source-byte SHA-256
`80ce00e848304953b54ab80aaa023ad0a58240f8dc3d3fc803f41973b7bbcac9`.

Honest limits: Soufflé still independently computes closure only; Python code in `souffle.py`
performs mapping joins, quantifier folding, diagnostics, and structured missing-premise
materialization. This is not independent end-to-end verdict or provenance evidence. A replay
with `replay_reproduced=false` is only the original blocking input, and any
`shrink_truncated=true` replay is not proved minimal. The JSON static schema is verified in the
source tree after merging section-29 derived/runtime targets; installed-wheel resource inclusion
was not established, and no runtime consumer was added. Producer authority and generic-rule
causal projection remain deferred to `datalog-certificates`; CLI work remains with
`reference-evaluator`, and performance/evaluation remains with `datalog-evaluation`. No Shen,
SCIP, certificate, specialization, external application execution, receipt, real-Go, Linux,
production CLI, section-22 recommendation, or driver checkpoint evidence is claimed.

### 2026-09-15 shared-semantic-blind-spot repair (attempt 7)

This sole-root reducer continued from the dirty attempt-6 tree at HEAD
`6fdb00b7e9a469d33c2ef5aae8523c69b85df1d0`; `git merge-base --is-ancestor
 d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765 HEAD` exited 0. The task packet listed no
parallel artifact, so no patch was applied. The dependency order remains the previously
integrated `python-reference`, then `souffle-kernel`; no worker commit or worker worktree was
used. The reducer made no commit, and no driver checkpoint is claimed.

The request-changes findings were reproduced as shared semantic defects rather than accepted
because both kernels agreed:

- Mixed-binding validation now treats negated ordinary atoms as relation reads. Completeness
  declarations must have the same binding as their target, and a completeness atom inherits its
  target's binding/compatibility identity during join validation. Thus a runtime observation plus
  runtime-labelled closure for a negated indexed static relation cannot bypass the exact positive
  `index/run` compatibility witness. Static assumptions now have the same indexed-static boundary
  as observations/completeness; a mutation of `authz_symbol__accepted` that drops `index` fails
  `static-context`.
- Missing-premise materialization in both claim-folding paths now applies
  `requires_all_evidence`, `requires_any_evidence`, `excludes_evidence`, and `when_claim`, using
  claim-relevant reviewed Evidence IDs. Inactive or incomplete missing-premise templates do not
  render, and unrelated observed/forbidden outputs no longer erase the semantic fallback.
  `derived`/`underived` are also distinguished. Fixture 08 therefore gained an explicit reviewed
  `authorization_rejected` missing-premise declaration for its unresolved missing-denial claim;
  both the fixture-local oracle and `expected.json` now require
  `{"relation":"authorization_rejected","reason":"no explicit rejection for the claimed actor"}`.
  Its verdict, operational status, basis, and support/refutation leaves did not change.
- Soufflé claim folding now takes a universal's member set from the full closure and separately
  requires every member to survive claim-local eligibility. Revoking one member's sole producer
  returns `unresolved/complete/bounded-history-model` with the same `domain-evidence` premise as
  Python instead of shrinking the quantified domain and supporting the remainder.

Additional adversarial checks from the read-only scouts were verified and closed in this same
kernel-semantics scope. A `FORALL` claim must ground every domain context position, preventing a
member from one run and a closure row from another from being combined. An `all` aggregate proof
now retains every scoped domain-member proof as AND evidence, while duplicate producers remain OR
alternatives. Differential missing-premise normalization canonicalizes strings as JSON strings,
so a structured object cannot collide with text containing the same JSON spelling. Ground
empty-body axioms are rejected as `evidence-free-rule` rather than authorizing leafless claims.
The deferred producer-authority and transitive generic-rule projection gaps are not represented as
fixed by these direct checks and remain owned by `datalog-certificates` as recorded above.

Pinned runtime and per-fixture observation used the exact command:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; p=$(command -v souffle); printf "path=%s\\n" "$p"; souffle --version 2>&1; python --version; nix --version; cd packages/capabilities && PYTHONPATH=src python - <<"PY"
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims.differential import compare
for path in sorted(Path("tests/claim_semantics/corpus").glob("[0-9][0-9]-*.json")):
    result = compare(load_fixture(path), shrink=False)
    claims = ";".join(f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}" for claim in result.python.claims)
    print(path.stem, len(result.python.relations), result.python.canonical_digest, claims)
PY'
```

Exit 0. Soufflé resolved to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`; its banner again left
`Version:` blank and reported 32-bit word size with `ffi ncurses sqlite zlib`. Python was 3.12.14
and Nix was Determinate Nix 3.21.5 / Nix 2.34.8. All fourteen fixtures matched every declared
relation and admitted claim field. Relation counts remain 51 (52 for fixture 11). Digests remain
those in the attempt-6 table except fixture 08, whose newly reviewed missing premise changes its
report digest to `00ecc41d396887ae9062a3a1be41d1520467d72d7a5845347f40a2954518c387`.
Fixture 08 remains explicit-denial `refuted/complete/derivational` and missing-denial
`unresolved/complete/derivational`. The other thirteen digests were byte-for-byte unchanged.

The exact manifest `differential-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Exit 0. Differential discovery ran 26 tests in 31.178s and shrinker discovery ran 10 tests in
3.789s; both were `OK`, and the explicit skip rejection did not fire.

The exact manifest `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0. Its five discoveries ran 1, 11, 13, 2, and 33 tests in 0.047s, 0.009s, 0.064s,
0.309s, and 2.810s. Every discovery was `OK`; neither real-Soufflé discovery skipped.

The exact manifest regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0 on the final rerun: `Ran 662 tests in 38.167s`, `OK (skipped=67)`. Those broad-suite skips are the existing
optional-tool/platform skips and are not used as Soufflé evidence. The focused kernel gates above
resolved the pinned binary and rejected skips. `git diff --check` exited 0. Fixture 08's file
SHA-256 is `069955b6ba9a0eb3d2b0f57c5d10c73d1fc726c075913505f40df153421585ef`, and the updated
review table SHA-256 is `9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`.
The frozen static schema source remains byte digest
`80ce00e848304953b54ab80aaa023ad0a58240f8dc3d3fc803f41973b7bbcac9` and canonical relation
digest `d936ba0c35465bcded2d3a51d5d3facfdd9fe2b27991de7fa216bac252299071`.

Honest limits remain: Soufflé computes independent relational closure, while Python in
`souffle.py` still performs mappings, diagnostics, quantifier folding, and structured
missing-premise rendering; this is not independent end-to-end verdict or provenance evidence.
Output evidence triggers are scoped by the currently declared direct mapping/diagnostic/proof
causality, not a transitive information-flow certificate. Producer-class authority and generic
causal-identity projection remain deferred to `datalog-certificates`. A truncated differential
replay is only a bounded reproducer. No Shen, SCIP, external execution, receipt, certificate,
specialization, real-Go, Linux, production CLI, section-22 recommendation, or driver checkpoint
is claimed.

### Open findings after six review rounds (specification for `datalog-kernel-closure`)

Owned by `kernel-closure` (write set: `claims/{evaluator,souffle,validation,output,ir}.py` and their tests):

1. `evaluator._Engine.add` replaces a row's canonical proof whenever a recursively nested
   signature changes, so for valid positive cycles (`reach(X) :- reach(X)` sorting before its
   base rule) the fixed point never stabilizes and `signature()`/`repr()` recursion can raise
   `RecursionError`. Required: a stable canonical-proof choice (prefer the proof with the
   smaller depth, then lexical) so cycles converge; any bound hit yields a named operational
   report; a test with a derived row reachable through both a base rule and a self-cycle.
2. `output._relevant` builds claim values from constants only, so mapped evidence for a
   variable-valued or universally quantified claim compares `None` to the evidence value and
   is classified irrelevant; `requires_all_evidence`, `requires_any_evidence`,
   `excludes_evidence`, and evidence-backed fields then evaluate falsely in both kernels.
   Required: unify variables against evidence rows; tests with variable-valued claims.
3. `_validate_context_joins` accepts a compatibility witness by name and `repr`-equality of
   terms without checking that the payload column types equal the target `index` (digest)
   and `run` types, so untyped literals can forge a witness. Required: typed check and a
   negative test.

Owned by `differential-closure` (write set: `claims/{differential,shrinker}.py` and their tests):

4. `shrinker._candidate` drops `OutputTemplate`s whose evidence references are no longer
   retained and rewrites `bundle.outputs`, so shrinking changes reviewed diagnostic semantics;
   `_difference_shape` keeps only the names of differing claim fields, so a minimized bundle
   can exhibit a different missing-premise disagreement than the original. Required: reduce
   facts and matching evidence only; assert relations, rules, claims, mappings, diagnostics,
   and outputs are byte-identical in every replay; preserve the original left/right values; a
   mismatch that disappears on the baseline rerun persists the original disagreement.

Everything listed under "Scope boundary and deferred findings" stays deferred.

### 2026-09-15 parallel kernel-closure integration (`kernel-closure-integrate`, attempt 1)

The driver applied exactly the two listed fan-out artifacts in manifest dependency order; journal
sequences 106 and 107 are `fanout-patch-applied` for `kernel-closure` and then
`differential-closure`:

1. `.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch`, SHA-256
   `c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`;
2. `.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch`, SHA-256
   `86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.

Before making reducer edits, both corresponding `git apply --reverse --check` commands exited 0,
proving the working tree contained each complete patch, and the only changed paths were the seven
paths declared by the two workers. No patch was applied twice, no worker commit was consumed, and
no worker worktree was present or mutated. The tested integration parent is
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`; required ancestor
`d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765` was rechecked with
`git merge-base --is-ancestor` (exit 0). `14965ed1168b5cbeaf110a19e3a24818c165ca2b`
remains the explicitly unapproved WIP from section 26, not completion evidence. The implementer
made no commit. The driver must append its admitted checkpoint hash after review; inventing that
future hash here would violate checkpoint ownership and could not be truthful.

The patches implement depth-then-lexical canonical proof selection (with `alternatives` excluded
from the choice), variable-aware output relevance, typed compatibility payloads, fact/evidence-only
shrinking, and exact left/right mismatch shape. Reducer adversarial review added controls for a
late-arriving shorter child proof propagating through an already-retained same ground path, a
base-plus-self-cycle bundle compared through both real kernels, wrong `index` and wrong `run`
compatibility types plus untyped and explicitly typed controls at both kernel boundaries, repeated
claim variables/wrong constants/wrong run scope, and every shrink candidate's complete invariant
after blanking only `facts` and `evidence`. That last control wraps both runners, so it checks the
initial input, strict reloads, all ddmin candidates, and final replay rather than inspecting only
the persisted result.

The reducer also reproduced one shared output-policy blind spot: while evaluating a `forall`,
`relevant_evidence_ids` looked the claim id up in the bundle and recovered the open aggregate claim
instead of the grounded member. Evidence for member `a` could therefore activate a missing-premise
template while evaluating the sole domain member `b` in both claim-folding paths. Output relevance
now accepts the grounded claim instance, and universal missing premises are deduplicated from the
already-grounded subresults rather than rendering templates again against the open claim. This is
shared Python claim-policy code used around both closure engines, not independent Soufflé semantic
evidence; the new differential control nevertheless requires the two complete reports to agree.

No corpus JSON changed. The exact byte-stability command

```sh
git diff --exit-code HEAD -- packages/capabilities/tests/claim_semantics/corpus
```

exited 0 after all edits; `corpus/expected.json` remained SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`.
No reviewed corpus verdict, status, basis, missing premise, or leaf set changed. The change in
`test_provenance_leaves.py` from `leaf-a` to `leaf-z` is a non-corpus topology control: `leaf-z`
is the shallower proof and therefore correctly wins before lexical tie-breaking. It must not be
reported as a reviewed corpus leaf change.

The existing GC root remained live at
`.capcov/pi-workflow/devshell-gcroot -> /nix/store/hc9i3s6l94vdlq8hx10zxmy4shq3gfjr-nix-shell`.
The two dependency gates and all three reducer gates were then run from the pinned shell. The exact
`kernel-closure-tests` dependency command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0 on the final run. Its ten discoveries ran 13, 20, 15, 1, 16, 11, 5, 23, 2, and 33
tests; every discovery reported `OK`, and neither real-Soufflé discovery skipped. An earlier run
during reducer repair exited 1 in the first 13-test discovery because the initial universal fix
returned the same grounded missing-premise object twice for fixture 11. The reducer deduplicated
by canonical JSON and reran the complete exact gate above; the failed run is not presented as
evidence.

The exact `differential-closure-tests` dependency command and the reducer's byte-identical
`differential-tests` command were each executed separately:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Both executions exited 0. The dependency run reported 26 differential tests in 36.293s and 13
shrinker tests in 5.797s; the reducer run reported the same counts in 33.881s and 5.608s. All were
`OK`; skip rejection did not fire.

The exact reducer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0. Its six discoveries ran 1, 11, 13, 15, 2, and 33 tests; all reported `OK`, and both
focused Soufflé discoveries had no skips. The cross-engine cycle control asserts the exact
`reachable={("v",)}` closure and identical `supported/complete/derivational` claim fields with
canonicalized empty missing premises. The typed-boundary controls require both wrappers to return
named `invalid-input` for wrong or untyped payloads and require the explicitly typed valid bundle
to match.

The exact reducer regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 680 tests in 45.768s`, `OK (skipped=67)`. Those are existing optional/platform
skips and are not Soufflé evidence; the focused gates above resolved the real binary and rejected
any skip. `git diff --check` exited 0 after all changes.

The pinned tool and all-fixture assertion command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; p=$(command -v souffle); printf "path=%s\n" "$p"; case "$p" in /nix/store/*) ;; *) exit 1;; esac; souffle --version 2>&1; python --version; nix --version; cd packages/capabilities; PYTHONPATH=src python - <<'\''PY'\''
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims.differential import COMPARABLE_CLAIM_FIELDS, compare
paths = sorted(Path("tests/claim_semantics/corpus").glob("[0-9][0-9]-*.json"))
assert len(paths) == 14, len(paths)
for path in paths:
    bundle = load_fixture(path)
    result = compare(bundle, shrink=False)
    assert result.matched
    expected_names = tuple(decl.name for decl in bundle.relations)
    assert tuple(name for name, _ in result.python.relations) == expected_names
    assert result.python.relations == result.souffle.relations
    assert len(result.python.claims) == len(bundle.claims)
    assert len(result.souffle.claims) == len(bundle.claims)
    for left, right in zip(result.python.claims, result.souffle.claims):
        assert left.key == right.key and left.index == right.index
        for field in COMPARABLE_CLAIM_FIELDS:
            assert getattr(left, field) == getattr(right, field), (path, left.key, field)
    claims = ";".join(
        f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}/missing:{len(claim.missing_premises)}"
        for claim in result.python.claims
    )
    print(path.stem, len(result.python.relations), result.python.canonical_digest, claims)
PY'
```

Exit 0. It asserted all declared relation payloads and every claim's `semantic`, `operational`,
`basis`, and canonicalized `missing_premises` for exactly 14 fixtures. Relation counts were 51
(52 for fixture 11). Digests 01–14 were respectively `b8dff89a…`, `50b3d206…`, `dbe4b81c…`,
`80909bf0…`, `01027fa9…`, `e5ab74db…`, `bad57767…`, `00ecc41d…`, `fff1921e…`, `ce16e161…`,
`7cc9b29d…`, `e9ea27eb…`, `6773e22a…`, and `a0f542b5…`, exactly matching the attempt-7 corpus
record. Tool observation was
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`, Python 3.12.14, and
Determinate Nix 3.21.5 / Nix 2.34.8. The Soufflé executable's banner again left `Version:` blank;
the immutable Nix package path identifies 2.5, and no banner value is invented.

Remaining boundaries and owners are unchanged and explicit:

- Soufflé independently computes relational closure only. `souffle.py` still performs mappings,
  quantifier/status folding, diagnostics, and missing-premise rendering in Python and shares
  `output.py`; agreement is not independent end-to-end verdict or provenance evidence.
- Engine-independent provenance extraction belongs to `scip-datalog-differential`; independent
  ground replay belongs to `datalog-certificates`. Producer-class authority and transitive
  causal-identity projection through generic rules also belong to `datalog-certificates`. The
  manifest currently runs that authority task after `scip-datalog-differential`, so static/runtime
  correspondence cannot be admitted as trusted before the later gate; this sequencing gap is not
  waived.
- Shrinking preserves exact named operational failures, not `KernelReport.message`; messages are
  outside the admitted differential contract. A `shrink_truncated=true` replay remains a bounded
  reproducer, never unconditional minimality.
- Performance, memory, startup, artifact size, maintenance burden, and the recommendation belong
  to `datalog-evaluation`.
- The historical experimental-CLI assignment to legacy `reference-evaluator` is superseded by
  the ownership table below: the active owner is `datalog-evaluation`. No production CLI behavior
  was changed here.
- Static-schema installed-wheel inclusion and Linux execution remain unproved and are assigned in
  the ownership table below. No Shen, SCIP,
  certificate, specialization, generated experiment, external execution, receipt, real-Go, or
  final recommendation evidence is claimed by this integration.

### Ownership of deferred items and the checkpoint-hash rule (2026-09-15)

The first `kernel-closure-integrate` review round refused the task for two plan-level reasons
the human owns: the acceptance text asked section 27 to record "the closure commit", which the
driver creates only after review, so no implementer can satisfy it; and one deferred item (the
experimental CLI) was left without an owning task. Rules from here on: an implementer records
the integration parent commit, patch digests, gate commands and outputs, and tool store paths;
the driver alone records the checkpoint hash in `task-completed`. Owners of deferred items:

| deferred item | owning task |
|---|---|
| Soufflé-side provenance / engine-independent certificates | `scip-datalog-differential` (extractor), `datalog-certificates` (checker) |
| producer-class authority | **closed** by `6605d44` (cherry-picked from shen1's `experiment/replay-claims` e45384d): `evidence-producer` at ingestion; `ebb5897` (e7f624b) makes fact attribution unconditional |
| causal-identity projection in generic rules | `datalog-certificates` |
| unconditional replay minimality | not required (bounded shrinking with `shrink_truncated`) |
| installed-wheel inclusion of `claims/static/schema_static_v1.json` | `scip-datalog-differential` (owns `pyproject.toml`, `MANIFEST.in`) |
| experimental `capcov experiment claims validate/evaluate` CLI | `datalog-evaluation` (owns `capcov/cli.py`, `claims/cli.py`) |
| Linux execution of the claim kernels | `datalog-evaluation` via the nix `test-nix` CI check, else UNKNOWN |
| section 22 performance, memory, artifact size, recommendation | `datalog-evaluation` |

The `datalog-kernel-closure` fan-out itself succeeded on the first attempt of each worker
(`differential-closure` 10 minutes, `kernel-closure` 12 minutes; both gates green in their
worktrees; patches 16 KB and 28 KB applied cleanly in manifest order). A driver defect was observed:
two concurrent fan-out `task-attempt` events received the same `seq` (97); `appendEvent` is
not serialized under `Promise.all`. It does not affect completion derivation and is left as a
recorded harness limit. This ownership table supersedes every older section-27 reference to the
experimental CLI as `reference-evaluator` work or as unowned: CLI and Linux execution are
`datalog-evaluation`; installed-wheel static-schema inclusion and the provenance extractor are
`scip-datalog-differential`; the checker, producer authority, and generic causal projection are
`datalog-certificates`; performance and recommendation are `datalog-evaluation`. Nominal ownership
is not execution evidence, and the downstream target-go prerequisite may still prevent
`datalog-evaluation` from running.

### 2026-09-15 post-review semantic closure and isolated artifact replay

This continuation began at HEAD `065cd447ddb2eefa8c641586da54879f22434e31`, the human-owned
plan/manifest repair after the artifact integration. The artifact integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`. The artifact names and SHA-256 digests remain,
in manifest order, `kernel-closure` `c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`
and `differential-closure` `86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.
No worker commit was consumed and no worker worktree was read or mutated.

Unlike the earlier reverse checks on the integrated tree, this command performed an isolated
forward replay from the integration parent. It exported that revision to a fresh temporary
directory, checked and applied each complete artifact in manifest order, then removed the
directory:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; root=$PWD; git_path=$(command -v git); case "$git_path" in /nix/store/*) ;; *) echo "unpinned git=$git_path" >&2; exit 1;; esac; tmp=$(mktemp -d); trap '\''rm -rf "$tmp"'\'' EXIT; git archive 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 | tar -x -C "$tmp"; cd "$tmp"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; test -f packages/capabilities/tests/claim_semantics/test_kernel_closure.py; printf "integration_parent=%s\ngit=%s\nmanifest_order=kernel-closure,differential-closure\nforward_replay=ok\n" 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 "$git_path"'
```

Exit 0. It printed pinned Git
`/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`, the stated parent,
`manifest_order=kernel-closure,differential-closure`, and `forward_replay=ok`.

The remaining semantic findings were then closed. Validation rejects a `FORALL` variable in a
claim context column as `claim-context`, before either kernel can substitute a domain member that
contradicts the declared context; both wrappers return `invalid-input` for the run-a/run-b
adversary. Existential context variables retain their established context-filtering behavior.
The exact late-arriving-shorter-proof factory now runs through `compare`: Python provenance still
proves canonical `leaf-short` at depth 3, while the differential control requires identical full
relation closure and all four admitted claim fields. This is not a claim that Soufflé independently
selects or exposes provenance. Finally, output templates requiring multiple mapped Evidence IDs
now backtrack over one shared claim-variable environment. Individually relevant rows assigning
`a` and `b` to the same variable do not activate the template in either report; the semantic
fallback remains. A same-value positive control activates it. Explicit output/payload Evidence IDs
must also be relevant, closing the wrong-scope payload control.

The exact `kernel-closure-tests` dependency gate command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

The final execution exited 0. Its ten discoveries ran 13, 21, 20, 1, 16, 11, 5, 23, 2, and 33
tests, all `OK`; neither focused real-Soufflé discovery skipped. An earlier execution exited 1 in
the final 33-test discovery because the first validation repair rejected a pre-existing existential
context variable. Validation was narrowed to the vulnerable `FORALL` substitution path and the
complete exact gate was rerun; that failed run is not evidence.

The exact `differential-closure-tests` dependency command and byte-identical reducer
`differential-tests` command were run separately:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Both exited 0 on the final executions. The dependency execution ran 26 differential tests in
30.830s and 13 shrinker tests in 5.557s; the reducer execution ran 26 in 35.098s and 13 in 5.966s.
Every discovery was `OK` and skip rejection did not fire.

The exact reducer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Exit 0. Its six discoveries ran 1, 11, 13, 20, 2, and 33 tests; all were `OK`, and neither
focused Soufflé discovery skipped.

The exact regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0 on the final execution: `Ran 686 tests in 46.720s`, `OK (skipped=67)`. Those broad-suite optional/platform skips
remain non-Soufflé evidence. The focused gates resolved
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` and rejected skips.

The exact pinned-shell all-fixture/oracle command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; p=$(command -v souffle); printf "path=%s\n" "$p"; case "$p" in /nix/store/*) ;; *) exit 1;; esac; cd packages/capabilities; PYTHONPATH=src python - <<'\''PY'\''
import json
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims import canonical_json
from capcov.claims.differential import COMPARABLE_CLAIM_FIELDS, compare
root = Path("tests/claim_semantics/corpus")
expected_document = json.loads((root / "expected.json").read_text(encoding="utf-8"))
expected = expected_document["cases"]
paths = sorted(root.glob("[0-9][0-9]-*.json"))
assert len(paths) == 14, len(paths)
for path in paths:
    bundle = load_fixture(path)
    result = compare(bundle, shrink=False)
    assert result.matched
    names = tuple(decl.name for decl in bundle.relations)
    assert tuple(name for name, _ in result.python.relations) == names
    assert result.python.relations == result.souffle.relations
    assert len(result.python.claims) == len(bundle.claims) == len(result.souffle.claims)
    for declared, left, right in zip(bundle.claims, result.python.claims, result.souffle.claims):
        assert left.key == right.key and left.index == right.index
        for field in COMPARABLE_CLAIM_FIELDS:
            assert getattr(left, field) == getattr(right, field), (path, left.key, field)
        oracle = expected[path.stem]["claims"][declared.id]
        assert left.semantic == oracle["semantic_verdict"]
        assert left.operational == oracle["operational_status"]
        assert left.basis == expected_document["evaluation_basis_by_quantifier"][declared.quantifier.value]
        assert left.missing_premises == tuple(sorted(canonical_json(item) for item in oracle["missing_premises"]))
    print(path.stem, len(result.python.relations), result.python.canonical_digest)
PY'
```

Exit 0. It loaded exactly 14 numbered fixtures, checked every declared relation and
`COMPARABLE_CLAIM_FIELDS`, and additionally checked each report against `corpus/expected.json`
for semantic verdict, operational status, quantifier basis, and canonical missing premises.
Relation counts were 51 (52 for fixture 11), and report digests 01--14 were `b8dff89a…`,
`50b3d206…`, `dbe4b81c…`, `80909bf0…`, `01027fa9…`, `e5ab74db…`, `bad57767…`, `00ecc41d…`,
`fff1921e…`, `ce16e161…`, `7cc9b29d…`, `e9ea27eb…`, `6773e22a…`, and `a0f542b5…`.

Finally, `git diff --check` and
`git diff --exit-code HEAD -- packages/capabilities/tests/claim_semantics/corpus` both exited 0.
`corpus/expected.json` remains SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`; no corpus byte or reviewed
expectation changed. No checkpoint hash is recorded or promised here: only the driver may append
it in the post-review `task-completed` event.

Limits remain unchanged: Soufflé independently computes relational closure, but Python in
`souffle.py` performs mapping joins, quantifier/status folding, diagnostics, and missing-premise
rendering and shares `output.py`. Cross-kernel report agreement therefore is not independent
end-to-end semantics or provenance. The producer output and matching kernels are evidence, not an
oracle. No Shen, SCIP, external execution, receipt, certificate, real-Go, Linux, performance,
recommendation, or production behavior is claimed by this closure.

### 2026-09-15 corrected fail-closed contract and adversarial matrix

This reviewer-backpressure continuation used the existing integrated working tree at HEAD
`1756f71b9867ec62e6b6d36e5cc701b580ba511f`; it did not reapply either patch, consume a worker
commit, or read or mutate a worker worktree. The artifact integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`. In manifest order the artifacts remain
`claims-20260914185300567-kernel-closure-1.patch` SHA-256
`c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`, then
`claims-20260914185300567-differential-closure-1.patch` SHA-256
`86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.
No implementer checkpoint hash is recorded or promised; the driver alone may append that hash in
a post-review `task-completed` event.

The cross-kernel report contract is now documented in `claims/differential.py`. A top-level
complete result requires exact closure for every declared relation and exact `semantic`,
`operational`, `basis`, and canonical `missing_premises` for every claim. For invalid or exhausted
input, only the ordered pair of named top-level failures is cross-kernel contract data; relation
payloads, per-claim payloads, messages, resources, diagnostics, and provenance may be
backend-specific. Even an identical failure pair is never admitted: `compare` blocks and persists
a strict replay, and `_difference_shape` preserves the exact ordered names. The actual invalid
FORALL-context case demonstrates the intentional payload asymmetry: Python retains one invalid
claim result and declared empty relations while Soufflé stops at validation with no claims or
relations; both names are `invalid-input`, and the differential still blocks.

The prior semantic findings were repaired and tested rather than hidden by engine agreement:

- proof choice now orders depth first and then `canonical_json` of explicit recursive proof
  structure with `alternatives` omitted. Equal-depth alternatives from
  `JSON_METADATA_ONLY` rows select `leaf-a` in reversed construction order and after strict
  canonical serialize/reload; `_FrozenMap` allocation addresses no longer participate;
- output exclusions are anti-joined against each environment satisfying required and selected
  requires-any evidence. Required `X=a` plus excluded `X=b` renders the reviewed missing premise,
  while a separate excluded `X=a` producer suppresses it. Both existential and grounded FORALL
  controls cross the differential;
- the typed compatibility positive now contains attributed static, runtime, and
  `index_describes_run` facts plus a derived `joined("v")` claim. Both kernels produce exactly
  `joined={("v",)}` and `supported/complete/derivational`; removing only the witness fact and its
  Evidence leaves `joined` empty and the claim unresolved;
- `test_differential_adversarial_matrix.py` is the explicit registry. Fourteen valid entries
  cover base+self-cycle, late-shorter replacement, variable exists/FORALL output relevance,
  repeated-variable/scope filtering, compatible/incompatible joint triggers, canonical JSON
  proof input, compatible/same-binding exclusions in exists/FORALL, and populated/absent typed
  compatibility. Each uses the real `compare` path and asserts exact relations and every admitted
  claim field. Four invalid entries (FORALL context alias, wrong index type, wrong run type,
  untyped witness) and three exhausted entries (Python iteration, Soufflé rows, alternative
  provenance) require a blocking mismatch, the exact named failure pair, a persisted digest-equal
  strict replay, and `replay_reproduced=true`. The alternative-provenance case intentionally
  remains asymmetric: Python is `resource-exhausted`, Soufflé finds support, and the differential
  blocks. This is the intended fail-closed outcome, not false agreement.

The isolated forward artifact replay was rerun without touching the working tree:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; root=$PWD; git_path=$(command -v git); case "$git_path" in /nix/store/*) ;; *) echo "unpinned git=$git_path" >&2; exit 1;; esac; tmp=$(mktemp -d); trap '\''rm -rf "$tmp"'\'' EXIT; git archive 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 | tar -x -C "$tmp"; cd "$tmp"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; test -f packages/capabilities/tests/claim_semantics/test_kernel_closure.py; printf "integration_parent=%s\ngit=%s\nmanifest_order=kernel-closure,differential-closure\nforward_replay=ok\n" 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 "$git_path"'
```

Exit 0. It printed `integration_parent=7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`,
`manifest_order=kernel-closure,differential-closure`, `forward_replay=ok`, and pinned Git
`/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`.

The exact `kernel-closure-tests` dependency command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Its final execution exited 0. The ten discoveries ran 13, 21, 23, 1, 16, 11, 5, 23, 2, and 33
tests; all were `OK`, and neither focused Soufflé discovery skipped.

The exact `differential-closure-tests` dependency command and byte-identical reducer
`differential-tests` command were executed separately:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Both final executions exited 0. The dependency execution ran 29 differential tests in 40.691s
and 13 shrinker tests in 5.060s; the reducer execution ran 29 in 40.315s and 13 in 5.538s. Every
discovery was `OK`, and skip rejection did not fire.

The exact reducer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Its final execution exited 0. The six discoveries ran 1, 11, 13, 23, 2, and 33 tests; all were
`OK`, and neither focused Soufflé discovery skipped.

The exact reducer regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Exit 0: `Ran 692 tests in 50.560s`, `OK (skipped=67)`. Those broad-suite optional/platform skips
are not Soufflé evidence. Every focused gate resolved
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` and rejected skips.

The exact 14-fixture oracle command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; p=$(command -v souffle); printf "path=%s\n" "$p"; case "$p" in /nix/store/*) ;; *) exit 1;; esac; cd packages/capabilities; PYTHONPATH=src python - <<'\''PY'\''
import json
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims import canonical_json
from capcov.claims.differential import COMPARABLE_CLAIM_FIELDS, compare
root = Path("tests/claim_semantics/corpus")
expected_document = json.loads((root / "expected.json").read_text(encoding="utf-8"))
expected = expected_document["cases"]
paths = sorted(root.glob("[0-9][0-9]-*.json"))
assert len(paths) == 14, len(paths)
for path in paths:
    bundle = load_fixture(path)
    result = compare(bundle, shrink=False)
    assert result.matched
    names = tuple(decl.name for decl in bundle.relations)
    assert tuple(name for name, _ in result.python.relations) == names
    assert result.python.relations == result.souffle.relations
    assert len(result.python.claims) == len(bundle.claims) == len(result.souffle.claims)
    for declared, left, right in zip(bundle.claims, result.python.claims, result.souffle.claims):
        assert left.key == right.key and left.index == right.index
        for field in COMPARABLE_CLAIM_FIELDS:
            assert getattr(left, field) == getattr(right, field), (path, left.key, field)
        oracle = expected[path.stem]["claims"][declared.id]
        assert left.semantic == oracle["semantic_verdict"]
        assert left.operational == oracle["operational_status"]
        assert left.basis == expected_document["evaluation_basis_by_quantifier"][declared.quantifier.value]
        assert left.missing_premises == tuple(sorted(canonical_json(item) for item in oracle["missing_premises"]))
    print(path.stem, len(result.python.relations), result.python.canonical_digest)
PY'
```

Exit 0. It asserted exactly 14 fixtures against `corpus/expected.json`, every declared relation,
and every admitted claim field. Relation counts were 51 (52 for fixture 11); digests 01--14 were
`b8dff89a…`, `50b3d206…`, `dbe4b81c…`, `80909bf0…`, `01027fa9…`, `e5ab74db…`, `bad57767…`,
`00ecc41d…`, `fff1921e…`, `ce16e161…`, `7cc9b29d…`, `e9ea27eb…`, `6773e22a…`, and
`a0f542b5…`.

The final byte checks were `git diff --check` and
`git diff --exit-code HEAD -- packages/capabilities/tests/claim_semantics/corpus`; both exited 0.
`corpus/expected.json` remained SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`. No corpus byte, reviewed
expectation, or production CLI behavior changed.

Limits remain explicit. Soufflé independently computes relation closure only; mappings,
quantifier/status folding, diagnostics, and missing-premise rendering remain Python in
`souffle.py` and shared `output.py`, so agreement is not independent end-to-end semantic or
provenance evidence. Canonical Python proof selection is not a Soufflé provenance comparison.
The producer and either kernel remain evidence, not authority. Deferred ownership is unchanged:
CLI/Linux/performance/recommendation are `datalog-evaluation`; installed-wheel static-schema
inclusion and provenance extraction are `scip-datalog-differential`; ground checking,
producer-class authority, and generic causal projection are `datalog-certificates`. The active
DAG may block `datalog-evaluation` on external target-go prerequisites, so ownership is not execution
evidence. No Shen, SCIP, external execution, receipt, certificate, real-Go, Linux, performance,
recommendation, checkpoint, or production behavior is claimed here.

### 2026-09-15 recursion-exhaustion boundary repair and implementer re-verification

This continuation used the existing integrated working tree at HEAD
`dabd4308f479ecd71eaed23cbfd3e35626212f46`. It did not reapply either artifact to the working
tree, consume a worker commit, or read or mutate a worker worktree. The integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`. The artifacts remain, in manifest order,
`claims-20260914185300567-kernel-closure-1.patch` SHA-256
`c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`, then
`claims-20260914185300567-differential-closure-1.patch` SHA-256
`86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.
The isolated forward-replay command quoted in the preceding record was rerun from that exact
parent and exited 0, printing pinned Git
`/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`,
`manifest_order=kernel-closure,differential-closure`, and `forward_replay=ok`.

The remaining fail-closed boundary was repaired before these final implementer runs:

- validation's strongly-connected-component traversal is now iterative and enforces an explicit
  rule-dependency depth limit of 256. A deeper syntactically valid producer graph raises a
  validation resource error, not an interpreter stack exception;
- both complete kernel report wrappers convert `RecursionError`, including translation and report
  normalization, to top-level `resource-exhausted`; `compare` guards injected runners and passes
  guarded runners through every shrink replay/candidate invocation;
- a 300-relation acyclic chain requires the exact
  `("resource-exhausted", "resource-exhausted")` pair, blocking `DifferentialMismatch`, exact
  `_difference_shape`, a digest-identical strict replay, and `replay_reproduced=true`. A separately
  registered injected-runner recursion control proves the comparison boundary also fails closed;
- the generic same-binding cross-context compatibility path now checks each witness payload
  column's type against the corresponding target context column and requires typed term identity.
  The matrix has a negative all-runtime digest/symbol confusion with untyped matching literals and
  an explicitly typed positive control. Both invalid kernel reports are named `invalid-input`, and
  comparison persists a blocking replay.

The central matrix retains all prior cases and now registers 15 valid, five invalid, and five
exhausted names. Its first focused implementer run exposed that shrink-candidate validation could
propagate the new validation resource error; that run exited 1 and is not evidence. Candidate
validation was made fail-closed, and the exact focused rerun passed all three test methods in
1.801s. The later exact manifest gates below include that successful matrix.

The exact dependency `kernel-closure-tests` command for this implementer's final run was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. Its ten discoveries ran 13, 21, 23, 1, 16, 11, 5, 23, 2, and 33
tests in 0.077s, 0.005s, 1.342s, 0.042s, 0.273s, 0.009s, 0.001s, 0.003s, 0.077s, and
2.450s. Every discovery was `OK`; the two focused Soufflé discoveries reported `rc=0` and no
skip.

The exact dependency `differential-closure-tests` and byte-identical reducer
`differential-tests` command was executed separately for each named gate:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Implementer dependency result: exit 0; 30 differential tests ran in 35.829s and 13 shrinker
tests in 5.374s, both `OK`, with `rc=0` and no focused skip. Implementer reducer result: exit 0;
30 differential tests ran in 39.647s and 13 shrinker tests in 5.797s, both `OK`, with `rc=0` and
no focused skip.

The exact reducer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. Its six discoveries ran 1, 11, 13, 23, 2, and 33 tests in 0.046s,
0.009s, 0.071s, 2.501s, 0.080s, and 2.801s. Every discovery was `OK`; both focused Soufflé
discoveries reported `rc=0` and no skip.

The exact reducer `regression` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Implementer result: exit 0, `Ran 693 tests in 47.818s`, `OK (skipped=67)`. Its deprecation
warnings and expected CLI negative-fixture text do not alter the successful result. The 67 broad
optional/platform skips are not Soufflé evidence; all focused gates resolved
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` and rejected skipped tests.

The exact 14-fixture `expected.json` oracle command quoted in the preceding record was rerun
unchanged and exited 0. It asserted exactly 14 numbered fixtures, every declared relation, all
four admitted claim fields, and each claim's expected semantic verdict, operational status,
quantifier basis, and canonical missing premises. Relation counts remained 51 (52 for fixture 11),
and report digests 01--14 remained `b8dff89a…`, `50b3d206…`, `dbe4b81c…`, `80909bf0…`,
`01027fa9…`, `e5ab74db…`, `bad57767…`, `00ecc41d…`, `fff1921e…`, `ce16e161…`, `7cc9b29d…`,
`e9ea27eb…`, `6773e22a…`, and `a0f542b5…`. `git diff --check` and the exact corpus-byte command
`git diff --exit-code HEAD -- packages/capabilities/tests/claim_semantics/corpus` exited 0.
`corpus/expected.json` remains SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`.

These are explicitly the implementer's own command summaries, not authoritative driver gate
outputs. The authoritative outputs are the driver's `gate-result` journal events for whichever
attempt is accepted. No checkpoint hash is recorded or promised here; only the driver appends it
in the post-review `task-completed` event.

Limits and deferred ownership remain unchanged. Soufflé independently computes relation closure
only; `souffle.py` and shared `output.py` still implement mapping, quantifier/status folding,
diagnostics, and missing-premise rendering in Python, so this is not independent end-to-end
semantics or provenance. CLI, Linux execution, performance, and recommendation remain owned by
`datalog-evaluation`; installed-wheel static-schema inclusion and provenance extraction by
`scip-datalog-differential`; ground checking, producer-class authority, and generic causal
projection by `datalog-certificates`. Ownership is not execution evidence. No Shen, SCIP,
external execution, receipt, certificate, real-Go, Linux, recommendation, checkpoint, or
production behavior is claimed.

### 2026-09-15 malformed-input and compatibility-dimension repair (`kernel-closure-integrate`, attempt 2)

This continuation used the existing integrated tree at HEAD
`dabd4308f479ecd71eaed23cbfd3e35626212f46`; it did not reapply either artifact to the working
copy, consume a worker commit, or read or mutate a worker worktree. The integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`. In manifest order the only artifacts remain
`kernel-closure` SHA-256 `c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`, then
`differential-closure` SHA-256 `86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.
The exact isolated forward-replay command in the preceding record was rerun unchanged: exit 0,
with pinned Git `/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`, the stated
parent, `manifest_order=kernel-closure,differential-closure`, and `forward_replay=ok`. The required
ancestor check also exited 0.

The two rejected-attempt findings were repaired before the final implementer gates:

- `Bundle` now rejects non-IR members in every canonical collection at construction, including
  arbitrary relation, Evidence, and output objects. Raw JSON has a separate named
  `BundleIngestionError` carrying `operational_failure="invalid-input"`; raw malformed bytes do
  not pretend to have a canonical Bundle digest or replay. Validation retains defensive typed
  filtering for deliberately mutated frozen instances, including recursion, evidence dependency,
  and output-duplicate second passes. It does not broadly catch `AttributeError` as producer error.
- Three distinct canonical semantic-invalid bundles (bad relation declaration, Evidence record,
  and output field) cross both real kernel wrappers as the exact ordered
  `("invalid-input", "invalid-input")` pair. Each blocks `compare`, persists canonical bytes,
  reloads with an identical digest, and reports `replay_reproduced=true`. Noncanonical arbitrary
  Python objects stop at construction or named raw ingestion and therefore correctly have no
  fabricated differential replay.
- Schema v1 generic runtime compatibility is now deliberately restricted to one differing context
  dimension. Its two declared compatibility payload positions mean, in rule-body pair order, the
  left and right value for that sole dimension, with exact target and payload types. A swapped
  one-dimensional pair fails. Multi-dimensional generic compatibility is rejected because v1 has
  no explicit target-dimension-to-payload association: tenant-only, swapped, and duplicated
  two-symbol witnesses cannot authorize simultaneous tenant and run differences even when both
  dimensions reuse the literal values `a` and `b`. The separately explicit static `index` / runtime
  `run` path is unchanged. Supporting generic multi-dimensional witnesses requires a future schema
  form with explicit correspondence; column names are not inferred as authority.

`test_differential_adversarial_matrix.py` now registers exact sets of 15 valid, 12 invalid, and
five exhausted adversarial names. The invalid/exhausted matrix requires exact ordered failure
names, blocking `DifferentialMismatch`, exact operational difference shape, digest-identical
strict replay for every canonical Bundle, and `replay_reproduced=true`; valid cases still require
exact closure and every `COMPARABLE_CLAIM_FIELDS` member. `test_claim_ir.py` separately proves
constructor rejection, named raw ingestion, and total validation of deliberately mutated relation,
Evidence, and output collections.

The two exact dependency gate commands and all three exact reducer gate commands are the commands
quoted verbatim in the immediately preceding implementer record and in
`.pi/workflows/capcov-experiment.json`; each was rerun byte-identically after the final code and
test change. Fresh implementer-labelled results:

- dependency `kernel-closure-tests`: exit 0. Its ten discoveries ran 13, 21, 23, 1, 16, 11, 8,
  23, 2, and 33 tests in 0.074s, 0.004s, 1.251s, 0.045s, 0.288s, 0.010s, 0.001s, 0.003s,
  0.077s, and 2.870s. All were `OK`; both focused Soufflé commands returned `rc=0` without a
  skip.
- dependency `differential-closure-tests`: exit 0. Differential discovery ran 30 tests in
  37.221s and shrinker discovery ran 13 tests in 5.883s, both `OK`; skip rejection did not fire.
- reducer `differential-tests`: exit 0. Differential discovery ran 30 tests in 34.317s and
  shrinker discovery ran 13 tests in 5.040s, both `OK`; skip rejection did not fire.
- reducer `kernel-tests`: exit 0. Its six discoveries ran 1, 11, 13, 23, 2, and 33 tests in
  0.047s, 0.010s, 0.073s, 1.376s, 0.074s, and 3.113s. All were `OK`; both focused Soufflé
  commands returned `rc=0` without a skip.
- reducer `regression`: the exact command
  `nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'`
  exited 0: `Ran 696 tests in 48.711s`, `OK (skipped=67)`. These broad optional/platform skips
  are not Soufflé evidence.

Every focused gate resolved the real pinned executable at
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`; no banner version was
invented. The exact 14-fixture `expected.json` oracle command quoted above was rerun unchanged and
exited 0. It checked every declared relation, all four admitted claim fields, and each claim's
reviewed semantic verdict, operational status, quantifier basis, and canonical missing premises.
Relations remained 51 per fixture (52 for fixture 11), and report digests 01--14 remained
`b8dff89a…`, `50b3d206…`, `dbe4b81c…`, `80909bf0…`, `01027fa9…`, `e5ab74db…`, `bad57767…`,
`00ecc41d…`, `fff1921e…`, `ce16e161…`, `7cc9b29d…`, `e9ea27eb…`, `6773e22a…`, and
`a0f542b5…`.

`git diff --check` and
`git diff --exit-code HEAD -- packages/capabilities/tests/claim_semantics/corpus` both exited 0.
No corpus byte or reviewed expectation changed; `corpus/expected.json` remains SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`.
These are implementer observations, not authoritative acceptance evidence: only the driver's
accepted-attempt `gate-result` events are authoritative, and only the driver may append a
checkpoint hash in `task-completed`. No checkpoint hash is recorded or promised here.

Limits and ownership remain explicit. Soufflé independently computes relational closure only;
`claims/souffle.py` and shared `output.py` still perform mapping, quantifier/status folding,
diagnostics, and missing-premise rendering in Python, so full reports are not independent
end-to-end semantic or provenance evidence. CLI, Linux execution, performance, and recommendation
remain `datalog-evaluation`; installed-wheel static-schema inclusion and provenance extraction
remain `scip-datalog-differential`; ground checking, producer authority, and generic causal
projection remain `datalog-certificates`. Producer/kernel agreement is evidence, not authority,
and ownership is not execution evidence. No Shen, SCIP, external execution, receipt, certificate,
real-Go, Linux, recommendation, production behavior, or checkpoint is claimed.

### 2026-09-15 recursive malformed-IR repair (`kernel-closure-integrate`, attempt 3)

This continuation used the existing integrated tree at HEAD
`dabd4308f479ecd71eaed23cbfd3e35626212f46`. It did not reapply either artifact to the working
copy, consume a worker commit, or read or mutate a worker worktree. The integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`; the only artifacts remain, in manifest order,
`kernel-closure` SHA-256 `c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`, then
`differential-closure` SHA-256 `86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.
The isolated forward replay command quoted under "post-review semantic closure and isolated
artifact replay" was rerun unchanged from that exact parent. Implementer result: exit 0; pinned Git
was `/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`, and it printed the stated
parent, `manifest_order=kernel-closure,differential-closure`, and `forward_replay=ok`.

The request-changes finding was reproduced with the exact public construction
`Evidence("e", object(), source="producer")` inside a top-level typed `Bundle`. Validation now
runs an explicit recursive structural-shape pass before any semantic pass dereferences nested
members. Malformed `Evidence.atom`, `Atom.terms`, `Rule.head`, `Rule.body`, comparison terms,
aggregation shape, claim/context fields, mapping projections, `DiagnosticRule.predicate`, and
output fields/triggers become validation issues. The semantic passes also guard ground-key,
context, rule, recursion, and output-causality second passes. No `AttributeError` catch was added:
unexpected programming faults remain visible. Directly constructed nested controls cross
`run_python` and `run_souffle` as the exact named pair `("invalid-input", "invalid-input")`;
separate deliberately mutated frozen-object controls prove validation remains total, with no raw
implementation exception.

Arbitrary nested Python objects are not canonical replay input: they cannot be serialized and
strictly reloaded as schema-v1 IR, so this record does not invent a bundle digest or replay for
them. `compare` now blocks that case with named `ReplayPersistenceError` before creating any
file; the digest calculation is inside the persistence boundary rather than leaking `TypeError`.
The canonical malformed relation/Evidence/output matrix remains separate: all twelve
canonical invalid cases still block through `compare` with digest-identical strict replay. Raw
malformed JSON remains pre-differential `BundleIngestionError("invalid-input")` evidence.

The exact dependency `kernel-closure-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. Its ten discoveries ran 13, 21, 23, 1, 16, 11, 10, 23, 2, and 33
tests in 0.086s, 0.005s, 0.964s, 0.056s, 0.313s, 0.010s, 0.002s, 0.003s, 0.225s, and
3.016s. Every discovery was `OK`; both focused Soufflé discoveries returned `rc=0` with no skip.

The exact dependency `differential-closure-tests` and byte-identical reducer
`differential-tests` command was executed separately for each named gate:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Implementer dependency result: exit 0; 32 differential tests ran in 37.448s and 13 shrinker
tests in 5.748s, both `OK`, with no focused skip. Implementer reducer result: exit 0; 32
differential tests ran in 37.543s and 13 shrinker tests in 5.406s, both `OK`, with no focused
skip.

The exact reducer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. Its six discoveries ran 1, 11, 13, 23, 2, and 33 tests in 0.058s,
0.010s, 0.084s, 0.893s, 0.076s, and 3.270s. Every discovery was `OK`; both focused Soufflé
commands returned `rc=0` without a skip.

The exact reducer regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Implementer result: exit 0, `Ran 700 tests in 52.643s`, `OK (skipped=67)`. Its deprecation
warnings and expected CLI negative-fixture text do not alter the result. The broad optional/tool
platform skips are not Soufflé evidence. Every focused gate resolved
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` and rejected skipped tests.
Its own banner again left `Version:` blank; the immutable package store path identifies 2.5.

The exact 14-fixture `expected.json` oracle command quoted under "post-review semantic closure and
isolated artifact replay" was rerun unchanged and exited 0. It asserted exactly 14 numbered
fixtures, every declared relation, every admitted claim field, and each claim's reviewed semantic
verdict, operational status, quantifier basis, and canonical missing premises. Relation counts
remained 51 (52 for fixture 11), and report digests 01--14 remained `b8dff89a…`, `50b3d206…`,
`dbe4b81c…`, `80909bf0…`, `01027fa9…`, `e5ab74db…`, `bad57767…`, `00ecc41d…`, `fff1921e…`,
`ce16e161…`, `7cc9b29d…`, `e9ea27eb…`, `6773e22a…`, and `a0f542b5…`.

`git diff --check` and
`git diff --exit-code HEAD -- packages/capabilities/tests/claim_semantics/corpus` both exited 0.
No corpus byte or reviewed expectation changed; `corpus/expected.json` remains SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`.
These are implementer observations, not authoritative acceptance evidence: only the driver's
accepted-attempt `gate-result` events are authoritative, and only the driver may append a
checkpoint hash in `task-completed`. No checkpoint hash is recorded or promised here.

Limits and owners remain unchanged. Soufflé independently computes relational closure only;
`claims/souffle.py` and shared `output.py` still perform mappings, quantifier/status folding,
diagnostics, and missing-premise rendering in Python, so report agreement is not independent
end-to-end semantics or provenance. CLI, Linux execution, performance, and recommendation remain
owned by `datalog-evaluation`; installed-wheel static-schema inclusion and provenance extraction
by `scip-datalog-differential`; ground checking, producer-class authority, and generic causal
projection by `datalog-certificates`. No Shen, SCIP, external execution, receipt, certificate,
real-Go, Linux, recommendation, production behavior, or checkpoint is claimed.

### 2026-09-15 boundary-totality finalizer (`kernel-closure-finalize`, attempt 1)

This sole-root finalizer began from the clean branch at HEAD
`9c603a088e05dd9a75c49dfef0f2fc5f494aa72b`. The integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`. The only listed artifacts were verified at their
full SHA-256 values and retained in manifest order:

1. `claims-20260914185300567-kernel-closure-1.patch`:
   `c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`;
2. `claims-20260914185300567-differential-closure-1.patch`:
   `86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.

The branch already contained both artifacts plus later reducer repairs, so they were not applied
again to the working tree. No worker commit was used and no worker worktree was read or mutated.
Instead, the artifacts were checked and applied in manifest order to an isolated archive of the
recorded parent with this exact command:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; root=$PWD; git_path=$(command -v git); case "$git_path" in /nix/store/*) ;; *) echo "unpinned git=$git_path" >&2; exit 1;; esac; tmp=$(mktemp -d); trap '\''rm -rf "$tmp"'\'' EXIT; git archive 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 | tar -x -C "$tmp"; cd "$tmp"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; test -f packages/capabilities/tests/claim_semantics/test_kernel_closure.py; printf "integration_parent=%s\ngit=%s\nmanifest_order=kernel-closure,differential-closure\nforward_replay=ok\n" 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 "$git_path"'
```

Implementer result: exit 0. It printed pinned Git
`/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`, the stated parent,
`manifest_order=kernel-closure,differential-closure`, and `forward_replay=ok`.

The four inherited request-changes findings were reproduced and closed before final gates:

- `DiagnosticRule.when_missing` and `required` now require real Boolean values, and `message`
  requires a string, during construction/ingestion even with `validate=False`. Defensive
  validation reports deliberately mutated frozen instances.
- `bundle_from_json` converts ingestion/construction `RecursionError` to
  `BundleIngestionError` with `operational_failure="invalid-input"`; deep JSON text and an
  already-decoded nested Mapping retain `RecursionError` as `__cause__`. Kernel recursion remains
  the existing `resource-exhausted` contract.
- Recursive IR shape is checked before Bundle canonical sorting. Evidence-atom, Atom-term,
  Rule-head, Rule-body, and diagnostic-predicate arbitrary objects cannot become Bundles.
  Mutation-only controls retain validation totality. Canonical semantic-invalid Bundles still
  traverse `compare()`, preserve exact ordered failure pairs, block even when names are identical,
  and strictly replay.
- `_joint_environments` recurses unconstrained only when there is no applicable mapping. If
  mappings exist and all fail, there is no environment. Diagnostic- and proof-relevance tests
  each contain an `a/b` failure and `a/a` positive control and assert the exact fallback/rendered
  output rather than relying only on shared-kernel agreement.

`test_differential_kernels.py` now asserts exactly 14 fixture paths before iteration, full
payload equality for every declared relation, all four `COMPARABLE_CLAIM_FIELDS`, and each
claim's reviewed verdict/status/basis/missing-premise oracle. The central registry now contains
19 valid Bundle cases, 12 canonical invalid cases, five exhausted cases, and one explicit
constructor-rejection test for the five noncanonical nested graphs. Every actual Bundle remains
on a valid or blocking `compare()` path.

The exact dependency `kernel-closure-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The ten discoveries ran 13, 21, 25, 1, 16, 11, 13, 23, 2, and
33 tests in 2.394s, 0.029s, 35.135s, 0.285s, 1.436s, 0.050s, 0.022s, 0.014s, 2.982s, and
99.373s. All were `OK`; both focused Soufflé commands returned `rc=0` without a skip.

The exact dependency `differential-closure-tests` command and byte-identical finalizer
`differential-tests` command were run separately:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Implementer dependency result: exit 0; 31 differential tests ran in 625.079s and 13 shrinker
tests in 30.685s, all `OK`, with `rc=0` and no focused skip. Implementer finalizer result: exit
0; 31 differential tests ran in 290.862s and 13 shrinker tests in 15.339s, all `OK`, with
`rc=0` and no focused skip. The slower dependency run reflected machine contention, not a
reclassified timeout.

The exact finalizer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH=src python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH=src python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The six discoveries ran 1, 11, 13, 25, 2, and 33 tests in
0.193s, 0.031s, 0.259s, 2.712s, 0.281s, and 7.235s. All were `OK`; both focused Soufflé
commands returned `rc=0` without a skip.

The exact finalizer regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
```

Implementer result: exit 0, `Ran 704 tests in 337.566s`, `OK (skipped=67)`. Deprecation
warnings and expected negative-fixture CLI text do not alter the result. The 67 broad-suite
optional/tool/platform skips are not Soufflé evidence; every focused gate resolved the real
pinned executable and explicitly rejected skips.

The exact 14-fixture oracle command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; p=$(command -v souffle); printf "path=%s\n" "$p"; case "$p" in /nix/store/*) ;; *) exit 1;; esac; souffle --version 2>&1; python --version; cd packages/capabilities; PYTHONPATH=src python - <<'\''PY'\''
import json
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims import canonical_json
from capcov.claims.differential import COMPARABLE_CLAIM_FIELDS, compare
root = Path("tests/claim_semantics/corpus")
expected_document = json.loads((root / "expected.json").read_text(encoding="utf-8"))
expected = expected_document["cases"]
paths = sorted(root.glob("[0-9][0-9]-*.json"))
assert len(paths) == 14, len(paths)
for path in paths:
    bundle = load_fixture(path)
    result = compare(bundle, shrink=False)
    assert result.matched
    names = tuple(decl.name for decl in bundle.relations)
    assert tuple(name for name, _ in result.python.relations) == names
    assert result.python.relations == result.souffle.relations
    assert len(result.python.claims) == len(bundle.claims) == len(result.souffle.claims)
    for declared, left, right in zip(bundle.claims, result.python.claims, result.souffle.claims):
        assert left.key == right.key and left.index == right.index
        for field in COMPARABLE_CLAIM_FIELDS:
            assert getattr(left, field) == getattr(right, field), (path, left.key, field)
        oracle = expected[path.stem]["claims"][declared.id]
        assert left.semantic == oracle["semantic_verdict"]
        assert left.operational == oracle["operational_status"]
        assert left.basis == expected_document["evaluation_basis_by_quantifier"][declared.quantifier.value]
        assert left.missing_premises == tuple(sorted(canonical_json(item) for item in oracle["missing_premises"]))
    claims = ";".join(f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}/missing:{len(claim.missing_premises)}" for claim in result.python.claims)
    print(path.stem, len(result.python.relations), result.python.canonical_digest, claims)
PY'
```

Implementer result: exit 0. Python was 3.12.14. Soufflé resolved to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`; its banner again left
`Version:` blank and reported 32-bit word size with `ffi ncurses sqlite zlib`, so no banner value
is invented. All 14 fixtures matched every declared relation and all four admitted claim fields
against `expected.json`. Fresh implementer per-fixture output was:

| fixture | relations | canonical report digest | claim results |
|---|---:|---|---|
| 01-correlated-positive | 51 | `b8dff89a3a46448425fc2964ee0f687d7256797576b0e9e3338aef51b096472e` | terminal supported/complete/derivational/missing:0 |
| 02-surface-mismatch | 51 | `50b3d20617546a30c9d43fb8022ad9fccdbd9424ea76cef7937b107b195a07d4` | effect unresolved/complete/derivational/missing:1 |
| 03-post-without-creation | 51 | `dbe4b81c5c09637ca7cecda2464e67b9b2fce428b5b0cea806146fbd0d56ff5f` | created unresolved/complete/derivational/missing:1; request supported/complete/derivational/missing:0 |
| 04-authorization-polarity | 51 | `80909bf03217a43a5fde19c83d19a136bff799df1e49126e0ab983a06a8214c2` | allow supported/complete/derivational/missing:0; deny supported/complete/derivational/missing:0 |
| 05-wrong-event-email | 51 | `01027fa9dfb1d53b46e743088d7526909b08a308cb9b75dc7f4170371e86eedb` | target-mail unresolved/complete/derivational/missing:1 |
| 06-context-contamination | 51 | `e5ab74db0791c24170b551c15250bd371662518bd924d1e86be8ba8128ada7f9` | terminal unresolved/complete/derivational/missing:1 |
| 07-shared-mistaken-assumption | 51 | `bad57767c10e8b173ececbc63bb587a62bbc6cc8470786041eb6b555324987a0` | delivered unresolved/complete/derivational/missing:1 |
| 08-rejection-versus-missing | 51 | `00ecc41d396887ae9062a3a1be41d1520467d72d7a5845347f40a2954518c387` | explicit-denial refuted/complete/derivational/missing:0; missing-denial unresolved/complete/derivational/missing:1 |
| 09-support-and-refutation | 51 | `fff1921eb4d63a325e7b9fd630e8a2e5a57360ed2909b671b72469f88a76bdd2` | terminal conflicting/complete/derivational/missing:0 |
| 10-revoked-assumption-alternative | 51 | `ce16e1617483fa669a05b8b18ce4f9f0ddd84eed972f4f205b58866069f3cc6d` | saved supported/complete/derivational/missing:0 |
| 11-compatible-history-sets | 52 | `7cc9b29dd5fb2efaecc92f4fab1072bbeddf92b0fcd4b5b1506926fbe41aa378` | universal unresolved/inconsistent-premises/bounded-history-model/missing:1; mixed unresolved/complete/bounded-history-model/missing:1 |
| 12-unexpected-runtime-surface | 51 | `e9ea27ebf410d2103d876cdd61b7f67fef03c3b000c89a2332e1d253b18d81d0` | model-complete unresolved/out-of-scope/derivational/missing:1 |
| 13-acceptance-sql-ack-failure | 51 | `6773e22a599444967bff3ef84c095026e68d369731bbb5c272e75c58fda66a2e` | terminal unresolved/complete/derivational/missing:1; provider supported/complete/derivational/missing:0 |
| 14-bounded-no-resend | 51 | `a0f542b53bcb8e66ca1001ac233c5cd10aeafbcda085145f1a809d437d0f6f91` | bounded supported/complete/derivational/missing:0; forever unresolved/complete/derivational/missing:1 |

No verdict, status, basis, missing premise, or leaf oracle changed.

A focused five-module pre-gate command also exited 0 with 89 tests in 758.213s and no skips.
Final `git diff --check` and
`git diff --exit-code HEAD -- packages/capabilities/tests/claim_semantics/corpus` exited 0, so no
corpus byte or reviewed support/refutation leaf set changed. The 13-test provenance discovery
passed. `corpus/expected.json` remains SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`; the static schema source
remains `80ce00e848304953b54ab80aaa023ad0a58240f8dc3d3fc803f41973b7bbcac9`.

These are the implementer's own observations, not authoritative admission evidence. Only the
driver's `gate-result` events for the accepted attempt are authoritative, and only the driver may
append a checkpoint hash in `task-completed`; no checkpoint is recorded or promised here.

Limits and owners remain explicit. Soufflé independently computes relational closure only;
`claims/souffle.py` and shared `output.py` still perform mapping, quantifier/status folding,
diagnostics, and missing-premise rendering in Python, so report agreement is not independent
end-to-end semantics or provenance. CLI, Linux execution, performance, and recommendation remain
owned by `datalog-evaluation`; installed-wheel static-schema inclusion and provenance extraction
by `scip-datalog-differential`; ground checking, producer-class authority, and generic causal
projection by `datalog-certificates`. Producer/kernel output is evidence, not authority, and
ownership is not execution evidence. No Shen, SCIP, external execution, receipt, certificate,
real-Go, Linux, performance recommendation, production CLI behavior, or checkpoint is claimed.

### 2026-09-15 restarted finalizer qualification after post-WIP integration

This implementer continuation began from the clean committed branch at HEAD
`8adc19709d49e95737ecaa4dbda15fd84ab609df`. That HEAD includes the later indexed/memoized
evaluator, semi-naive fixpoint, Soufflé translation cache, upstream `bdb67b8`, and the gate-command
repair that makes `PYTHONPATH` absolute. The only new semantic-closure edit routes eleven
previously boundary-only, canonical invalid Bundles through blocking `compare()`: the nine
mixed-binding mutants, the indexless static declaration, and the mapping-to-decoy claim. Their
shared helper asserts the ordered `("invalid-input", "invalid-input")` pair, blocking mismatch,
real replay file, byte-identical canonical replay contents, digest identity after strict reload,
and `replay_reproduced`. The established central counts remain exactly 19 valid, 12 invalid, and
five exhausted cases; the five structurally noncanonical graphs remain constructor rejections.

The integration parent and artifacts are unchanged. Live SHA-256 checks again produced, in
manifest order:

1. `claims-20260914185300567-kernel-closure-1.patch`:
   `c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`;
2. `claims-20260914185300567-differential-closure-1.patch`:
   `86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.

They were not reapplied to the current branch. This exact Nix command instead replayed each full
artifact, in that order, inside a disposable archive of the recorded integration parent; it used
no worker commit and did not read or mutate a worker worktree:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; root=$PWD; git_path=$(command -v git); case "$git_path" in /nix/store/*) ;; *) echo "unpinned git=$git_path" >&2; exit 1;; esac; tmp=$(mktemp -d); trap '\''rm -rf "$tmp"'\'' EXIT; git archive 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 | tar -x -C "$tmp"; cd "$tmp"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; test -f packages/capabilities/tests/claim_semantics/test_kernel_closure.py; printf "integration_parent=%s\ngit=%s\nmanifest_order=kernel-closure,differential-closure\nforward_replay=ok\n" 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 "$git_path"'
```

Implementer result: exit 0 in 6.718s. It printed pinned Git
`/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`,
`integration_parent=7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`, the manifest order, and
`forward_replay=ok`.

The exact dependency `kernel-closure-tests` command from the live manifest was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The ten discoveries ran 13, 21, 25, 1, 16, 11, 13, 23, 2,
and 33 tests in 0.415s, 0.048s, 2.094s, 0.075s, 0.352s, 0.010s, 0.005s, 0.004s,
0.202s, and 5.060s; all were `OK`. The tool-reported wall time was 27.387s. Both focused
Soufflé discoveries returned `rc=0` and the gate's skip guards did not fire.

The exact dependency `differential-closure-tests` command and the byte-identical finalizer
`differential-tests` command were run separately:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Implementer dependency result: exit 0; 31 differential tests ran in 57.735s and 13 shrinker
tests in 7.914s, all `OK`, with `rc=0` and no focused skip. Implementer finalizer result: exit
0; the same 31 and 13 tests ran in 134.483s and 14.713s, all `OK`, with `rc=0` and no
focused skip. Nix reported temporary contention with another input-fetch process during the
second run; the pinned shell opened and the real test result, rather than the wait, is recorded.

The exact finalizer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The six discoveries ran 1, 11, 13, 25, 2, and 33 tests in
4.769s, 0.025s, 0.263s, 41.757s, 0.665s, and 8.300s. All were `OK`; the guarded focused
Soufflé commands returned `rc=0` without a skip.

The exact finalizer regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -t .'
```

Implementer result: exit 0, `Ran 884 tests in 133.353s`, `OK (skipped=125)`. This includes
the post-finalizer evaluator-index and Soufflé-cache modules, and the two moving-`origin/main`
compatibility tests that failed the prior attempt now pass. The 125 broad-suite skips are
optional tool/platform cases and are not used as Soufflé evidence; the focused gates above
resolved the real pinned executable and rejected skips.

The two post-WIP performance modules were also selected explicitly with this command:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; cd packages/capabilities; PYTHONPATH="$PWD/src" python -m unittest tests.claim_semantics.test_evaluator_index; out=$(PYTHONPATH="$PWD/src" python -m unittest tests.claim_semantics.test_souffle_cache 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0; three evaluator-index tests ran in 0.027s and four Soufflé-cache
tests in 0.156s, all `OK`; the cache discovery returned `rc=0` without a skip.

The corrected supplemental 14-fixture oracle used the same Python payload printed in the
immediately preceding finalizer record, with every `PYTHONPATH=src` changed to
`PYTHONPATH="$PWD/src"`. It resolved Soufflé to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`, observed Python
3.12.14, and exited 0 in 6.574s. Its 14 output rows reproduced exactly the 14 relation counts,
full report digests, and claim results in the preceding table. The script asserted the exact
14-file count, every declared relation on both sides, claim key/index, every
`COMPARABLE_CLAIM_FIELDS` field, and the independent `expected.json` verdict/status/basis/
missing-premise oracle. A first supplemental wrapper attempt exited 2 before Python executed
because the outer orchestration shell expanded `$()` and `$PWD`; it is not presented as a test
result or hidden as a semantic failure.

`corpus/expected.json` remains SHA-256
`9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`; the fresh corpus
differential and provenance discoveries are green. No reviewed corpus byte, verdict/status/basis/
missing-premise oracle, or leaf oracle changed.

These are implementer observations only. The driver's `gate-result` events for this attempt, if
admitted, remain the authoritative gate evidence, and only the driver may append a checkpoint hash
in `task-completed`; neither is recorded or promised here. The semantic limits and deferred owners
remain unchanged: Soufflé independently computes relational closure, while claim folding,
diagnostics, mappings, and output rendering remain Python-mediated. CLI, Linux execution,
performance evaluation, and recommendation are owned by `datalog-evaluation`; installed-wheel
static-schema inclusion and provenance extraction are owned by `scip-datalog-differential`;
ground checking, producer authority, and generic causal projection are owned by
`datalog-certificates`. Producer/kernel output remains evidence, not authority. No Shen, external
execution, receipt, certificate, real-Go, Linux, production CLI behavior, or checkpoint is claimed.

### 2026-09-15 ingestion-boundary repair (`kernel-closure-finalize`, attempt 2)

This implementer continuation began at HEAD
`8adc19709d49e95737ecaa4dbda15fd84ab609df`. It preserved the pre-existing dirty plan record and
the eleven-adversary `test_differential_kernels.py` change described immediately above. The two
dependency artifacts were not reapplied to the evolved working tree. Their SHA-256 values were
rechecked in manifest order as
`c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf` for
`claims-20260914185300567-kernel-closure-1.patch`, then
`86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8` for
`claims-20260914185300567-differential-closure-1.patch`. The integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`, which is an ancestor of this HEAD. A targeted
archive containing every pre-existing path touched by the patches replayed both complete
artifacts in that order; `test_kernel_closure.py` was created by the first patch. The command
used pinned Git and neither read nor mutated a worker worktree:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; root=$PWD; git_path=$(command -v git); case "$git_path" in /nix/store/*) ;; *) echo "unpinned git=$git_path" >&2; exit 1;; esac; tmp=$(mktemp -d); trap '\''rm -rf "$tmp"'\'' EXIT; git archive 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 packages/capabilities/src/capcov/claims/evaluator.py packages/capabilities/src/capcov/claims/output.py packages/capabilities/src/capcov/claims/validation.py packages/capabilities/tests/claim_semantics/test_provenance_leaves.py packages/capabilities/src/capcov/claims/shrinker.py packages/capabilities/tests/claim_semantics/test_shrinker_bundle.py | tar -x -C "$tmp"; cd "$tmp"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-kernel-closure-1.patch"; git apply --check "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; git apply "$root/.capcov/pi-workflow/patches/claims-20260914185300567-differential-closure-1.patch"; test -f packages/capabilities/tests/claim_semantics/test_kernel_closure.py; printf "integration_parent=%s\ngit=%s\nmanifest_order=kernel-closure,differential-closure\nforward_replay=ok\n" 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9 "$git_path"'
```

Implementer result: exit 0. It printed pinned Git
`/nix/store/yqw09igi72yxpgy3d1b25vbh5l8rx227-git-2.55.0/bin/git`, the stated parent,
`manifest_order=kernel-closure,differential-closure`, and `forward_replay=ok`.

The rejected attempt's public-ingestion failure was reproduced and repaired before the gates.
`Context.from_mapping` now explicitly requires a Mapping. Schema-v1 ingestion distinguishes an
absent object/array field from a present `null`, `false`, `0`, empty string, or wrong container.
Wire objects and their exact canonical pair-list forms remain accepted for context, metadata,
diagnostic predicates, and output fields. Every top-level and nested array is checked before tuple
conversion, so values such as `relations=""`, `claims={}`, `columns=""`, and
`producer_classes="ab"` can no longer become empty or character-wise collections. No broad
`AttributeError` catch was added: producer-controlled shape errors raise `TypeError`/`ValueError`
at their parser boundary and become exact `BundleIngestionError` values with
`operational_failure="invalid-input"`; unrelated implementation defects remain visible.
`validate=False` retains these structural checks for strict replay reloads. Canonical but
semantic-invalid Bundles still traverse the blocking differential and persist canonical replay.

`test_claim_ir.py` covers malformed metadata, diagnostic policy, claim/evidence context,
diagnostic predicate, and output fields as both decoded mappings and JSON text under both
validation modes. It also covers wrong top-level/nested array containers and positive absent,
empty wire-object, canonical-context, canonical-metadata, and canonical round-trip controls. A
120-probe Nix-shell diagnostic over the six object-shaped boundaries exited 0: every invalid
shape produced the exact named ingestion failure and the three intentionally valid empty
canonical pair lists remained valid. The first focused unit run exited 1 because the newly added
positive control omitted the already-required non-empty evidence source; the test fixture was
corrected rather than weakening validation. The rerun over `test_claim_ir`,
`test_evidence_policy`, `test_kernel_closure`, and `test_shrinker_bundle` exited 0 with 70 tests
in 21.292s.

The exact dependency `kernel-closure-tests` command from the live manifest was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The ten discoveries ran 13, 21, 25, 1, 16, 11, 16, 23, 2,
and 33 tests in 0.539s, 0.084s, 13.928s, 0.246s, 1.363s, 0.034s, 0.030s, 0.015s,
1.486s, and 45.994s. All 161 tests were `OK`; both focused Soufflé discoveries returned
`rc=0`, and the skip guards did not fire.

The exact dependency `differential-closure-tests` and byte-identical finalizer
`differential-tests` command were executed separately:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Implementer dependency result: exit 0; 31 differential tests ran in 116.313s and 13 shrinker
tests in 21.564s, all `OK`, with `rc=0` and no focused skip. Implementer finalizer result: exit
0; the same 31 and 13 tests ran in 92.803s and 19.152s, all `OK`, with `rc=0` and no focused
skip.

The exact finalizer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The six discoveries ran 1, 11, 13, 25, 2, and 33 tests in
0.368s, 0.040s, 0.364s, 2.791s, 0.764s, and 6.145s. All 85 tests were `OK`; both focused
Soufflé commands returned `rc=0` without a skip.

The exact finalizer regression command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -t .'
```

Implementer result: exit 0, `Ran 887 tests in 200.979s`, `OK (skipped=125)`. The 125 broad
optional-tool/platform skips are not Soufflé evidence; every focused gate above resolved the
real pinned executable and rejected skips.

The exact supplemental 14-fixture oracle command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'set -eu; p=$(command -v souffle); printf "path=%s\n" "$p"; case "$p" in /nix/store/*) ;; *) exit 1;; esac; souffle --version 2>&1; python --version; cd packages/capabilities; PYTHONPATH="$PWD/src" python - <<'\''PY'\''
import json
from pathlib import Path
from tests.claim_semantics.adapter import load_fixture
from capcov.claims import canonical_json
from capcov.claims.differential import COMPARABLE_CLAIM_FIELDS, compare
root = Path("tests/claim_semantics/corpus")
expected_document = json.loads((root / "expected.json").read_text(encoding="utf-8"))
expected = expected_document["cases"]
paths = sorted(root.glob("[0-9][0-9]-*.json"))
assert len(paths) == 14, len(paths)
for path in paths:
    bundle = load_fixture(path)
    result = compare(bundle, shrink=False)
    assert result.matched
    names = tuple(decl.name for decl in bundle.relations)
    assert tuple(name for name, _ in result.python.relations) == names
    assert result.python.relations == result.souffle.relations
    assert len(result.python.claims) == len(bundle.claims) == len(result.souffle.claims)
    for declared, left, right in zip(bundle.claims, result.python.claims, result.souffle.claims):
        assert left.key == right.key and left.index == right.index
        for field in COMPARABLE_CLAIM_FIELDS:
            assert getattr(left, field) == getattr(right, field), (path, left.key, field)
        oracle = expected[path.stem]["claims"][declared.id]
        assert left.semantic == oracle["semantic_verdict"]
        assert left.operational == oracle["operational_status"]
        assert left.basis == expected_document["evaluation_basis_by_quantifier"][declared.quantifier.value]
        assert left.missing_premises == tuple(sorted(canonical_json(item) for item in oracle["missing_premises"]))
    claims = ";".join(f"{claim.key}={claim.semantic}/{claim.operational}/{claim.basis}/missing:{len(claim.missing_premises)}" for claim in result.python.claims)
    print(path.stem, len(result.python.relations), result.python.canonical_digest, claims)
PY'
```

It exited 0 in 21.680s. It resolved Soufflé to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` and Python 3.12.14.
All fourteen output rows were byte-for-byte the relation counts, canonical report digests, and
claim results recorded in the preceding table. The executable's banner again left `Version:`
blank; the immutable Nix store path identifies the packaged version without inventing a banner
value. The command asserted exactly 14 fixtures, every declared relation and payload, claim
key/index, all four `COMPARABLE_CLAIM_FIELDS`, and the independent reviewed `expected.json`
verdict/status/basis/missing-premise oracle.

Final `git diff --check` passed and the corpus is unchanged. These are implementer observations,
not authoritative admission evidence. The driver must supply fresh `gate-result` events if this
attempt is admitted, and only the driver may append a checkpoint hash in `task-completed`; neither
is recorded or promised here. Limits and deferred ownership remain exactly as in the section-27
table: Soufflé independently establishes relational closure, while claim folding, diagnostics,
mappings, and missing-premise rendering remain Python-mediated. CLI and Linux execution belong to
`datalog-evaluation`; installed-wheel static-schema inclusion belongs to
`scip-datalog-differential`; ground checking, producer authority, and generic causal projection
belong to `datalog-certificates`. Producer/kernel output remains evidence, not authority. No Shen,
SCIP, external execution, receipt, certificate, real-Go, Linux, performance recommendation,
production CLI behavior, or checkpoint is claimed.

### 2026-09-15 trust-boundary finalizer (`kernel-closure-finalize`, attempt 3)

This sole-root reducer continued from the rejected attempt-2 dirty tree at HEAD
`8adc19709d49e95737ecaa4dbda15fd84ab609df`. It did not commit, reset, stash, checkout, merge,
consume a worker commit, or read or mutate a worker worktree. The integration parent remains
`7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`; `git merge-base --is-ancestor
d1550e4d49401a0e8fa8cdd813fb2fd7bbd00765 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9`
exited 0. The two dependency artifacts were already integrated in manifest order, so they were
not applied a second time to the evolved tree. Fresh `shasum -a 256` output, in that order, was:

1. `claims-20260914185300567-kernel-closure-1.patch`:
   `c823f18e1f5375d128f17d3554c63d81daaa03339741cf42a8339941b7bcaebf`;
2. `claims-20260914185300567-differential-closure-1.patch`:
   `86b8fbb458b9a17d2cb683ff174d9df2215804fa273b0f5feeb0b8e626b75ab8`.

The patch headers name old blobs `d3f7364`, `7f00861`, `8bde9e1`, `ae222f6`, `fb0cd9c`, and
`69ecaaf`; fresh `git rev-parse 7b5e8ab52f291b964f6c41c0b566b5e57d9b04a9:<path>` calls
returned those exact full blob prefixes for all six pre-existing paths, and the first artifact's
new `test_kernel_closure.py` path was absent at that parent. Because the artifacts touch disjoint
paths, this verifies their clean forward base and manifest ordering without reapplying them or
creating a worker-derived tree. Current-tree forward and reverse checks are not claimed: later
review repairs intentionally changed artifact-owned paths.

The attempt-2 reviewer findings were reproduced before repair: a mixed Evidence object selected
`atom.relation="trusted"` while silently discarding `relation="decoy"`; the legal wire contexts
`{"values":"producer-context"}`, `{"values":[]}`, and
`{"values":[["tenant","x"]]}` respectively failed, became empty, and changed keys; and direct
`Bundle(schema_version=True)` and `Bundle(schema_version=1.0)` both constructed. The repair now:

- requires exactly one Evidence atom representation: canonical `atom`, or wire `relation` plus
  optional `terms`; matching and conflicting duplicates fail with named `invalid-input` under
  Mapping/JSON ingestion and `validate=False/True`;
- gives Context one injective representation, the same flat object on the wire and in canonical
  JSON. The legal key `values` remains legal for scalar, empty-array, and pair-list-shaped values;
  claim and evidence contexts preserve semantics and digest on canonical reload;
- recursively verifies the canonical frozen pairs inside Claim and Evidence Contexts, every
  DiagnosticPolicy string field, and every TemplateValue payload before a Bundle can exist.
  TemplateValue copies mappings/lists into immutable values at construction, while rendering
  converts constants back to ordinary JSON shapes so observable output is unchanged;
- requires the schema version to be an actual non-Boolean integer equal to 1 at both ingestion and
  direct Bundle construction. Missing, `true`, `1.0`, `"1"`, and `null` are rejected;
- checks every `_sequence_field` consumer, including atom/evidence terms, rule body, aggregation
  group-by, relation index/target arrays, mapping indices/bindings, diagnostic indices, and every
  output evidence array; and
- expands the central adversarial registry from 12 to 23 canonical invalid Bundles by adding the
  nine mixed-binding mutants, the indexless static declaration, and the mapping-to-decoy claim.
  It also registers 14 constructor-rejected recursive graphs: the prior five plus Claim/Evidence
  Context internals, all six DiagnosticPolicy fields, and TemplateValue payload mutation. The five
  exhausted Bundles remain in the blocking differential. Identical named `invalid-input` or
  `resource-exhausted` reports remain blocking results with strict replay, never agreement.

An initial focused run exposed that immutable template arrays were being returned as tuples at the
rendering boundary. That run exited 1 with two `test_evidence_policy` failures. The implementation
was repaired to thaw template constants only at rendering; the internal immutability assertion was
updated to expect a tuple. A subsequent focused command over `test_claim_ir`,
`test_claim_contract_review`, `test_evidence_policy`, and
`test_differential_adversarial_matrix` exited 0: 64 tests ran in 10.062s.

The exact dependency `kernel-closure-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_validation_section27*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_evidence_policy*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_ir*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_contract_review*.py'\'' -t . && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The ten discoveries ran 13, 21, 25, 1, 16, 11, 21, 23, 2,
and 33 tests in 0.346s, 0.015s, 7.226s, 0.253s, 1.102s, 0.032s, 0.049s, 0.011s,
0.474s, and 11.707s. All 166 tests were `OK`; both focused Soufflé commands returned
`rc=0`, and neither skip guard fired.

The exact dependency `differential-closure-tests` command and the byte-identical finalizer
`differential-tests` command were each executed as a separate process:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_differential*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_shrinker*.py'\'' -t .'
```

Implementer dependency result: exit 0; 31 differential tests ran in 172.611s and 13 shrinker
tests in 19.152s, all `OK`, with `rc=0` and no focused skip. Implementer finalizer result: exit
0; the independent invocation ran the same 31 and 13 tests in 93.879s and 14.403s, all `OK`,
again with `rc=0` and no focused skip.

The exact finalizer `kernel-tests` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'command -v souffle && set -eu; for c in souffle; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_python_evaluator*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_provenance*.py'\'' -t . && PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_kernel_closure*.py'\'' -t . && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p '\''test_souffle_evaluator*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac && out=$(PYTHONPATH="$PWD/src" python -m unittest discover -s tests -p '\''test_claim_souffle*.py'\'' -t . 2>&1; echo rc=$?); printf '\''%s\n'\'' "$out"; case "$out" in *skipped*) echo '\''skipped tests are not evidence'\'' >&2; exit 1;; esac; case "$out" in *rc=0*) ;; *) exit 1;; esac'
```

Implementer result: exit 0. The six discoveries ran 1, 11, 13, 25, 2, and 33 tests in
0.237s, 0.026s, 0.252s, 2.395s, 0.391s, and 5.362s. All 85 tests were `OK`; both focused
Soufflé commands returned `rc=0` and neither skip guard fired.

The exact finalizer `regression` command was:

```sh
nix develop --no-update-lock-file --command bash -lc 'cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -t .'
```

Implementer result: exit 0, `Ran 892 tests in 102.970s`, `OK (skipped=125)`. Those 125
optional-tool/platform skips are not Soufflé evidence. The focused gates above resolved the real
pinned executable and rejected any skip.

The supplemental 14-fixture oracle was the exact command and 31-line Python body recorded in the
attempt-2 section above (the block beginning `nix develop --no-update-lock-file --command bash -lc
'set -eu; p=$(command -v souffle)`). It was executed again, not copied as stale evidence.
Implementer result: exit 0. It resolved Soufflé to
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` and Python 3.12.14;
the executable's banner again printed a blank value after `Version:`. All 14 fixtures matched on
every relation and claim field and satisfied the independent reviewed `expected.json` assertions.
The report digests were, in fixture order:

| fixture | relations | report digest |
|---|---:|---|
| 01-correlated-positive | 51 | `b8dff89a3a46448425fc2964ee0f687d7256797576b0e9e3338aef51b096472e` |
| 02-surface-mismatch | 51 | `50b3d20617546a30c9d43fb8022ad9fccdbd9424ea76cef7937b107b195a07d4` |
| 03-post-without-creation | 51 | `dbe4b81c5c09637ca7cecda2464e67b9b2fce428b5b0cea806146fbd0d56ff5f` |
| 04-authorization-polarity | 51 | `80909bf03217a43a5fde19c83d19a136bff799df1e49126e0ab983a06a8214c2` |
| 05-wrong-event-email | 51 | `01027fa9dfb1d53b46e743088d7526909b08a308cb9b75dc7f4170371e86eedb` |
| 06-context-contamination | 51 | `e5ab74db0791c24170b551c15250bd371662518bd924d1e86be8ba8128ada7f9` |
| 07-shared-mistaken-assumption | 51 | `bad57767c10e8b173ececbc63bb587a62bbc6cc8470786041eb6b555324987a0` |
| 08-rejection-versus-missing | 51 | `00ecc41d396887ae9062a3a1be41d1520467d72d7a5845347f40a2954518c387` |
| 09-support-and-refutation | 51 | `fff1921eb4d63a325e7b9fd630e8a2e5a57360ed2909b671b72469f88a76bdd2` |
| 10-revoked-assumption-alternative | 51 | `ce16e1617483fa669a05b8b18ce4f9f0ddd84eed972f4f205b58866069f3cc6d` |
| 11-compatible-history-sets | 52 | `7cc9b29dd5fb2efaecc92f4fab1072bbeddf92b0fcd4b5b1506926fbe41aa378` |
| 12-unexpected-runtime-surface | 51 | `e9ea27ebf410d2103d876cdd61b7f67fef03c3b000c89a2332e1d253b18d81d0` |
| 13-acceptance-sql-ack-failure | 51 | `6773e22a599444967bff3ef84c095026e68d369731bbb5c272e75c58fda66a2e` |
| 14-bounded-no-resend | 51 | `a0f542b53bcb8e66ca1001ac233c5cd10aeafbcda085145f1a809d437d0f6f91` |

`packages/capabilities/tests/claim_semantics/corpus/expected.json` remains byte-unchanged at
SHA-256 `9c448aacb3b714a68ae532df6c7ff022425565fa64ee275bea9cb2caeee9139c`; no corpus file changed.
The report digests changed because canonical Context JSON is intentionally now flat and injective,
not because a reviewed verdict/status/basis/missing-premise oracle changed. Scalar `values`
contexts pass semantic validation in both ingestion modes. Empty-array and pair-list-shaped
`values` contexts are canonical and digest-preserving under strict `validate=False` reload, but are
not executable relation contexts because schema-v1 deliberately excludes `json-metadata-only`
from kernel field types; this is a recorded type-system limit, not a claimed semantic execution.

Final `git diff --check` passed, and all seven modified paths are inside the declared write set.
These are implementer observations only. The driver's fresh `gate-result` events for attempt 3 are
the authoritative gate evidence if admitted, and only the driver may append a checkpoint hash in
`task-completed`; neither is recorded or promised here. The deferred ownership table above is
unchanged: CLI, Linux execution, performance evaluation, and recommendation belong to
`datalog-evaluation`; installed-wheel static-schema inclusion and provenance extraction belong to
`scip-datalog-differential`; ground checking, producer authority, and generic causal projection
belong to `datalog-certificates`. Soufflé independently establishes relational closure only;
claim folding, diagnostics, mappings, output semantics, and missing-premise rendering remain
Python-mediated. Producer and kernel output remain evidence, not authority. No Shen, SCIP,
external execution, receipt, certificate, real-Go, Linux, production CLI behavior, performance
recommendation, authoritative gate event, or checkpoint is claimed.

## 28. Stage 0 addendum — SCIP toolchain

Owner: `scip-toolchain` (single-task wave). Write set: `flake.nix`, `flake.lock`,
`tests/scip/**`, `packages/capabilities/tests/fixtures/scip_go_app_index.json`, this document.

- Add `scip` and `scip-go` to the devShell `toolPackages` (pinned nixpkgs
  `34ab99075ac4f7e40cf037eef32cb1c360bb85e9` provides `scip` 0.9.0, `scip-go` 0.2.7,
  `souffle` 2.5; it does not provide `scip-python`, which is out of scope). Add `pkgs.souffle`
  and `LC_ALL=C` to the `capability-regression` check so the Soufflé kernel tests run there.
- New check `scip-go-index-smoke`: copy `tests/fixtures/go_app` (its `go.mod` has no
  `require`, so the sandbox needs no network), set `HOME`, `GOCACHE`, `GOPATH` under
  `$TMPDIR`, `GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local LC_ALL=C`, run
  `scip-go --output index.scip`, `scip print --json`, canonicalize with
  `tests/scip/canonicalize.jq` (drop `metadata.project_root`; sort documents by
  `relative_path`, occurrences by range and symbol, symbols by symbol), and `diff -u` against
  the committed golden; record `scip --version` and `sha256(index.scip)` in `$out`.
- `tests/fixtures/scip_go_nested_symbols.json` indexes module `github.com/example/gonest`,
  not go_app (`github.com/example/jobsvc`). The golden `scip_go_app_index.json` is a new
  deliverable produced once under `nix develop` with the same jq script.
- Re-record Stage 0 evidence here: versions and `/nix/store` paths for `scip`, `scip-go`,
  `souffle`, `go`, `python`; devShell closure size before and after; the smoke derivation
  path and index sha256; host and Nix version; `flake.lock` sha (expected unchanged,
  `d078f9fb…`, which proves nothing about the closure — the store paths and closure size are
  the evidence). If scip-go output differs across darwin and Linux after canonicalization,
  change the assertion to sorted symbol set plus per-document occurrence counts and record
  the nondeterminism explicitly.

### SCIP toolchain record (2026-09-15, task `scip-toolchain`)

Worktree `/Users/dev/projects/capcov-scip-toolchain`, branch `agent/scip-toolchain`, parent
HEAD `cfd3af4e7a8ecbcf142a13bcc729fde840c57370`. Host `aarch64-darwin`, Darwin kernel `25.5.0`
(macOS 26.5.2, build 25F84), Nix `nix (Determinate Nix 3.21.5) 2.34.8` (host Nix CLI is not
pinned by the flake). `flake.lock` was not edited and `nix flake update` was not run;
`shasum -a 256 flake.lock` is `d078f9fba512323fd35b24afc6a81aa3bb95c63caa1d00acf700e0827f9e6bac`
before and after. That unchanged lock proves only that nixpkgs is still
`34ab99075ac4f7e40cf037eef32cb1c360bb85e9`; the closure evidence is the store paths and sizes below.

Changes in this task's write set:

- `flake.nix`: `scip` and `scip-go` added to devShell `toolPackages`; `capability-regression`
  now has `nativeBuildInputs = [ pkgs.python312 pkgs.souffle ]`, exports `LC_ALL=C`, and runs
  with `PYTHONPATH="$PWD/src"` (absolute) because the merged upstream test
  `tests.test_feature_evidence.FeatureEvidenceTests.test_cli_reconciles_in_a_real_subprocess`
  spawns `python -m capcov` with a temporary cwd, where a relative `src` does not resolve; new
  check `scip-go-index-smoke` (inputs `values.go`, `pkgs.scip`, `pkgs.scip-go`, `pkgs.jq`)
  copies `cleanSource ./packages/capabilities/tests/fixtures/go_app`, sets
  `HOME`/`GOCACHE`/`GOPATH` under `$TMPDIR` with `GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local
  LC_ALL=C`, runs `scip-go --output index.scip`, `scip print --json`,
  `jq -S -f tests/scip/canonicalize.jq`, `diff -u` against the committed golden, and writes
  `scip_go_app_index.json`, `scip-version.txt`, `scip-go-version.txt`, `go-version.txt`, and
  `index.scip.sha256` under `$out`.
- `tests/scip/canonicalize.jq`, `tests/scip/README.md`: canonicalization and rationale.
- `packages/capabilities/tests/fixtures/scip_go_app_index.json`: golden, produced once in the
  devShell with that exact jq script; sha256
  `0b5183fc8d03afc1f86331ae3e1d5bdfe9ff87e0159c96156662b6bde51e687e` (1369 lines, trailing
  newline). The go_app fixture lives at `packages/capabilities/tests/fixtures/go_app`, which is
  the path the manifest gate uses; the `tests/fixtures/go_app` spelling earlier in this section
  is shorthand for the same directory.

Pinned tools observed through `nix develop --no-update-lock-file --command bash -lc`, all under
`/nix/store`:

- scip `v0.9.0` at `/nix/store/hckm2075va6x941b4lwncv8ls3p6ssr1-scip-0.9.0/bin/scip` (closure 22.4 MiB)
- scip-go `0.2.7` at `/nix/store/3inxss33qhklfr6416j0kwp4cbjkdlys-scip-go-0.2.7/bin/scip-go` (closure 14.4 MiB)
- souffle `2.5` at `/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` (closure 1.4 GiB; already in the devShell before this task)
- go `go1.27.0 darwin/arm64` at `/nix/store/lz3qw52rpazqga73xgsqlj4qz1lgs4hg-go-1.27.0/bin/go`
- python `3.12.14` at `/nix/store/p1wfv7znig26m3hns4583cb9va3kzxkg-python3-3.12.14/bin/python`
- jq `1.8.2` at `/nix/store/d01nk4ck93bwlzwbnnb1qf1kv4d94a09-jq-1.8.2-bin/bin/jq`

devShell closure (`nix build --no-update-lock-file .#devShells.aarch64-darwin.default
--out-link .capcov/devshell-gcroot`; `nix path-info -S`):

- before: `/nix/store/hc9i3s6l94vdlq8hx10zxmy4shq3gfjr-nix-shell`, 2,075,908,424 bytes (`-Sh`: 1.9 GiB); identical to the driver's existing GC root
- after: `/nix/store/mfaim3jlm3qfx1xl9f0hzcn19fgpr9im-nix-shell`, 2,108,790,296 bytes (`-Sh`: 2.0 GiB); delta +32,881,872 bytes, consistent with scip + scip-go

Smoke derivation `/nix/store/0bjmfii20s639nac455mj13my06y4849-scip-go-index-smoke.drv`, output
`/nix/store/xdi059dwma7qm4ybbyn9fk26j97znmj1-scip-go-index-smoke`; `$out/scip_go_app_index.json`
sha256 `0b5183fc…` (equal to the golden); `$out/index.scip.sha256` =
`7b267d0f35ad1973c221a036fecb433522d18b8bd08d29e6f622adf8e20f3731`; `scip-version.txt` =
`scip version v0.9.0`; `scip-go-version.txt` = `0.2.7`; `go-version.txt` = `go version go1.27.0
darwin/arm64`. Regression derivation
`/nix/store/nfk4qqfmdhn8p17zdp1qzlhxif35yxg0-capcov-capability-regression.drv`.

Determinism, observed rather than assumed: two consecutive `scip-go` runs on copies of go_app in
the same devShell produced different `index.scip` digests (`6726ce99…`, `a0b4be0b…`) and different
raw `scip print --json` output. Apart from `metadata.project_root` (`file://` URI of the temp
directory), the only difference was the order of entries in each document's `symbols` array (Go
map iteration order); document order, occurrence order, and the per-document symbol and occurrence
multisets were equal. After `canonicalize.jq` both runs were byte-identical (`0b5183fc…`), and the
sandboxed check reproduced the same bytes, so the byte-for-byte assertion stands; it was not
weakened to symbol-set plus counts. Sort keys (`symbol` within `symbols`, `(range, symbol)` within
`occurrences`) were checked unique per document in the golden, so the sort is a total order. The
raw output with `project_root` removed contains no `/tmp`, `/private`, `/Users`, or `file://`
strings; `external_symbols` is absent in scip-go's output for go_app and is normalized to `[]`.
The `index.scip` digest under `$out` embeds `project_root` and is a record of that build, not an
invariant; the canonical JSON digest is the invariant.

Gates, run with the exact manifest command form `nix develop --no-update-lock-file --command bash
-lc '…'` from the worktree with the new files staged (Nix warned `Git tree … has uncommitted
changes`; unstaged files would be excluded from `self`):

```sh
nix flake check --no-update-lock-file
```

Exit 0. Built `capability-regression`, `scip-go-index-smoke`, `shen-evaluator-smoke`,
`souffle-recursive-typed-smoke`; `shen-package` previously built. Sandboxed regression log:
`Ran 880 tests in 320.539s`, `OK (skipped=127)`. Linux checks omitted on this host.

```sh
set -eu; for c in scip scip-go souffle go python; do p=$(command -v "$c"); case "$p" in /nix/store/*) ;; *) echo "unpinned $c=$p" >&2; exit 1;; esac; done; scip --version; souffle --version; go version; test "$(shasum -a 256 flake.lock | cut -d' ' -f1)" = d078f9fb…
```

Exit 0 (`scip version v0.9.0`, Soufflé 2.5 banner, `go version go1.27.0 darwin/arm64`).

```sh
# scip-go-index-smoke-develop (manifest command: mktemp, cp go_app, scip-go, scip print, jq -S -f, diff -u golden)
```

Exit 0; `diff -u` printed nothing.

```sh
nix flake check --all-systems --no-build --no-update-lock-file
```

Exit 0. Evaluated `scip-go-index-smoke`, `souffle-recursive-typed-smoke`, `capability-regression`,
`shen-*`, packages, and devShells for `aarch64-darwin`, `aarch64-linux`, `x86_64-linux`. Linux is
evaluation-only; no Linux build or execution is claimed, and the golden's cross-platform validity
is untested.

```sh
cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .
```

Exit 1: `Ran 880 tests in 217.378s`, `FAILED (failures=1, skipped=125)`. The single failure is
`tests.test_feature_evidence.FeatureEvidenceTests.test_cli_reconciles_in_a_real_subprocess`:
`AssertionError: 1 != 0 : /nix/store/p1wfv7znig26m3hns4583cb9va3kzxkg-python3-3.12.14/bin/python:
No module named capcov`. The test runs `sys.executable -m capcov` with `cwd` set to a temp
directory, so the manifest's relative `PYTHONPATH=src` does not resolve there. This is a manifest
command defect, not a toolchain or test defect; the test and `.pi/workflows/capcov-experiment.json`
are outside this write set and were not edited. Same suite with the absolute form:

```sh
cd packages/capabilities && PYTHONPATH="$PWD/src" python -m unittest discover -s tests -t .
```

Exit 0: `Ran 880 tests in 89.245s`, `OK (skipped=125)`. **Needed manifest change:** the
`regression` gate command for this task (and any other task using the relative form) should read
`PYTHONPATH="$PWD/src"`; the flake's `capability-regression` check already uses it.

Soufflé in the sandbox: `tests.test_claim_souffle.SouffleBackendTests` is the only
`skipUnless(shutil.which("souffle"))` class and holds 31 tests (`unittest -v` in the devShell:
33 tests in the module, 31 in that class, all `ok`). The sandboxed check skipped 127 versus 125 in
the devShell, the same two-test gap documented in section 14 for Go/Git-dependent tests; had souffle
been absent in the sandbox the gap would be 33. The sandboxed run does not print per-test names, so
this is inferred from skip counts, not read off a verbose log.

**Limits:** Linux remains evaluation-only, and the golden has only been reproduced on
`aarch64-darwin` (twice in the devShell, once in the sandbox). A clean-checkout rebuild from the
committed SHA has not been demonstrated by this task (the commit is made after these runs;
`nix flake check` ran against the staged, uncommitted tree). `scip-go --version` prints `0.2.7`
followed by an empty `Version:` banner; the recorded version is the first line. The host Nix CLI
is unpinned. `scip-python` is not provided by this nixpkgs revision and is out of scope.

## 29. SCIP → Datalog: static observations as claim evidence

Owner: wave `scip-datalog` (`scip-fact-export` and `static-rule-pack` in parallel,
`scip-datalog-differential` reducer). Hypothesis: SCIP gives Soufflé and the Python kernel a
large, naturally relational source of real program facts, and the existing evidence
discipline (typed relations, bounded provenance, completeness witnesses, digests) can be
preserved for static observations. Falsifier: the two kernels disagree on closure and the
shrinker cannot localize it; or static facts cannot be joined to runtime evidence without
weakening context checks; or completeness claims cannot be stated without lying witnesses.

SCIP stays a producer of static observations, never an oracle: a SCIP path cannot prove a
runtime effect occurred, and a missing SCIP edge may mean incomplete indexer support rather
than absence. Completeness claims therefore require indexer and language coverage witnesses.

### Identity and context

Every static relation carries exactly one context column `index` (type `digest`,
`context: true`), whose value is a content digest of the normalized relations the exporter
emits — the `static-relations-v1` identity:

```text
index = sha256("static-relations-v1:" + canonical_json({
          "relations": sorted(<every relation name the bundle declares>),
          "rows": {relation: sorted(rows with the index column removed, by canonical JSON)
                   for every exported primitive relation with at least one row,
                   except the compatibility relations index_describes_run / scip_index_comparable}}))
```

`export_bundle` builds every fact under a placeholder index, computes this digest from the
finished rows, then sets every `index` column to it and computes the evidence ids (which embed
`index[:12]` and the row digest): content digest → index → ids. Two exports of the same
normalized content therefore carry the same `index`, the same evidence ids and the same bundle
digest regardless of the indexer's emission order (scip-go writes per-document `symbols` in Go
map order, section 28) and of which copy of the tree was indexed. Compatibility relations bind
the index to *other* contexts (a run, another index) and are supplied at claim time, so they are
keyed by the identity rather than part of it. The digest of the index file the runner read —
`sha256(index.scip bytes)` (`binary`) or `sha256("scip-json:" + canonical_json(raw))` for a
checked-in JSON fixture (`json`) — is a *run receipt*, not identity: `read_scip_index` still
returns it as `index_digest` / `index_digest_kind`, the exporter reports it in
`ExportResult.messages`, carries it in bundle metadata as `index_file_digest` /
`index_file_digest_kind`, and `scip_facts.bundle_digest` excludes those two keys
(`RECEIPT_METADATA_KEYS`); `scip_index.digest_kind` carries the literal `static-relations-v1`.
Tree-sitter-side facts (routes, op sites, blind spots) are
keyed by the same `index`: the exporter binds one tree walk to one index and refuses to export
unless the language-scoped tree digest matches (`artifacts.tree_sha256` gains per-language
patterns; today Go and PHP trees hash as empty). Under `validation.py` this means cross-index
joins need `scip_index_comparable`, negation of any static relation needs a completeness
relation with `context_indices == ("index",)`, and static/runtime joins need
`index_describes_run(index, run)` via the new `mixed-binding-join` check.

### Primitive relations (frozen in `claims/static/schema_static_v1.json`)

All `modality=observation`, `binding=static`, `primitive=true`, `context_indices=["index"]`
unless noted. Types: S symbol, U unsigned, B boolean, D digest, J json.

- Identity: `scip_index(index, indexer:S, indexer_version:S, language:S, project_root:S,
  digest_kind:S)` finite, nonempty; `scip_index_tree(index, tree_digest:D, file_count:U,
  pattern:S)`; `scip_index_commit(index, commit:S)` optional; `static_scope(index,
  scope_kind:S ∈ {all, package_prefix, document_set}, scope_value:S)`;
  `static_language_covered(index, language:S)`.
- Documents and symbols: `scip_document(index, path, language, occurrence_count:U,
  symbol_count:U, enclosing_synthesized:B)`; `static_source_file(index, path, language)` (what
  should have been indexed); `scip_symbol(index, symbol, kind, category, display_name)`;
  `scip_symbol_node(index, symbol, node)`; `scip_symbol_unrooted(index, symbol, reason ∈ {local,
  unknown-scheme, non-node-descriptor, no-package})`; `scip_relationship(index, symbol, related,
  kind)` when the indexer supplies relationships (scip-go 0.2.7 emits none on the fixtures).
- Occurrence-derived (raw occurrences are not exported in the slice profile; they are referenced
  by `external:scip-occurrence:<index12>:<occ12>` evidence ids): `scip_definition_site(index,
  path, line:U, symbol)`; decoded role relations `scip_generated_site`, `scip_test_site`,
  `scip_import_site`, `scip_write_site`, `scip_read_site` (same columns);
  `scip_enclosing(index, symbol, path, start_line, end_line, synthesized:B)`;
  `static_site_owner(index, path, line, symbol)` (innermost enclosing definition for every
  route, op, and call site; new `map.site_owners`); `scip_may_reference(index, caller, callee,
  path, line, occurrence:D, caller_synthesized:B)` from `map.call_edges`, rooted edges only;
  `scip_module_scope_reference(index, callee, path, line, occurrence)` for `caller is None`;
  `scip_type_reference(index, referrer, type_symbol, path, line, occurrence)` (new
  `map.type_references`; constructor calls live here, not in the call graph).
- Tree-sitter and recognizer side: `route_site(index, surface, path, line, handler_name)`;
  `route_handler_location(index, surface, path, line)` (from `_node_locations`, the deep
  binding of record); `route_site_excluded(index, surface, reason)`; `static_op_site(index,
  path, line, verb, entity)`; `static_entity(index, entity, path, line, table)`;
  `static_blind_spot(index, path, line, kind, reason)`; `scip_unresolved_site(index, path,
  line, callee_text, kind)` from `resolve._residue`; `static_unresolved(index, kind, node,
  path, line)`; consumer-supplied `changed_symbol(index, symbol, change_kind)`; assumption
  `authz_symbol__accepted(index, symbol)`.
- Claim-time: `source_tree_observed(tree_digest:D)` (static, no context);
  `run_built_from_commit(run, commit)` (runtime, context `run`).
- Completeness (`modality=completeness`, context `index`): `scip_documents_closed(index)`
  completes `scip_document_path`; `scip_definitions_closed(index, path)` completes the
  projection `scip_definition_site_at`; `scip_references_closed(index, path)` completes
  `scip_may_reference` (emitted only when the document is in scope, has occurrences, has no
  synthesized spans, no residue or blind spots, and no duplicate definitions);
  `static_route_inventory_closed(index)`; `static_scope_closed(index)` (withheld, with
  `static_scope_leak(index, symbol, defined_in)` rows, when an in-slice edge lands on
  first-party code outside the slice); `static_reachability_closed(index)` completes
  `static_reaches`. Emission conditions are the exporter's audited contract: each witness's
  `Evidence.source` names the predicate version.
- Compatibility: `scip_index_comparable(index_a, index_b, basis)`;
  `index_describes_run(index, run)`.

Evidence ids are `scip:<index12>:<relation>:<row12>` (tree-sitter side `static:`), with
`row12 = sha256(canonical_json([relation, row]))[:12]`. `Evidence.source` is the producer
string (`scip-go 0.2.7`, `scip 0.9.0 print --json`, `treesitter-routes go`,
`capcov.claims.static.scip_facts v1`). `depends_on` chains: an edge depends on its document,
its reference occurrence, and the caller-definition occurrence; sites depend on the tree
identity; witnesses depend on their document and the tree identity; `scip_index_commit`
depends on `external:git-commit:<sha>`. Bundle metadata records export version, index identity
(`index_digest`, kind `static-relations-v1`), the index-file receipt (`index_file_digest`,
`index_file_digest_kind`; outside `bundle_digest`), scope, producer versions, and profile
(`slice` or `full`).

### Runner retention (opt-in, backward compatible)

`normalize_scip_json(doc, *, retain=False)` and `read_scip_index(path, *, retain=False)`
keep their default output byte-identical (a runner test asserts exact dict equality). With
`retain=True` they add top-level `metadata` (tool name, version, arguments, project root,
encoding), `external_symbols`; per document `language` and `enclosing_synthesized`; per
occurrence the raw `symbol_roles`, decoded `roles`, end position, and a synthesized-span flag;
per symbol `relationships` and `kind_number`. `read_scip_index` returns `index_digest` and
`index_digest_kind`; the exporter's impure entry keeps `index.scip` long enough to hash it.
`_Normalizer.explain(symbol)` returns the node or a reason instead of a silent `None`.

### Rule pack (`experiments/claim-semantics/static/rules-static-v1.json`, raw IR JSON)

Derived relations (`primitive=false`, context `index`): `static_edge`, `static_root`,
`static_reaches` (recursive, positive), `static_reaches_eq`, `static_route_handler`,
`static_route_declared_surface` (finite, nonempty; the `forall` domain), `static_op_owner`,
`static_path_to_storage`, `static_capability_op`, `static_capability` (claim),
`static_index_current`, `scip_index_stale`, `static_file_unindexed`,
`scip_duplicate_definition`, `change_reaches` (recursive), `affected_capability` (claim),
`runtime_route_without_static` (negative claim, context tenant/surface/run/index),
`static_route_authorized` (claim), `static_route_authorization_gap`,
`static_route_authorized_closed` (derived completeness).

```text
static_index_current(IX) :- scip_index_tree(IX,T,_n,_p), source_tree_observed(T).
scip_index_stale(IX,T,O)  :- scip_index_tree(IX,T,_n,_p), source_tree_observed(O), T != O.
static_edge(IX,S,D)       :- scip_may_reference(IX,S,D,_p,_l,_o,_s).
static_root(IX,H)         :- static_route_handler(IX,_s,H).
static_reaches(IX,R,D)    :- static_root(IX,R), static_edge(IX,R,D).
static_reaches(IX,R,D)    :- static_reaches(IX,R,M), static_edge(IX,M,D).
static_route_handler(IX,S,Sym) :- route_handler_location(IX,S,F,L),
                                  scip_definition_site(IX,F,L,Sym), scip_symbol(IX,Sym,_k,"callable",_d).
static_op_owner(IX,Sym,E,V)    :- static_op_site(IX,F,L,V,E), static_site_owner(IX,F,L,Sym).
static_path_to_storage(IX,S,E,V) :- static_route_handler(IX,S,H), static_reaches_eq(IX,H,N),
                                    static_op_owner(IX,N,E,V).
static_capability_op(IX,S,E,V)   :- static_path_to_storage(IX,S,E,V), static_index_current(IX).
runtime_route_without_static(T,S,R,IX) :- runtime_route_observed(T,S,_e,R), index_describes_run(IX,R),
                                          static_route_inventory_closed(IX), !static_route_declared_surface(IX,S).
static_route_authorized(IX,S) :- static_route_handler(IX,S,H), static_reaches_eq(IX,H,N),
                                 authz_symbol__accepted(IX,N), static_index_current(IX).
static_route_authorization_gap(IX,S) :- static_route_declared_surface(IX,S),
                                        static_route_authorized_closed(IX), !static_route_authorized(IX,S).
scip_duplicate_definition(IX,Sym,PA,LA,PB,LB) :- scip_definition_site(IX,PA,LA,Sym), scip_definition_site(IX,PB,LB,Sym),
                                                 scip_symbol(IX,Sym,_k,Cat,_d), Cat != "other", PA != PB.
scip_duplicate_definition(IX,Sym,PA,LA,PB,LB) :- scip_definition_site(IX,PA,LA,Sym), scip_definition_site(IX,PB,LB,Sym),
                                                 scip_symbol(IX,Sym,_k,Cat,_d), Cat != "other", LA != LB.
```

The category guard on `scip_duplicate_definition` is the exporter's own predicate
(`_symbol_category(symbol) != "other"`, `scip_facts.py`): namespace (package) symbols, whose
descriptor ends in `/`, are defined by scip-go in every file of the package, and `local N`
symbols are file-scoped, so neither is an ambiguous definition; only `callable`, `type` and
`term` symbols can be. A guard on `scip_symbol_unrooted(IX,Sym,"local")` was not used because
negating it would need a completeness witness the exporter does not emit.

Validation consequences already verified against `validation.py`: negating a relation with
unbound extra columns is `unsafe-negation`, so negations go through projections and
`completes` points at the projection; `forall` claims need the domain declared `finite` and
`nonempty` (an empty route inventory yields `inconsistent-premises`, which is correct);
digest inequality comparisons are allowed. Only `static_reaches` and `change_reaches` are
recursive and neither SCC contains negation or aggregation. The IR has no arithmetic, so hop
counts are not in the rule pack.

### Certificates for both engines

Soufflé computes relations only. `claims/static/certificate.py` re-derives a ground
certificate from relation rows: fact rows map to evidence ids; derived rows unify against
rules in canonical order, enumerate body instantiations over the rows (negated atoms checked
absent, comparisons re-evaluated), and recurse with `max_depth=64`, `max_nodes=10_000`. For the
recursive relations a BFS over `static_edge` from the root yields the shortest path and
exactly k ground step applications (k ≤ 64, matching `fixpoint.distances(max_hops)`), else
`truncated: true`. The same extractor runs over the Python kernel's rows, so certificates are
engine-independent and replayable by the Stage C checker without search. `souffle --provenance`
was rejected (interactive, Soufflé-only, incompatible with the any/all helper lowering), as was
a hop-column encoding for every root (`roots × reach × 65` rows against the 100k cap); a
`static_reaches_within(index, root, dst, hops)` relation over a finite `hop_succ(0..64)` is
kept only in the go_app differential bundle to cross-check the extractor's k.

### Bounds and slicing

Soufflé counts every relation's rows, inputs included, against 100k rows and 16 MiB.
go_app is about 150 input rows; a 50k-occurrence service is about 120k rows unsliced and
20–35k with a package-prefix slice. Raw occurrences are never exported in the slice profile;
`scip_unresolved_site` and `static_blind_spot` are exported but the full call-site census is
summarized by the per-document completeness witnesses; `static_scope` is an explicit fact;
witnesses are emitted only for in-scope documents; `profile=full` is permitted only for a
`document_set` scope of at most 50 documents. Positive reachability stays derivable in a
slice; negatives become `unresolved` with a visible missing premise, never silently true.

### Adversarial static cases (`experiments/claim-semantics/static/cases/`)

| # | case | seeded facts | reviewed expectation |
|---|---|---|---|
| 01 | unresolved symbol | edge to `local 3`, `scip_symbol_unrooted`, no `scip_symbol_node` | symbol-level capability supported; node-level unresolved with missing premise `scip_symbol_node` and discrepancy `unrooted-symbol` |
| 02 | incomplete indexer | `static_source_file` without `scip_document`; `static_reachability_closed` withheld | positive supported; `static_file_unindexed` derived; negative gap claim unresolved; a variant with a seeded lying witness is labelled as a seeded fault |
| 03 | dynamic dispatch | `static_blind_spot(interface_dispatch)` on the path | positive supported (over-approximation is the safe direction); negative unresolved because `scip_references_closed` is withheld; discrepancy `blind-spot-on-path` |
| 04 | generated code | handler defined in `scip_generated_site` | `forall` supported plus discrepancy `handler-in-generated-code`; `generated_code_in_scope__accepted` clears it, `__rejected` yields out-of-scope |
| 05 | stale index | `scip_index_tree(IX,T1)`, `source_tree_observed(T2)` | unresolved / `stale` via a diagnostic on `scip_index_stale`; missing premise `static_index_current` |
| 06 | synthesized enclosing (scip-php) | `enclosing_synthesized=true`, edges `caller_synthesized=true` | supported plus discrepancy `caller-attribution-synthesized`; every completeness witness withheld so negatives stay unresolved |
| 07 | constructor as type reference | `scip_type_reference` to `Job#`, no edge | capability supported through the op owner; `static_reaches(GetJob, Job#)` unresolved and documented |
| 08 | module-scope reference | `handle(...)` at package scope | route → handler supported; "init reaches storage" unresolved (no root symbol) |
| 09 | duplicate definitions | two `scip_definition_site` rows for one symbol | supported plus discrepancy `ambiguous-definition`; negatives unresolved |
| 09 (variant `-package-symbol`) | package symbol defined per file | `Handler#GetJob` defined once; the package symbol `api/` (category `other`) defined in two files; every reference witness present | `scip_duplicate_definition` empty, claim unresolved with missing premise `scip_symbol`; no discrepancy; the negative gap claim resolves (`supported`) because the witnesses are not withheld |

### Cross-check against the current resolver

On the go_app golden index, `static_capability_op(index, surface, entity, verb)` must equal
the capabilities `core.fixpoint.bind` derives from `resolve.calls_graph(map.call_edges(...),
language="go")` (stdlib path; the tree-sitter `cli discover --resolver scip` comparison is
skip-guarded and not a gate). Expected chain: `api/Handler#GetJob().` → `service/Service#Fetch().`
→ `jobs/Repo#Get().` and `Repo#Write().`, ops `read` on `jobs` and `create` on `audit_logs`. Any
difference outside an enumerated set of legitimate differences is a `differential-mismatch`.
The corpus adapter's premise syntax cannot express recursion, so static fixtures carry facts,
evidence, and claims in corpus style and rules as raw IR JSON through
`tests/claim_semantics/static_rules/adapter.py`.

### Stop conditions for this wave

Kernel disagreement the shrinker cannot localize within 200 steps or after three `wave-repair`
events blocks the wave with the replay bundle. A static-versus-fixpoint difference outside the
enumerated set is a mismatch, not a pass. `resource-exhausted` on the bounded slice is reported,
never fixed by raising limits silently. A golden mismatch across machines changes the assertion
basis explicitly. A bundle whose `index_digest` differs from the index actually evaluated is
`stale`. The go_app pilot is never described as target-go evidence.

### Reducer record (2026-09-15, task `scip-datalog-differential`)

Worktree `/Users/dev/projects/capcov-scip-datalog`, branch `scip-datalog/fan-in`, integration
parent `7b1a65ed94e73d64ac70277436972a6550e79e62` (the three parallel deliverables merged:
`agent/scip-toolchain` 2f3b4d8, `agent/scip-fact-export` 98e695f, `agent/static-rule-pack`
e6c1845). Host `aarch64-darwin`, Darwin `25.5.0`; devShell GC root rebuilt first
(`nix build --no-update-lock-file .#devShells.aarch64-darwin.default --out-link
.capcov/devshell-gcroot` → `/nix/store/mfaim3jlm3qfx1xl9f0hzcn19fgpr9im-nix-shell`, the same
closure section 28 recorded). Soufflé store path
`/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle` (`souffle-2.5`); scip
`/nix/store/hckm2075va6x941b4lwncv8ls3p6ssr1-scip-0.9.0/bin/scip`; scip-go
`/nix/store/3inxss33qhklfr6416j0kwp4cbjkdlys-scip-go-0.2.7/bin/scip-go`; python
`/nix/store/p1wfv7znig26m3hns4583cb9va3kzxkg-python3-3.12.14/bin/python`. No driver checkpoint
hash is recorded or promised here.

**Reconciliation decisions (items 1–5).**

1. *Line frame.* 1-based everywhere, as the exporter's `LINE_FRAME` says: SCIP's 0-based range
   lines are lifted once in `scip_facts.export_bundle`, and `route_handler_location(IX,S,F,L)`
   joins `scip_definition_site(IX,F,L,Sym)` without a per-rule shift. The hand-written control
   case `00-go-app-control` already agreed (GetJob defined on `api/jobs.go:10`, route on 17,
   `Repo.Get`/`Repo.Write` on `internal/jobs/repo.go` 14/19, sites on 15/20; the golden's
   definition occurrence for `GetJob` has range line 9). The frame is now stated in the rule pack
   README ("Line frame"), together with the fact that the control case is a go_app-*shaped*
   synthetic (abbreviated symbols, an extra `internal/authz` package); the exporter's own output
   over the golden is evaluated by the new differential tests through
   `tests/claim_semantics/static_rules/go_app.py`.
2. *Duplicate declarations.* The exporter keeps declaring the five stubs (its bundle must validate
   alone: the frozen witnesses' `completes` targets and `index_describes_run`'s compatibility
   target must resolve), but they are now byte-identical to the pack's declarations
   (`modality=derived`; `scip_definition_site_at` gained the `line` column the pack declares).
   New `claims/static/combine.py::combine(*bundles, ...)` merges declaration sets by name and
   raises `CombineError` on a non-identical duplicate (tested with a widened `static_reaches`),
   unions facts/rules/claims/mappings/diagnostics/outputs, requires unique evidence ids and equal
   diagnostic policies, and validates the result. So: option "merge identical declarations by
   name", with identity enforced rather than assumed; the pack stays the authority on rules.
3. *`project_root`.* `scip_index.project_root` now carries
   `scip_facts.canonical_project_root(reported)` = `file:///<basename>` of the indexer's root
   (or `""` when the index has none, as the canonicalized JSON golden does); the reported host
   path goes to `ExportResult.messages`, not into any fact and not into bundle metadata (metadata
   is part of the bundle digest). The exporter test's `file:///tmp/gonest` expectation became
   `file:///gonest`; the live go_app export records `file:///go_app`. The committed exported-bundle
   digest for the golden (below) is asserted by `test_differential_static_reachability.py`.
4. *Validator.* `validation._validate_context_joins` now skips the context-free static atom when
   the body has no runtime atom and still returns `mixed-binding-join` when it has one
   (regression test `test_context_free_static_join_is_flagged_only_when_runtime_evidence_is_read`
   in `test_validation_section27.py`). The pack's bridge `static_source_tree_observed(index,
   tree_digest)` was therefore removed: `static_index_current` and `scip_index_stale` read the
   frozen `source_tree_observed(T)` directly, exactly as this section writes them; every case
   dropped its bridge fact and the reviewed leaf sets now name the claim-time
   `static:claim-time:source_tree_observed:<row12>` leaf instead (mechanical rewrite of the 13
   case files and `expected.json`; the Python-evaluator agreement test and the Soufflé
   differential over all cases pass unchanged in verdicts). The README's "Validator findings"
   records the history.
5. *No faked census.* `export_from_tree` still emits no `scip_references_closed` without a
   census. The go_app differential uses the JSON golden plus a hand-built `ast_raw`
   (`static_rules/go_app.py`: route `http:GET /jobs/{id}` at `api/jobs.go:17`, handler location
   `api/jobs.go:10`, op sites `internal/jobs/repo.go:15` read `jobs` and `:20` create
   `audit_logs`, two entities) whose empty `blind_spots`/`scip_residue` are a *hand review* of the
   five Go files — stated in the module docstring and here, not presented as recognizer output.
   The surface id follows the deep adapter's `http:<METHOD> <path>` spelling, so the acceptance
   statement's `GET /jobs/{id}` reads as that surface.

**Files.** New: `packages/capabilities/src/capcov/claims/static/certificate.py` (certify,
recheck, claim_conclusions, rules_digest), `.../static/combine.py`,
`tests/claim_semantics/static_rules/go_app.py`, and tests
`test_differential_static_reachability.py`, `test_differential_static_certificate.py`,
`test_static_crosscheck_fixpoint.py`, `test_static_adversarial_both_engines.py`,
`test_static_evidence_policy.py`, `test_bounds_static.py`, `test_static_schema_package_data.py`.
Changed: `claims/validation.py` (item 4), `claims/static/scip_facts.py` (items 2, 3;
`primitive_relations`, `STUB_RELATIONS`, `canonical_project_root`), `claims/static/__init__.py`
(schema read through `importlib.resources`), `pyproject.toml`
(`[tool.setuptools.package-data] "capcov.claims.static" = ["*.json"]`), `MANIFEST.in`, the rule
pack, its 13 cases, `expected.json` and README (item 4, item 1), `test_scip_facts_export.py`
(project root), `test_scip_facts_live.py` (see limits), `test_validation_section27.py`.

**go_app bundle identities (all computed by me in the devShell; the tests assert the first).**
Golden `tests/fixtures/scip_go_app_index.json` sha256 `0b5183fc8d03afc1f86331ae3e1d5bdfe9ff87e0159c96156662b6bde51e687e`;
index identity (`static-relations-v1`, see "Identity and context"; recomputed with the identity
rebase recorded at the end of this section, when the file receipt
`sha256("scip-json:"+canonical_json)` = `4a500048401a2c4e45d4f86710568a5543570e21db83f143965bf0a3d0b7c8da`
stopped being the identity) `0360df877c99d8259f7f7f24cdca357afa64c4be9b27a739e1e78bb94c564320`,
the same for the plain export and for the export that also declares `index_describes_run(run-1)`;
Go tree digest of
`tests/fixtures/go_app` over `**/*.go` `68a0ccf1d2af57276cca57696430f657e1de895e0af1906c36762376224dd870`
(5 files). Exported bundle (facts+evidence+declarations+metadata minus the receipts, no
rules/claims): digest `585240159f4abfa9eb96a778abaa1bbba4ab95553f79e7163901f5f91ca1a49d` (was
`53dcade7…` under the file-digest identity), 210 facts / 210 evidence records, identical under
two seeded permutations of documents, occurrences, symbols and of the ast_raw lists exported
under a different fake file receipt. Exported row counts: `scip_definition_site` 38, `scip_read_site` 42,
`scip_symbol` 37, `scip_symbol_node` 22, `scip_symbol_unrooted` 9, `scip_type_reference` 9,
`scip_enclosing` 8, `scip_may_reference` 7, `scip_document` 5, `static_source_file` 5,
`scip_definitions_closed` 5, `scip_references_closed` 5, `static_site_owner` 3, `static_op_site` 2,
`static_entity` 2, and one each of `scip_index`, `scip_index_tree`, `route_site`,
`route_handler_location`, `static_scope`, `static_language_covered`, `scip_documents_closed`,
`static_route_inventory_closed`, `static_scope_closed`, `static_reachability_closed`,
`index_describes_run` (run-1). Exporter message: 5 type references at module scope have no
section-29 relation and are not exported. Combined differential bundle (exporter + pack +
`source_tree_observed` + two `runtime_route_observed` rows + `hop_succ(1..63→2..64)` /
`static_reaches_within` cross-check + 7 claims): digest
`1b61ce60009110b6cb923765502e235954b4bcd730d76083f8177b7893cbd299` (`scip_facts.bundle_digest`,
receipt-free; the plain `claims.ir.digest` of the same bundle, which still sees the file receipt
nested under `source_0`, is `77e157a175600a92e986722df69ddc6091dc9beabc0d42bcb81caa23a95588b6`), 276 facts,
29 rules, 70 relations; rules digest `3c7c80822404fc2ef221b91edd209db7ea8e73a40122a9f9764be20398a4d36c`;
rule pack file sha256 `141867ba8aac496db62e52a9b27b3e2be55881f8886249c7f80d4474e8dafe66` (the
bundle, Soufflé and kernel-report digests and the closure counts below were recomputed after the
duplicate-definition guard and again after the identity rebase, both recorded at the end of this
section; the reducer run at parent 7b1a65e had bundle `8b94be89…`, rules `128f22fb…`, pack
`87959f38…`, program `f54bd921…`, output `71637edc…`, evidence `4f24b0bb…`, report `4588948e…`,
368 rows / 399 provenance nodes and 22 `scip_duplicate_definition` rows; after the guard alone,
bundle `20e2ed9b…`, program `9832600f…`, output `0203dbdf…`, evidence `ad9b29a9…`, report
`39b9c5ff…`). Soufflé program digest `9832600f50fe8cea420d7587efd6ae9de7361e57d7f7e2135ba7805f18129b4e`, output digest `1595607d9ffe8e2cb082fe606cfcacadf48ee342b892312eb8dd9bd36b1a5e1f`, Soufflé evidence
digest `f2e02a84a8ac95aa1e47616eada231f0445d73683cb7240e4affe50f275746ab`, runtime `souffle-2.5`; kernel report canonical digest (equal for Python
and Soufflé) `3bfbbde544e081240e9bd079e35c09667dc98ae4dcc6d55639512d06928033b2`. Closure: 346 rows over all
relations (Python `derived_rows` 346, `provenance_nodes` 357, 0 unattributed facts, 0 discarded
alternatives); derived rows of note: `static_edge` 7, `static_root` 1, `static_reaches` 5
(GetJob → Fetch, Repo.Get, Repo.Write, DB.First, DB.Create), `static_reaches_eq` 6,
`static_reaches_within` 5 (hops 1/2/2/3/3), `static_route_handler` 1, `static_op_owner` 2,
`static_path_to_storage` 2, `static_capability_op` 2 = `static_capability` 2 =
{(`http:GET /jobs/{id}`, jobs, read), (`http:GET /jobs/{id}`, audit_logs, create)},
`static_index_current` 1, `scip_index_stale` 0, `runtime_route_without_static` 1
(`tenant-a`, `http:POST /jobs`, run-1), `static_route_authorized` 0,
`static_route_authorization_gap` 1, `scip_document_path` 5, `scip_definition_site_at` 27,
`scip_duplicate_definition` 0 (22 before the guard; see the record at the end of this section). Claims,
identical in both kernels:
`claim-cap-jobs-read` and `claim-cap-audit-create` supported (10 leaves each:
`scip_definition_site`, `scip_index`, `scip_index_tree`, 2× `scip_may_reference`, `scip_symbol`,
`route_handler_location`, `static_op_site`, `static_site_owner`, claim-time
`source_tree_observed`), `claim-reaches-repo-get` / `-repo-write` supported (5 leaves),
`claim-reaches-register` unresolved, `claim-all-routes-authorized` unresolved
(bounded-history-model; domain closed, member unproven), `claim-runtime-route-gap` refuted
(leaves `runtime:` + `static:` — `runtime_route_observed`, `index_describes_run`,
`static_route_inventory_closed`). Certificates from Python rows and from Soufflé rows are
identical for every conclusion (5 in go_app: steps 0/1/1/1/1, nodes 7/72/70/37/37; 25 across the
14 static cases), `recheck` accepts them against both closures with no unchecked negation, their
leaves equal the Python evaluator's support/refutation leaves for every `exists` claim in go_app,
`steps+1` equals both `static_reaches_within.hops` and `fixpoint.distances`, and a substituted
leaf, row, conclusion, rule or a negated row smuggled into the closure is rejected; a foreign
bundle digest is rejected; `max_depth=1` / `max_nodes=3` yield `truncated: true`.

**Cross-check against the resolver (stdlib path).** `map.call_edges` → `calls_graph(...,
language="go")` gives GetJob→Fetch, Register→{GetJob, handle}, Fetch→{Repo.Get, Repo.Write},
Repo.Get→DB.First, Repo.Write→DB.Create (7 edges); `direct` from the two op sites' owners;
`fixpoint.bind([api:GetJob])` = `{jobs: 2, audit_logs: 2}`, history `[0, 0, 2, 2]`;
`fixpoint.chain` = GetJob → Service.Fetch → Repo.Get / Repo.Write. Facets compared:
capabilities per root, reachable node set per root, edge set (after `scip_symbol_node`), hop
counts. Legitimate-differences table:

| class | reason | observed on go_app |
|---|---|---|
| `unrooted-endpoint` | Datalog keeps a symbol-level edge whose endpoint has no `scip_symbol_node` (local, parameter, unknown scheme); `calls_graph` cannot root it and drops it | none |
| `module-scope-reference` | a reference with no enclosing definition is `scip_module_scope_reference` on the Datalog side and a `caller=None` edge the fixpoint consumer skips | none |

Observed set = ∅ = `EXPECTED_DIFFERENCES`; the test asserts exact equality and that any other
shape is `differential-mismatch`. The function-as-value reference Register→GetJob is *not* a
difference on this path — both sides read the same callable reference occurrences — it would be
one against the tree-sitter AST call resolver, which is the skip-guarded, non-gate comparison.

**Gates (manifest command form, run by me from the worktree; exit codes and final unittest
lines).**

- `scip-differential` (`-p 'test_differential_static*.py'`, guarded against "skipped"): exit 0 —
  `Ran 17 tests in 17.396s` / `OK` / `rc=0`.
- `static-fixpoint-crosscheck` (`-p 'test_static_crosscheck*.py'`): exit 0 — `Ran 5 tests in
  0.223s` / `OK`.
- `static-adversarial` (`-p 'test_static_adversarial*.py'`, guarded against "skipped"): exit 0 —
  `Ran 5 tests in 19.209s` / `OK` / `rc=0`.
- `static-evidence-policy` (`-p 'test_static_evidence_policy*.py'` then `-p 'test_bounds*.py'`):
  exit 0 — `Ran 5 tests in 3.650s` / `OK` and `Ran 2 tests in 3.478s` / `OK`.
- `regression` (`-s tests -t .`): exit 0 — `Ran 1004 tests in 316.547s` / `OK (skipped=126)`
  (880 before this wave's merges plus the new suites; the skip count is the documented
  tool-dependent set plus the package-data install test below).
- live exporter, `-p 'test_scip_facts_live*.py'` (scip/scip-go in this devShell): exit 0 —
  `Ran 8 tests in 2.276s` / `OK`. One earlier run of this file and of `regression` failed on my
  own first version of the re-index test's identity-free comparison (it blanked the 12-character
  prefix before the full digest and did not re-key evidence ids); fixed and rerun as recorded.
- Not a gate, recorded as evidence of the fifth acceptance: the install layer of
  `test_static_schema_package_data.py` is skip-guarded because the devShell python has neither
  `pip` nor `setuptools`; on the host interpreter (`python3` 3.14.7, pip 26.2.1, setuptools
  84.0.0) `PYTHONPATH=src python3 -m unittest discover -s tests/claim_semantics -p
  'test_static_schema_package*.py' -t .` ran `pip install --no-deps --no-build-isolation
  --target <tmp> .` and loaded `schema_static_v1.json` from the installed tree through
  `importlib.resources`: `Ran 3 tests in 12.802s` / `OK`. Build byproducts (`build/`,
  `src/synapse_capabilities.egg-info`) were removed afterwards.

**Bounds evidence.** `test_bounds_static.py`: a 120-handler directed ring (605 facts, 14 400
`static_reaches` rows) with `ResourceLimits(max_derived_rows=10_000, max_provenance=40_000)` and
Soufflé `max_rows=10_000` yields `operational_failure == "resource-exhausted"` in both kernels
with no exception, and `reports_match` refuses the identical failure pair; a 6-handler ring
completes and matches (36 + 36 rows, claim supported). Limits were passed explicitly, not
raised.

**Remaining limits.**

- The census behind `scip_references_closed`/`static_reachability_closed` in the go_app bundle is
  a hand review of five files, so the negative verdict `claim-runtime-route-gap` rests on that
  review, not on tree-sitter; the `treesitter` extra is still not in the devShell.
- (Fixed, see the identity record below.) Binary index identity was per run: two `scip-go`
  indexings of the *same* copy produced different `index.scip` bytes (per-document `symbols`
  order, section 28), so `binary` bundles from separate runs differed in every evidence id and
  the live test could only compare them modulo identity.
- `scip_duplicate_definition` over-approximated (fixed, see the record below): on go_app it had 22
  rows, all `local N` symbols, and on a multi-file Go package it would also fire on the package
  symbol scip-go defines in every file, so `scip_references_closed` would have been withheld for
  nearly every package of a real service (target-go) and every negative claim left unresolved for a
  wrong reason.
- `certificate.py` handles linear recursion only (one SCC atom per body, which is all the pack
  has); a non-linear recursive rule raises `CertificateError`. `forall` claims are certified per
  domain member; the closure witness and domain rows the evaluator adds to a universal's support
  set are not part of the member certificates.
- `static_reaches_within`/`hop_succ` live only in the go_app differential bundle (63 facts), as
  this section intended; the pack has no arithmetic.
- The `scip-differential` and `static-adversarial` tests fail rather than skip without Soufflé;
  `test_static_corpus_evaluation`'s Soufflé class still skips (unchanged, outside the gate).
- Linux remains evaluation-only; every run above is aarch64-darwin.

### Duplicate-definition guard (2026-09-15, follow-up on branch `scip-datalog/fan-in`)

Both `scip_duplicate_definition` rules now join `scip_symbol(IX,Sym,_,Cat,_)` and require
`Cat != "other"` (positive join plus a constant comparison; the IR supports both in either
kernel and `validation.py` accepts it without a completeness witness, which a negated
`scip_symbol_unrooted(IX,Sym,"local")` guard would have needed). This is the exporter's own
predicate for withholding `scip_definitions_closed` / `scip_references_closed`
(`_symbol_category != "other"`, which already covered both the namespace and the `local`
class), so the derived relation and the witness policy agree; the pack README documents the
guard. Effects: go_app `scip_duplicate_definition` 22 → 0 rows (all 22 were `local 0..3`), the
five `scip_references_closed` witnesses and `static_reachability_closed` are unchanged, closure
368 → 346 rows, and the identities above were recomputed (the exported bundle digest
`53dcade7…` was unchanged by the guard because the exporter did not change; it changed with the
identity rebase below). Reviewed expectations: case 09's
verdicts are unchanged; `claim-duplicate`'s support and observed leaf sets gain the callable's
`scip_symbol:b87c0b7fbf06` row, because the guard is now part of the proof (the leaf-set change
the previous limit predicted). New variant `09-duplicate-definitions-package-symbol`: `GetJob`
defined once, the package symbol `api/` (`kind Package`, category `other`,
`scip_symbol_unrooted(non-node-descriptor)`) defined in `api/jobs.go:1` and
`api/jobs_legacy.go:1`, all six `scip_references_closed` witnesses and
`static_reachability_closed` present — `scip_duplicate_definition` is empty in both kernels,
`claim-duplicate` is unresolved with missing premise `scip_symbol`, the capability has no
`ambiguous-definition` discrepancy, and the negative gap claim resolves (`supported`) instead of
being withheld. Tests: `test_differential_static_reachability` asserts zero duplicate rows and
five reference witnesses in both kernels on the golden and that the only repeated definitions
are `local` or package symbols; `test_static_adversarial_both_engines` asserts the two callable
rows in 09 and the empty relation plus six witnesses in the variant, in both kernels;
`test_static_corpus_schema` asserts the guard's shape in both rules and the variant's table;
`test_scip_facts_export` asserts the gonest fixture's repeated definitions (`local 0..2` and the
`internal/jobs` package symbol) are all category `other` and withhold no witness. Certificates:
25 across the 14 static cases (was 23 across 13).

### Identity rebased onto the exported relations (2026-09-15, follow-up on `scip-datalog/fan-in`)

`scip_facts.export_bundle` now derives `index` from the content it exports ("Identity and
context" above holds the recipe): facts are assembled under a placeholder, `_Facts.identity()`
digests the sorted index-free rows of every non-compatibility primitive relation plus the
declared relation names under the prefix `static-relations-v1:`, `_Facts.rebase(index)` sets
every `index` column, recomputes every evidence id and rewrites `depends_on` (including the
`external:scip-occurrence:<index12>:…` references) through the old→new map, and only then is
the bundle materialized. `scip_index.digest_kind` is the literal `static-relations-v1`; the
file digest the runner hashed (`read_scip_index` is unchanged) is reported in
`ExportResult.messages` and carried as metadata `index_file_digest` / `index_file_digest_kind`,
which `bundle_digest` strips (`RECEIPT_METADATA_KEYS`) — the one thing that had to stay
receipt-only and outside the digest, because the requirement that two indexings of the same
tree yield the same bundle digest cannot hold if the differing file bytes are digested. The
frozen `schema_static_v1.json` is untouched; no `scip_index_receipt` relation was needed since
the receipt is provenance of the export run, not a fact any rule joins. Compatibility relations
(`index_describes_run`, `scip_index_comparable`) are excluded from the recipe on purpose: they
bind the index to a run or another index at claim time, and including them made the golden's
identity differ between the plain export and the differential bundle's export
(`describes_runs=(run-1,)`), which the first cut of this change exposed. go_app identity
`0360df877c99d8259f7f7f24cdca357afa64c4be9b27a739e1e78bb94c564320`, exported bundle digest
`585240159f4abfa9eb96a778abaa1bbba4ab95553f79e7163901f5f91ca1a49d`; the differential identities
above were recomputed. Tests: `test_scip_facts_export` asserts the metadata split (identity vs
receipt), the `scip_index` literal, that a permuted copy of the same normalized index exported
under a *different* fake `binary` receipt yields the same `index`, the same evidence id set and
the same `bundle_digest` while the plain IR digest differs only by the receipts, that the recipe
recomputes from the bundle's own rows, that changed content is a different identity, and that
the placeholder never leaks; `test_differential_static_reachability` pins the golden identity
and digest and repeats the shuffled export under a fake receipt; `test_scip_facts_live` replaces
the modulo-identity comparison with strict equality of `index`, evidence id set, facts, evidence
records and `bundle_digest` across two independent scip-go indexings of the same copy, with only
the receipt keys allowed to differ — result: two independent `scip-go` indexings of the same copy in the devShell gave equal `index`, evidence
id sets, facts, evidence records and `bundle_digest` (`test_scip_facts_live`: `Ran 8 tests` / `OK`, the
re-indexing test `ok`, not skipped). The synthetic static cases keep their
hand-written `IX` constants.

## 30. target-go static path pilot

Owner: `scip-target-go-pilot` (reducer; blocks when `CAPCOV_GO_FIXTURE_ROOT` is absent).

Target checkout (observed 2026-09-14): `/Users/dev/fg/target-go`, module
`git.internal.example/org/target-go`, `go 1.25.0` (pinned Go 1.27 with
`GOTOOLCHAIN=local` suffices), HEAD `7e339e0` with two dirty files, 53 `require` lines and a
`go.sum`, no `vendor/`, and nested `.worktrees/*` checkouts that must be excluded from the tree
digest, the index, and the slice (index a `git archive HEAD` copy). scip-go needs the module
cache (`GOFLAGS=-mod=mod`, `GOMODCACHE` recorded; network is allowed in `nix develop` and pinned
by `go.sum`; the sandboxed nix check is not used for target-go). Candidate path: a route in
`internal/httpserver/server.go` to `internal/pilot/{dispatch,notifications}.go`
(route → notification) or to SQL inside `internal/pilot`. Prior related work exists in the
`notification-capcov-bind` worktree; inspect it before choosing the route, do not copy code.

Acceptance a mocked index cannot satisfy: the test itself runs pinned scip-go (store path
asserted) on the archived copy; `index_digest` is the sha256 of the bytes it wrote;
`tool_info.name == "scip-go"`; the go.mod module path equals the package prefix of every rooted
symbol; target-go commit and dirty state are recorded in bundle metadata and here (no target-go source
is committed). The slice is the import closure of the chosen route's package within
`ExportLimits` (500 documents, 200k occurrences); exceeding it is `resource-exhausted`,
reported rather than narrowed silently. Route → SQL and route → notification
`static_capability_op` rows must be identical in both engines with replayable certificates;
where the tree-sitter route query does not cover target-go's router, the route handler is a
labelled assumption fact. The negative control (a route known not to reach the sender) is
`unresolved`, never `refuted`, because no call-graph completeness witness exists. A runtime
join happens only through `index_describes_run` when a retained target-go receipt exists;
otherwise the record says "static half only". Rooted-edge coverage below 0.9 or any
`deep-unresolved` on the route closure records the result as UNKNOWN.

If the fixture is absent the driver emits `task-blocked` and the record below is BLOCKED; the
go_app pilot is never described as target-go evidence.

### 2026-09-15 run record (task `scip-target-go-pilot`, worktree `capcov-target-go-pilot`, parent `64ee8bb`)

Result: **static half only, `supported`**. One route of target-go statically reaches a
`database/sql` write through one first-party hop, identically in both kernels, with replayable
certificates; the notification *sender* is not route-reachable in target-go's router, so the
route → notification half of the candidate path is the negative control, not the claim.

**Target checkout.** `/Users/dev/fg/target-go`, HEAD `7e339e07dbaafe7e606a20afe644623a1f58228f`,
`git status --porcelain` = `?? .worktrees/`, `?? tools/corejs-map/` (two untracked entries, no
modified tracked file; the run is labelled `dirty: true` and both entries are outside the
archive by construction). `go.mod`: module `git.internal.example/org/target-go`,
`go 1.25.0`. The indexed tree is `git archive --format=tar HEAD | tar -x` into
`<tmp>/capcov-target-go-pilot-*/target-go` (`claims/static/pilot.archive_head`): 120 `.go` files,
tree digest over `**/*.go` `67d035789074e6f61eb61694d8b11a67bc1011d456e23676ff31f01f62d370c6`.
The archive directory's basename is part of the identity through `scip_index.project_root =
file:///target-go` (section 29, item 3); a hand run of the same tree in a directory named
`fgarchive` produced identity `77d013fe…` for otherwise identical rows, so the test fixes the
basename. The `notification-capcov-bind` worktree under `target-go/.worktrees/` was inspected
(three commits on top of a loopback mailer; capcov plans and docs, no capcov code) and nothing
was copied.

**Toolchain (nix devShell, all store paths asserted by the test).** scip-go
`/nix/store/3inxss33qhklfr6416j0kwp4cbjkdlys-scip-go-0.2.7/bin/scip-go` (`0.2.7`), scip
`/nix/store/hckm2075va6x941b4lwncv8ls3p6ssr1-scip-0.9.0/bin/scip` (`v0.9.0`), go
`/nix/store/lz3qw52rpazqga73xgsqlj4qz1lgs4hg-go-1.27.0/bin/go` (`go1.27.0 darwin/arm64`,
`GOTOOLCHAIN=local`), Soufflé `/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5/bin/souffle`
(its `--version` prints an empty `Version:` line in this build; the store path is the pin),
python 3.12.14. Go environment: `GOFLAGS=-mod=mod`, `GOTOOLCHAIN=local`, `GOMODCACHE` and
`GOCACHE` under `$CAPCOV_GO_CACHE_ROOT` (default `$TMPDIR/capcov-target-go-pilot/`); for these runs
the session scratchpad's `gomodcache` (198 MB, populated from `go.sum` pins on the first run) and
`gocache` (323 MB). Indexing wall time: 89 s cold, 43 s with a warm module cache, 4–14 s with a
warm build cache; `read_scip_index` 0.3 s.

**Index receipts (not identity).** `sha256(index.scip)` differed on every indexing, as section
28 predicts: `15d71940…` (hand run), `c5b430f5…` (warm run 1), `5128b4ad…` (warm run 3),
`a3141c39c7f04f4e0a120896c12bf3b5c29e0b2a14bf6c01697b82b66496aa25` (cold run 1, the committed
receipt), `549e29ad…` (cold run 2). 2,328,103 bytes;
`tool_info.name == "scip-go"`, `tool_version 0.2.7`, arguments `--output index.scip`;
scip-go visited 28 packages; 105 documents, 28,284 occurrences. Standard-library symbols are
spelled under the go.mod directive (`scip-go gomod github.com/golang/go/src go1.25.0
\`database/sql\`/Tx#ExecContext().`), not the toolchain version. The 24 `.go` files without a
document (`static_file_unindexed` 24 in both kernels) are all `//go:build integration` or
test-harness `_test.go` files; the test asserts no production file is unindexed.

**Route, and why.** `internal/httpserver/server.go:47` mounts the app handler at `/`;
`cmd/target-go/main.go:181` passes `Runtime.Handler()` (`internal/pilot/runtime.go:160`), which
registers `GET /api/cloud/notification-unsubscribe/<action>-email` for `action ∈ {decrypt,
unsubscribe, subscribe}` at `internal/pilot/runtime.go:163` with `r.recipientLinks(action)`
(defined `internal/pilot/recipient_links.go:13`), `POST /inquire/` with `Runtime.cloudSave`,
and two closures (`GET`/`DELETE /api/cloud/project/{project}/issues/…`) whose bodies SCIP
attributes to `Handler()` itself. `recipientLinks` is the only route that touches the
notification subsystem: it calls `legacyissues.ChangeSubscription(ctx, r.DB, …)`
(`internal/legacyissues/subscriptions.go:31`), which opens a transaction (`db.BeginTx`, line 48)
and issues `tx.ExecContext` writes (lines 54–78) to `notification_unsubscribed` and
`go_notification_confirmation`. The mail sender (`legacyissues.SendDueDigests`,
`Mailer.Send` over smtp/SES/loopback) is reached only from the worker loop
`Runtime.RunNotifications` (`internal/pilot/notifications.go`), never from a route, so
route → notification is not derivable from this router and is used as the negative control.
Declared surface: `http:GET /api/cloud/notification-unsubscribe/subscribe-email` (one of the
three concrete patterns; all three share the closure `recipientLinks` returns). Handler symbol:
`scip-go gomod git.internal.example/org/target-go . \`git.internal.example/org/target-go/internal/pilot\`/Runtime#recipientLinks().`

**Handler binding is a labelled assumption.** The go_app tree-sitter route query does not
match `ServeMux.HandleFunc` on a returned closure, and tree-sitter is not in the devShell, so
no `route_site` / `route_handler_location` row is emitted (the test asserts their absence and
the absence of `static_op_site`). Instead the claim-time bundle declares
`route_handler_symbol__accepted(index, surface, symbol)` (modality `assumption`, binding
static, primitive, context `index`; `Evidence.kind = "assumption"`, source `human-declared from
router source: internal/pilot/runtime.go:163 registers GET /api/cloud/notification-unsubscribe/<action>-email -> r.recipientLinks(action); handler defined at internal/pilot/recipient_links.go:13; app mounted at internal/httpserver/server.go:47 and wired at cmd/target-go/main.go:181`,
evidence id `static:0759ccef8fbb:route_handler_symbol__accepted:517419cba2c0`, depending on
the `scip_index` row) and one rule, `static_route_handler_from_accepted_symbol`:
`static_route_handler(IX,S,Sym) :- route_handler_symbol__accepted(IX,S,Sym),
scip_symbol(IX,Sym,_,"callable",_)`. The pack is unchanged (it is outside this task's write
set); the rule is added through `combine`, and the join with the index's own `scip_symbol` row
means a misdeclared name yields `unresolved`, never a path. The test re-reads the five archived
lines it names (registration, definition, mount, wiring, SQL site) so a drift in target-go fails
the binding loudly. This is the "assumption fact" option of the task, not the "grep of
httpserver registration" option.

**Op sites.** target-go does not use gorm: SQL goes through `database/sql` (`*sql.DB`, `*sql.Tx`,
driver `github.com/go-sql-driver/mysql`) and the recognizer has no `static_op_site` producer
for it, so the claims are `static_reaches(index, handler, sink)` for named sinks rather than
`static_capability_op`. The section's "route → SQL and route → notification
`static_capability_op` rows" acceptance is therefore met as symbol reachability, which is
recorded here as a decision rather than as a recognizer result it is not.

**Slice.** Import closure of `internal/pilot` computed from the packages of the first-party
symbols each document references (`pilot.package_closure`; scip-go 0.2.7 emits no `Import`
symbol roles, and a cross-package reference is only possible through an import): 9 packages —
`internal/{issues, legacyfiles, legacyflags, legacyissues, legacypermissions, legacyprojects,
legacysessions, phpcache, pilot}` — over 11 package edges; 54 documents (46 test documents
excluded: `_test.go` files and scip-go's `pkg.test` / `pkg_test` packages), 15,392 occurrences;
scope `document_set`, profile `slice`; `ExportLimits(500, 200_000, 100_000)`, none tripped.
Export `complete` in 3–6 s: 20,617 facts — `scip_read_site` 11,591, `scip_definition_site` 2,561,
`scip_symbol` 2,508, `scip_may_reference` 1,714, `scip_symbol_node` 935, `scip_type_reference`
667, `scip_enclosing` 165, `static_source_file` 120, `scip_symbol_unrooted` 115, `scip_document`
96 (the index's 105 documents minus the nine out-of-tree `_testmain.go` documents; see *Identity
defect* below), `scip_definitions_closed` 54, `static_scope` 54, `scip_module_scope_reference` 23,
`scip_relationship` 8 (scip-go does emit relationships on target-go), one each of `scip_index`,
`scip_index_tree`, `scip_index_commit`, `static_language_covered`, `scip_documents_closed`,
`static_scope_closed`; no `static_scope_leak`, so the closure is closed. 105 type references at
module scope have no section-29 relation and are not exported (exporter message). No census
(`census_available: false`): no `scip_references_closed`, no `static_reachability_closed`.

**Identities.** Index identity (`static-relations-v1`)
`0759ccef8fbb6024b7d215c8adc3019e93bfd277e112090acaa1304813323a3b`; exported bundle digest
(receipt-free) `89d2988a92a4f5e17d9eea77002a07b44768c875ce071660c40245d36771e4f0`; combined
bundle (exporter + pack + assumption bundle + claim-time `source_tree_observed` + three claims)
`scip_facts.bundle_digest` `413014e24facd45783b79eb3905bafb49773c853ea137e6aee71658ff089e253`,
20,619 facts, 28 rules, 69 relations, rules digest
`1490a850b07272f5c53a750d7cbc8375fb3538cbd70b03e333c3b87a607160ec`. The plain IR digest of the
combined bundle differs per run (it sees the index-file receipt; cold run 1 `95ec166e…`), which
the pin test asserts. Two cold-cache runs from fresh `nix develop` shells
(`/tmp/nix-shell.pkTq7q` and `/tmp/nix-shell.ThRZ5i`, each with its own empty `GOMODCACHE` and
`GOCACHE` under the default cache root, no `CAPCOV_GO_CACHE_ROOT`) reproduced the identity, the
exported digest, every row count, the out-of-tree receipt, the combined digest, the kernel
digest and the certificate derivations. The three earlier warm runs (identity `153c788961ef…`,
superseded) shared one scratch build cache and so could not have exposed the defect below;
"three independent indexings" was true of the indexer's emission order only, not of the cache.

**Kernel agreement.** `compare` matched: Python and Soufflé canonical report digest
`06daf07b4a6dd63038390e2c055b152856bc3f07b83b12a7dd3e62adb4d4ff16`, no operational failure, no
shrink; 25–80 s per run (190 s in the hand run). Derived rows: `static_edge` 1,095,
`static_root` 1, `static_route_handler` 1, `static_reaches` 47 (the handler's closure: 48
symbols including the root), `static_index_current` 1, `scip_index_stale` 0,
`scip_duplicate_definition` 0, `static_scope_closed` 1, `static_file_unindexed` 24,
`scip_references_closed` 0, `static_reachability_closed` 0.

**Claims and the derived path.** `claim-route-reaches-change-subscription`
(`static_reaches(IX, Runtime#recipientLinks()., legacyissues/ChangeSubscription().)`) —
supported, complete, derivational in both kernels; certificate steps 0, 13 nodes, 3 leaves.
`claim-route-reaches-sql-tx-exec` (`… → \`database/sql\`/Tx#ExecContext().`) — supported in
both; certificate steps 1, 173 nodes, 4 leaves; the symbol chain is
`Runtime#recipientLinks()` → `legacyissues/ChangeSubscription()` → `database/sql/Tx#ExecContext()`
(the closure also holds `DB#BeginTx()`, `Tx#Commit()`, `Tx#Rollback()`,
`Result#RowsAffected()`). Certificates extracted from the Python rows and from the Soufflé rows
are identical, `recheck` accepts both against both closures, every leaf is a `scip:`/`static:`
id and the assumption leaf is among them: the first-party claim rests on
`scip:0759ccef8fbb:scip_may_reference:795036b39318` (the `recipientLinks` → `ChangeSubscription`
reference), `scip:0759ccef8fbb:scip_symbol:ac84fe7dafb3` (the handler is a callable) and the
assumption; the SQL claim adds `scip:0759ccef8fbb:scip_may_reference:711c00868b3b`
(`ChangeSubscription` → `Tx#ExecContext`). Derivation digests (certificate minus its
`bundle_digest`, run-independent): `267bc470a769…` and `02bd7b2203e9…`; the full certificates
for cold run 1 are committed as
`tests/claim_semantics/target_go/artifacts/certificate-<claim>.json` with the receipt
`receipt.json` (symbol names, paths, lines, digests and counts only — no target-go source).
Negative control `control-route-reaches-send-due-digests`
(`… → legacyissues/SendDueDigests().`) — `unresolved`, operational `complete`, missing
premise the claim row itself, in both kernels; it can never be `refuted` here because
`static_reachability_closed` and `scip_references_closed` are absent (no call-graph
completeness witness), which the test asserts.

**Coverage and outcome.** Rooted edges / resolved edges = 1,714 / 1,714 = 1.0 on the slice
(every `scip_may_reference` endpoint has a `scip_symbol_node`); 115 unrooted symbols in the
slice (104 `local`, 11 `non-node-descriptor`), none on the route closure; 0 `deep-unresolved`
(no tree-sitter side). Decision rule (`pilot.outcome`): `supported`. Every rooted symbol
*defined* in the index carries the module path as its package prefix (asserted); referenced
standard-library and third-party symbols are rooted under their own packages and are counted
in the coverage ratio, not against the module-prefix check.

**Runtime join.** None. No retained target-go run receipt exists in this repository, so no
`index_describes_run` row was declared and none was fabricated; the record is static half
only.

**Gates.** `target-go-static-pilot` (manifest command form, run from the worktree with
`CAPCOV_GO_FIXTURE_ROOT=/Users/dev/fg/target-go` and `CAPCOV_GO_CACHE_ROOT` pointing at the
scratch caches above): first run failed on three test-side expectations (no committed receipt
yet; the certificate edge chain is emitted root-to-sink; bundle metadata `scope` is a
`_FrozenMap`), corrected and rerun; the pin then failed on the per-run certificate
`bundle_digest`, corrected to compare the derivation only; warm run `Ran 9 tests in 47.315s`
/ `OK` / `rc=0`. That state (commit `939fb57`) failed the coordinator's cold reruns — see
*Identity defect* below. After the fix: cold run 2, the exact manifest command from a fresh
shell with the default (cold) cache root, `Ran 9 tests in 195.320s` / `OK` / `rc=0`, not
skipped, pin satisfied against cold run 1's committed receipt. The closing warm rerun and the
full regression are recorded in the last paragraph of this record.

**Identity defect found by cold reruns, and the fix.** The coordinator reran the manifest gate
from two fresh `nix develop` shells (cold default cache roots) and got identities
`bf16337e57e1…` and `1a629d8fd97a…` against the committed `153c788961ef…` — same slice, same
fact count, same coverage, three identities. Root cause, established by diffing the exported
primitive rows (index column stripped) of two cold exports into two fresh cache roots
(identities `72afaa0c…` vs `d6c6fecc…`, `scratchpad/coldexport.py`): exactly one relation
differed, `scip_document`, in 9 of its 105 rows, whose `path` values were
`../../../<host path>/gocache/<hh>/<hash>-d`. Those nine documents are Go's generated
`_testmain.go` for the nine `<pkg>.test` packages scip-go loads
(`internal/{httpserver,issues,legacyfiles,legacyissues,legacysessions,phpcache,pilot}.test`,
`test-harness/{notification…,policy}.test`; each defines `package main` and imports `os` and
`testing`), read out of `GOCACHE` and spelled relative to the project root. Their
content-addressed basenames (`0ff5b09e…-d`, `4a6eb265…-d`, …) and occurrence counts were
identical in both runs; only the cache location differed. No other relation and no other
metadata value differed, so this is an exporter fact leaking a per-run path — not
module-resolution nondeterminism (the module basis from `go.sum` was the same in both runs).
Fix, in `scip_facts.export_bundle`: a document whose path is absolute or climbs out of the
project root is not a document of the indexed tree; it contributes to no fact (the identity
rows in particular) and is recorded in metadata `out_of_tree_documents` as
`{basename, occurrence_count}`, a receipt excluded from `bundle_digest`
(`RECEIPT_METADATA_KEYS`), with an exporter message naming the count. `scip_documents_closed`
therefore reads "every document of the tree is exported", the only truthful reading. The pilot
test now asserts one out-of-tree document per `.test` package in the index, that no
`scip_document` path escapes the tree, that no fact or metadata names either Go cache, and
pins the identity for this HEAD in code (`PINNED_IDENTITY`) as well as against the committed
receipt. The exporter's own 48 tests and the 66 static-rules tests pass unchanged.

**Limits.** (1) Static half only; the SQL sink is a standard-library method, not an entity/verb
op site, so nothing here names a table. (2) The handler binding is an assumption a human read
from the router; the index attests only that a callable of that name is defined at the
declared line. (3) The closure comes from references, not `Import` roles. (4) Closures inside
`Runtime.Handler()` attribute to `Handler()`, so a claim about those two routes would root at
`Handler()`. (5) No census, so every negative stays `unresolved`. (6) The identity binds the
archive basename through `project_root`. (7) During this task the host disk hit `ENOSPC`
mid-run (not caused by the pilot's ~520 MB of Go caches; it cleared without intervention); the
run record above is from the runs that completed. (8) The identity pin is for HEAD `7e339e07`
under scip-go 0.2.7 / go 1.27.0; a run on any other HEAD or toolchain compares against nothing
and prints that it did not.

**Closing verification (after the fix).** Warm rerun of the manifest gate against the scratch
caches (`CAPCOV_GO_CACHE_ROOT` set) with the committed cold-run-1 receipt and `PINNED_IDENTITY`
in place: `Ran 9 tests in 52.357s` / `OK` / `rc=0`, identity `0759ccef8fbb…`, kernel digest
`06daf07b…` — the same values as both cold runs. Full regression (`discover -s tests -t .` in
the devShell with `CAPCOV_GO_FIXTURE_ROOT` and `CAPCOV_GO_CACHE_ROOT`, so the pilot runs inside
it): `Ran 1017 tests in 124.515s` / `OK (skipped=126)` / `rc=0`; the skip set is the documented
tool-dependent one, unchanged. Cold-run wall times: index 100–106 s, compare 50–80 s, 167–216 s
total per run.

### 2026-09-15 `datalog-kernel-closure` wave: fan-out succeeded, reducer exhausted

Fan-out (`7b5e8ab`): `differential-closure` and `kernel-closure` each passed their gate in an
isolated worktree on the first attempt (patches 16 KB and 28 KB). Reducer
`kernel-closure-integrate`: five review rounds across four runs (`065cd44`, `1756f71`,
`dabd430`, and the exhausted run on `dabd430`), every round green on all three driver gates,
every round refused by both reviewers. Three of the refusals included plan-level defects the
human corrected between runs (an acceptance that demanded the not-yet-existing checkpoint hash;
one that demanded agreement from bundles designed to trip a fail-closed boundary; one that
demanded quoting gate outputs the driver produces after the implementer returns); each
correction stopped the run during scouts, was committed as a `manifest-checkpoint`, and reset
the human-aborted attempt with its reason journaled. Code findings closed during the wave:
`forall` context-column grounding; late-shorter-proof cross-kernel coverage; `_FrozenMap`
canonical ordering; environment-scoped `excludes_evidence`; typed compatibility joins;
adversarial-bundle matrix with a documented fail-closed report contract; `RecursionError` at
both kernel boundaries with an explicit 256-rule dependency bound; recursive malformed-IR
validation; compatibility dimension identity.

Findings still open after the final round (`run-stopped: attempt limit reached` at 13:10 UTC):
`DiagnosticRule` scalar fields (`when_missing`, `required`, `message`) are not type-checked at
ingestion, so `"when_missing":"false"` is truthy; `bundle_from_json` does not convert
`RecursionError` on deeply nested JSON into `invalid-input`; five malformed-nested-`Bundle`
adversaries (constructed through the dataclass API, not raw JSON) are exercised at each kernel
boundary but not through `compare()`; `output._joint_environments` discards a failed mapping
constraint when the same evidence is also relevant through a diagnostic or proof path.

The final tree (13 changed files, about 2,100 lines over the previous WIP commit) is committed
as a second unapproved WIP and journaled as a `human-checkpoint`. Driver gate results for the
last attempt: `differential-tests` ok (45.8 s), `kernel-tests` ok (6.6 s), `regression` ok
(55.0 s), Soufflé at `/nix/store/hjf84h92h4ynbbn9sg9q1biyr25r617i-souffle-2.5`. Decision on how
to proceed is deferred to the driver owner; the options recorded are: continue hardening in a
further narrow task; restrict the fail-closed contract to the raw-ingestion boundary
(`bundle_from_json`) and treat programmatic construction of malformed dataclasses as out of
contract, then close the three remaining concrete defects in one narrow task; or advance to
`scip-toolchain` with the kernel as-is and the open findings carried by `datalog-certificates`.

### 2026-09-15 duration analysis and Codex backend trial

Driver log accounting for the 2026-09-15 runs (04:16–13:10 UTC, about 9 h wall): 15 implementer
runs averaging 20.8 min (311 min), 32 scout runs averaging 5.4 min (174 min, two in parallel),
26 reviewer runs averaging 5.3 min (137 min), 43 gate runs totalling 35 min, plus 22 min of
parallel-worker time. Busy time 11.3 h, about 9.9 h wall after scout parallelism. Cost drivers,
in order: (1) every attempt re-runs two scouts and two reviewers even when the tree changed by a
few hundred lines, so a review round costs about 45–60 min regardless of patch size; (2) 13
review rounds, of which 3 were spent on acceptance statements the human wrote that no implementer
could satisfy and 2 on infrastructure (a 30-minute timeout, a collected devShell); (3) 8 human
interventions each requiring a stop, a commit, a `manifest-checkpoint`, and a relaunch; (4) the
reviewers examine the whole kernel each round, so a large task accrues findings faster than one
implementer can close them. The remedies already applied: 90-minute agent budget, GC-rooted
devShell, detached launch, satisfiable acceptance wording, task splitting. Not yet applied:
reusing scout output across attempts, scoping reviewers to the patch, and capping review
rounds per task in the manifest.

Codex backend trial: the driver gained `CAPCOV_AGENT_BACKEND=codex` (`codex exec` with
`--ephemeral --json -o`, prompt on stdin, read-only sandbox for scouts and reviewers, unsandboxed
writer as with Pi). The exhausted `kernel-closure-integrate` is retired and replaced by
`kernel-closure-finalize`, whose acceptance adds the four findings left open, so the comparison
is: same tree, same gates, same reviewer lenses, different agent runtime. Codex results are
labelled `backend=codex` on every `agent-start` line in `driver.log`.

### 2026-09-15 runtime join follow-up

The target-go pilot now accepts an optional retained runtime receipt via
`CAPCOV_TARGET_GO_RUNTIME_RECEIPT`. The producer is the existing disposable
`tools/check_subscription_links.py` path in target-go, extended at candidate
`bc404ec84d576220993777cade81c6e238fe19e8`. The successful receipt records run
`claims-runtime-20260915-02`, tenant `tenant-a`, the concrete subscribe surface,
HTTP 200, a run-bound request id, the final SQL state (no unsubscribe row and one
cancelled confirmation), and zero owned resources after cleanup.

The pilot validates that receipt before admitting `runtime_route_observed`, asks
the SCIP exporter to emit `index_describes_run(index, run)`, and derives
`runtime_route_observed_on_index` in both Python and Souffle. The two kernels
agreed and all 10 pilot tests passed in 178.828 seconds. The mixed certificate
contains runtime receipt, `scip_index`, and `index_describes_run` leaves. The
existing independent static certificate proves the handler reaches
`database/sql.Tx.ExecContext`. These are complementary certificates, not a
single claim that runtime tracing observed the call stack or SQL statement.

The first attempted rule tried to introduce a new runtime SQL relation. Bundle
validation rejected it because the frozen compatibility witness does not
authorize that producer/target pair. The final rule stays within the declared
`index_describes_run` target set; this fail-closed result is retained as a design
constraint for the producer-authority work.

Reproduction from `packages/capabilities`:

```sh
CAPCOV_GO_FIXTURE_ROOT=/Users/dev/fg/.worktrees/target-go-capcov-claims-runtime \
CAPCOV_GO_CACHE_ROOT=/Users/dev/projects/.capcov-go-cache \
CAPCOV_TARGET_GO_RUNTIME_RECEIPT="$PWD/tests/claim_semantics/target_go/artifacts/runtime-recipient-route.json" \
nix develop --no-update-lock-file --command bash -lc \
  'export PYTHONPATH="$PWD/src"; python -m unittest discover -s tests/claim_semantics -p "test_target_go_static*.py" -t .'
```

## 31. Performance: evaluator access paths and artifact caching

Two independent efforts on 2026-09-15, stacked on branch `codex/capcov-performance-cas` (`0d7d514`):

- `0d7d514` (Codex, isolated worktree): per-column value indexes in the Python evaluator with a
  full-scan fallback and parity tests; a filesystem content-addressed store (`capcov/cas.py`:
  SHA-256 objects, integrity checks, atomic publication, canonical parent-linked snapshots,
  staged materialization); an opt-in Soufflé translation/facts cache keyed by bundle digest,
  requested outputs, executable identity, and limits. Result caching stays disabled because
  runtime inputs are not fully identifiable by content. Validated with 49 selected tests; real
  Soufflé was unavailable in that environment.
- `perf/claims-evaluator-fixpoint` (this checkpoint): memoised proof-tree keys on `Derivation`
  (`leaves`, `depth`, `signature`, `choice_key`, `path_key`), a per-relation cached canonical
  row order, a signature fast path in `_Engine.add`, and a semi-naive fixed point driven by
  rows whose retained proofs or candidate set changed (not only new rows). A derivation is a
  pure function of its children's retained proofs and candidate counts, so re-deriving from
  unchanged inputs cannot change the outcome; the fixed point therefore reaches the same result
  as the previous full-pass loop while doing work proportional to what changed. Two counter
  assertions in `test_evaluator_index.py` were updated because non-recursive rules now match in
  one complete pass instead of two.

Host Python 3.14 measurements (`packages/capabilities/benchmarks/claims_evaluator_bench.py`,
tracemalloc off for the before/after pairs; before = `9c603a0`):

| case | size | before | after |
|---|---|---|---|
| one-hop projection | 5,000 facts | 3.8 s | 0.31 s |
| equijoin | 1,000 rows/side | 85 s | 0.13 s |
| chain closure | 50 nodes (1,325 rows) | 116 s | 0.04 s |
| chain closure | 200 nodes (20,300 rows) | 226 s (indexed only) | 0.72 s |

A 400-node chain reports `resource-exhausted` (proof depth 400 exceeds the recursion guard);
section 29 bounds static witnesses at 64 hops, so this is outside the intended envelope and is a
named result, not a crash. Soufflé wrapper performance remains UNKNOWN until measured with the
pinned binary; the differential shrinker's 200-execution bound is unchanged. Not done from the
review's list: incremental file-manifest caching for `tree_sha256`, copy-on-write snapshot
materialization for the Go consumer (lives in target-synapse), and threading one provenance object
through a qualification.

### 2026-09-15 base refresh: merge of upstream `main` (`bdb67b8`)

Upstream `millstonehq/synapse` main advanced from the recorded integration base `d1550e4` to
`bdb67b8` (PR #47 plugin-adapter seam; PR #48 feature map: `capcov features map|report|reconcile`
with Harvey glyphs, feature outcome evidence reconciliation, the HAR probe, the Laravel route
reader with service-provider mounts, OpenAPI collision boundaries, mount keys). This branch
merges it in full. The only conflicts were `flake.nix` and `flake.lock`: upstream added a minimal
flake (`go jq python312 uv git`, nixpkgs `ef34387d`, unstable); the experiment's Stage 0 flake
is a superset (same tools plus hyperfine, souffle, shen-go, the sandboxed checks, and the
`bash -lc` PATH wrapper) pinned at nixpkgs `34ab9907`, to which every recorded Stage 0 result
binds. The experiment flake is kept; upstream's `.envrc` (`use flake`) therefore loads it.
Full regression on the merged tree is recorded below when it completes.

### 2026-09-15 target-go causal runtime trace follow-up

The recipient-link fixture now emits schema `capcov-target-go-runtime-route/v2` from target-go commit
`01fe913`: one request identity is preserved across route entry, entry into `ChangeSubscription`,
two successful transaction SQL operations, commit and route completion. CapCov imports those as
typed runtime facts, rejects evidence whose producer class is not `target-go-runtime-trace-v2`, joins
the run to the exact SCIP index, and derives `runtime_route_reaches_sql_on_index` in Python and
Soufflé. The real fixture gate passed 10 tests in 302.9 seconds (index 19.3 s, differential compare
185.8 s); the validation/export policy gate passed 68 tests. Missing or mismatched causal
identities remain unresolved rather than being inferred from terminal database state.

Soufflé can become the sole derivation engine after the deferred ground checker independently
validates its certificates. Python remains in the trusted path today for receipt parsing, schema
and producer-authority validation, claim folding and certificate construction; deleting that code
before the checker exists would reduce, not improve, independent assurance.

### 2026-09-15 close-out of `datalog-kernel-closure` and integration of the SCIP → Datalog wave

`kernel-closure-finalize` ran three Codex-backed attempts on the merged tree (`8adc197`; driver
gates green on every attempt — final attempt: differential 44.8 s, kernel 7.5 s, regression
54.0 s — and both reviewers refused each round). The refusals narrowed to wire-format ambiguity
at the ingestion boundary: round 1, `metadata` and claim/evidence `context` of the wrong JSON
type leaked `AttributeError`; round 2, evidence accepting `atom` and `relation`/`terms`
simultaneously, and the `{"values": …}` context wrapper colliding with a legal context key;
round 3, freeze checks that discarded the frozen result, and the flattened context encoding
silently reinterpreting pre-existing schema-v1 bytes. The attempt-3 tree was committed as WIP
(`941ecc5`) and the two round-3 findings were closed by hand in `8a54a04`: values must already
be frozen (not merely freezable), and the retired `{"values": [[k, v], …]}` wrapper is rejected
by name rather than reinterpreted, with a genuine `values` key of any other shape still
accepted. Full suite on that tree: 896 tests OK under nix. Remaining kernel scope is carried by
`datalog-certificates` per the section 27 ownership table; no further reset of this task.

The SCIP → Datalog wave was delivered by four subagents in isolated worktrees and merged as
`1a0ed69`: `scip-toolchain` (`2f3b4d8`; scip 0.9.0 and scip-go 0.2.7 pinned, sandboxed
`scip-go-index-smoke` check, go_app golden `0b5183fc…`, Soufflé in the regression check),
`scip-fact-export` (`98e695f`; opt-in retention, pure exporter, index provenance),
`static-rule-pack` (`e6c1845`; 22 derived relations, 27 rules, 13 reviewed cases, Python and
Soufflé agree on all 30 claims), and the reducer (`821ae51`, `d21b144`; certificates identical
across engines for 28 conclusions, fixpoint cross-check with zero differences, wheel packaging,
`mixed-binding-join` validator fix, canonical `project_root`), followed by `a66bafa`
(`scip_duplicate_definition` guarded by symbol category: 22 bogus go_app rows → 0) and
`64ee8bb` (static index identity derived from the exported relations; two independent scip-go
indexings of the same copy now produce identical index, evidence ids, and bundle digest, with
the index-file digest kept only as a run receipt). Each deliverable's gates were rerun by the
integrator before merging. The target-go static pilot (section 30) is in progress on that base.

#### 2026-09-15 target-go pilot integrated into the experiment line (`7e8b391`)

`agent/scip-target-go-pilot` (`939fb57`, `3630c84`) merged without conflicts. On the merged tree the
pilot gate failed one pin: `export.exported_bundle_digest` `89d2988a…` → `65f82965…`, with the
combined bundle digest, the plain IR digest, and the two certificate hashes (which bind to the
exact bundle) moving with it. Every run-independent value was equal: the static identity
`0759ccef…`, all relation row counts, the kernel report digest `06daf07b…` (Python = Soufflé),
coverage, and the certificate derivations. Cause, as for the go_app pin in section 29: the
kernel line (`8a54a04`) serialises Context as a flat object, which changes each evidence
record's canonical bytes; the pilot worktree predates that line. The committed artifacts
(`receipt.json`, two certificates) are replaced by the merged-tree run's, so the pinned bundle
digests describe the tree they live in; the identity pin is unchanged. Merged-tree gates
(integrator's runs): full regression 1029 tests with that single failure before the re-pin;
static differential 18, adversarial 6, cross-check 5, live exporter 8 all OK; pilot gate 9 OK
after the re-pin.

### 2026-09-15 base refresh: merge of upstream `main` (`1b6a47a`, PR #49)

PR #49 (`perf(capcov): reuse incremental source snapshots`, merged upstream by the repository
owner) replaces `artifacts.tree_sha256` with a metadata-keyed incremental snapshot cache
(`snapshot_tree`, `SourceSnapshot`, `language_pattern`, `normalise_patterns`, `CAPCOV_NO_CACHE`)
and threads a carried `CAPCOV_SOURCE_PROVENANCE` through `observe`. It is the production-facing
half of the section 31 performance review (repeated whole-tree hashing); the experiment's
evaluator, Soufflé cache, and content-addressed store remain experiment-internal. Merged as
`e80003f`. Conflicts: `artifacts.py` — upstream taken wholesale and the SCIP exporter's
`patterns_for` / `tree_manifest` / `manifest_sha256` rebuilt on `snapshot_tree` so a tree is
walked once and the digest formula is shared (verified equal on go_app: manifest digest ==
`tree_sha256`, 5 files); `PLUGINS.md`, `har_probe.py`, and four test files — upstream versions
(this line had not modified them), the observe-env back-compat test adopting upstream's contract
(additions over the pinned `7801732` baseline are exactly the nonce and the carried provenance).
Integrator's runs on `e80003f`: exporter 48, static differential 18, static corpus 18,
`test_cli_engine` + `test_snapshot_performance` 43 (1 skip), full regression `Ran 1053 tests`,
`OK (skipped=135)`. The target-go pilot gate on this tree is recorded below when it completes; one
attempt was killed by host memory pressure from an unrelated qualification job.
target-go pilot gate on `e80003f`/`7c781e4` (integrator's rerun, PR #49 artifacts in place): `Ran 9 tests in 221.1s`, `OK`, not skipped; identity `0759ccef…` unchanged.

### 2026-09-15 replay judge (shen1 session) integrated; Shen runtime aligned

The `shen1` session built an executable domain model of the candidate in Shen (on the
candidate's model branch) whose admissible-state sets, effect lists, and declared
write-sets become `model_admissible`, `model_effect`, `model_writes` facts with honest
completeness witnesses, consumed by a PHP-vs-Go-vs-model binlog replay runner. On the capcov
side that work is `experiment/replay-claims` (pushed to the pyrex41 fork at `e373bb3`, off this
line's `3e8a5f8`): `claims/replay/{schema_replay_v1.json, replay_facts.py}` (receipt directory →
strict schema-v1 bundle, `Evidence.source` set from a per-file producer label or the schema's
producer classes), the rule pack `experiments/claim-semantics/replay/rules-replay-v1.json`
(26 primitives, 34 derived, 36 rules; every witness owned by a producer class; qualification
gated on the pack's own contradiction detectors), a reviewed replay corpus (cases 00–11, two
rejected), certificates identical from both kernels, and three manifest gates. Two of its
commits touch `validation.py` and were cherry-picked first (`6605d44` evidence-producer
enforcement, `ebb5897` unconditional fact attribution); the branch was then merged as `9553a1a`
without conflicts. `schema_replay_v1.json` is **v1-draft** until the target-go `export-facts` runner
and the model host produce a real receipt; a re-merge follows that SHA. Layering agreed between
the sessions: shen1's Shen is a fact producer below the IR; Stage D (this line) is the rule
workbench above it; both consume the same rule-pack wire form and the frozen
`capcov-static-certificate-v1` shape with `recheck` unchanged. shen1 runs shen-go `c12933d`
through bifrost; the flake was repinned to the same revision (`643491c`), with the
Shen-Backpressure crash warning and this line's 300-call probe recorded above section 15. Merged-tree gates (integrator's runs on `9553a1a`): replay 73, validation-producer 4, static differential 18, static adversarial 6, exporter 48, manifest seam tests, and the full regression recorded in the log above this line.

### 2026-09-15 target-go runtime join integrated (second fork); producer-authority collision resolved

Upstream PR #50's head branch lives in `pyrex41/synapse-capcov` (GitHub's registered fork of
`millstonehq/synapse`; the `pyrex41/synapse` repository used earlier for "fork main" has an
unrelated re-rooted history). Another agent (`codex/fork-souffle-trial`) continued on that PR
branch from `3e8a5f8` and pushed `507ef19`: an optional retained target-go runtime receipt
(`CAPCOV_TARGET_GO_RUNTIME_RECEIPT`, schema `capcov-target-go-runtime-route/v2`, produced by target-go's
disposable `tools/check_subscription_links.py` path at candidate `01fe913`) whose trace preserves
one request identity across route entry, `ChangeSubscription`, two transaction SQL operations,
commit, and completion; `index_describes_run(index, run)` emitted by the exporter; and
`runtime_route_reaches_sql_on_index` derived in both kernels — the runtime join that section 30
had left open, with static and runtime certificates kept complementary rather than fused. Also:
CI runs the differential suite with Soufflé, and the Soufflé timeout test is made deterministic.
Merged into this line as `5c22a89` without conflicts.

Collision: `507ef19` had also added a `producer-authority` validation issue requiring
`Evidence.kind` to be one of the relation's `producer_classes`, and labelled its runtime
evidence with `kind="target-go-runtime-trace-v2"`. On the merged tree that rejected every replay
record (kind `fact`): the replay suite fell to 19 failures and 32 errors, and conversely the
runtime evidence (source first token `target-go`) would have failed the cherry-picked
`evidence-producer` check. One contract wins, the plan's (section 13): producer identity is the
first token of `Evidence.source`; `Evidence.kind` stays `fact`/`assumption`/`completeness`/
`compatibility`. The kind-based check is removed, the runtime evidence is relabelled
(`source="target-go-runtime-trace-v2 receipt sha256:…"`, default kind), and the section 27 test
now asserts `evidence-producer`. Integrator's runs after the fix: validation 23 + 4, replay 73,
static corpus 18, static differential 18, evidence policy 5 all OK; target-go pilot gate with the Full regression on `dbd062b`: `Ran 1132 tests in 115.156s`, `OK (skipped=136)`.

## 32. 2026-09-16 deepen: runtime join, Stage C why/why-not, producer authority

Stacked on `experiment/claim-semantics` (`b9ced12`). Production `core/reconcile.py` and
production `capcov` consumer commands were not touched.

### What landed

1. **Runtime join as a library path.** `claims/static/runtime_receipt.py` is the only admitted
   importer of a retained `capcov-target-go-runtime-route/v2` receipt. It validates schema, identity,
   HTTP/SQL terminal state, cleanup, and the ordered causal trace; it never synthesizes a fake
   target-go run. The live pilot (`tests/claim_semantics/target_go/test_target_go_static_pilot.py`) now
   calls this module and still skip-gates on `CAPCOV_GO_FIXTURE_ROOT` plus the pinned
   scip-go/scip/go tools. `CAPCOV_TARGET_GO_RUNTIME_RECEIPT` remains the optional retained-artifact
   gate; when set, the receipt's `candidate_commit` must equal the indexed HEAD.

2. **Fixture-backed correspondence (no live target-go tree).**
   `tests/claim_semantics/test_runtime_join_fixture.py` joins the committed real receipt
   (`target_go/artifacts/runtime-recipient-route.json`, run `claims-runtime-trace-20260915-02`) to a
   synthetic `scip_index` through `index_describes_run`. Both `runtime_route_observed_on_index`
   and `runtime_route_reaches_sql_on_index` derive in the Python kernel when the witnesses
   agree; a mismatched run stays `unresolved`, never `refuted`. The synthetic index digest is
   `sha256("capcov-fixture-correspondence-index-v1")` and is explicitly not the target-go
   `static-relations-v1` identity. Static and runtime certificates stay independent: the
   runtime certificate's leaves are receipt + `index_describes_run`, never `scip_may_reference`.

3. **Stage C ground why/why-not.** `claims/static/ground.py` answers `why`, `why_not`,
   `impact`, and `shared_assumptions` against a kernel closure and the existing
   `capcov-static-certificate-v1` artifact. The queries do not search the application, launch
   Soufflé, or fold claims. `why_not` names the closest failed rule instantiation and records
   whether a completeness witness for that premise is present; it never sets `refuted`.
   `recheck` now also refuses a leaf whose `Evidence.source` token is not in the relation's
   `producer_classes` (tamper / unauthorized producer). Tests:
   `tests/claim_semantics/test_ground_certificate.py`.

4. **Producer-class authority end-to-end.** The causal-trace primitives
   (`runtime_function_entered`, `runtime_sql_executed`, `runtime_tx_committed`,
   `runtime_route_completed`) still admit only `target-go-runtime-trace-v2`. An unauthorized
   source (`generic-json`) fails `validate_bundle` with `evidence-producer` (≥4 issues),
   `evaluate` returns `invalid-input` with an empty closure, and `run_python` /
   `run_souffle` report `operational_failure=invalid-input`. `runtime_route_observed` stays
   unconstrained so the go_app probe is unaffected. Tests:
   `tests/claim_semantics/test_runtime_producer_authority.py`.

Declarations for the trace primitives and `runtime_route_reaches_sql_on_index` now live in
`runtime_receipt.py` and are imported by `scip_facts._DERIVED_TARGET_DECLS`, so the exporter
stubs cannot drift from the producer path.

### How to reproduce

From `packages/capabilities` (Python-only; no target-go tree, no Soufflé):

```sh
PYTHONPATH="$PWD/src" python -m unittest \
  tests.claim_semantics.test_runtime_join_fixture \
  tests.claim_semantics.test_runtime_producer_authority \
  tests.claim_semantics.test_ground_certificate \
  tests.claim_semantics.test_validation_producer \
  tests.claim_semantics.test_static_corpus_schema \
  tests.claim_semantics.test_static_corpus_evaluation
```

Inside `nix develop` (Soufflé + optional live target-go):

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -t .
CAPCOV_GO_FIXTURE_ROOT=/path/to/target-go \
CAPCOV_TARGET_GO_RUNTIME_RECEIPT="$PWD/tests/claim_semantics/target_go/artifacts/runtime-recipient-route.json" \
PYTHONPATH="$PWD/src" python -m unittest discover -s tests/claim_semantics -p "test_target_go_static*.py" -t .
```

The committed receipt was produced at target-go `01fe913`. A live join against HEAD `7e339e0`
fails closed on commit mismatch; that is the intended gate, not a defect.

### What this environment ran (2026-09-16, Linux, no nix)

`nix` and `souffle` were not on PATH. Python 3.12.3 ran the new modules plus the
Python-only static corpus / validation / exporter / evidence-policy suites. Results:

- `test_runtime_join_fixture`: 6 passed, 1 skipped (Soufflé dual-kernel)
- `test_runtime_producer_authority`: 4 passed, 1 skipped (Soufflé unauthorized path)
- `test_ground_certificate`: 10 passed
- `test_static_corpus_schema` / `test_static_corpus_evaluation` (Python evaluator): passed;
  Soufflé differential skipped
- `target_go.test_target_go_static_pilot`: 10 skipped (`CAPCOV_GO_FIXTURE_ROOT` absent)
- Pre-existing: `test_static_evidence_policy.test_both_kernels_agree_on_both_shapes` asserts
  Soufflé on PATH (fails outside nix); `test_static_schema_package_data` install check fails
  on this host's setuptools vs `project.license` — neither is caused by this deepen

### Remaining limits

- Dual-kernel agreement on the fixture join is implemented and skip-gated; it has not been
  executed in this environment.
- The live target-go pilot has not been re-run here (no checkout, no scip-go).
- Why/why-not is a ground query over one closure, not a second claim-folding engine.
  Alternative support beyond the canonical certificate path is not enumerated exhaustively.
- `runtime_route_observed` remains unconstrained by design (two honest producers).
- Production four-cell reconcile and production CLI are unchanged.

### 2026-09-16 Stage D and the receipt-backed replay judge integrated; remote PRs noted

Stage D (`agent/shen-workbench` `36dc528`, section 18 record) merged as `114a35a` with no
conflicts. On the merged tree its suite failed 7 of 22: `test_fixture_is_the_handoff_bundle`
and every certificate `bundle_digest` compared against the pinned go_app digest
`50e64261…cdb7`, while the tree computes `7e5a0b1f…d092`. Cause, not a defect: Stage D was cut
from `3e8a5f8`, and the runtime-join merge `5c22a89` later added five declarations to
`schema_static_v1.json` and `index_describes_run` emission to the exporter, which are part of
the go_app bundle; the rules digest `3c7c8082…d36c` is unchanged. Re-pinned in `86b2fe1`; the
untracked handoff fixtures under `.capcov/shen-handoff/` were regenerated from the same bundle
(certificate rechecks `ok=True`). After the re-pin: Shen suite `Ran 22 tests … OK` with
`CAPCOV_SHEN_REQUIRED=1` against `.capcov/shen-go-c12933d/shen-go`.

shen1's receipt-backed replay judge (`pyrex41/synapse` `experiment/replay-claims` `623cb4f`;
adds `c9dbc88` real-receipt join + pilot join and `623cb4f` honest-verdict assertions; no schema
change beyond `e373bb3`, `schema_replay_v1` now receipt-backed) merged as `86b2fe1`. One
conflict, in the target-go static pilot: both lines had recorded a runtime join under the receipt key
`runtime_join` — this line's route trace receipt (`CAPCOV_TARGET_GO_RUNTIME_RECEIPT`, `5c22a89`) and
shen1's replay-judge receipt directory (`CAPCOV_REPLAY_RECEIPT_DIR`). They are different joins
(route→SQL causal trace on the exact index vs. replay corpus constraint and op qualification), so
both are kept: `runtime_join` stays the route trace and `replay_join` records the judge. shen1's
pilot assertion had required `op_qualified == "supported"`, which their own `623cb4f` receipt
suite contradicts for the real receipt; the pilot now accepts exactly the two shapes that suite
asserts (qualified with no missing premise, or `unresolved` with `missing_premise ==
["model_writes"]`, `blocking_premise.relation == "undeclared_any"` and the write-set gap named).

Integrator's runs on the merged tree (aarch64-darwin, `nix develop --no-update-lock-file`):
replay 73 OK; validation section 27, 23 OK; static corpus 18 OK; static differential 18 OK;
production CLI back-compat 19 OK (1 skipped); manifest checks (`test-capcov-experiment.mjs`,
`test-capcov-runtime.mjs`) ok; shen1's receipt suite 17 OK (8 skipped without a receipt
directory; 1 skipped with `CAPCOV_REPLAY_RECEIPT_DIR` = their `target-go-5988859-model` receipts,
read only). target-go pilot with `CAPCOV_GO_FIXTURE_ROOT=/Users/dev/fg/.worktrees/target-go-capcov-claims-runtime`
(`01fe913`), the committed route receipt, and that replay receipt directory: `Ran 10 tests in
205.9s OK`; identity pin held; receipt `runtime_join.run = claims-runtime-trace-20260915-02`,
`replay_join = {status: complete, ops: [delete-issue], run: 333072ef11f5}` with
`delete-issue.op_qualified = unresolved`, blocked by undeclared writes (go: authentication,
entity_statistics, go_issue_outbox, mongo:issue, redis; php: authentication, entity_statistics,
jobs_statuses, mongo:issue, redis) — recorded as-is. Full regression on the working tree that
became `86b2fe1` (before the final pilot-assertion edit): `Ran 1171 tests in 125.5s`, `OK
(skipped=161)`; bound to `86b2fe1` itself: `Ran 1171 tests in 109.3s`, `OK (skipped=161)`.

Remote PRs at this point (2026-09-16): upstream `millstonehq/synapse` #50 (this line → `main`,
head `b9ced12` before this push, CLEAN, 3 comments, 0 reviews) and #36 (`feat/python-route-source-identity`,
not ours). Registered fork `pyrex41/synapse-capcov`: #1 (this branch → fork `main`, stale
Stage 0 body), #2 (`perf/incremental-source-snapshots` → fork `main`, superseded by upstream #49
merged), and #3 (`cursor/claim-semantics-deepen-7cc3` `78341c3` → this branch, a Cursor agent's
"runtime join, Stage C why/why-not, producer authority", based on `b9ced12`, run without nix,
Soufflé or target-go; overlaps the runtime join and producer authority already on this line and adds
`claims/static/ground.py` and `runtime_receipt.py`). `pyrex41/synapse` has only dependabot PRs.
Disposition of #3 is recorded in the next entry (section 32 above is PR #3's own record).

### 2026-09-16 PR #3 (Cursor agent deepen) integrated

`pyrex41/synapse-capcov` PR #3, `cursor/claim-semantics-deepen-7cc3` `78341c3` (one commit on
`b9ced12`, +1222/−186, 11 files; its own record is section 32 above). What it adds: Stage C
ground `why`/`why_not`/`impact`/`shared_assumptions` over `capcov-static-certificate-v1`
artifacts (`claims/static/ground.py`); the retained-receipt loader and trace declarations moved
into `claims/static/runtime_receipt.py` (the exporter's stub declarations now import them, so
they cannot drift); `recheck` refusing a leaf whose `Evidence.source` producer token is not in
the relation's `producer_classes`; fixture-backed runtime-join correspondence against a synthetic
index (explicitly not the target-go identity). It overlaps the runtime join and producer authority
already on this line but changes neither contract: `runtime_route_observed` stays unconstrained,
the trace primitives admit only `target-go-runtime-trace-v2`, `Evidence.kind` stays untouched.

Its environment was Linux without nix, Soufflé or an target-go checkout, so its Soufflé-dependent
tests and the live pilot were skip-gated there. Verified here first on its own head in a
throwaway worktree (`nix develop`, aarch64-darwin): the three new modules `Ran 24 tests … OK`
with Soufflé present; the whole `tests/claim_semantics` directory `Ran 356 tests … OK
(skipped=11)`; go_app bundle digest `7e5a0b1f…d092` and rules digest `3c7c8082…d36c`
unchanged, so the Stage D pin survives. Merged as `8829591` onto `45ca81f`. Conflicts were
only in the two markdown files (both sides kept; the handoff's live-pilot recipe now names the
target-go worktree at the receipt's candidate commit `01fe913`, because `/Users/dev/fg/target-go`
HEAD fails closed on the commit mismatch — correct behaviour, wrong recipe).

One latent defect surfaced on the first real run: PR #3 trimmed the pilot's `capcov.claims`
import to the names its refactor still used but left the static-only branch's `Bundle(())`, so
`setUpClass` raised `NameError: name 'Bundle' is not defined`. Skip-gating hid it in the
authoring environment. Import restored in the merge commit; an AST scan of the module finds no
other undefined name. Merged-tree runs: Shen 22 OK (`CAPCOV_SHEN_REQUIRED=1`); PR #3 modules
9 + 5 + 10 OK; static differential 18 OK; evidence policy 5 OK; shen1's receipt suite 17 OK
(1 skipped) against the real receipt directory; validation section 27, 23 OK; production CLI
19 OK (1 skipped); manifest checks ok; target-go pilot with the route trace receipt and the replay
receipt directory `Ran 10 tests in 193.3s OK`, receipt `outcome supported`,
`runtime_join.run = claims-runtime-trace-20260915-02`, `replay_join.status = complete`,
`delete-issue.op_qualified = unresolved`. Full regression on the merged working tree before the
one-line import fix (index tree `2ee50f3`): `Ran 1195 tests in 232.1s`, `OK (skipped=161)`.
Bound to `8829591` itself: `Ran 1195 tests in 133.5s`, `OK (skipped=161)`.

### 2026-09-16 shen1's committed replay receipt fixture integrated

`pyrex41/synapse` `experiment/replay-claims` `b8c781a` merged as `4933f0e`, no conflicts. It
commits the real, conforming target-go replay receipt (candidate `5988859`, run `333072ef11f5`,
synthetic oracle seed only, local evidence paths scrubbed to `<evidence>/` inside the
identity-excluded `receipts` block, with a `fixture_note`) under
`tests/claim_semantics/fixtures/replay_receipt_target_go_5988859/`, and `replay_join.receipt_dir()`
now defaults to that directory when `CAPCOV_REPLAY_RECEIPT_DIR` is unset (the env var still
overrides). Integrator's checks: the fixture contains no absolute local paths and no
credential-shaped keys; receipt suite with no env `Ran 17 tests … OK (skipped=1)` (the
conditional full-span skip awaits target-go's model write-set); replay suite 73 OK; target-go pilot
with the route trace receipt and no replay env `Ran 10 tests in 256.4s OK`, receipt
`replay_join = {status: complete, run: 333072ef11f5}`, `delete-issue.op_qualified = unresolved`
— the pilot's replay half is now exercised on every real run, not only when a work directory is
named. Full regression bound to `4933f0e`: `Ran 1195 tests in 106.8s`, `OK (skipped=154)` — seven
fewer skips than on `8829591`, exactly the receipt suite now running un-gated.

### 2026-09-16 publication rewrite absorbed; identity contract finding; pilot made checkout-derived

The `fixleak` session rewrote the public history of all three remotes (blob text, commit
messages and paths: the company name, host and module path, ticket prefix, `oracle`, and the
target's former short name, now `target_go`/`target-go` in paths and `TARGET_GO` in env vars);
tip `b9353b7` replaces `407fdf8` (kept locally as `backup/pre-rewrite-407fdf8`). Nothing was
rebased over it. On the rewritten tip, in the pinned devShell:

- Row-level content of every bundle is unchanged, but two go_app pins moved because the exporter's
  stub declarations now admit producer class `target-go-runtime-trace-v2` and every bundle
  carries those declarations: Stage D `GO_APP_BUNDLE_DIGEST` → `f64eddd2…ccbe` (rules digest
  `3c7c8082…d36c` unchanged; canonical-JSON diff against the pre-rewrite bundle is exactly the
  four producer-class strings) and `EXPORTED_BUNDLE_DIGEST` → `2ce5f5c3…a536`. Facts, evidence
  ids, closure and `GOLDEN_INDEX` are unchanged; Shen 22 OK and static differential 18 OK after
  the re-pins.
- The live pilot could not slice the real checkout: its `MODULE` constant had become the
  placeholder and `cmd/<name>/main.go` had been renamed, so the handler package closure was empty
  (`scope 'document_set' needs at least one value`). The pilot now reads the module path from the
  checkout's `go.mod` (`pilot.parse_go_mod`) when `CAPCOV_GO_FIXTURE_ROOT` is set and derives the
  main-package directory and the archive basename from it; the repository names no real module
  path. Router/sink file:line anchors are declared per head (`01fe913` and `7e339e07`), which
  also repairs an older incoherence: the runtime-join merge had moved the anchors to `01fe913`
  while the identity pin and the committed receipt still named `7e339e07`, so no run had compared
  the pinned identity since `5c22a89`.
- Identity finding. `static_relations_index` hashes the sorted list of declared relation names
  together with the rows (documented: "the declared relation names do" matter). Running the
  section 30 slice at `7e339e07` under the pin-era exporter (`3630c84`, throwaway worktree) and
  under this tip gives byte-identical per-relation row hashes for all 20 exported relations; the
  only difference is five stub declarations the runtime-join merge added (`runtime_function_entered`,
  `runtime_sql_executed`, `runtime_tx_committed`, `runtime_route_completed`,
  `runtime_route_reaches_sql_on_index`). So `0759ccef…3a3b` was that head's identity under the
  20-name contract; under the current contract it is `367b5675…7894` (archive basename restored to
  the module basename; with the rewrite's `target-go` basename it was `d955db0c…`, which shows the
  basename is part of identity as recorded in section 29). Pinned: `7e339e07` → `367b5675…7894`,
  `01fe913` → `ae62aba1…c9c7`. A contract change moving the identity is by design; the record is
  the correction, not a widening of the pin.
- Committed pilot artifacts are now redacted copies of the real run at `01fe913` (with the route
  trace receipt and the default replay fixture): receipt plus four certificates, with the module
  path, checkout path and host temp paths replaced by markers and a `redaction` block naming the
  rules and the unredacted receipt's sha256. Every digest, identity, row count and certificate
  entry in the committed receipt is of the unredacted run, and the identity test compares only
  those. The retained runtime receipt's symbol strings were neutralized by the rewrite; the
  runtime join is by run/request/tx/surface/index identity, never by symbol string, so it still
  derives and its certificates still recheck.
- Runs: pilot at `01fe913` with runtime receipt `Ran 10 tests in 219.1s OK` (identity compared
  with the committed receipt); pilot at `7e339e07` `Ran 10 tests in 140.7s OK (skipped=1)`
  (pinned identity held, per-head anchors verified); receipt suite 17 OK (1 skipped); replay 73
  OK; PR #3 modules 24 OK; evidence policy 5, validation 23, CLI 19 (1 skipped), manifest checks
  ok. Full regression bound to `3eac405`: `Ran 1195 tests in 98.1s`, `OK (skipped=154)`.
Note for the record: a first commit attempt that named the former short names literally was
blocked by the local leak-guard pre-commit hook (correctly: no commit was created). The
integrator's script had put the follow-up `git log` on its own line rather than chained to the
commit, so a done-marker fired anyway and the first regression bound itself to the previous
head; the hook was briefly and wrongly reported as not failing the commit. The regression was
rerun bound to the final commit.

Second rewrite (fixleak, same day): user home-directory paths that predated this line's records
were generalized away across the full history; tip `b47c24f` replaces `0ece816` (kept locally as
`backup/pre-rewrite2-0ece816`). Content differences are confined to those path strings.
Full regression bound to `7d14b45` (the docs commit on that tip): `Ran 1195 tests in 135.1s`,
`OK (skipped=154)`; PR #50 CLEAN on it with every check green. The devShell had to rebuild
`shen-go` after a store path was collected and first failed on a full disk; only this session's
own scratch (cold-shell Go caches, a nixpkgs unpack, identity dumps, about 2.3 GB) was removed.

### 2026-09-16 reviewer scope exclusions for the replay judge integrated (shen1, `6f003f6`)

`pyrex41/synapse` `experiment/replay-claims-rewritten` `6f003f6` (three commits on `f9d0cec`:
`c42088d` schema + exporter, `fb1af9c` pack gating, `6f003f6` join/receipt reporting) merged as
`b8bdd82`, no conflicts, zero identifier hits in its delta. What it adds: `model_scope_exclusion
(model, table, reason)` and `model_scope_exclusions_closed(model)` with producer `reviewer`, a
derived `model_scope_excluded` projection with its own closure, `undeclared_write` negating it,
and the committed replay fixture gaining a reviewer exclusions file that names reviewer, date,
model digest and run id (the exporter refuses a stale review). As agreed before it was built:
exclusion rows enter as assumption-modality evidence, an empty exclusion set without its closure
qualifies nothing, and the join summary reports the exclusions applied.

Integrator's runs on `b8bdd82` (pinned devShell): replay 79 OK; receipt suite 19 OK (1
conditional skip); Shen 22 OK; static differential 18 OK; live pilot at `01fe913` with the route
trace receipt `Ran 10 tests in 384.6s OK`, `replay_join.status = complete`, four exclusions
applied (authentication, go_issue_outbox, jobs_statuses, redis, each with its reason),
`delete-issue.op_qualified = unresolved` with the remaining undeclared writes
`{entity_statistics, mongo:issue}` on both the PHP and Go sides. shen1 reports the candidate
now declares those two tables; the receipt proving full qualification comes as a separate commit.
Full regression bound to `b8bdd82`: `Ran 1203 tests in 95.3s`, `OK (skipped=154)`.

Certificate-format decision (owner: this line, Stage D/certificates). shen1 notes that a negated
atom carries no leaf in `capcov-static-certificate-v1`, so the reviewer exclusion rows cannot
appear inside the `op_qualified` certificate; they are assumption leaves of the companion
`exclusion_applied` certificate and the summary counts assumption leaves across both. Decision:
keep v1 unchanged. The justification of a negated atom in this IR is its completeness witness,
and that witness (`model_scope_exclusions_closed`, producer `reviewer`) is a positive atom whose
leaf does appear in the qualifying certificate; the exclusion rows are not premises of the
negated instance but of the projection's absence, which the companion certificate carries. A
`capcov-static-certificate-v2` that additionally records negation witnesses (the complement basis
rows) is backlog, to be taken up only if a consumer needs one certificate to be self-contained.

### 2026-09-16 full-coverage replay receipt integrated (shen1, `c701706`)

`experiment/replay-claims-rewritten` `c701706` (`b37a84a` commits the scrubbed full-coverage
receipt — target run `eca6e793…`, model digest `08380c9c…`, `model_writes` now declaring
`entity_statistics`, `issue`, `mongo:issue` — as `fixtures/replay_receipt_target_go_qualified/`,
the earlier receipt renamed to `…_unqualified/` and kept as the negative path; `c701706` makes the
qualified fixture the default) merged as `f35547b`, no conflicts, zero identifier hits. shen1 also
fixed a real defect on the way: `evaluate_join` kept only the last row's certificate for the open
`exclusion_applied` claim, so assumption leaves were undercounted (1 instead of 4); it now emits
one certificate per row.

Integrator's runs on `f35547b`: replay 79 OK; receipt suite 22 OK with no skips; live pilot at
`01fe913` with the route trace receipt `Ran 10 tests in 136.2s OK`, `replay_join.status =
complete`, `delete-issue.op_qualified = supported`, `operational = complete`, `missing_premise =
[]`, exclusions applied `authentication, go_issue_outbox, jobs_statuses, redis`. This is the first
run in which the replay judge qualifies the real op end to end; the qualification rests on four
reviewer exclusions carried as assumption leaves, and the pilot receipt says so. Full regression
bound to `f35547b`: `Ran 1206 tests in 102.5s`, `OK (skipped=153)`.

### 2026-09-16 explain-evidence merge verified; snapshot blob index and heavy-work lock (upstream PR #51)

`pyrex41/synapse-capcov` `experiment/claim-semantics` `1e6656b` (another session: `why`/`why_not`
explanations for every certified pilot claim and for the replay join's `op_qualified`, persisted
in the pilot receipt under `explanations` and per op under `explanation`, without duplicating the
certificate) merged as `300f6d2`. Verified under heavy contention: receipt suite 22 OK, replay 79
OK, ground 10 OK, full regression bound to `300f6d2` `Ran 1206 tests in 528.3s`, `OK
(skipped=153)`; live pilot at `01fe913` with the route trace receipt `Ran 10 tests in 416.7s OK`,
explanations present for all four certified claims, `delete-issue` `op_qualified = supported` with
`explanation.holds = True` and two shared assumptions.

Performance follow-up to section 31, delivered upstream as PR #51 (`perf/blob-keyed-snapshot-cache`
`0ba637e`, CI CLEAN including the pinned Nix toolchain job): `artifacts.snapshot_tree` gains a
machine-wide digest index keyed by git blob id, so a fresh worktree of a known commit re-hashes
only what git reports modified (measured on two Go worktrees at different commits: 166 of 169
digests reused with zero reads, digest equal to the exact walk); the digest formula, and therefore
every identity pinned on this line, is unchanged (static differential 18, crosscheck 5, exporter
48, corpus 18 OK on a merge of the change onto this head). It cannot help untracked trees; the
24,675-file PHP oracle copy that triggered the incident is untracked and snapshotted from a
per-run temporary root. `scripts/with-heavy-lock.py` serializes disk-heavy steps across agents;
this session's devShell runs were killed twice by the host's low-memory guard while seven of
shen1's units ran unwrapped, and shen1 has adopted the lock for every later stage.

### 2026-09-17 round-two replay judge integrated; the Stage D contract is live and honestly unmet

shen1's `experiment/replay-claims`-line round two, `pyrex41/synapse` `experiment/r2-judge`
`ae86257` (based on this line's `19ca3fc`; merges `1dd4c59` assumption registry with per-run
impact and invalidation, `46d994e` ordering / repeat-delete / oracle-stability claims, `dd84698`
compiled Soufflé checker as a gate with a three-kernel differential and a judge CLI, `746231c`
the Stage D contract, then `e2ef499`, `f073faa`, `cb015a4`, `ae86257`), merged in two steps as
`775e66d` and `b77be19`, no conflicts, zero identifier hits. Pack identity now 115 relations /
71 rules, `program_digest 9addbe39…`.

The Stage D contract, as agreed and now in `schema_replay_v1`: `model_well_formed(model, checker,
checker_version, certificate)` (observation, context `model`, producer class `modelcheck`; `shen`
and `reviewer` are refused by `evidence-producer`) and `model_checker_admitted(checker,
checker_version)` (reviewer-owned allowlist, `model_checkers.json`), both positive premises of
`op_qualified_rt` joined on the same model digest as `model_describes_run`; no closures. The
receipt file is `model_well_formed.json` = `{"producer": "modelcheck <checker> <version>
model:<digest12>", "rows": [...]}`; a row for a foreign model digest makes the export stale. The
canonical input the checker must digest is the `.shen` source in `load.shen` order (shen1's
recipe, served by the model host); nothing else joins.

Integration finding, corrected before it reached the PR: `746231c` shipped every real-receipt
fixture with a `model_well_formed` fact from checker `stage-d-typecheck 0.1-pending` whose
certificate is `sha256("pending: checker not yet built")`, admitted by the fixtures' own
allowlist, so the real op read `supported` on a premise no checker produced — a fabricated
observation filling the very gate it was added to guard. shen1 agreed at once; `e2ef499` removes
it from the real fixtures (the labelled-synthetic `replay_receipt_min` keeps a synthetic
certificate as the corpus source), the real qualified receipt now reads `unresolved` with
`model_well_formed` as its only missing premise and `qualification: pending model_well_formed`,
and the compiled gate exits 5 for that state so a CI consumer can tell "pending checker" from
"unsupported". The pilot's replay assertion (this line's two-shape rule from `86b2fe1`) gained
that third shape and accepts nothing else.

Runs on `b77be19` (pinned devShell, every heavy step under `with-heavy-lock.py`; the pilot
visibly waited for one of shen1's compiled-judge steps, which is the lock doing its job): Shen
22 OK with the runtime; replay 108; receipt 34; compiled kernel 8; compiled checker script 13;
assumption registry 44; static differential 18; production CLI 19 (1 skipped); full regression
`Ran 1343 tests in 698.9s`, `OK (skipped=153)`; live pilot at `01fe913` with the route trace
receipt `Ran 10 tests in 181.9s OK`, `replay_join.status = complete`, `delete-issue`:
`op_qualified = unresolved`, `qualification = pending model_well_formed`, four reviewer
exclusions applied, effect order respected on both sides, no repeat-delete violations,
`learn_consistent = supported`.

Two results from shen1 recorded here because they bear on this line: (1) the target's newest
replay receipt over the full lineage-derived corpus (98 mutants, 37 survivors, `mutants_closed`
held) is judged NOT supported with blocking premise `corpus_constrains`, kernels matched — the
judge withdrawing a verdict it had given on a six-mutant corpus, which is what the closure work
was for; (2) on upstream PR #52 (advisory classifier for surviving mutants) a shared diagnostic
hint in the request preamble swung all 35 classifications the same way in two opposite passes,
while the neutral pass scored 5/8 and a pattern-packet pass with runtime facts as candidate-specific
evidence items scored 6/8 with no unanimity — the "advisory only" boundary holds, and evidence for
a classification must travel as an evidence field, never as prose.

Stage D (typed well-formedness of the model, section 18 decision) can now start: the contract it
must satisfy is fixed, the fixture that must flip from pending to qualified is named, and shen1's
in-flight units are landed.

