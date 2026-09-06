---
id: TDD-capability-mapping-mbt
type: tdd
title: Capability Mapping and Model Based Testing
status: proposed
owner: cpb
created: '2026-09-06T00:00:00.000Z'
updated: '2026-09-06T00:00:00.000Z'
tags: [capabilities, testing, architecture, adapters]
summary: Optional Synapse extension for mapping implementation evidence into system capabilities, executable journeys, and explicit completeness gaps.
related_adrs: []
---

## Summary

Point at a supported, runnable repository or a declared set of repositories and produce an evidence-backed capability map, generated executable tests, and an explicit account of everything preventing complete coverage. The goal is practical completeness for understanding, regression testing, and rebuilding products; no claim of formal verification or exhaustive inference from arbitrary code is made.

The home is an optional extension in the Synapse framework. Synapse owns the durable system/capability documents, schemas, validation, and presentation. A standalone local engine owns discovery, planning, execution evidence, and coverage reconciliation. The first implementation runs in the consuming project's development environment and writes local artifacts, with no required hosted service, central database, or Mill dependency. The Python engine lives in `packages/capabilities`, preserving the `capcov` command and import package. Consumers pin a public Synapse revision and that subdirectory, without installing the Node packages. Synapse CI owns conformance tests and distribution builds; package-specific tags publish independent Python releases. Optional documentation/CLI integration remains open.

## Overview

Capabilities belong to a system or product. Repositories supply implementation evidence. A customer journey may cross a frontend, API, worker, and reporting repository. A repository-only scan remains useful and can subsequently join a system map without changing its evidence identifiers.

There are three distinct automation tasks:

1. Discover implementation structure through source analysis and runtime observation.
2. Establish meaningful behavior: actors, prerequisites, actions, expected outcomes, and representative fixtures.
3. Generate journeys, execute them, and reconcile outcome evidence against the declared capability scope.

Source-derived candidates are not automatically confirmed business capabilities. Running a code path does not establish that its outcome is correct. Building and running locally does not supply every role, lifecycle state, configuration, external failure, or business expectation.

## Architecture

```text
 Repository / system manifest
              |
 Technology detection + discovery adapters
              |
 Source graph <---- runtime observations
              |
 Candidate capabilities + unresolved findings
              |
 Confirmed behavior models + fixture recipes
              |
 Journey planner --> execution adapters
              |              |
              +---- outcome evidence
                             |
                Coverage reconciliation
                             |
             Synapse documents + explicit gaps
```

### Package boundaries

- Synapse integration: schemas, scaffolding, document links, report projection, and optional CLI commands. Normal documentation validation must not start applications or require browser/database dependencies.
- Standalone core: versioned graph/model contracts, planning, coverage rules, provenance, and machine-readable output. It must also work without a Synapse vault.
- Discovery adapters: technology-specific interpretation of source, framework configuration, runtime registrations, and effects. Compose language parsing with framework semantics rather than writing a parser per repository.
- Execution adapters: translate modeled actions into browser, HTTP, CLI/process, queue, mobile, or desktop interactions; return observations and assertions.
- Repository/system recipes: startup, reset, seed data, identities, service connections, and target bindings. These are application-specific even when the adapters are reusable.

### Local-first execution

Start by attaching to an application already running locally, using declared test identities and fixture/reset hooks. Where startup automation is needed, invoke the repository's existing commands or Compose setup. Use local checkout paths for multi-repo systems and write maps, plans, and evidence into the consuming project's output directory.

Build only the lifecycle handling needed by the first working consumer. Do not introduce a runner service, scheduler, remote execution protocol, environment provisioner, or adapter marketplace up front. Package boundaries below describe responsibilities; they do not require separate packages in the first implementation.

Application tooling remains a prerequisite: native targets need a compatible host, and external dependencies need declared test endpoints or substitutes with explicit evidence limits. Model-assisted discovery may use a configured model provider; executing a validated plan must not require an LLM call.

### Future option: remote execution

If scheduled scans or CI capacity later justify it, another machine can run the same local command and collect its artifacts. Mill could supply that machine and retention. Remote workers, scheduling, and centralized storage are deferred; no hosted control plane or remote-runner abstraction is required for the local milestone.

An agent can propose semantic groupings, fixture recipes, and assertions from evidence. Proposals retain source references and uncertainty. Deterministic validation and actual execution decide whether evidence satisfies an obligation; prose or a confidence score cannot mark an outcome covered.

### Rebuild contract

```text
 Incumbent capability + expected outcomes
                  |
          +-------+-------+
          |               |
     Old bindings     New bindings
          |               |
     Old runtime      New runtime
          |               |
          +-------+-------+
                  |
       Compare business outcome evidence
```

Keep the incumbent denominator when evaluating a rebuild. A feature absent from the replacement must remain a visible missing capability. Separate observed compatibility expectations from intended business rules, so an incumbent bug is not silently promoted into a requirement.

## Information Model

- **Product/system:** stable identifier, scope, owner, participating components, and external boundaries. Membership is many-to-many; shared services can participate in several systems and a monorepo can implement several products.
- **Repository snapshot:** origin, commit or content digest, included paths, exclusions with reasons, adapter versions, and configuration digest.
- **Component:** deployable application, service, job, library, or platform export within a repository. System membership can initially be inferred but must carry confirmation status.
- **Discovery node/edge:** source location and digest, category, relationships, extraction confidence, and unresolved references. Unsupported declarations remain findings.
- **Capability:** stable business identifier, actor, intent, preconditions, operations, outcomes, and links to one or more implementation nodes. Preserve business identity across implementation changes.
- **Transition:** required/forbidden facts, action, resulting facts, expected outcomes, fixture requirements, and target-specific bindings.
- **Journey:** ordered transitions plus scenario data, actor, environment, and coverage obligations. Cross-service correlation and bounded asynchronous completion are explicit.
- **Evidence:** source/model/plan digests, run and step identifiers, observed surfaces/effects, assertions, environment identity, and result.
- **Gap:** unclassified, unresolved, unmapped, unconfirmed, blocked, untested, failing, or stale; owner and rationale where supplied.

