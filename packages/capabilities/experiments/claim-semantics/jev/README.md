# Jev advisory binding experiment

This experiment inserts a fast semantic judgment between deterministic
candidate generation and evidence acquisition:

```text
SCIP/static facts -> Datalog candidate set -> Jev advisory -> targeted probe
                                                       \-> human review
```

Jev selects from supplied candidates; it does not generate identifiers. One
System One call asks two independent questions over the same state:

1. a `Choice` selects the candidate that directly implements the modeled
   outcome, including the mandatory `no_match` option;
2. a `Noul` estimates whether any candidate directly matches at all.

The resulting `capcov-jev-advisory-v1` artifact binds the judgment to hashes of
the full request state and candidate set and retains the complete probability
distribution. It records both the requested model alias and the concrete model
resolved by the service. It is an **assumption**, not a CapCov fact. Its contract forbids
using it as a completeness witness, compatibility witness, runtime/static
observation, or qualifying claim. A later deterministic rule may use it to
choose which probe to run; the resulting receipt is the evidence.

## Run

Set the experiment credential and assess the example:

```sh
export JEV_API_KEY=...
capcov experiment claims jev assess \
  --request packages/capabilities/experiments/claim-semantics/jev/example-request.json \
  --out jev-assessment.json \
  --claims-out jev-assumptions.json
```

For replay and tests, `--response response.json` validates a retained API
response and builds the same artifact without a network call.

The API key is read only for the request and is never written to the artifact.
`TYPESAFE_API_KEY` is accepted as a fallback for SDK-compatible environments;
`TYPESAFE_ENDPOINT` or `--endpoint` can override the endpoint.

`--claims-out` emits two producer-authorized Datalog input relations:
`jev_candidate_probability` and `jev_selected_candidate`. Both have modality
`assumption`, admit only the `jev` producer class, and deliberately provide no
rules, claims, completeness relation, or compatibility relation.

## Intended next join

The first consumer should derive a work item, not coverage:

```text
probe_requested(Route, Operation) :-
  static_candidate(Route, Operation),
  jev_advises(Route, Operation, "high").
```

`covered`, `op_qualified`, compatibility, and closure relations must continue
to depend on their existing authoritative producers.

## Neutral pattern packets and sensitivity

Patch triage has a second, stricter protocol for the case where the candidates
are causal patterns rather than program symbols. It deliberately accepts no
free-form preamble, diagnosis, or hypothesis field. SCIP and Soufflé should
first reduce the repository to neutral, provenance-bearing facts; Shen can
check that the packet shape and producer authority are valid. Jev then receives
one explicit pattern definition, its signatures and exclusions, the facts, and
a list of evidence known to be missing.

The command asks three independent Nouls: pattern match, evidence sufficiency,
and exclusion applicability. It concurrently repeats them under four
meaning-preserving forms: baseline, reversed evidence order, opaque identifiers,
and a neutral paraphrase. The caller supplies `--max-spread` as an explicit
campaign policy. A result exceeding it is retained but marked unstable; it is
not silently averaged into a stronger verdict.

```sh
capcov experiment claims jev pattern \
  --request packages/capabilities/experiments/claim-semantics/jev/example-pattern-request.json \
  --max-spread 0.20 \
  --out jev-pattern.json \
  --claims-out jev-pattern-assumptions.json
```

For offline replay, `--responses` accepts an object whose exact keys are
`baseline`, `reversed_evidence`, `opaque_ids`, and `neutral_paraphrase`.
The emitted `jev_pattern_assumption` and `jev_pattern_sensitivity` relations
remain runtime assumptions. They can rank a survivor or request the missing
probe named by the packet; they cannot qualify or close a claim.

At campaign scope, track the low-match rate and the score distribution. A
collapse toward one answer across every survivor is evidence that the request
or pattern definition is framing the result, even when per-item perturbations
are stable.
