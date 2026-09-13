---
id: ADR-0001
type: adr
title: capcov's literature foundations
status: accepted
owner: cpb
created: '2026-09-13T00:00:00.000Z'
updated: '2026-09-13T00:00:00.000Z'
tags:
  - adr
  - capabilities
  - testing
summary: Anchors each capcov mechanism in named testing and program-analysis literature and adopts Software Reflexion Models as the explicit frame for static-vs-runtime reconciliation.
---

## Context

capcov was built from first principles. Its two load-bearing ideas — that
"completeness is a vector" rather than a single percentage, and that a system's
behaviour decomposes into named capability nouns — were a homegrown synthesis
carrying no citations. The TDD that specifies it
([[capability-mapping-and-model-based-testing]]) left `related_adrs` empty, so a
reader had no way to check the design against the fields it borrows from, and no
record of which claims were established practice versus local invention.

That gap has two costs. First, it hides where capcov is well-calibrated: several
of its deliberate refusals — no claim of formal verification, naming unresolved
calls instead of dropping them, enumerating blind spots, treating each branch
outcome as its own obligation — are positions the literature already argues for,
and stating that raises confidence in them. Second, it hides where capcov
*overclaims*: without the soundiness frame it is easy to read the reachability
fixpoint's "converged" history as complete reachability, and easy to imagine
importing a resolver whose accuracy figures capcov has not measured.

The mechanisms are real and each has a lineage in published work. Naming that
lineage is cheap, changes no behaviour, and lets future contributors reason about
capcov in the vocabulary of the relevant subfields.

## Decision

Anchor each capcov mechanism in named literature, recorded here and cited in the
code as short `Author Year (see ADR-0001)` docstrings. The map:

**A. The flow model is model-based testing over an EFSM/STRIPS transition system.**
`flows/model.py` represents a capability as facts (state variables) and
transitions carrying `requires`/`forbids` guards and `adds`/`removes` effects —
an extended finite-state machine with STRIPS-style operators. `plan()` does a BFS
that emits one shortest-prerequisite scenario per transition: this is
"all-transitions" test generation, and the `blocked` list plus the `max_states`
budget are the honest statement that transition coverage is only meaningful over
*reachable* transitions. Lineage: Chow 1978 (the W-method and FSM
transition testing), Utting & Legeard 2007 (model-based testing as a tools
discipline), Lee & Yannakakis 1996 (the FSM-testing survey).

**B. Obligations are test requirements — the literal denominator.**
`flows/model.py::reconcile()` treats the obligation set as the denominator against
which `covered` / `unproven` / `unmapped` are counted, and keeps each branch
outcome (allowed/denied, success/failure) as a *separate* obligation rather than
collapsing them. Lineage: Ammann & Offutt, whose four structures a coverage
criterion reduces to — graphs, logic, input space, syntax — are the facets of
test completeness, and whose insistence that distinct outcomes are distinct
requirements is exactly the non-collapse capcov enforces.

**C. The reachability fixpoint and the "soundy" resolver.**
`core/fixpoint.py` propagates entity references backward along a `calls` graph to
a fixpoint. `adapters/python_fastapi_sqlalchemy.py` is a deliberately *soundy*
resolver: it resolves what it can syntactically and *enumerates* its blind spots
(`getattr`/`eval`/dynamic import/ambiguous multi-candidate dispatch) with file and
line, binding them to none rather than guessing — "name it, don't drop it."
Lineage: Livshits et al. 2015 (the soundiness manifesto — a sound-core analysis
that documents its unsound corners), Shivers 1991 (k-CFA; higher-order control
flow is not decidable from syntax alone), Samhi et al. 2024 (measured call-graph
unsoundness, and the inverse precision/soundness relationship), Néron et al. 2015
and Creager & van Antwerpen 2023 for name resolution as a first-class problem.

**D. Static-vs-runtime reconciliation is a Software Reflexion Model.** This is the
anchor capcov most needed and previously omitted. Adopt Murphy, Notkin & Sullivan
1995 as the explicit frame for `core/reconcile.py`, `core/gate.py`, and the
surface comparison inside `flows/model.py::reconcile()`. A reflexion model
compares a high-level model against extracted source and labels every relationship
convergence, divergence, or absence. capcov's declared inventory is the high-level
model; runtime observation is the reality. The correspondence is exact:

- **convergence** (declared AND present) == capcov `covered` — the `both` cell in
  `core/reconcile.py`, and in `flows/model.py::reconcile()` an obligation proven
  by a passing scenario.
- **divergence** (present, NOT declared) == capcov `runtime-only` — the
  `runtime_only` cell; surfaced by `core/gate.py`'s `undiscovered-surface`
  ("runtime reached this surface and discover never found it") and
  `flows/model.py`'s `runtime-only surface` failure.
- **absence** (declared, NOT present) == capcov `dead` / `unmounted` — the
  `neither` cell; surfaced by `core/gate.py`'s `_explain` ("declared in the schema
  and neither reachable nor observed. Dead.") and `flows/model.py`'s
  `unmounted surface` failure.

The `static_only` cell (declared and statically reachable, but no exercise reached
it) is the coverage-gap case the three reflexion labels do not name directly: the
declaration and the static extraction converge, but the *testing* obligation is
still `unproven` — "write the test." Naming it keeps convergence-of-structure
distinct from convergence-of-evidence.

**E. Capability nouns descend from Feature-Oriented Domain Analysis.** capcov's
"capabilities and their facets" is the same shape as a FODA feature model:
capabilities as a tree with mandatory/optional/alternative/or facets plus
requires/excludes constraints. Lineage: Kang et al. 1990. capcov is *not*
currently structured as a feature model in code; FODA is named here as the
lineage, and adopting its variability structure (mandatory/optional/alternative,
requires/excludes) is a **future option**, not part of this decision.

