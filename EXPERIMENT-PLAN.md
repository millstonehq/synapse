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
`context: true`), whose value is the SCIP index digest: `sha256` of the `index.scip` bytes
(`digest_kind = binary`) or `sha256("scip-json:" + canonical_json(raw))` for a checked-in JSON
fixture (`digest_kind = json`). Tree-sitter-side facts (routes, op sites, blind spots) are
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
depends on `external:git-commit:<sha>`. Bundle metadata records export version, index digest,
scope, producer versions, and profile (`slice` or `full`).

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
```

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

If the fixture is absent the driver emits `task-blocked`; record BLOCKED here and keep the
go_app pilot as the delivered static evidence without calling it target-go.
