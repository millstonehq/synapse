"""Experimental CLI for the claim-semantics workbench (EXPERIMENT-PLAN section 18).

Reached only through the ``experiment`` namespace of ``capcov``::

    capcov experiment claims jev assess --request REQUEST.json
    capcov experiment claims jev pattern --request REQUEST.json --max-spread .2
    capcov experiment claims shen authority (--bundle B.json | --rules PACK.json)
    capcov experiment claims shen evaluate --bundle B.json --relation R --row '[...]'
    capcov experiment claims shen why-not  --bundle B.json --relation R --row '[...]'

Every command prints one JSON document on stdout.  Exit status: 0 when the
authority verdict is ok / the row is derivable / a why-not report was
produced; 1 when the authority verdict is not ok or the row is not
derivable (a semantic answer, not an error); 3 for a named operational
failure of the Shen runtime (``ShenUnavailable`` / ``ShenFailure``), whose
JSON carries ``operational_failure``; 2 for usage errors.

Stage D's model checker (``claims/modelcheck.py``) is reached the same way::

    capcov experiment claims modelcheck --model DIR [--out DIR] [--timeout S] [--keep]

It typechecks the Shen domain model under ``DIR`` (``DIR/shen/load.shen``) and
prints the certificate; with ``--out`` it writes ``modelcheck-certificate.json``,
the transcript, ``model_well_formed.json`` for valid global structure, and
``model_operation_checked.json`` for successful operation-local checks. Exit 0
when global structure is well formed (operation judgements may still fail), 1
when global structure is ill formed, and 3 for a checker or runtime failure.

The static producer profile (``claims/static/scip_facts.py`` plus
``claims/static/closure.py``) is reached the same way::

    capcov experiment claims static --static scip --target TREE [--language go]
        [--ast-raw AST.json] [--scope all|package:PREFIX|documents:A,B] [--out BUNDLE.json]

It indexes the tree with the SCIP toolchain, exports the static facts exactly as
the exporter always has, and ADDITIONALLY emits the resolver's enumerated
residue as ``static_unresolved_call_site`` rows plus, for each scope whose
residue is empty, the ``call_graph_closed`` witness a negative static claim needs
(``rules-static-closure-v1``).  Exit 0 with a bundle, 2 for a usage refusal, 3
for a named operational failure -- an absent SCIP toolchain reported in
``capcov discover --resolver scip``'s own words among them.

The advisory profile is reached the same way and is the one profile nothing may
depend on::

    capcov experiment claims jev [ARGS...]

``jev`` is the Jev pattern reviewer: it talks to a network service with
``$JEV_API_KEY`` and returns patterns a reader weighs.  No claim, premise or
verdict is derived from it, which is what *advisory* means here -- a checkout
without the module, without the key or without the network judges exactly the
same.  Its module (``claims/jev.py``) is imported inside this branch only, so
naming any other command never loads it, and when it is not part of the
checkout the command answers with a named ``profile-unavailable`` refusal
(exit 3) rather than an ImportError.

The assumption registry (``claims/assumptions.py``) is reached the same way::

    capcov experiment claims assumptions registry   --receipt DIR [--out DIR]
    capcov experiment claims assumptions invalidate --receipt DIR --drop ID [--drop ID]

``--evaluator`` chooses the kernels both commands judge with: ``python``
(the default, standard library only), ``souffle``, ``souffle-compiled``, a
comma list of them, or ``all`` for every one whose tool is present.  Naming one
that is not here is a refusal (exit 2) that names the tool and how to install
it; the default needs nothing, so a bare invocation judges in any checkout.

``registry`` judges a replay receipt with the target-go join and prints the A2
registry document; ``invalidate`` additionally withdraws each ``--drop``
assumption (an ``asm:`` id or the evidence id of an assumption row -- either
way every record attesting that assumption is withdrawn), prints one A3
document per drop and, with ``--out``, writes ``assumptions.json`` and
``invalidation-<id12>.json`` beside the join's ``receipt.json``.  Exit 0 when
the documents were produced, 2 for a refusal (the exporter refused the receipt,
an unknown id, or a withdrawal that would refute a claim), 3 when the two
kernels disagree on the withdrawn bundle (the replay path is printed).

Two shapes a consumer has to know, stated here because they are the contract:

* stdout is a **wrapper**, not a bare document: ``{"registry": <A2>}`` for
  ``registry`` and ``{"registry": <A2>, "invalidations": [<A3>, ...]}`` for
  ``invalidate``.  ``--out DIR`` writes the bare documents as files.
* ``--receipt`` is optional and **defaults to the committed fixture receipt**
  (``CAPCOV_REPLAY_RECEIPT_DIR`` overrides it).  A bare invocation therefore
  judges the fixture rather than refusing; pass ``--receipt`` to judge a run.

Both assumption commands need the target-go join (``tests/claim_semantics``),
which carries the experiment's fixtures and is not part of the installed
package.  ``_join_module`` finds it on ``sys.path`` when the checkout's
``tests`` package is importable and otherwise beside this package, and refuses
with exit 2 -- never a traceback -- when neither is there.  The refusals that
say nothing about the join are answered *before* it is reached, so a bad
``--receipt`` is named as a bad ``--receipt`` wherever the command runs.

``--out`` is a **directory** for these two commands (the join's artifacts),
unlike the ``shen`` commands where it is a file, so a refusal or a kernel
mismatch is printed on stdout only and never written into it.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from typing import Any

from pathlib import Path

from .ir import BundleIngestionError, bundle_from_json
from .validation import ValidationError

#: The producer profiles this namespace can run, and the module each one lives
#: in.  Every profile is imported inside the branch that names it and nowhere
#: else, so registering one costs nothing: a checkout without the module, the
#: key or the runtime it needs still parses and runs every other command, and a
#: caller who never names the profile never loads it.  ``shen`` is the semantic
#: workbench, ``modelcheck`` Stage D's typed checker, ``jev`` the *advisory*
#: pattern reviewer -- advisory because nothing in a verdict may depend on it:
#: it needs a network service and ``$JEV_API_KEY``, and its output is a report,
#: never a premise.
PROFILE_MODULES = {
    "shen": "capcov.claims.shen",
    "modelcheck": "capcov.claims.modelcheck",
    "jev": "capcov.claims.jev",
}


def _emit(document: Any, out: str | None) -> None:
    text = json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False)
    if out:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)


def _load_bundle(path: str):
    with open(path, encoding="utf-8") as handle:
        return bundle_from_json(handle.read())


def _load_json(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _row(text: str) -> list[Any]:
    row = json.loads(text)
    if not isinstance(row, list):
        raise argparse.ArgumentTypeError("--row must be a JSON array")
    return row


def _common(parser: argparse.ArgumentParser, *, need_row: bool) -> None:
    parser.add_argument("--bundle", required=need_row, help="schema-v1 bundle JSON")
    parser.add_argument("--rules", default=None,
                        help="rule pack JSON (authority: the pack to check; evaluate/why-not: must be contained in the bundle)")
    parser.add_argument("--frozen", default=None, help="frozen elaborated-pack checksum the Shen side must reproduce")
    parser.add_argument("--timeout", type=float, default=None, help="hard per-call timeout in seconds (default 60)")
    parser.add_argument("--keep", action="store_true", help="keep the generated driver directory")
    parser.add_argument("--out", default=None, help="also write the JSON document to this file")
    if need_row:
        parser.add_argument("--relation", required=True)
        parser.add_argument("--row", required=True, type=_row, help="JSON array of the conclusion row")
        # the defaults live in ``static.certificate`` and are read once the shen
        # profile is imported, so building the parser imports nothing
        parser.add_argument("--max-depth", type=int, default=None)
        parser.add_argument("--max-nodes", type=int, default=None)


#: How the target-go join is named once the checkout is on ``sys.path``: as part
#: of the ``tests`` package (``unittest discover -t .``), as ``claim_semantics``
#: (``discover -s tests``), or top-level (``discover -s tests/claim_semantics``).
_JOIN_MODULES = ("tests.claim_semantics.target_go.replay_join",
                 "claim_semantics.target_go.replay_join",
                 "target_go.replay_join")


def _is_receipt_dir(path: Path) -> bool:
    """A receipt is a directory carrying ``receipt.json`` -- not a file, not an empty directory."""
    return path.is_dir() and (path / "receipt.json").is_file()


def _join_module():
    """The target-go replay join lives beside its fixtures, under ``tests/claim_semantics``.

    Source-checkout only, deliberately: the join carries the experiment's
    fixtures and is not part of the installed package.  Import wins over the
    path probe, because ``capcov`` being an installed wheel says nothing about
    whether the checkout's tests are on ``sys.path`` -- they are, for instance,
    when the release job runs ``unittest discover`` against the installed
    interpreter -- while the path beside an installed ``capcov`` names a
    directory that does not exist.
    """
    for name in _JOIN_MODULES:
        try:
            return importlib.import_module(name)
        except ImportError:
            continue
    tests = Path(__file__).resolve().parents[3] / "tests" / "claim_semantics"
    if not (tests / "target_go" / "replay_join.py").is_file():
        raise FileNotFoundError(f"the replay join was not found under {tests}")
    if str(tests) not in sys.path:
        sys.path.insert(0, str(tests))
    from target_go import replay_join  # noqa: E402
    return replay_join


def _assumptions(args: argparse.Namespace) -> int:
    """``claims assumptions registry|invalidate`` over a replay receipt directory."""
    import shutil
    import tempfile

    from .assumptions import InvalidationError
    from . import differential as differential_mod
    from .differential import DifferentialMismatch, EvaluatorMismatch

    # --out names a DIRECTORY here (the join's artifacts), so every document
    # below is printed and never written to it -- writing a refusal to --out
    # raised IsADirectoryError on top of the refusal it was trying to report.
    def emit(document: dict[str, Any]) -> None:
        _emit(document, None)

    # an explicit --receipt is judged before the join is reached: a path that is
    # not a receipt directory is a bad argument, and saying so does not depend
    # on the experiment's fixtures being importable
    receipt = Path(args.receipt) if args.receipt else None
    if receipt is not None and not _is_receipt_dir(receipt):
        emit({"refusal": "no receipt directory (pass --receipt DIR)"})
        return 2
    # the evaluators are resolved and checked before the join is reached, so an
    # absent souffle is named as an absent souffle wherever the command runs
    try:
        evaluators = differential_mod.resolve_evaluators(args.evaluator)
        differential_mod.require_evaluators(evaluators)
    except (differential_mod.UnknownEvaluator, differential_mod.EvaluatorUnavailable) as exc:
        emit({"refusal": str(exc)})
        return 2
    try:
        replay_join = _join_module()
    except (FileNotFoundError, ImportError) as exc:
        emit({"refusal": f"the replay join is unavailable: {exc}"})
        return 2
    if receipt is None:
        receipt = replay_join.receipt_dir()
        if receipt is None or not _is_receipt_dir(receipt):
            emit({"refusal": "no receipt directory (pass --receipt DIR)"})
            return 2
    owned = args.replay_root is None
    replay_root = args.replay_root or tempfile.mkdtemp(prefix="capcov-assumptions-")
    # a kernel disagreement is the one outcome whose evidence lives in the
    # replay root, so that is the one case an owned temporary root survives
    keep = False
    try:
        admissions = ()
        if args.reviewer_admissions:
            try:
                admissions = _load_json(args.reviewer_admissions)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                emit({"refusal": "reviewer admissions are not readable JSON"})
                return 2
        try:
            join = replay_join.build(receipt, reviewer_admissions=admissions)
            if join.bundle is None:
                emit({"refusal": "the exporter refused the receipt",
                      "contract_findings": list(join.contract_findings)})
                return 2
            replay_join.evaluate_join(join, replay_root, evaluators=evaluators)
            if join.mismatch is not None:
                keep = True
                emit({"kernel_mismatch": "the kernels disagree on the join",
                      "replay": str(join.mismatch.replay_path)})
                return 3
            document: dict[str, Any] = {"registry": replay_join.assumption_registry(join)}
            if args.command == "invalidate":
                document["invalidations"] = [replay_join.invalidate(join, drop, replay_root).as_dict()
                                             for drop in args.drop]
        except (DifferentialMismatch, EvaluatorMismatch) as exc:
            keep = True
            emit({"kernel_mismatch": "the kernels disagree on the withdrawn bundle",
                  "replay": str(exc.result.replay_path)})
            return 3
        except AssertionError as exc:
            # certify_claims: the kernels agree on the rows but not on the claim
            # rows or the certificates of the withdrawn bundle -- a judge with
            # two answers has none, so this is exit 3 like any other mismatch
            keep = True
            emit({"kernel_mismatch": "the kernels disagree on the claims of the withdrawn bundle",
                  "error": str(exc), "replay": replay_root})
            return 3
        except (InvalidationError, ValidationError) as exc:
            emit({"refusal": str(exc)})
            return 2
        if args.out:
            replay_join.write_artifacts(join, Path(args.out))
        emit(document)
        return 0
    finally:
        if owned and not keep:
            shutil.rmtree(replay_root, ignore_errors=True)


class _ProfileUnavailable(RuntimeError):
    """A producer profile's module could not be imported."""


