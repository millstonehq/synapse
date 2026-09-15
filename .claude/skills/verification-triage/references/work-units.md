# Deriving implementation work units from capcov

Read this when establishing breadth, assigning implementation work or estimating
remaining work. A work unit is consumer-side planning metadata over native capcov
records, not another coverage engine or an automatically proven capability.

## Ground the view in the installed version

Inspect the project's pinned capcov version and existing consumer artifacts before
choosing commands or fields. Reuse discovery obligations, the source-derived flow
catalog where available, and authored transitions with their evidence bindings.
If catalog support or an adapter is unavailable, group the existing obligations
and source findings in the consumer and retain the missing discovery boundary.
Do not extend the engine merely to obtain a planning count.

Keep these meanings distinct:

| Native representation | Meaning for planning |
| --- | --- |
| Entity `operations` and `untested_operations` | Access/effect labels and reconciliation gaps; not business deliverable counts |
| Inventory obligations | Source-grounded requirements/findings, including surfaces and unresolved boundaries |
| Catalog flow families and memberships | Candidate groupings rooted in actions, surfaces, workflows, schedules and other supported kinds; overlapping reachability is possible |
| Flow transitions | Actor, preconditions, outcome and linked obligations, with bindings as available; multiple transitions can establish one usable behavior |
| Execution/reconciliation evidence | Support for specific behavior in a particular build and environment; preserve native status and evidence limits |

## Group by independently acceptable outcomes

Start across incumbent entry points: client actions, HTTP surfaces, commands,
schedules, workers and hooks. Trace their required downstream effects using the
existing graph and source. A work unit has one caller-visible outcome that can be
accepted independently. The caller can be a user or another system.

Reuse a native ID when it already identifies that outcome. Otherwise give the
consumer grouping a stable ID and explicit member references; do not relabel it
as a native capcov operation. Retain:

- Catalog root/family IDs and obligation IDs, plus transition IDs when modeled.
- Incumbent source revision and the inventory/model identity those IDs belong to.
- Actor, prerequisites and a short observable acceptance condition, including
  required persisted or downstream effects.
- Candidate implementation pointers, dependencies, evidence references and scope
  (build, environment and relevant identity/configuration).
- Separate missing functionality, unresolved semantics and missing verification.

Keep these in the existing ledger or consumer metadata; reference native facts
rather than copying their definitions or translating native coverage statuses into
an incompatible second set. A provisional source-only unit explicitly retains its
unmapped finding until discovery/modeling can bind it.

Group aliases and equivalent entry points under one outcome. Treat refusal,
retry and other variants as acceptance cases unless they provide independently
required behavior. Split only when outcomes can be accepted separately; identical
outcome text alone does not establish equivalence across actors or prerequisites.
Attach internal steps and background effects to their owning outcome. A shared
prerequisite may have its own implementation task without earning an additional
business-outcome completion. Distinct scheduled/service contracts can be units.

Example: request report -> render -> publish -> download can form one unit,
“authorized user obtains the requested report.” Link its request/status/download
surfaces, worker effects and behavioral transitions. Completing only the callback
records partial implementation/evidence; it does not complete that journey. If
status tracking has its own independently required contract, record that distinct
outcome explicitly rather than counting every endpoint automatically.

## Count without inflating progress

Count each accepted outcome once, even if several roots reach it or workers share
its obligations. Retain many-to-many membership; do not delete shared obligations
to make the count look disjoint. Check that discovered in-scope obligations are
linked to work units or explicitly retained as unmapped/unresolved. Exclusions
need their existing scope disposition; an absent mapping is not zero work.

For a stated inventory revision and acceptance scope, report total known units,
implemented units, demonstrated units, and the corresponding remaining counts.
Partial units retain their completed subclaims without becoming fractional or
multiple completions. Keep unknown areas and release gates alongside these counts;
known-unit completion is not a percentage of an incompletely discovered system.

Record splits/merges with old-to-new IDs and their outcome rationale. Recalculate
baseline and current counts consistently; regrouping does not earn throughput.
Forecast by comparable unit size/complexity and actual new completions, keeping
integration/release effort explicit. If samples or discovery are weak, give an
assumption-bound range instead of treating raw counts as equal-duration tasks.