**F. The resolver build-vs-rent argument.** The decision to rent a per-language
resolver rather than grow capcov's own is argued in the spirit of Sutton's "The
Bitter Lesson" (2019, cited as an essay, not peer-reviewed): general
method plus leverage beats hand-built special-case machinery over time. It is
weighed against soundiness (C): a rented resolver whose blind spots capcov cannot
enumerate would forfeit capcov's central honesty property.

**Resolver decision (recorded, from a prior spike).** The resolver is **hybrid**:
SCIP is rented per language as the resolver; capcov's own AST pass is **demoted to
the blind-spot enumerator** and stays, because it is the component that can *name*
what it cannot resolve. Stack graphs are **out** — archived, no Go support,
syntactic-only. Building SCIP-as-resolver is separate future work, not authorised
by this ADR.

## Consequences

**Two overclaims are corrected in prose and comments, with no behaviour change.**

1. `core/fixpoint.py` described the reference history as converging "by
   construction" and treated "converged" as final. Corrected: the history
   converges over the **resolved** call edges — the fixpoint has closed over the
   *given* call graph, which is not the same as having found every truly-reachable
   entity. Reference-derived edges are unsound for higher-order and virtual
   dispatch (Shivers 1991; Samhi et al. 2024). A one-line caveat now
   says so; the algorithm is unchanged.
2. capcov must never imply it can report stack graphs' "soundness/precision": the
   stack-graphs paper reports scale and incrementality and carries **no
   precision/recall figure**. The correct claim is "syntactically resolved; blind
   spots enumerated; accuracy unmeasured." (This overclaim does not currently
   appear in the code or docs; the framing is recorded here so it is not
   introduced later.)

**What stays well-calibrated (endorsed by the literature above).** capcov makes no
claim of formal verification; it keeps completeness as a vector rather than
collapsing it to one percentage; it names unresolved calls instead of dropping
them; it enumerates its blind spots; and it treats each branch outcome as its own
obligation. Ammann & Offutt, Chow, and the soundiness manifesto each argue for one
or more of these directly. The named risk is importing a resolver whose unsoundness
capcov can no longer enumerate — which is why the AST pass is retained as the
blind-spot enumerator (see the resolver decision above).

**Deferred.** Adopting FODA's structural variability model (mandatory/optional/
alternative facets, requires/excludes) is a future option, not undertaken here.
SCIP-as-resolver is a separate future build. Neither renames any existing code
field or verdict: `covered`, `runtime-only`, `dead`, `unproven`, `unmapped`, and
the `both`/`static_only`/`runtime_only`/`neither` cells stay exactly as they are —
this ADR documents the correspondence, it does not rename.

## References

**A. Model-based testing / FSM transition coverage**

- T. S. Chow, "Testing Software Design Modeled by Finite-State Machines," *IEEE
  Transactions on Software Engineering* SE-4(3):178–187, 1978.
  https://doi.org/10.1109/TSE.1978.231496
- Mark Utting & Bruno Legeard, *Practical Model-Based Testing: A Tools Approach*,
  Morgan Kaufmann, 2007.
- D. Lee & M. Yannakakis, "Principles and Methods of Testing Finite State Machines
  — A Survey," *Proceedings of the IEEE* 84(8):1090–1123, 1996.
  https://doi.org/10.1109/5.533956

**B. Coverage criteria as test requirements**

- Paul Ammann & Jeff Offutt, *Introduction to Software Testing*, Cambridge
  University Press, 1st ed. 2008 / 2nd ed. 2016.

**C. Name resolution, call-graph reachability, and soundiness**

- Pierre Néron, Andrew Tolmach, Eelco Visser & Guido Wachsmuth, "A Theory of Name
  Resolution," *ESOP 2015*, LNCS 9032, pp. 205–231.
  https://doi.org/10.1007/978-3-662-46669-8_9
- Douglas A. Creager & Hendrik van Antwerpen, "Stack graphs: Name resolution at
  scale," arXiv:2211.01224 (2022); *Eelco Visser Commemorative Symposium (EVCS
  2023)*, OASIcs vol. 109, art. 8. https://arxiv.org/abs/2211.01224 — reports
  scale and incrementality; **no precision/recall figure**.
- Ben Livshits, Manu Sridharan, Yannis Smaragdakis, et al., "In Defense of
  Soundiness: A Manifesto," *Communications of the ACM* 58(2):44–46, 2015.
  https://doi.org/10.1145/2644805
- Olin Shivers, "Control-Flow Analysis of Higher-Order Languages" (k-CFA), PhD
  thesis, Carnegie Mellon University, 1991.
- Jordan Samhi, René Just, Tegawendé F. Bissyandé, Michael D. Ernst & Jacques
  Klein, "Call Graph Soundness in Android Static Analysis," *ISSTA 2024*.
  https://arxiv.org/abs/2407.07804

**D. Model-vs-reality reconciliation**

- Gail C. Murphy, David Notkin & Kevin Sullivan, "Software Reflexion Models:
  Bridging the Gap between Source and High-Level Models," *ACM SIGSOFT FSE 1995*.
  https://doi.org/10.1145/222124.222136

**E. Capability decomposition**

- Kyo C. Kang, Sholom G. Cohen, James A. Hess, William E. Novak & A. Spencer
  Peterson, "Feature-Oriented Domain Analysis (FODA) Feasibility Study," Technical
  Report CMU/SEI-90-TR-21, Software Engineering Institute, 1990.

**F. Build-vs-rent (essay, not peer-reviewed)**

- Richard Sutton, "The Bitter Lesson," 2019.
  http://www.incompleteideas.net/IncIdeas/BitterLesson.html
