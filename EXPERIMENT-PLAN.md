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

Add root `flake.nix` and `flake.lock` files. The default development shell should pin:

- Python 3.12;
- `uv`;
- Go;
- Git and `jq`;
- a benchmark tool such as `hyperfine`;
- the selected Shen runtime.

Package `github.com/pyrex41/shen-go` at a clean pinned revision using `buildGoModule`. Expose a stable `shen` or `kl` wrapper used by tests. Do not use the locally installed dirty binary.

Initial checks:

```sh
nix flake check
nix develop --command bash -lc \
  'cd packages/capabilities && PYTHONPATH=src python -m unittest discover -s tests -t .'
nix develop --command shen --version
```

Record exact package revisions, closure information, commands, and initial test results here.

**Exit criterion:** a clean checkout can run the Python and Shen smoke tests entirely through Nix.

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