def _profile(name: str):
    """Import the module a producer profile lives in, or say which one is missing.

    A profile that is not part of this checkout is a named refusal, never an
    ImportError traceback: the namespace is a workbench, and a missing optional
    profile says nothing about the profiles that are here.
    """
    try:
        return importlib.import_module(PROFILE_MODULES[name])
    except ImportError as exc:
        raise _ProfileUnavailable(
            f"the {name} profile is not available in this checkout "
            f"({PROFILE_MODULES[name]}: {exc})") from exc


def _jev_command(args) -> int:
    """Run the Jev advisory subcommands, importing its modules only on demand."""
    try:
        jev = _profile("jev")
        jev_binding = importlib.import_module("capcov.claims.jev_binding")
        jev_patterns = importlib.import_module("capcov.claims.jev_patterns")
    except _ProfileUnavailable as exc:
        _emit({"operational_failure": "profile-unavailable", "error": str(exc),
               "advisory": True}, None)
        return 3
    except ImportError as exc:
        _emit({"operational_failure": "profile-unavailable",
               "error": f"the jev profile support module is unavailable: {exc}",
               "advisory": True}, None)
        return 3

    try:
        if args.command == "bind":
            try:
                advisory = _load_json(args.advisory)
                judge = _load_json(args.judge)
            except OSError as exc:
                raise jev.JevError("invalid-input", "cannot read Jev binding input") from exc
            artifact = jev_binding.bind(advisory, judge)
            try:
                _emit(artifact, args.out)
            except OSError as exc:
                raise jev.JevError("invalid-output", "cannot write Jev binding output") from exc
            return 0
        if args.command == "pattern":
            request = jev_patterns.PatternRequest.parse(_load_json(args.request))
            if args.responses:
                artifact = jev_patterns.build_artifact(
                    request, _load_json(args.responses), max_spread=args.max_spread)
            else:
                artifact = jev_patterns.assess(
                    request, max_spread=args.max_spread,
                    endpoint=args.endpoint, timeout=args.timeout)
            if args.claims_out:
                from .ir import canonical_json
                Path(args.claims_out).write_text(
                    canonical_json(jev_patterns.claims_bundle(artifact)) + "\n",
                    encoding="utf-8")
            _emit(artifact, args.out)
            return 0
        request = jev.AssessmentRequest.parse(_load_json(args.request))
        if args.response:
            response_bytes = Path(args.response).read_bytes()
            try:
                response_document = json.loads(response_bytes)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise jev.JevError("invalid-response", "offline response is not JSON") from exc
            artifact = jev.build_artifact(
                request, response_document, raw_response=response_bytes,
                response_mode="offline-file-unattested")
        else:
            artifact = jev.assess(request, endpoint=args.endpoint, timeout=args.timeout)
        if args.claims_out:
            from .ir import canonical_json
            Path(args.claims_out).write_text(
                canonical_json(jev.claims_bundle(artifact)) + "\n", encoding="utf-8")
        _emit(artifact, args.out)
        return 0
    except (BundleIngestionError, ValidationError, OSError, ValueError) as exc:
        _emit({"operational_failure": "invalid-input", "error": str(exc)}, args.out)
        return 3
    except jev.JevError as exc:
        document = {"operational_failure": exc.kind, "error": str(exc)}
        try:
            _emit(document, None if exc.kind == "invalid-output" else args.out)
        except OSError:
            _emit({"operational_failure": "invalid-output",
                   "error": "cannot write command output"}, None)
        return 3


