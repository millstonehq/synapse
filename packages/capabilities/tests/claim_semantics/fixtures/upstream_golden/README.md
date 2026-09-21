# upstream_golden — what capcov does with no flags and no optional tools

The baseline this branch must not move. Every artifact here was produced by
**upstream main**, from a separate read-only checkout, with the optional
toolchain hidden from `PATH` and no extras installed. Our branch's job is to
reproduce all of it byte-for-byte after normalization when no flag and no
`capcov.toml` key asks for anything new.

## Provenance

| | |
|---|---|
| upstream commit | `649be7f84f5cb191531e3f65688615f16f55bb65` (`649be7f`, "Merge pull request #51 from pyrex41/perf/blob-keyed-snapshot-cache") |
| package | `packages/capabilities` of that checkout, referred to below as `<upstream>/packages/capabilities` |
| python | CPython **3.13.12** (`3.13.12 (main, Feb  3 2026, 17:53:27) [Clang 21.1.7]`), the host interpreter — no `nix develop`, no venv |
| installed extras | **none**. `tree_sitter`, `tree_sitter_language_pack`, `pytest`, `yaml` are all absent from the interpreter |
| date produced | 2026-09-17 |

### The hidden PATH

Every command below ran under a scrubbed environment built with `env -i`, so no
inherited variable (`SCIP_CLI`, `SCIP_PHP_BIN`, `JEV_API_KEY`, `VIRTUAL_ENV`, …)
could reach the process:

```
PATH=<python-bindir>:/usr/bin:/bin:/usr/sbin:/sbin
env -i PATH="$PATH" HOME="$HOME" TERM=dumb LANG=en_US.UTF-8 \
       PYTHONPATH="<upstream>/packages/capabilities/src" …
```

`<python-bindir>` is the host CPython 3.13.12 `bin` directory; it holds only
`python*`/`pydoc*`/`idle*` and no indexer. It is placed **first** so `python3`
does not resolve to the macOS system 3.9.6 in `/usr/bin`.

Verified absent under that PATH: `souffle`, `scip`, `scip-go`, `shen-go`, `go`,
`node`. (On the unhidden host PATH `shen-go` *is* present at `~/.local/bin`; the
hidden PATH is what removes it. The other five are absent host-wide.)
`git` resolves to `/usr/bin/git`, which upstream's own
`tests/test_cli_engine.py` needs to fetch its pre-unification baseline blob.

## 1. Historical upstream full unittest suite

The suite transcript below remains the run from `1b6a47a`. It is retained as
historical context and is not used by the byte comparison. The CLI artifacts
and manifest provenance were refreshed at `649be7f` after the upstream blob
cache added three source-verification fields; the optional-profile gate runs
the focused artifact comparison from an installed wheel.

```
cd <upstream>/packages/capabilities
PYTHONPATH="$PWD/src" python3 -m unittest discover -s tests -t . -v
```

Result: **`Ran 672 tests` — `OK (skipped=125)`**, exit 0.
`suite/summary.txt` and `suite/skips.txt` are the two result lines and the skip
histogram, and they are what is committed: the full `-v` transcript is a `*.log`
(gitignored, and 130 KB of per-test lines that say nothing the histogram does
not), so it is reproduced by re-running the command above rather than stored.

All 125 skips are genuine tool/extra absence, not silent green:

```
 90  treesitter extra not installed
  8  deep PHP e2e needs the treesitter extra + php + the standalone scip-php script (SCIP_PHP_BIN) + the scip CLI
  6  needs scip-python + the scip CLI (set SCIP_CLI)
  6  deep Go e2e needs the treesitter extra + scip-go + the scip CLI + go on PATH
  5  requires target pytest
  3  deep go/php hybrid census needs the treesitter extra
  3  capture-name contract needs the treesitter extra
  2  needs both scip-python and the scip CLI (set SCIP_CLI)
  1  scip-python not installed
  1  deep join census needs the treesitter extra
```

### The one PYTHONPATH gotcha

With a **relative** `PYTHONPATH=src` the suite reports `672 tests, FAILED
(failures=1, skipped=125)`. The single failure is
`tests/test_feature_evidence.py::…::test_cli_reconciles_in_a_real_subprocess`,
which spawns `python -m capcov` with `cwd=<a temp dir>`; the relative `src`
entry no longer resolves from that cwd and the child dies with `No module named
capcov`. It is an artifact of the *invocation*, not of upstream. **Use an
absolute `PYTHONPATH`** (as above) — then it is a clean `OK`. Our branch must be
compared against the absolute-PYTHONPATH number: **672 / OK / 125 skipped**.

## 2. The CLI goldens

Regenerate with `generate.py` then `normalize.py` (both committed here; see the
module docstrings). Layout, per command `X`:

* `X.cmd` — the exact argv, with paths already tokenized
* `X.stdout`, `X.stderr`, `X.exit` — captured verbatim
* `X.error_line` — for failing runs, the last non-empty stderr line (the stable
  contract; the traceback above it moves with any edit to `cli.py`)
* sibling `*.json` — the artifact the command wrote, when it wrote one

