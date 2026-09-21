# Bounded qualification measurements

`scripts/measure_qualification.py` runs a local JSON manifest one sample at a
time under the package's machine-wide heavy lock. It accepts at most eight
samples and 900 seconds of declared command time. The default lock timeout is
zero, so a live producer keeps the lock; an unacquired sample is recorded as
blocked and later samples do not start.

The report records source commit and a working-tree identity that includes the
tracked diff and non-ignored untracked files, input/output tree hashes,
native-cache snapshots, lock wait, child execution time, exit status, and
cold/warm output identity comparisons. On timeout it terminates the owned
process group and kills any descendants that remain after the grace period. It
never records command argv,
environment values, host paths, or raw inputs. The JSON report and capped
stdout/stderr tails are private files (directories mode `0700`, files mode
`0600`); each tail is limited to 16 KiB and common credential forms are
redacted.

The manifest schema is `capcov-qualification-measurement-v1`. Each sample
names a safe `id` and `phase`, `source_root`, `command` as an argv array, and
optional `input_root`, `output_root`, `cache_dir`, `env`, `timeout_seconds`,
`toolchain` revision pins, and `toolchain_binaries` (safe IDs mapped to
absolute executable paths). The report stores only each declared executable's
SHA-256 and byte size, never its path. Cold and warm samples that share
`comparison_group` have their output tree hashes compared. A `cold` sample must
start with an empty cache directory; a `warm` sample must start with a
nonempty one.

For a Bifrost shake sample, set `require_go_target: true` and provide
`shake_case`. The command must pass `--shake --json --only <case> --impls
shen-go`; the tool accepts the sample only when that exact case reports the
`shen-go` implementation as `PASS` and the detail confirms one target ran.
This rejects Bifrost's zero-target `PASS` and every skipped Go target.

The measurement plan for a qualification checkpoint is five samples: the
existing observation judge, one Stage D modelcheck invocation, one export,
and a cold then warm rejudge of that same export. Toolchain pins belong in the
manifest as revisions or binary digests. A native worker is not proposed from
these results; matching identities and at least a 2x warm end-to-end gain
would only justify a later review of that option.