#: The static producer profiles ``claims static --static`` can run.  One today,
#: named the way ``capcov discover --resolver scip`` names it, and asking for it
#: where the SCIP toolchain is absent gets that command's own refusal verbatim.
STATIC_PROFILES = ("scip",)


def _static_scope(value: str | None):
    """``all`` (default), ``package:PREFIX`` or ``documents:A.go,B.go``."""
    from .static.scip_facts import Scope

    if value in (None, "", "all"):
        return Scope.all()
    kind, _, rest = value.partition(":")
    if kind == "package" and rest:
        return Scope.package_prefix(rest)
    if kind == "documents" and rest:
        return Scope.document_set(part for part in rest.split(",") if part)
    raise ValueError(f"--scope must be 'all', 'package:PREFIX' or 'documents:A,B', got {value!r}")


def _static(args) -> int:
    """``claims static --static scip`` -- the static producer profile.

    Upstream's resolver produces the facts: ``scip.runner`` indexes the tree once,
    ``resolve.hybrid_raw`` folds that index into the tree-sitter dict (giving
    ``scip_resolved_edges`` and the enumerated ``scip_residue``),
    ``blindspots.enumerate_blind_spots`` takes the blind-spot census, and
    ``static.scip_facts`` exports the bundle exactly as it always has.  The
    profile ADDS ``static.closure``: the residue as
    ``static_unresolved_call_site`` rows and, for each scope whose residue is
    empty, the ``call_graph_closed`` witness that lets a negative claim resolve.
    Nothing in ``capcov.scip`` is modified or re-implemented here; the export
    keeps its own identity, and the closure rows are merged beside it.

    The bundle written by ``--out`` carries the export, the closure rows and the
    closure pack's own rules; the derived relations it borrows are *declared*
    but derived by ``rules-static-v1``, so a consumer that wants to evaluate it
    merges that pack (``combine``) exactly as the static corpus does.

    Exit 0 when a bundle was produced, 2 for a usage refusal, 3 for a named
    operational failure -- an absent SCIP toolchain among them, reported in
    ``capcov discover --resolver scip``'s own words.
    """
    from ..scip import blindspots, resolve, runner
    from .ir import canonical_dict, canonical_json
    from .static import closure, scip_facts

    if args.static not in STATIC_PROFILES:
        _emit({"refusal": f"unknown static profile {args.static!r}; expected one of "
                          f"{', '.join(STATIC_PROFILES)}"}, None)
        return 2
    root = Path(args.target)
    if not root.is_dir():
        _emit({"refusal": f"--target {args.target!r} is not a directory"}, None)
        return 2
    try:
        scope = _static_scope(args.scope)
    except ValueError as exc:
        _emit({"refusal": str(exc)}, None)
        return 2
    ast_raw = {}
    if args.ast_raw:
        try:
            loaded = _load_json(args.ast_raw)
        except (OSError, json.JSONDecodeError) as exc:
            _emit({"refusal": f"cannot read --ast-raw JSON: {exc}"}, None)
            return 2
        if not isinstance(loaded, dict):
            _emit({"refusal": "--ast-raw must hold the tree-sitter raw dict (a JSON object)"}, None)
            return 2
        ast_raw = loaded
    try:
        resolve.normalizer(args.language)
    except ValueError as exc:
        _emit({"refusal": str(exc)}, None)
        return 2
    try:
        # Fail before invoking an indexer if this language cannot be censused.
        # A missing parser must never turn into an empty census and a closure
        # witness over work that was not examined.
        blindspots.require_census_tools(args.language)
    except ValueError as exc:
        _emit({"operational_failure": "census-unavailable", "error": str(exc)}, None)
        return 3
    try:
        closure.require_scip_tools(args.language, root)
    except (resolve.ScipToolsUnavailable, ValueError) as exc:
        _emit({"operational_failure": "scip-tools-unavailable", "error": str(exc)}, None)
        return 3
    try:
        index_path = runner.run_scip_index(root, args.language, timeout=args.timeout_seconds)
        try:
            normalized = runner.read_scip_index(index_path, retain=True)
        finally:
            index_path.unlink(missing_ok=True)
        # upstream's fold, unmodified: it is what carries scip_resolved_edges and the
        # enumerated residue.  The blind-spot census is the other half of what the
        # exporter calls an available census, so it is taken here too.  A census
        # that cannot be taken is named as that and nothing else: an empty one
        # would close a call graph nobody looked at.
        try:
            raw = resolve.hybrid_raw(ast_raw, normalized, root, language=args.language,
                                     deep="_node_locations" in ast_raw)
            raw["blind_spots"] = blindspots.enumerate_blind_spots(root, args.language)
        except ValueError as exc:
            _emit({"operational_failure": "census-unavailable", "error": str(exc)}, None)
            return 3
        exported = scip_facts.export_bundle(
            normalized, ast_raw=raw, source_root=root, language=args.language, scope=scope,
            index_digest=normalized["index_digest"],
            index_digest_kind=normalized["index_digest_kind"])
    except (resolve.ScipToolsUnavailable, runner.ScipCliNotFound) as exc:
        _emit({"operational_failure": "scip-tools-unavailable", "error": str(exc)}, None)
        return 3
    except (OSError, ValueError) as exc:
        _emit({"operational_failure": "static-export-failed", "error": str(exc)}, None)
        return 3
    if exported.status != scip_facts.STATUS_COMPLETE or exported.bundle is None:
        _emit({"operational_failure": "static-export-failed", "status": exported.status,
               "messages": list(exported.messages)}, None)
        return 3
    try:
        bundle = closure.attach(exported.bundle, raw)
    except (ValidationError, ValueError) as exc:
        _emit({"operational_failure": "static-closure-failed", "error": str(exc)}, None)
        return 3
    if args.out:
        Path(args.out).write_text(canonical_json(canonical_dict(bundle)) + "\n", encoding="utf-8")
    rows = {}
    for fact in bundle.facts:
        rows[fact.relation] = rows.get(fact.relation, 0) + 1
    closed = sorted(fact.terms[1].value for fact in bundle.facts
                    if fact.relation == closure.CLOSED_RELATION)
    _emit({"profile": args.static, "pack": closure.PACK_ID, "base_pack": closure.BASE_PACK_ID,
           "index": dict(exported.bundle.metadata)["index_digest"],
           "scope": {"kind": scope.kind, "values": scope.rows()},
           "census_available": dict(exported.bundle.metadata)["census_available"],
           closure.UNRESOLVED_RELATION: rows.get(closure.UNRESOLVED_RELATION, 0),
           closure.CLOSED_RELATION: closed,
           "row_counts": rows, "out": args.out,
           "messages": list(exported.messages)}, None)
    return 0


