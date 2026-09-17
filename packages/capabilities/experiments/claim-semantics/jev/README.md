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