| directory | what it pins | exit |
|---|---|---|
| `go_app/` | `discover` on `tests/fixtures/go_app` with no extras | 1 |
| `go_app/` | the same with `--resolver scip` | 1 |
| `python_app/` | the whole `discover → observe → reconcile → gate → report` pipeline | 0,0,0,**1**,0 |
| `python_app/` | `discover --resolver scip` with no indexer | 1 |
| `structured_spec/` | `discover` on an OpenAPI document (the honest-denominator carriers) | 0 |
| `flows/` | `capcov flows coverage` and `capcov flows gate` | 0 |
| `features/` | `capcov features validate` on the shipped example model, and `--help` | 0 |
| `outcomes/` | `capcov outcomes --help` | 0 |
| `cli/` | `capcov --help` and each subcommand's `--help` | 0 |

### go_app needs an extra, so with no extras it names it

`tests/fixtures/go_app` is driven by `treesitter-routes`; upstream's own
`test_deep_go_e2e.py` gates on the `treesitter` extra **plus** `scip-go` + the
`scip` CLI + `go`. With none of them the run does not produce a degraded
artifact and does not go green — it exits 1 with

```
ValueError: treesitter-routes needs the 'treesitter' extra
```

and writes no `capabilities.json`. `--resolver scip` on the same fixture fails
identically (the adapter is reached before the resolver). There is therefore no
`go_app/coverage.json` and no `go_app` gate to record: with no extras the go
fixture never gets past `discover`, so `python_app/` is the golden for
`reconcile` and `gate`. This is the shape our
additions must copy.

### `--resolver scip`, the convention being copied

On a project that *does* run with no extras (`python_app/`), asking for the
opt-in resolver without the tool gives the named, actionable message and
exit 1 — and writes nothing:

```
capcov discover --resolver scip: --resolver scip needs the python indexer
'scip-python', which is not on PATH. Install it with:
npm install -g @sourcegraph/scip-python
```

### The python_app pipeline

A throwaway project built from upstream's own `tests/support.py::APP` fixture
(the python-fastapi-sqlalchemy tree that `test_cli_engine.py` uses for its
byte-identity test), with `capcov.toml`:

```toml
[capcov]
adapter = "python-fastapi-sqlalchemy"
source = "src"
probe = "load"
```

`observe` uses the in-process `load` probe, the one probe that self-drives with
no command and no `pytest` — so the pipeline completes with zero extras. Headline
numbers, all pinned in the files:

* `discover`: 3 entities, 5 surfaces, 3 entities bound, history `2 -> 2 -> 3 -> 3`, 2 blind spots; 8 call edges by import, 0 by name, residue 0
* `reconcile`: `both 0, static_only 3, runtime_only 0, neither 0`
* `gate`: **FAIL — 4 unexplained**, exit 1 (3 static-only entities + the `load` probe's own `unresolved:load:driver`). The `load` probe ships the contract, not the observation; it is meant to fail the gate, and that failure is the baseline.
* `report`: exit 0, the table plus 4 unreached surfaces and the 2 blind spots

**Neither `excluded_surfaces` nor `unresolved` appears in
`python_app/capabilities.json`** (the `scip_*` conditional pattern — absent keys
on the python path); both **do** appear in `structured_spec/capabilities.json`.
Any new top-level key on either of those documents is a regression.

## 3. Normalization

`normalize.py` is a **textual** pass — no JSON re-dump — so key order, indent and
whitespace are pinned exactly as upstream emitted them. Three classes of value
are rewritten, and nothing else:

| what | from | to | why |
|---|---|---|---|
| producing-machine paths | absolute prefixes, longest first | `<root>` (the throwaway project tree), `<out>`, `<scratch>`, `<upstream>`, `<home>` | run-specific, and the public-repo rule forbids machine home paths |
| `"extracted_at"` | ISO-8601 instant | `"<timestamp>"` | wall clock |
| any `"<name>_ms"` | int | `0` | wall clock: `discover_ms`, `observe_ms`, `reconcile_ms`, `total_ms`, `duration_ms` |

`suite/summary.txt` additionally has `Ran N tests in <elapsed>s` tokenized (the
same rule a re-run's transcript needs: per-test `(<elapsed>)` and
`/tmp/tmpXXXXXXXX` temp dirs).

**Deliberately NOT normalized:** `derived_from.source_snapshot`, its
`artifact_sha256`, file counts, every capability/surface/entity/binding, every
summary count, blind-spot `file:line`, and all human text. Those are the
contract.

Determinism was **measured, not assumed**: `generate.py` was run twice into two
separate raw trees; the only differences were `extracted_at`, `*_ms`, and the
raw-directory prefix. After `normalize.py` the two trees `diff -r` clean —
byte-identical. That is the sole justification for the three rules above.

`MANIFEST.json` carries the upstream commit and a sha256 for every file here, so
a later comparison can prove it read *these* bytes.

## How to check our branch against this

From our `packages/capabilities`, with the same hidden PATH and host python:

```bash
python3 <golden>/generate.py  /tmp/raw          # CAPCOV_CAP_ROOT=<our>/packages/capabilities
python3 <golden>/normalize.py /tmp/raw /tmp/cmp \
    "/tmp/raw/_work=<root>" "/tmp/raw=<out>" "<our>/packages/capabilities=<upstream>/packages/capabilities"
diff -r <golden> /tmp/cmp      # ignoring README.md / MANIFEST.json / generate.py / normalize.py / suite/
```

Anything that differs is a place our additions leaked into the default path.
