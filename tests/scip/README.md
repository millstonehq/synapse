# SCIP toolchain fixtures

This directory supports the `scip-go-index-smoke` flake check and the
`scip-go-index-smoke-develop` workflow gate (EXPERIMENT-PLAN.md sections 14 and 28).

Both index `packages/capabilities/tests/fixtures/go_app` (module
`github.com/example/jobsvc`; its `go.mod` has no `require` lines, so indexing needs
no network) with the pinned `scip-go`, print the result with the pinned `scip`
CLI (`scip print --json`), canonicalize it with `canonicalize.jq`, and compare the
result byte for byte with the committed golden
`packages/capabilities/tests/fixtures/scip_go_app_index.json`.

Note that `tests/fixtures/scip_go_nested_symbols.json` is an index of a different
module (`github.com/example/gonest`), not of `go_app`.

## Environment used for indexing

`HOME`, `GOCACHE`, and `GOPATH` are placed under a temporary directory and
`GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local LC_ALL=C` are exported, so the run
cannot download modules or a Go toolchain and does not depend on the host's Go
caches or locale.

## What `canonicalize.jq` changes, and why

Run it as `jq -S -f tests/scip/canonicalize.jq raw.json`; `-S` sorts object keys,
the script handles array order and host-specific content:

1. `del(.metadata.project_root)` -- the only host-specific field observed in the
   raw output. It is an absolute `file://` URI of the directory that was indexed
   (a fresh `mktemp -d` in the develop gate, the Nix build directory in the
   sandboxed check). Everything else (`relative_path`, symbols of the form
   `scip-go gomod github.com/example/jobsvc . ...`) is relative to the module, and
   the raw output was scanned for `/tmp`, `/private`, `/Users`, and `file://` with
   `project_root` removed: zero hits.
2. `documents` sorted by `relative_path`. Observed order was already sorted, but
   the emission order is not part of scip-go's contract.
3. Per document, `occurrences` sorted by `(range, symbol)` and `symbols` sorted by
   `symbol`. This step is load-bearing: two consecutive `scip-go` runs on the same
   tree in the same shell produced different `index.scip` digests and different raw
   JSON, and the difference (besides `project_root`) was purely the order of entries
   in each document's `symbols` array (Go map iteration order). The multisets were
   equal. Sort keys were checked to be unique within each document in the golden, so
   the sort yields a total order rather than a stable sort over nondeterministic input.
4. `external_symbols` normalized to a list sorted by `symbol`; scip-go omits the
   field entirely for `go_app` (no non-stdlib imports), so the golden carries `[]`.

Nothing else is rewritten: `TypedRange: null` / `TypedEnclosingRange: null`
placeholders emitted by `scip print --json` are kept as-is so the golden reflects the
pinned `scip` CLI's actual output shape.

## Regenerating the golden

Only when `scip`, `scip-go`, Go, or the fixture change, and only from the pinned
devShell:

```sh
nix develop --no-update-lock-file --command bash -lc '
  set -eu; tmp=$(mktemp -d)
  cp -R packages/capabilities/tests/fixtures/go_app "$tmp/go_app"; chmod -R u+w "$tmp/go_app"
  export HOME="$tmp" GOCACHE="$tmp/gocache" GOPATH="$tmp/gopath" GOFLAGS=-mod=mod GOPROXY=off GOTOOLCHAIN=local LC_ALL=C
  (cd "$tmp/go_app" && scip-go --output index.scip)
  scip print --json "$tmp/go_app/index.scip" | jq -S -f tests/scip/canonicalize.jq \
    > packages/capabilities/tests/fixtures/scip_go_app_index.json
  rm -rf "$tmp"'
```

Run it twice and confirm the two results are identical before committing, and record
the tool versions, store paths, and golden digest in EXPERIMENT-PLAN.md section 28.

## Known limits

- The `sha256(index.scip)` recorded under the check's `$out` is the digest of the raw
  protobuf, which embeds `project_root`; it is evidence of what that build produced,
  not a cross-run or cross-host invariant. The canonical JSON is the invariant.
- The golden was produced on `aarch64-darwin`. Linux is evaluation-only until the
  check is built there; if canonical output differs on Linux, section 28 says how the
  assertion is to be weakened (sorted symbol set plus per-document occurrence counts)
  and the difference must be recorded, not hidden.