Completeness is a vector: source accounted, references resolved, behavior modeled, required outcome classes tested, and target parity established. Do not collapse it into a single percentage that hides missing discovery support. Coverage of all modeled transitions is not coverage of all input values, action orderings, timing, or concurrent interleavings.

## Interfaces

Proposed adapter contracts are versioned data interfaces; exact implementation language and package names remain open.

```text
DiscoveryAdapter
  detect(snapshot) -> applicability + supported conventions + limits
  discover(snapshot, scope) -> nodes + edges + census + findings
  observe(runtime) -> mounted surfaces + registrations + observed effects

ExecutionAdapter
  prepare(recipe) -> isolated environment identity
  execute(step, context) -> observations + assertion results
  reset/cleanup(context) -> result

Core
  reconcile(discovery, model, plan, evidence) -> coverage + gaps
```

Required invariants:

1. Every scoped source file and relevant declaration category is accounted for or explicitly unsupported/excluded. Regenerating a catalog cannot erase unknown categories.
2. Discovered nodes remain candidates until their business meaning and expected outcomes are established.
3. Missing fixtures/bindings and unreachable prerequisites produce blocked work. Planner budget exhaustion fails explicitly rather than returning a complete-looking truncated plan.
4. Coverage requires fresh evidence tied to exact source, model, plan, scenario, and step. An unrelated request cannot satisfy a step's surface obligation.
5. Allowed/denied, success/failure, and relevant branch outcomes are separate obligations. Persistence and downstream outcomes need corresponding assertions.
6. Runtime-only surfaces and unmounted expected surfaces remain discrepancies. An arbitrary passing assertion cannot close an unresolved discovery boundary.
7. Approved exclusions have scope and reasons. Baselines and exemptions do not turn an incomplete system into a complete one.

## Files and Layout

Illustrative structure. Start with one portable module and the existing adapter conventions; split packages only when actual consumers require it:

```text
synapse framework
  packages/capabilities/src/capcov/ standalone Python core and adapters
  packages/capabilities/tests/      engine conformance tests
  packages/cli/                   optional integration
  packages/schemas/               shared document/data schemas

consumer vault or repository
  capabilities/system.yaml       components, scope, runtime recipes
  capabilities/models/           reviewed behavior and target bindings
  content/                       human-facing system/capability documents
  output/capabilities/            generated graphs and run artifacts
```

Keep reviewed intent separate from generated projections; regeneration must preserve authored outcomes and adjudications. Store compact manifests and models in Git, with large graphs/traces in retained artifacts referenced by digest. Private source-derived details stay in the consumer's access boundary. Existing Synapse document types should be extended where suitable, avoiding a competing capability vocabulary.

## Work Plan

1. Deliver one local vertical slice from the existing proof of concept: local checkout and running app to capability map, planned journeys, execution evidence, and gap report. Reuse existing startup and fixture hooks. Acceptance: it runs from the consuming project without a hosted framework service or Mill dependency, and a seeded outcome failure is detected. Preserve evidence rejection tests before moving consumers.
2. Implement the optional Synapse integration and system/component membership. Acceptance: a single-repo scan can join a multi-repo system with stable references and no duplicated capability identity.
3. Pilot three contrasting systems: modern web/API, legacy monolith, and asynchronous processing. Establish source census, representative roles/data, and selected complete journeys in each.
4. Add high-reuse technology adapters through actual repositories. Maintain a support matrix by framework/convention/version, including known unsupported constructs.
5. Expand capability and outcome coverage, then old/new bindings for a rebuild. Keep omissions visible against the incumbent scope.

Measure time to first useful map, onboarding effort, unresolved/unmapped counts, reviewed outcome coverage, seeded-fault detection, flaky runs, and effort to close gaps. Reaching a route count is not an acceptance criterion for behavioral completeness.

## Risks and Mitigations

- Static and runtime discovery can share blind spots. Combine source census, explicit boundary declarations, runtime registration inventories, existing specifications/tests, and business review.
- Dynamic configuration, reflection, generated code, and external services defeat naive source interpretation. Declare support limits and retain unresolved findings; inspect runtime registrations where available.
- Per-system fixtures and outcome definitions may dominate cost after adapters exist. Reuse recipes, but measure this effort independently of parser work.
- Asynchronous and multi-tenant behavior require isolation, correlation, time control, and bounded waits. A mocked dependency proves only the tested boundary; distinguish it from full integration evidence.
- The test model can repeat an implementation bug. Keep independent business rules and compatibility observations distinguishable.
- Framework versions and legacy conventions require additional modules. A shared language parser alone does not establish semantic support.
- Coupling test execution to documentation would burden every Synapse consumer. Keep runtime dependencies optional and the core invocable independently.

## Operations

Run discovery read-only against pinned snapshots. Run mutations in declared test environments with reset/cleanup recipes and explicit external-service policies. Retain enough evidence to reproduce failures without copying credentials or unnecessary customer data into documentation.

For the first implementation, artifacts are local files and execution is a foreground command. Clean up only processes/resources started by that run; attach mode leaves the user's application running. CI can invoke the same command without adding a framework service.

Expose separate CI checks for inventory drift, model validation, execution, and completeness. A successful documentation build must never imply successful behavioral testing.