def _modelcheck(args) -> int:
    try:
        modelcheck = _profile("modelcheck")
    except _ProfileUnavailable as exc:
        _emit({"operational_failure": "profile-unavailable", "error": str(exc)}, None)
        return 3
    if args.keep:
        # Preserve the explicit scratch-directory debugging mode.  The normal
        # producer-profile path uses preflight below, which has a stable
        # never-raises contract for callers that are gating a command.
        try:
            result = modelcheck.check(args.model, out_dir=args.out,
                                      timeout=args.timeout, keep=True)
        except modelcheck.ModelcheckUnavailable as exc:
            _emit({"operational_failure": "modelcheck-unavailable", "error": str(exc)}, None)
            return 3
        except modelcheck.ModelcheckFailure as exc:
            _emit({"operational_failure": "modelcheck-failure", "error": str(exc)}, None)
            return 3
        report = {"status": result.status, "model": result.model_digest,
                  "fact": result.fact["rows"][0] if result.fact else None,
                  "certificate_sha256": result.certificate["certificate_sha256"],
                  "failures": [{"id": j.id, "message": j.message} for j in result.failures],
                  "error": None, "workdir_retained": result.workdir is not None}
    else:
        report = modelcheck.preflight(args.model, out_dir=args.out, timeout=args.timeout)
    if report["status"] in {"unavailable", "failed"}:
        failure = "modelcheck-unavailable" if report["status"] == "unavailable" else "modelcheck-failure"
        _emit({"operational_failure": failure, "error": report["error"]}, None)
        return 3
    document = {"verdict": report["status"], "model": report["model"],
                "failures": list(report["failures"]),
                "certificate_sha256": report["certificate_sha256"],
                "fact": report["fact"],
                "workdir_retained": bool(report.get("workdir_retained", False))}
    _emit(document, None)
    return 0 if report["status"] == "well-formed" else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="capcov experiment")
    sub = parser.add_subparsers(dest="area", required=True)
    claims = sub.add_parser("claims", help="claim-semantics experiment commands")
    claims_sub = claims.add_subparsers(dest="tool", required=True)
    jev_parser = claims_sub.add_parser(
        "jev", help="advisory semantic judgments over bounded candidates")
    jev_sub = jev_parser.add_subparsers(dest="command", required=True)
    jev_assess = jev_sub.add_parser(
        "assess", help="rank candidates without granting evidence authority")
    jev_assess.add_argument("--request", required=True,
                            help="capcov-jev request JSON")
    jev_assess.add_argument("--response", default=None,
                            help="offline TypeSafe response JSON (no API call)")
    jev_assess.add_argument("--endpoint", default=None,
                            help="TypeSafe endpoint override")
    jev_assess.add_argument("--timeout", type=float, default=30.0)
    jev_assess.add_argument("--out", default=None,
                            help="also write the advisory artifact to this file")
    jev_assess.add_argument("--claims-out", default=None,
                            help="also write Datalog assumption facts as a claim bundle")
    jev_pattern = jev_sub.add_parser(
        "pattern", help="test a neutral pattern packet under framing perturbations")
    jev_pattern.add_argument("--request", required=True,
                             help="capcov-jev pattern request JSON")
    jev_pattern.add_argument("--responses", default=None,
                             help="offline map of sensitivity variant to TypeSafe response")
    jev_pattern.add_argument("--max-spread", required=True, type=float,
                             help="policy threshold; larger Noul spread labels the result unstable")
    jev_pattern.add_argument("--endpoint", default=None)
    jev_pattern.add_argument("--timeout", type=float, default=30.0)
    jev_pattern.add_argument("--out", default=None)
    jev_pattern.add_argument("--claims-out", default=None,
                             help="write assumption-only pattern and sensitivity facts")
    jev_bind = jev_sub.add_parser(
        "bind", help="bind an advisory to an exact deterministic judge artifact")
    jev_bind.add_argument("--advisory", required=True)
    jev_bind.add_argument("--judge", required=True)
    jev_bind.add_argument("--out", required=True)
    shen_parser = claims_sub.add_parser("shen", help="executable Shen semantic workbench (section 18)")
    shen_sub = shen_parser.add_subparsers(dest="command", required=True)
    _common(shen_sub.add_parser("authority", help="structural authority checks over a rule pack"), need_row=False)
    _common(shen_sub.add_parser("evaluate", help="search for a derivation and emit its certificate"), need_row=True)
    _common(shen_sub.add_parser("why-not", help="bounded missing-premise alternatives for a row"), need_row=True)
    asm = claims_sub.add_parser("assumptions", help="assumption registry and invalidation over a replay receipt")
    asm_sub = asm.add_subparsers(dest="command", required=True)
    for name, help_text in (("registry", "list every assumption and the claims it carries"),
                            ("invalidate", "withdraw an assumption and report what every claim did")):
        command = asm_sub.add_parser(name, help=help_text)
        command.add_argument("--receipt", default=None, help="replay receipt directory (default: the committed fixture)")
        command.add_argument("--out", default=None, help="write the join artifacts to this directory")
        command.add_argument("--replay-root", default=None, help="differential replay directory for a kernel mismatch")
        command.add_argument(
            "--reviewer-admissions", default=None,
            help="JSON array of external exact-certificate reviewer admissions")
        command.add_argument("--evaluator", default=None, metavar="NAME[,NAME...]",
                             help="kernels to judge with: python (default, stdlib only), souffle, "
                                  "souffle-compiled, a comma list, or 'all' for every one present")
        if name == "invalidate":
            command.add_argument("--drop", action="append", default=[], required=True, metavar="ID",
                                 help="an asm: id or the evidence id of an assumption row (repeatable)")
    static = claims_sub.add_parser(
        "static", help="static producer profile: export SCIP facts plus the call-graph "
                       "closure witness")
    static.add_argument("--static", default=None, required=True, metavar="PROFILE",
                        help=f"the producer profile: {', '.join(STATIC_PROFILES)}")
    static.add_argument("--target", required=True, help="the source tree to index")
    static.add_argument("--language", default="go", help="SCIP language of the tree (default go)")
    static.add_argument("--ast-raw", default=None,
                        help="optional JSON file holding the adapter's AST_RAW facts; "
                             "the complete call-site census is read independently from the target")
    static.add_argument("--scope", default="all",
                        help="all (default), package:PREFIX or documents:A,B")
    static.add_argument("--timeout-seconds", type=int, default=600,
                        help="hard timeout for the indexer")
    static.add_argument("--out", default=None, help="write the combined bundle JSON here")
    mc = claims_sub.add_parser("modelcheck", help="Stage D: typed well-formedness of a Shen domain model")
    mc.add_argument("--model", required=True, help="model directory holding shen/load.shen")
    mc.add_argument("--out", default=None,
                    help="write the certificate, transcript, model_well_formed.json and model_operation_checked.json here")
    mc.add_argument("--timeout", type=float, default=None, help="seconds before the runtime is killed")
    mc.add_argument("--keep", action="store_true", help="keep the generated driver and units")
    args = parser.parse_args(argv)
    if args.tool == "jev":
        return _jev_command(args)
    if args.tool == "assumptions":
        return _assumptions(args)
    if args.tool == "modelcheck":
        return _modelcheck(args)
    if args.tool == "static":
        return _static(args)

    try:
        shen = _profile("shen")
    except _ProfileUnavailable as exc:
        _emit({"operational_failure": "profile-unavailable", "error": str(exc)}, None)
        return 3

    try:
        bundle = _load_bundle(args.bundle) if args.bundle else None
        rules = _load_json(args.rules) if args.rules else None
        if args.command == "authority":
            if bundle is None and rules is None:
                parser.error("authority needs --bundle or --rules")
            report = shen.authority(bundle, rules, frozen=args.frozen, timeout=args.timeout, keep=args.keep)
            _emit(report.as_dict(), args.out)
            return 0 if report.ok else 1
        max_depth = shen.DEFAULT_MAX_DEPTH if getattr(args, "max_depth", None) is None else args.max_depth
        max_nodes = shen.DEFAULT_MAX_NODES if getattr(args, "max_nodes", None) is None else args.max_nodes
        if args.command == "evaluate":
            result = shen.evaluate(bundle, rules, args.relation, args.row, frozen=args.frozen,
                                   max_depth=max_depth, max_nodes=max_nodes,
                                   timeout=args.timeout, keep=args.keep)
            _emit(result.as_dict(), args.out)
            return 0 if result.outcome == "positive" else 1
        report = shen.why_not(bundle, rules, args.relation, args.row, frozen=args.frozen,
                              max_depth=max_depth, max_nodes=max_nodes,
                              timeout=args.timeout, keep=args.keep)
        _emit(report, args.out)
        return 0
    except (BundleIngestionError, ValidationError, OSError, ValueError) as exc:
        _emit({"operational_failure": "invalid-input", "error": str(exc)}, args.out)
        return 3
    except shen.ShenUnavailable as exc:
        _emit({"operational_failure": exc.operational_failure, "error": str(exc)}, args.out)
        return 3
    except shen.ShenFailure as exc:
        _emit({"operational_failure": exc.kind, "error": exc.message,
               "returncode": exc.returncode, "stderr": exc.stderr[-4000:],
               "provenance": exc.provenance.as_dict() if exc.provenance else None}, args.out)
        return 3


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
