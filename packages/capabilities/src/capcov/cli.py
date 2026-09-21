"""capcov command line: discover, observe, reconcile, gate, report.

`discover` and `observe` both always run. There is no static-only mode and no
threshold that switches between them -- that was a rejected design, and what it
amounted to was a tool that sometimes does not work with the answer bolted on
beside it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

from . import artifacts
from .adapters import load as load_adapter
from .adapters import merge as merge_adapters
from .adapters import source_patterns as _adapter_source_patterns
from .core import fixpoint
from .core import gate as gate_mod
from .core import reconcile as reconcile_mod
from .probes import probe_registry


def _resolve(
    target: Path, source: str | None, adapter: str | None
) -> tuple[Path, list[tuple[str, dict | None]]]:
    """Resolve the source root and the adapter specs to run.

    An adapter spec is ``(name, config)``: ``config`` is the ``[[adapters]]`` entry
    the promoted route/contract adapters read, or ``None`` when the adapter reads
    its own ``capcov.toml`` (the stack adapter, and the ``--adapter`` override).

    Resolution (design §1.1). ``adapter`` (a single string) and ``adapters`` (a
    list) are XOR:

    * ``--adapter X`` overrides everything -> one adapter X, self-reading its
      config (``config=None``) -- today's override, unchanged.
    * ``[capcov] adapter`` -> one adapter, self-reading -- byte-identical to the
      single-adapter world: one adapter, one (merge-of-one) dict.
    * ``[[adapters]]`` -> run each with its entry as config, and merge them.
    * both ``[capcov] adapter`` and ``[[adapters]]`` set -> refused (XOR).
    """
    data: dict = {}
    config_path = target / "capcov.toml"
    if config_path.exists():
        import tomllib

        data = tomllib.loads(config_path.read_text())
    capcov = data.get("capcov", {})
    adapters_list = data.get("adapters", [])
    source_dir = target / (source or capcov.get("source", "src"))

    specs: list[tuple[str, dict | None]]
    if adapter:
        specs = [(adapter, None)]
    elif capcov.get("adapter") and adapters_list:
        raise SystemExit(
            f"both [capcov] adapter and [[adapters]] are set in {config_path}; "
            "use one -- a single adapter, or the adapters list (they are XOR)"
        )
    elif capcov.get("adapter"):
        specs = [(capcov["adapter"], None)]
    elif adapters_list:
        specs = []
        for entry in adapters_list:
            name = entry.get("name")
            if not name:
                raise SystemExit(f"an [[adapters]] entry has no name in {config_path}")
            specs.append((name, entry))
    else:
        raise SystemExit(
            f"no adapter: pass --adapter or set [capcov] adapter or [[adapters]] "
            f"in {config_path}"
        )
    if not source_dir.is_dir():
        raise SystemExit(f"source root {source_dir} does not exist")
    return source_dir, specs


def _capcov_block(target: Path) -> dict:
    """The ``[capcov]`` config block, or ``{}`` when there is no capcov.toml."""
    config_path = target / "capcov.toml"
    if not config_path.exists():
        return {}
    import tomllib

    return tomllib.loads(config_path.read_text()).get("capcov", {})


def _run_adapter(
    adapter, source_dir: Path, target: Path, name_match: bool, config: dict | None
) -> dict:
    """Run one adapter, forwarding a per-``[[adapters]]`` config when it takes one.

    The stack adapter (``python-fastapi-sqlalchemy``) reads its own config from
    capcov.toml and has no ``config`` parameter; the promoted route/contract
    adapters accept the ``[[adapters]]`` entry directly. A lone ``adapter`` string
    passes ``config=None``, so the stack-adapter call is byte-identical to today.
    """
    import inspect

    params = inspect.signature(adapter.discover).parameters
    if config is not None and "config" in params:
        return adapter.discover(source_dir, target, name_match=name_match, config=config)
    return adapter.discover(source_dir, target, name_match=name_match)


def _source_patterns(specs: list[tuple[str, dict | None]]) -> tuple[str, ...]:
    """Use the configured adapter inputs for source-bound artifact provenance.

    The rule itself lives in `capcov.adapters` -- the one place that is allowed to
    know what an adapter reads -- because the browser probe resolves the same set
    and `reconcile` refuses two artifacts hashed over different trees.
    """
    try:
        return _adapter_source_patterns(specs)
    except ValueError as error:
        # A config the adapter layer refuses (an unknown language with no
        # declared globs) is a user error, not a crash.
        raise SystemExit(f"capcov: {error}") from None


def _emit(path: Path, doc: dict, check: bool) -> int:
    """Write, or in --check mode re-render and diff against what is on disk."""
    if not check:
        artifacts.write(path, doc.pop("kind"), doc.pop("derived_from"), doc)
        return 0
    if not path.exists():
        print(f"capcov: {path} does not exist; run without --check to create it")
        return 1
    on_disk = json.loads(path.read_text())
    fresh = {"schema_version": artifacts.SCHEMA_VERSION, **doc}
    if artifacts.normalise(on_disk) == artifacts.normalise(fresh):
        return 0
    print(
        f"capcov: {path} is stale. What this system can do has changed and the "
        "committed capability set has not. Re-run without --check and read the "
        "diff -- it is the list of capabilities this change adds or removes."
    )
    _diff(artifacts.normalise(on_disk), artifacts.normalise(fresh), str(path))
    return 1


def _diff(old: str, new: str, label: str) -> None:
    import difflib

    for line in list(
        difflib.unified_diff(
            old.splitlines(True), new.splitlines(True), f"{label} (on disk)",
            f"{label} (re-derived)",
        )
    )[:80]:
        sys.stdout.write(line)


def _bounded_ms(value: object) -> int:
    return value if type(value) is int and 0 <= value <= 86_400_000 else 0


# --------------------------------------------------------------------------


def cmd_discover(args: argparse.Namespace) -> int:
    phase_started = time.perf_counter_ns()
    target = Path(args.target).resolve()
    source_dir, specs = _resolve(target, args.source, args.adapter)
    # `plugin` (present only in an [[adapters]] entry that brings a bespoke reader)
    # routes `load` to import that callable instead of a registered module. Absent
    # from every existing config, so `plugin=None` and this stays today's load.
    adapters = [load_adapter(name, plugin=(cfg or {}).get("plugin")) for name, cfg in specs]
    name_match = not args.no_name_match

    # Run every adapter and MERGE their core dicts (design §1.1/§1.2). A lone
    # adapter merges to itself -- byte-identical to today. A duplicate obligation
    # id across adapters is the collision the four-cell cannot represent, so the
    # merge refuses it loudly rather than letting one silently clobber the other
    # (R6); it never fires for a single-adapter list.
    discoveries = [
        _run_adapter(adapter, source_dir, target, name_match, config)
        for adapter, (_, config) in zip(adapters, specs)
    ]
    try:
        raw = merge_adapters(discoveries)
    except ValueError as exc:
        raise SystemExit(f"capcov discover: {exc}")

    # A deep adapter block emits a node-keyed call-graph dict (carrying
    # `_node_locations` for the (file,line)-join) that ONLY the SCIP resolver can
    # bind; without --resolver scip its `_calls` are unresolved placeholders and
    # the fixpoint would bind nothing. Deep is opt-in and the resolver stays an
    # explicit flag, so a deep block reached here without it is a misconfiguration
    # named loudly, not a silently empty capability set.
    if getattr(args, "resolver", "ast") != "scip" and "_node_locations" in raw:
        raise SystemExit(
            "capcov discover: a deep adapter block emits a call graph only "
            "--resolver scip can bind; re-run with --resolver scip"
        )

    # Optional hybrid: rent SCIP as the resolver for the call graph, keep the AST
    # pass as everything else (entities, surfaces, the enumerated blind spots).
    # The AST adapter always runs first -- it is the fallback and the enumerator;
    # SCIP only re-sources `_calls` and adds its resolved-edges + residue. It
    # re-sources ONE adapter's graph, so it is undefined across an adapters merge.
    if getattr(args, "resolver", "ast") == "scip":
        if len(adapters) != 1:
            raise SystemExit(
                "capcov discover --resolver scip: the SCIP resolver re-sources one "
                "adapter's call graph; it is not defined across an [[adapters]] merge"
            )
        from .scip import resolve as scip_resolve

        # The LANGUAGE seam (design §1.4): a promoted adapter's SCIP language is
        # per-config (go/php/python vary per [[adapters]] entry), not a module
        # constant, so read the entry's `scip_language` first (from the CLI's spec,
        # or -- for a --adapter override with no spec config -- the deep dict the
        # adapter tagged), then fall back to the adapter module's LANGUAGE.
        spec_config = specs[0][1] or {}
        language = (
            spec_config.get("scip_language")
            or raw.get("scip_language")
            or getattr(adapters[0], "LANGUAGE", "python")
        )
        # `deep` is what the adapter actually emitted: a node-keyed dict carries
        # `_node_locations`. A deep block whose SCIP tooling was absent degraded to
        # the shallow dict inside the adapter and NAMED the reason
        # (`deep-unavailable`); honor that by not shelling out to the very tool the
        # adapter already reported missing.
        deep = "_node_locations" in raw
        degraded = any(
            u.get("kind") == "deep-unavailable" for u in raw.get("unresolved", [])
        )
        if not degraded:
            try:
                raw = scip_resolve.resolve(
                    source_dir, raw, language=language, deep=deep
                )
            except scip_resolve.ScipToolsUnavailable as exc:
                raise SystemExit(f"capcov discover --resolver scip: {exc}")
    direct, calls, ops = raw["_direct"], raw["_calls"], raw["_ops"]

    roots = [s["handler"] for s in raw["surfaces"]]
    known = set(direct) | set(calls)
    missing_roots = sorted(r for r in roots if r not in known)
    per_root, history = fixpoint.bind(roots, calls, direct)

    capabilities = []
    for surface in raw["surfaces"]:
        bound = per_root.get(surface["handler"], {})
        reach = fixpoint.distances(surface["handler"], calls)
        for entity, hops in sorted(bound.items()):
            observed_ops = set()
            for node in reach:
                observed_ops |= ops.get(node, {}).get(entity, set())
            path = fixpoint.chain(surface["handler"], entity, calls, direct)
            capabilities.append(
                {
                    "entity": entity,
                    "surface": surface["id"],
                    "operations": sorted(observed_ops),
                    "evidence": {
                        "hops": hops,
                        "chain": path,
                        "kind": "direct" if hops == 0 else f"call-chain:{hops}",
                    },
                }
            )
    capabilities.sort(key=lambda c: (c["entity"], c["surface"]))

    patterns = _source_patterns(specs)
    # The fast path.  A cache hit makes this digest PROVISIONAL, and the
    # artifact says so (`source_snapshot.verification`).  It cannot reach the
    # gate on its own: reconcile requires an EXACT observed digest over the
    # same tree to agree with it, which is what makes a cached discover
    # digest authoritative -- or refuses it.
    snapshot = artifacts.snapshot_tree(source_dir, patterns)
    blind = [b for b in raw["blind_spots"] if b["blind"]]
    extractor = "capcov " + (
        adapters[0].NAME
        if len(adapters) == 1
        else "+".join(a.NAME for a in adapters)
    )
    doc = {
        "kind": "capabilities",
        "derived_from": artifacts.provenance(
            str(source_dir.relative_to(target)),
            snapshot.digest,
            extractor,
            snapshot.files,
            patterns,
            snapshot=snapshot,
        ),
        "timing": {
            "discover_ms": min(
                max(0, (time.perf_counter_ns() - phase_started) // 1_000_000),
                86_400_000,
            ),
            "source_verification": snapshot.verification,
        },
        "entities": raw["entities"],
        "surfaces": raw["surfaces"],
        "capabilities": capabilities,
        "binding_history": history,
        "blind_spots": blind,
        "resolved_dynamic_access": [
            b for b in raw["blind_spots"] if not b["blind"]
        ],
        "residue": raw["residue"],
        "residue_summary": raw["residue_summary"],
        "unbound_entry_points": missing_roots,
    }
    # When SCIP resolved the call graph, carry both halves of the hybrid into the
    # artifact: the edges SCIP resolved AND the residue it stayed silent about,
    # so coverage never reports a bare number -- resolved-by-SCIP plus
    # unresolved-enumerated, each named with a file and a line.
    if raw.get("resolver") == "scip":
        doc["resolver"] = "scip"
        doc["scip_resolved_edges"] = raw["scip_resolved_edges"]
        doc["scip_entities"] = raw["scip_entities"]
        doc["scip_residue"] = raw["scip_residue"]
        doc["scip_residue_summary"] = raw["scip_residue_summary"]
    # Honest-denominator carriers (Property 3): the promoted route/contract
    # adapters surface what static reading SAW-but-filtered (`excluded_surfaces`,
    # verb-allowlist drops) and could-not-resolve (`unresolved`: dynamic paths,
    # boundary limits, adapters that found nothing). Written conditionally --
    # exactly the scip_* pattern -- so the python-fastapi-sqlalchemy path, which
    # emits neither, is byte-identical to before (backward compatible), while a
    # route/contract discovery never drops its narrowing or its limits silently.
    if "excluded_surfaces" in raw:
        doc["excluded_surfaces"] = raw["excluded_surfaces"]
    if "unresolved" in raw:
        doc["unresolved"] = raw["unresolved"]
    rc = _emit(Path(args.out), dict(doc), args.check)
    if not args.quiet:
        bound_entities = {c["entity"] for c in capabilities}
        print(
            f"capcov discover: {len(raw['entities'])} entities, "
            f"{len(raw['surfaces'])} surfaces, {len(bound_entities)} entities bound, "
            f"history {' -> '.join(map(str, history))}, "
            f"{len(blind)} blind spots"
        )
        res = raw["residue_summary"]
        print(
            f"capcov discover: call edges {res['resolved_by_import']} by import, "
            f"{res['resolved_by_name']} by name; residue {res['ambiguous']} ambiguous "
            f"({res['external']} external, {res['chained']} chained, "
            f"{res['builtin_shadowed']} builtin-shadowed; none of these are residue)"
        )
        if missing_roots:
            print(
                "capcov discover: entry points with no analysed body: "
                + ", ".join(missing_roots)
            )
        if raw.get("resolver") == "scip":
            rs = raw["scip_residue_summary"]
            print(
                f"capcov discover: resolver scip -- {rs['scip_resolved_edges']} "
                f"edges resolved ({rs['scip_rooted_edges']} rooted in-project); "
                f"{rs['unresolved_enumerated']} of {rs['ast_call_sites']} call "
                "sites enumerated as unresolved (named, not dropped)"
            )
    return rc


def cmd_observe(args: argparse.Namespace) -> int:
    """Run the target's exercises with the selected probe installed.

    The probe writes observed.json itself. capcov sets one unified env contract
    (the ``CAPCOV_*`` variables of design §1.3, including a per-run
    ``CAPCOV_NONCE``) and hands off. The default ``pytest`` probe is
    command-driven -- capcov runs the command the target already runs and the
    pytest11 plugin does the rest, byte-identical to the pre-consolidation
    observe. The other probes (``browser``, ``load``) read the same env and drive
    their own exercise in-process, writing observed.json under the strong
    freshness guard.
    """
    phase_started = time.perf_counter_ns()
    target = Path(args.target).resolve()
    source_dir, specs = _resolve(target, args.source, args.adapter)
    probe_name = args.probe or _capcov_block(target).get("probe") or "pytest"
    probe_registry.resolve(probe_name)  # validate the name; unknown probe raises.

    out = Path(args.out)
    patterns = _source_patterns(specs)
    snapshot = artifacts.snapshot_tree(source_dir, patterns)
    # Handed to the probe as PROVISIONAL whatever this capture believed: the
    # artifact is published after the exercise, and only this process's exact
    # walk afterwards (`_publish_verified`) may stamp it exact.
    carried = artifacts.mark_provisional(
        snapshot.provenance(str(source_dir.relative_to(target)), "capcov source-snapshot")
    )
    # A successful command must publish evidence from this invocation.  The
    # command-driven pytest path cannot rely on a probe hook being installed to
    # remove yesterday's output.
    out.unlink(missing_ok=True)
    observe_env = {
        probe_registry.ENV_OBSERVE: "1",
        probe_registry.ENV_OUT: str(out.resolve()),
        probe_registry.ENV_SOURCE_ROOT: str(source_dir),
        probe_registry.ENV_TARGET: str(target),
        probe_registry.ENV_NONCE: uuid.uuid4().hex,
        probe_registry.ENV_SOURCE_PROVENANCE: json.dumps(
            carried, sort_keys=True, separators=(",", ":")
        ),
    }
    only = getattr(args, "only", None)
    if only:
        observe_env[probe_registry.ENV_ONLY] = only

    if probe_name == "pytest":
        if not args.command:
            raise SystemExit("capcov observe: give the command after --, e.g. -- pytest -q")
        env = {**os.environ, **observe_env}
        print(f"capcov observe: {' '.join(args.command)}")
        proc = subprocess.run(args.command, cwd=target, env=env)
        if proc.returncode != 0:
            print(
                f"capcov observe: the exercise failed (exit {proc.returncode}). "
                "Observation from a failing run is not evidence of anything; fix the "
                "run first."
            )
            return proc.returncode
        if not out.exists():
            print(
                f"capcov observe: the command succeeded and wrote no {args.out}. "
                "The probe did not load -- check that capcov is installed in the "
                "same environment as the exercise."
            )
            return 1
        return _publish_verified(snapshot, out, phase_started)

    # In-process probes (browser, load). They read the unified env contract and
    # drive their own exercise; the env is set for the duration of the call and
    # restored after, so a probe run leaves the caller's environment untouched.
    probe = probe_registry.load(probe_name)
    saved = {key: os.environ.get(key) for key in {*observe_env, probe_registry.ENV_ONLY}}
    try:
        os.environ.pop(probe_registry.ENV_ONLY, None)
        os.environ.update(observe_env)
        rc = probe.main(list(args.command or []))
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    if rc == 0 and not out.exists():
        print(
            f"capcov observe: the {probe_name} probe returned success but wrote no "
            f"{args.out}."
        )
        return 1
    if rc == 0:
        return _publish_verified(snapshot, out, phase_started)
    return rc


def _publish_verified(snapshot, out: Path, phase_started: int) -> int:
    """The publication boundary: one exact walk, then stamp or discard.

    The probe wrote a PROVISIONAL artifact under a carried identity and walked
    nothing.  This is the run's single byte-level verification, done in the
    process the exercise could not reach, and its result is carried outward
    onto the artifact.  A failed verification removes the artifact rather than
    leaving one whose `artifact_sha256` names a tree that is not there.
    """
    try:
        verified = snapshot.verify()
    except (ValueError, OSError) as error:
        out.unlink(missing_ok=True)
        print(
            f"capcov observe: source changed during the exercise: {error}; "
            f"discarded {out}"
        )
        return 1
    try:
        document = json.loads(out.read_text())
    except (OSError, json.JSONDecodeError):
        out.unlink(missing_ok=True)
        print(f"capcov observe: the probe wrote an unreadable {out}; discarded it")
        return 1
    if not isinstance(document, dict):
        out.unlink(missing_ok=True)
        print(f"capcov observe: the probe wrote a malformed {out}; discarded it")
        return 1
    derived_from = document.get("derived_from")
    if derived_from is not None:
        # A probe that publishes no provenance makes no claim to stamp (and
        # reconcile refuses it downstream).  One that publishes a DIFFERENT
        # identity than it was handed is not describing this run.
        try:
            if not isinstance(derived_from, dict):
                raise ValueError("derived_from is not an object")
            document["derived_from"] = artifacts.mark_exact(derived_from, verified)
        except ValueError as error:
            out.unlink(missing_ok=True)
            print(f"capcov observe: {error}; discarded {out}")
            return 1
    existing_timing = document.get("timing")
    if not isinstance(existing_timing, dict):
        existing_timing = {}
    document["timing"] = {
        **existing_timing,
        "observe_ms": min(
            max(0, (time.perf_counter_ns() - phase_started) // 1_000_000),
            86_400_000,
        ),
        "source_verification": verified.verification,
    }
    artifacts.write_document(out, document)
    return 0


JUDGE_ENGINES = ("four-cell", "claims")
JUDGE_DEFAULT = "four-cell"
JUDGE_OUT_DEFAULT = "capcov-judge"
#: Which evaluators the claims judge runs when nobody says: the stdlib kernel
#: alone, so `--judge claims` needs no optional tool either.  `souffle` and
#: `souffle-compiled` are asked for by name, exactly like `--resolver scip`.
JUDGE_EVALUATOR_DEFAULT = "python"
#: Producer profiles `--model` can run before judging.  A profile re-sources one
#: premise of the verdict from a producer the receipt did not carry; naming one
#: is the whole opt-in, exactly like `--resolver scip` and `--evaluator souffle`.
JUDGE_MODEL_PROFILES = ("shen",)
SHEN_GO_INSTALL_HINT = (
    "enter the pinned devShell with `nix develop` (it pins shen-go) and put the "
    "bifrost launcher on PATH, or name the binary in $SHEN_GO"
)


class _JudgeUsage(Exception):
    """The caller asked for a judge configuration that does not name a run.

    Reported like argparse reports a bad argument -- the message on stderr, exit
    2 -- because it is the same class of mistake, and never a claim about the
    system under test.
    """


#: capcov.toml paths this process has already said it could not read, so the
#: line below is written once per file however many `[judge]` keys are looked up
#: over it (engine, evaluator and model are three separate lookups of one file).
_JUDGE_BLOCK_UNREADABLE: set[str] = set()


def _judge_block(command: str) -> dict:
    """The working directory's ``[judge]`` table, or an empty one.

    `reconcile` and `gate` take artifact paths rather than a project root, so the
    config is read from the working directory those paths are already relative
    to.  Neither command read capcov.toml before these flags existed, so a file
    that cannot be read or parsed must not turn a working default run into a
    failure: it is passed over and the defaults stand.

    Passed over, but never in silence.  A team that opted in with ``[judge]
    engine = "claims"`` and later broke an unrelated line of that same file would
    otherwise get the four-cell gate's usual PASS and nothing anywhere saying the
    judge they believe is gating did not run -- "a flag that silently does
    nothing is how a gate goes green for the wrong reason", moved into the config
    file.  So the fallback keeps the exit code and the stdout it always had and
    names itself on **stderr**: one line saying which file could not be parsed,
    why, and what is deciding instead.  A missing capcov.toml and a well-formed
    one are untouched -- neither reaches this branch.
    """
    config = Path("capcov.toml")
    if not config.exists():
        return {}
    import tomllib

    try:
        data = tomllib.loads(config.read_text())
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        key = str(config.resolve())
        if key not in _JUDGE_BLOCK_UNREADABLE:
            _JUDGE_BLOCK_UNREADABLE.add(key)
            print(
                f"capcov {command}: {config} could not be parsed ({error}); no "
                f"[judge] key is read from it, so the judge is whatever --judge "
                f"names, or {JUDGE_DEFAULT} when it names nothing",
                file=sys.stderr,
            )
        return {}
    block = data.get("judge", {})
    return block if isinstance(block, dict) else {}


def _judge_engine(args: argparse.Namespace, command: str) -> str:
    """Which judge decides: ``--judge``, then ``[judge] engine``, then four-cell.

    With no flag and no key the answer is ``four-cell`` and nothing under
    `capcov.claims` is imported -- that is the whole point of the default.
    ``--judge`` on the command line never consults capcov.toml at all, so an
    explicit ask is never lost to an unreadable one.
    """
    engine = getattr(args, "judge", None)
    source = "--judge"
    if engine is None:
        config = Path("capcov.toml")
        engine = _judge_block(command).get("engine")
        source = f"[judge] engine in {config}"
    if engine is None:
        return JUDGE_DEFAULT
    if engine not in JUDGE_ENGINES:
        raise _JudgeUsage(
            f"capcov {command}: unknown judge engine {engine!r} ({source}); "
            f"expected one of {', '.join(JUDGE_ENGINES)}"
        )
    return engine


def _judge_evaluators(args: argparse.Namespace, command: str) -> tuple[str, ...]:
    """Which kernels judge: ``--evaluator``, then ``[judge] evaluator``, then python.

    Reached only from the claims branch, so naming an evaluator is the second
    half of an opt-in and the import below is behind it.  The default is the
    stdlib kernel alone; ``souffle`` and ``souffle-compiled`` need the Souffle
    2.5 executable, and asking for one that is not here is refused before any
    judging with a message that names the tool, where it was looked for, how to
    install it and the flag that needs nothing -- the ``--resolver scip``
    convention.  `reconcile` is the producer of coverage.json and writes it
    before the judge is reached at all, so "before any judging" is the honest
    claim, not "before any work".  ``all`` is every evaluator whose tool is
    present, so it is the one spelling that cannot fail for an absent one.
    """
    from .claims import differential

    value = getattr(args, "evaluator", None)
    source = "--evaluator"
    if value is None:
        value = _judge_block(command).get("evaluator")
        source = "[judge] evaluator in capcov.toml"
    if value is None:
        value = JUDGE_EVALUATOR_DEFAULT
        source = "the default"
    if not isinstance(value, str) and not isinstance(value, (list, tuple)):
        raise _JudgeUsage(
            f"capcov {command} --judge claims: {source} must name evaluators, got {value!r}")
    try:
        names = differential.resolve_evaluators(value)
    except differential.UnknownEvaluator as error:
        raise _JudgeUsage(f"capcov {command} --judge claims: {error} ({source})") from error
    try:
        differential.require_evaluators(names)
    except differential.EvaluatorUnavailable as error:
        raise _JudgeUsage(f"capcov {command} --judge claims: {error}") from error
    return names


def _shen_go_binary() -> str | None:
    """The shen-go binary the Stage D checker will run, or None.

    ``$BIFROST_SHEN_GO`` (what ``claims.modelcheck`` itself reads) first, then
    ``$SHEN_GO``, then ``shen-go`` on PATH.  Resolving the last two here rather
    than in ``modelcheck`` keeps the checker's own contract -- name the pinned
    binary explicitly -- exactly as it was; this is the CLI saying which binary
    the flag meant.
    """
    import shutil

    for value in (os.environ.get("BIFROST_SHEN_GO"), os.environ.get("SHEN_GO")):
        if value and os.path.isfile(value) and os.access(value, os.X_OK):
            return value
    return shutil.which("shen-go")


def _require_shen_go(command: str) -> str:
    """The binary ``--model shen`` needs, or a named refusal that judges nothing.

    The ``--resolver scip`` convention: raised before any judging, naming the tool,
    where it was looked for, how to install it, and what to do instead -- here,
    drop the flag and judge the ``model_*`` files the receipt already carries,
    which needs nothing.
    """
    import shutil

    missing = []
    if shutil.which("bifrost") is None:
        missing.append("the bifrost launcher is not on PATH")
    binary = _shen_go_binary()
    if binary is None:
        missing.append("the shen-go binary is not on PATH, $SHEN_GO or $BIFROST_SHEN_GO")
    if missing:
        raise _JudgeUsage(
            f"capcov {command} --judge claims: --model shen needs shen-go and "
            f"{'; '.join(missing)}. Install it with: {SHEN_GO_INSTALL_HINT}; or drop "
            f"--model and judge the model_* files the receipt already carries"
        )
    return binary


def _judge_model(args: argparse.Namespace, command: str) -> tuple[str, Path, str] | None:
    """Which producer profile runs before the judge: ``--model``, then ``[judge] model``.

    ``None`` -- the default -- means no profile runs, nothing under
    ``capcov.claims.modelcheck`` is imported, and the judge reads whatever
    ``model_*`` files the receipt already has.  A receipt with none is judged,
    not refused: its model premises are reported as missing and the ops they
    carry come out unresolved, which is the honest answer.

    ``PROFILE:DIR`` is the spelling (``shen:<model dir>`` today), and the
    profile's runtime is probed here, before any judging.
    """
    value = getattr(args, "model", None)
    source = "--model"
    if value is None:
        value = _judge_block(command).get("model")
        source = "[judge] model in capcov.toml"
    if value is None:
        return None
    if not isinstance(value, str) or ":" not in value:
        raise _JudgeUsage(
            f"capcov {command} --judge claims: {source} names a producer profile and a "
            f"directory, PROFILE:DIR (for instance shen:<model dir>), got {value!r}"
        )
    profile, _, directory = value.partition(":")
    if profile not in JUDGE_MODEL_PROFILES:
        raise _JudgeUsage(
            f"capcov {command} --judge claims: unknown model profile {profile!r} "
            f"({source}); expected one of {', '.join(JUDGE_MODEL_PROFILES)}"
        )
    if not directory or not Path(directory).is_dir():
        raise _JudgeUsage(
            f"capcov {command} --judge claims: --model {profile}: {directory!r} is not a "
            f"model directory"
        )
    return profile, Path(directory), _require_shen_go(command)


def _judge_out(args: argparse.Namespace, command: str, receipt: Path) -> Path:
    """Where the claims judge writes, and never inside the evidence it judges.

    The judge's own output directory contains a ``receipt.json`` of its own (its
    summary document, written by ``replay.join.write_artifacts``).  Pointed at
    the receipt it just judged it would overwrite the evidence; pointed at a
    previous ``--judge-out`` it would read that summary as if it were a receipt.
    Both are refused here, by name, before any judging.
    """
    out_dir = Path(getattr(args, "judge_out", None) or JUDGE_OUT_DEFAULT)
    resolved, evidence = out_dir.resolve(), receipt.resolve()
    if resolved == evidence or evidence in resolved.parents:
        raise _JudgeUsage(
            f"capcov {command} --judge claims: --judge-out {out_dir} is the receipt "
            f"directory {receipt} or inside it; the judge writes its own receipt.json "
            f"there and would overwrite the evidence it judged. Name a directory "
            f"outside --receipt."
        )
    return out_dir


def _judge_setup(
    args: argparse.Namespace, command: str
) -> tuple[str, tuple[str, ...], tuple[str, Path, str] | None, Path | None]:
    """Resolve the engine, the evaluators, the model profile and the output
    directory, and refuse an incoherent combination.

    ``--receipt``, ``--judge-out``, ``--evaluator`` and ``--model`` say nothing
    to the four-cell judge, so passing *any* of them without asking for the
    claims judge is refused rather than silently ignored -- including a
    ``--judge-out`` that happens to spell the default, which is why the option
    defaults to ``None`` and the default is resolved in the claims branch below.
    A flag that does nothing is how a gate ends up green for the wrong reason.
    """
    engine = _judge_engine(args, command)
    if engine == "claims":
        receipt = getattr(args, "receipt", None)
        if not receipt:
            raise _JudgeUsage(
                f"capcov {command} --judge claims: the claims judge judges a replay "
                f"receipt directory; pass --receipt DIR"
            )
        if not (Path(receipt) / "receipt.json").is_file():
            raise _JudgeUsage(
                f"capcov {command} --judge claims: {receipt} is not a replay receipt "
                f"directory (no receipt.json in it)"
            )
        out_dir = _judge_out(args, command, Path(receipt))
        return engine, _judge_evaluators(args, command), _judge_model(args, command), out_dir
    for flag, value in (("--receipt", getattr(args, "receipt", None)),
                        ("--judge-out", getattr(args, "judge_out", None)),
                        ("--evaluator", getattr(args, "evaluator", None)),
                        ("--model", getattr(args, "model", None))):
        if value is not None:
            raise _JudgeUsage(
                f"capcov {command}: {flag} is only meaningful with --judge claims"
            )
    return engine, (), None, None


def _run_model_preflight(args: argparse.Namespace, command: str,
                         model: tuple[str, Path, str]) -> int | None:
    """Run the named producer profile over the model, into the receipt directory.

    Stage D's checker (``capcov experiment claims modelcheck --model DIR --out
    <receipt>``) is the profile, reached by importing its module here -- inside
    the branch ``--model shen`` selects -- so a judge without the flag never
    loads it.  It writes ``modelcheck-certificate.json``, the transcript and,
    for a well-formed model only, the ``model_well_formed.json`` the exporter
    reads; an ill-formed verdict removes a stale one rather than leaving it.

    Returns an exit code when the run must stop, ``None`` when the judge should
    go on.  A checker that reached no verdict stops the run (exit 2): judging
    on could silently read a *previous* run's certificate and call it this
    model's.  An ill-formed model does not stop it -- the certificate says so,
    no fact was written, and the judge reports the missing premise, which is
    the honest verdict rather than a refusal.
    """
    profile, root, binary = model
    from .claims import modelcheck

    receipt = Path(args.receipt)
    # the checker names its runtime through $BIFROST_SHEN_GO and refuses to guess;
    # the flag already resolved which binary it meant (PATH / $SHEN_GO included),
    # so tell it, rather than widening what `modelcheck` will accept
    os.environ["BIFROST_SHEN_GO"] = binary
    report = modelcheck.preflight(root, out_dir=receipt)
    status = report["status"]
    if status == "unavailable":
        # probed in _judge_setup before any judging; only a racing environment gets here
        print(f"capcov {command} --judge claims: --model {profile}: the checker's runtime "
              f"became unavailable: {report['error']}", file=sys.stderr)
        return 2
    if status == "failed":
        print(f"capcov {command} --judge claims: --model {profile}: the checker reached no "
              f"verdict, so this model is unchecked: {report['error']}", file=sys.stderr)
        return 2
    digest = str(report["model"] or "")[:12]
    if status == "ill-formed":
        failures = ", ".join(f"{failure['id']}: {failure['message']}"
                             for failure in report["failures"]) or "no judgement passed"
        print(f"capcov {command} --judge claims: --model {profile}: model {digest} is "
              f"ill-formed ({failures}); no model_well_formed fact was written",
              file=sys.stderr)
        return None
    if not args.quiet:
        print(f"capcov {command} --judge claims: --model {profile}: model {digest} is "
              f"well-formed (certificate {str(report['certificate_sha256'])[:12]}); wrote "
              f"{receipt / 'model_well_formed.json'}")
    return None


def _gated_artifact(path: Path, coverage: dict, four_cell: str,
                    unexplained: int | None = None) -> dict:
    """The identity of the artifact the claims verdict was handed, for judge.json.

    A replay receipt names a run of the system under test; a coverage artifact
    names a source tree.  Neither names the other, so the CLI does not pretend
    the two are bound -- it records both identities, and the commands require
    BOTH verdicts.  Without this a judge.json read on its own could be taken for
    a verdict about whatever artifact happened to be on the command line.

    Digests and counts only, never the producing path: judge artifacts are
    publishable.
    """
    import hashlib

    derived = coverage.get("derived_from") if isinstance(coverage, dict) else None
    snapshot = derived.get("source_snapshot") if isinstance(derived, dict) else None
    document: dict = {
        "kind": "coverage",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_snapshot": snapshot if isinstance(snapshot, dict) else None,
        "summary": coverage.get("summary") if isinstance(coverage, dict) else None,
        # what the artifact's own judge said; the claims verdict is recorded
        # beside it, never instead of it
        "four_cell": four_cell,
    }
    if unexplained is not None:
        document["four_cell_unexplained"] = unexplained
    return document


def _run_claims_judge(args: argparse.Namespace, command: str,
                      evaluators: tuple[str, ...],
                      model: tuple[str, Path, str] | None = None,
                      out_dir: Path | None = None,
                      gated: dict | None = None) -> int:
    """Judge the receipt with the claims judge and collapse its verdict to pass/fail.

    The one place `capcov.cli` reaches into `capcov.claims`, and it is reached
    only from the `claims` branch, so the default path never imports it.

    Every evaluator was resolved and checked in `_judge_setup`, before any
    judging: an asked-for kernel whose tool is absent is a named, actionable exit
    2 there -- the convention `capcov discover --resolver scip` set for a missing
    indexer -- never a quiet degradation to a smaller differential here. The
    judge's own six exit codes are written into judge.json; what the CLI returns
    is 0 when every op the verdict turns on is qualified and 1 otherwise,
    because `gate` answers one question.

    ``gated`` is the identity of the artifact the calling command judged with
    its own judge, recorded into judge.json so the receipt's verdict is never
    readable as a verdict about that artifact.  The caller combines the two.
    """
    from .claims.replay import judge as claims_judge

    if model is not None:
        refusal = _run_model_preflight(args, command, model)
        if refusal is not None:
            return refusal
    receipt = Path(args.receipt)
    out_dir = Path(out_dir if out_dir is not None else (args.judge_out or JUDGE_OUT_DEFAULT))
    try:
        document, diagnostics = claims_judge.judge_receipt(receipt, out_dir, [],
                                                           evaluators=evaluators)
    except claims_judge.ReceiptContractFinding as error:
        # the receipt does not meet the exporter's contract: a finding about the
        # evidence, reported as one, never a traceback and never a verdict
        raise SystemExit(f"capcov {command} --judge claims: contract finding: {error}")
    except OSError as error:
        # the judge's own I/O -- its output directory -- not a finding about the receipt
        raise SystemExit(
            f"capcov {command} --judge claims: judge environment unavailable: {error}"
        )
    if gated is not None:
        # written after the judge, over the document it wrote: what the judge
        # decided is about the receipt, and this says what it was asked about
        # beside.  Every judge_receipt path wrote judge.json, so this rewrites
        # exactly one file, verdict included.
        document["gated_artifact"] = gated
        try:
            claims_judge.write_json(out_dir / claims_judge.JUDGE_FILE, document)
        except OSError as error:
            raise SystemExit(
                f"capcov {command} --judge claims: judge environment unavailable: {error}"
            )
    if not args.quiet and document["verdict"] in claims_judge.JUDGED_VERDICTS:
        for line in claims_judge.summary_lines(document):
            print(f"capcov {command} --judge claims: {line}")
    for line in diagnostics:
        print(f"capcov {command} --judge claims: {line}", file=sys.stderr)
    exit_code = int(document["exit_code"])
    # `--quiet` governs what this flag adds, as it governs the rest of the
    # command: the per-op summary above and this closing line are the judge's,
    # and a quiet run prints neither, leaving stdout exactly what it is without
    # `--judge claims` at all.  Nothing is lost by the silence -- judge.json
    # carries the verdict, the kernels and the judge's own exit code, and this
    # process's exit code answers the gate's question either way.  Diagnostics
    # stay on stderr, which `--quiet` has never governed.
    if not args.quiet:
        print(
            f"capcov {command} --judge claims: {document['verdict']} "
            f"(judge exit {exit_code}); kernels {', '.join(document['kernels']) or '-'}; "
            f"differential {document['differential']}; "
            f"wrote {out_dir / claims_judge.JUDGE_FILE}"
        )
    return 0 if exit_code == claims_judge.EXIT_OK else 1


def cmd_reconcile(args: argparse.Namespace) -> int:
    try:
        engine, evaluators, model, judge_out = _judge_setup(args, "reconcile")
    except _JudgeUsage as error:
        print(str(error), file=sys.stderr)
        return 2
    phase_started = time.perf_counter_ns()
    capabilities = artifacts.read(Path(args.capabilities), "capabilities")
    observed = artifacts.read(Path(args.observed), "observed")
    same, why = artifacts.same_artifact(capabilities, observed)
    if not same and not args.allow_drift:
        raise SystemExit(f"capcov reconcile: {why}")
    # The join point where a provisional digest becomes evidence or does not.
    # The observed side must be exact -- read from bytes at its publication
    # boundary.  The static side may be a cached discover; agreeing with an
    # exact digest over the same tree is what confirms it.  `--allow-drift`
    # relaxes WHICH tree, never whether the tree was read.
    try:
        runtime_verification = artifacts.snapshot_verification_of(observed["derived_from"])
    except ValueError as error:
        raise SystemExit(f"capcov reconcile: observed artifact: {error}")
    if runtime_verification != "exact":
        raise SystemExit(
            "capcov reconcile: the observed artifact is provisional (its source "
            "digest was taken from the cache, not from bytes). Produce it through "
            "`capcov observe`, which verifies the source exactly before publishing."
        )

    result = reconcile_mod.reconcile(capabilities, observed)
    reconcile_ms = min(
        max(0, (time.perf_counter_ns() - phase_started) // 1_000_000), 86_400_000
    )
    capabilities_timing = capabilities.get("timing", {})
    observed_timing = observed.get("timing", {})
    discover_ms = _bounded_ms(
        capabilities_timing.get("discover_ms")
        if isinstance(capabilities_timing, dict)
        else None
    )
    observe_ms = _bounded_ms(
        observed_timing.get("observe_ms")
        if isinstance(observed_timing, dict)
        else None
    )
    derived_from = dict(capabilities["derived_from"])
    if same and "source_snapshot" in observed["derived_from"]:
        # The static digest is the exact observed one (they agree), so the
        # coverage artifact carries the confirmed identity, not a provisional
        # one.  Under --allow-drift the trees differ and nothing is confirmed.
        derived_from["source_snapshot"] = observed["derived_from"]["source_snapshot"]
    doc = {
        "kind": "coverage",
        "derived_from": {
            **derived_from,
            "extractor": "capcov reconcile",
            "static_from": capabilities["derived_from"]["extractor"],
            "runtime_from": observed["derived_from"]["extractor"],
        },
        **result,
        "blind_spots": capabilities.get("blind_spots", []),
        "timing": {
            "discover_ms": discover_ms,
            "observe_ms": observe_ms,
            "reconcile_ms": reconcile_ms,
            "total_ms": min(discover_ms + observe_ms + reconcile_ms, 86_400_000),
        },
    }
    # Carry the hybrid's SCIP evidence through the reconcile so coverage reports
    # resolved-by-SCIP AND unresolved-enumerated -- both survive to the gate and
    # the report, and neither is collapsed into a single coverage figure. Absent
    # for an AST-resolved run, so this is backward compatible.
    for key in ("resolver", "scip_resolved_edges", "scip_residue", "scip_residue_summary"):
        if key in capabilities:
            doc[key] = capabilities[key]
    rc = _emit(Path(args.out), dict(doc), args.check)
    if not args.quiet:
        s = result["summary"]
        print(
            "capcov reconcile: "
            + ", ".join(f"{k} {s[k]}" for k in reconcile_mod.CELLS)
        )
        rs = capabilities.get("scip_residue_summary")
        if rs is not None:
            print(
                f"capcov reconcile: scip resolver -- {rs['scip_resolved_edges']} "
                f"edges resolved, {rs['unresolved_enumerated']} call sites "
                "unresolved-enumerated (each named in scip_residue)"
            )
    # The four-cell reconcile above is unchanged and coverage.json is written
    # either way -- reconcile is the producer of that artifact. What --judge
    # claims adds is a second verdict over a replay receipt: a successful
    # reconcile runs it, a failed one is reconcile's own answer and runs nothing,
    # and either way the artifact reconcile just wrote is named by digest in
    # judge.json so the receipt's verdict is never readable as a verdict on it.
    if engine == "claims" and rc == 0:
        out = Path(args.out)
        gated = (_gated_artifact(out, doc, "reconciled") if out.is_file() else None)
        return _run_claims_judge(args, "reconcile", evaluators, model, judge_out, gated)
    return rc


def cmd_gate(args: argparse.Namespace) -> int:
    try:
        engine, evaluators, model, judge_out = _judge_setup(args, "gate")
    except _JudgeUsage as error:
        print(str(error), file=sys.stderr)
        return 2
    coverage = artifacts.read(Path(args.coverage), "coverage")
    exemptions = Path(args.exemptions) if args.exemptions else None
    failures = gate_mod.gate(coverage, exemptions)
    rc = _report_gate(args, coverage, failures)
    if engine != "claims":
        return rc
    # `--judge claims` ADDS a verdict; it never speaks for the coverage artifact.
    # The receipt names a run of the system under test and the artifact names a
    # source tree, so nothing in either binds them: the gate runs both judges,
    # records the artifact's identity and its own verdict in judge.json, and
    # passes only when both pass.  Anything else makes the positional argument
    # decorative -- any supported receipt would turn any artifact green.
    judged = _run_claims_judge(args, "gate", evaluators, model, judge_out,
                               _gated_artifact(Path(args.coverage), coverage,
                                               "pass" if rc == 0 else "fail",
                                               len(failures)))
    if rc != 0:
        print(
            "capcov gate --judge claims: the four-cell gate over this coverage "
            f"artifact failed ({len(failures)} unexplained), so the gate fails "
            "whatever the receipt says: the claims judge adds a verdict, it does "
            "not replace the artifact's",
            file=sys.stderr,
        )
    return 0 if rc == 0 and judged == 0 else 1


def _report_gate(args: argparse.Namespace, coverage: dict, failures: list) -> int:
    """The four-cell gate's own answer, printed exactly as it always was.

    Split out of `cmd_gate` so it runs under either judge: the artifact's own
    verdict is not something an opt-in flag may skip.
    """
    if not failures:
        s = coverage["summary"]
        print(
            f"capcov gate: PASS -- {s['both']} capabilities covered, "
            f"{sum(s[c] for c in reconcile_mod.FAILING_CELLS)} exempted with reasons"
        )
        return 0
    print(f"capcov gate: FAIL -- {len(failures)} unexplained\n")
    for failure in failures:
        print(f"  {failure}\n")
    where = args.exemptions or "an exemptions file (--exemptions)"
    print(
        "Each of these is a question with an answer: write the test, fix the "
        f"adapter, delete the dead entity, or record why in {where}."
    )
    return 1


def cmd_report(args: argparse.Namespace) -> int:
    coverage = artifacts.read(Path(args.coverage), "coverage")
    width = max(len(r["entity"]) for r in coverage["rows"])
    print(f"{'entity'.ljust(width)}  cell          tests  surfaces  operations")
    for row in coverage["rows"]:
        print(
            f"{row['entity'].ljust(width)}  {row['cell'].ljust(12)}  "
            f"{len(row['tests']):>5}  "
            f"{len(row['static_surfaces'] or row['runtime_surfaces']):>8}  "
            f"{','.join(row['runtime_operations'] or row['static_operations'])}"
        )
    s = coverage["summary"]
    print("\n" + ", ".join(f"{k}: {s[k]}" for k in reconcile_mod.CELLS))
    unexercised = coverage.get("unexercised_surfaces", [])
    if unexercised:
        print(f"\nsurfaces no exercise reached ({len(unexercised)}):")
        for surface in unexercised:
            print(f"  {surface}")
    if coverage["blind_spots"]:
        print(f"\nstatic blind spots ({len(coverage['blind_spots'])}):")
        for spot in coverage["blind_spots"]:
            print(f"  {spot['file']}:{spot['line']}  {spot['expr']}  ({spot['kind']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    actual = sys.argv[1:] if argv is None else argv
    if actual and actual[0] == "outcomes":
        from .outcomes import main as outcomes_main

        return outcomes_main(actual[1:])
    if actual and actual[0] == "flows":
        from .flows.cli import main as flows_main

        return flows_main(actual[1:])
    if actual and actual[0] == "features":
        from .features.cli import main as features_main

        return features_main(actual[1:])
    if actual and actual[0] == "experiment":
        # Experimental namespace (EXPERIMENT-PLAN section 18); production
        # commands and their argparse below are untouched.
        from .claims.cli import main as experiment_main

        return experiment_main(actual[1:])
    parser = argparse.ArgumentParser(prog="capcov", description=__doc__)
    parser.add_argument("--quiet", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("flows", help="source obligations, flow planning, and browser outcome evidence")
    sub.add_parser("outcomes", help="scoped behavior obligations and fresh pytest evidence")
    sub.add_parser("features", help="FODA feature-model validation, configuration check, coverage rollup")

    def common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--target", default=".", help="the project root")
        p.add_argument("--source", default=None, help="source root under --target")
        p.add_argument("--adapter", default=None)
        p.add_argument("--quiet", action="store_true")

    def judge_options(p: argparse.ArgumentParser) -> None:
        """The opt-in claims judge, off unless asked for -- the --resolver scip shape.

        With no flag and no ``[judge] engine`` key nothing under `capcov.claims`
        is imported and the command behaves exactly as it did before these
        options existed.
        """
        p.add_argument(
            "--judge",
            choices=JUDGE_ENGINES,
            default=None,
            help="which judge decides: 'four-cell' (default, today's behavior) or "
            "'claims' (the replay judge over a receipt directory; needs --receipt DIR). "
            "Falls back to [judge] engine in capcov.toml, then four-cell.",
        )
        p.add_argument(
            "--evaluator",
            default=None,
            metavar="NAME[,NAME...]",
            help="which kernels --judge claims runs: 'python' (default, stdlib only), "
            "'souffle', 'souffle-compiled' (both need the souffle 2.5 executable on "
            "PATH or $SOUFFLE), a comma list of them, or 'all' for every one present. "
            "Two or more run the fail-closed differential; one records "
            "differential 'not-run (single evaluator)'. Falls back to [judge] "
            "evaluator in capcov.toml, then python.",
        )
        p.add_argument(
            "--model",
            default=None,
            metavar="PROFILE:DIR",
            help="run a producer profile over a model before judging: 'shen:DIR' "
            "typechecks the Shen domain model in DIR (Stage D) and writes "
            "model_well_formed.json and the certificate into --receipt. Needs shen-go "
            "(bifrost plus $SHEN_GO/$BIFROST_SHEN_GO or shen-go on PATH) and is refused "
            "by name when it is absent. Without the flag the judge reads the model_* "
            "files the receipt already carries. Falls back to [judge] model in "
            "capcov.toml.",
        )
        p.add_argument(
            "--receipt",
            default=None,
            help="the replay receipt directory --judge claims judges (required with it)",
        )
        p.add_argument(
            "--judge-out",
            default=None,
            help="where --judge claims writes judge.json and the certificates "
            "(default: capcov-judge); must be outside --receipt",
        )

    d = sub.add_parser("discover", help="static: entities, surfaces, bindings")
    common(d)
    d.add_argument("--out", default="capabilities.json")
    d.add_argument("--check", action="store_true", help="re-derive and diff")
    d.add_argument(
        "--no-name-match",
        action="store_true",
        help="resolve calls through imports only; report every name-match as residue",
    )
    d.add_argument(
        "--resolver",
        choices=("ast", "scip"),
        default="ast",
        help="call-graph resolver: 'ast' (default, hand-rolled, stdlib-only) or "
        "'scip' (type-aware cross-file; needs a SCIP indexer + the scip CLI). "
        "The AST pass runs either way and stays the blind-spot enumerator.",
    )
    d.set_defaults(func=cmd_discover)

    o = sub.add_parser("observe", help="runtime: run the exercises with the probe")
    common(o)
    o.add_argument("--out", default="observed.json")
    o.add_argument(
        "--probe",
        default=None,
        help="runtime-evidence probe: 'pytest' (default, unchanged) | 'browser' | "
        "'load' | 'har'. Falls back to [capcov] probe, then pytest.",
    )
    o.add_argument(
        "--only",
        default=None,
        help="optional inner-loop selector, passed to the probe as CAPCOV_ONLY",
    )
    o.add_argument("command", nargs=argparse.REMAINDER)
    o.set_defaults(func=cmd_observe)

    r = sub.add_parser("reconcile", help="the four-way diff")
    r.add_argument("capabilities")
    r.add_argument("observed")
    r.add_argument("--out", default="coverage.json")
    r.add_argument("--check", action="store_true")
    r.add_argument("--quiet", action="store_true")
    r.add_argument(
        "--allow-drift",
        action="store_true",
        help="compare artifacts derived from different trees (it is not a finding)",
    )
    judge_options(r)
    r.set_defaults(func=cmd_reconcile)

    g = sub.add_parser("gate", help="fail on anything unexplained")
    g.add_argument("coverage")
    g.add_argument("--exemptions", default=None)
    g.add_argument("--quiet", action="store_true")
    judge_options(g)
    g.set_defaults(func=cmd_gate)

    p = sub.add_parser("report", help="human-readable coverage table")
    p.add_argument("coverage")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    if args.command if hasattr(args, "command") else False:
        args.command = [a for a in args.command if a != "--"]
    return args.func(args)
