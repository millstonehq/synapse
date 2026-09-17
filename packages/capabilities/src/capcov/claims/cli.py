"""Experimental CLI for the claim-semantics workbench (EXPERIMENT-PLAN section 18).

Reached only through the ``experiment`` namespace of ``capcov``::

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
the transcript and, for a well-formed model only, ``model_well_formed.json``
(the receipt file the replay exporter reads).  Exit 0 well-formed, 1 ill-formed
(the failing judgements are in the JSON), 3 for a checker or runtime failure.

The assumption registry (``claims/assumptions.py``) is reached the same way::

    capcov experiment claims assumptions registry   --receipt DIR [--out DIR]
    capcov experiment claims assumptions invalidate --receipt DIR --drop ID [--drop ID]

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

Both assumption commands import the target-go join from ``tests/claim_semantics``
beside this package, so they run from a source checkout and not from an
installed wheel (``_join_module`` refuses with exit 2 when it is absent).
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pathlib import Path

from .ir import BundleIngestionError, bundle_from_json
from .validation import ValidationError
from . import modelcheck, shen
from .static.certificate import DEFAULT_MAX_DEPTH, DEFAULT_MAX_NODES


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
        parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
        parser.add_argument("--max-nodes", type=int, default=DEFAULT_MAX_NODES)


def _join_module():
    """The target-go replay join lives beside its fixtures, under ``tests/claim_semantics``.

    Source-checkout only, deliberately: the join carries the experiment's
    fixtures and is not part of the installed package.
    """
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
    from .differential import DifferentialMismatch

    try:
        replay_join = _join_module()
    except (FileNotFoundError, ImportError) as exc:
        _emit({"refusal": f"the replay join is unavailable: {exc}"}, args.out)
        return 2
    receipt = Path(args.receipt) if args.receipt else replay_join.receipt_dir()
    if receipt is None or not (receipt / "receipt.json").is_file():
        _emit({"refusal": "no receipt directory (pass --receipt DIR)"}, args.out)
        return 2
    owned = args.replay_root is None
    replay_root = args.replay_root or tempfile.mkdtemp(prefix="capcov-assumptions-")
    # a kernel disagreement is the one outcome whose evidence lives in the
    # replay root, so that is the one case an owned temporary root survives
    keep = False
    try:
        try:
            join = replay_join.build(receipt)
            if join.bundle is None:
                _emit({"refusal": "the exporter refused the receipt",
                       "contract_findings": list(join.contract_findings)}, args.out)
                return 2
            replay_join.evaluate_join(join, replay_root)
            if join.mismatch is not None:
                keep = True
                _emit({"kernel_mismatch": "the kernels disagree on the join",
                       "replay": str(join.mismatch.replay_path)}, args.out)
                return 3
            document: dict[str, Any] = {"registry": replay_join.assumption_registry(join)}
            if args.command == "invalidate":
                document["invalidations"] = [replay_join.invalidate(join, drop, replay_root).as_dict()
                                             for drop in args.drop]
        except DifferentialMismatch as exc:
            keep = True
            _emit({"kernel_mismatch": "the kernels disagree on the withdrawn bundle",
                   "replay": str(exc.result.replay_path)}, args.out)
            return 3
        except AssertionError as exc:
            # certify_claims: the kernels agree on the rows but not on the claim
            # rows or the certificates of the withdrawn bundle -- a judge with
            # two answers has none, so this is exit 3 like any other mismatch
            keep = True
            _emit({"kernel_mismatch": "the kernels disagree on the claims of the withdrawn bundle",
                   "error": str(exc), "replay": replay_root}, args.out)
            return 3
        except (InvalidationError, ValidationError) as exc:
            _emit({"refusal": str(exc)}, args.out)
            return 2
        if args.out:
            replay_join.write_artifacts(join, Path(args.out))
        _emit(document, None)
        return 0
    finally:
        if owned and not keep:
            shutil.rmtree(replay_root, ignore_errors=True)


def _modelcheck(args) -> int:
    try:
        result = modelcheck.check(args.model, out_dir=args.out, timeout=args.timeout, keep=args.keep)
    except modelcheck.ModelcheckUnavailable as exc:
        _emit({"operational_failure": "modelcheck-unavailable", "error": str(exc)}, None)
        return 3
    except modelcheck.ModelcheckFailure as exc:
        _emit({"operational_failure": "modelcheck-failure", "error": str(exc)}, None)
        return 3
    document = {"verdict": result.status, "model": result.model_digest,
                "judgements": [{"id": j.id, "verdict": j.verdict, "message": j.message} for j in result.judgements],
                "skipped": [{"op": op, "reason": reason} for op, reason in result.skipped],
                "certificate_sha256": result.certificate["certificate_sha256"],
                "fact": result.fact, "workdir": result.workdir,
                "elapsed_seconds": round(result.elapsed_seconds, 3)}
    _emit(document, None)
    return 0 if result.status == "well-formed" else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="capcov experiment")
    sub = parser.add_subparsers(dest="area", required=True)
    claims = sub.add_parser("claims", help="claim-semantics experiment commands")
    claims_sub = claims.add_subparsers(dest="tool", required=True)
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
        if name == "invalidate":
            command.add_argument("--drop", action="append", default=[], required=True, metavar="ID",
                                 help="an asm: id or the evidence id of an assumption row (repeatable)")
    mc = claims_sub.add_parser("modelcheck", help="Stage D: typed well-formedness of a Shen domain model")
    mc.add_argument("--model", required=True, help="model directory holding shen/load.shen")
    mc.add_argument("--out", default=None, help="write the certificate, transcript and model_well_formed.json here")
    mc.add_argument("--timeout", type=float, default=None, help="seconds before the runtime is killed")
    mc.add_argument("--keep", action="store_true", help="keep the generated driver and units")
    args = parser.parse_args(argv)
    if args.tool == "assumptions":
        return _assumptions(args)
    if args.tool == "modelcheck":
        return _modelcheck(args)

    try:
        bundle = _load_bundle(args.bundle) if args.bundle else None
        rules = _load_json(args.rules) if args.rules else None
        if args.command == "authority":
            if bundle is None and rules is None:
                parser.error("authority needs --bundle or --rules")
            report = shen.authority(bundle, rules, frozen=args.frozen, timeout=args.timeout, keep=args.keep)
            _emit(report.as_dict(), args.out)
            return 0 if report.ok else 1
        if args.command == "evaluate":
            result = shen.evaluate(bundle, rules, args.relation, args.row, frozen=args.frozen,
                                   max_depth=args.max_depth, max_nodes=args.max_nodes,
                                   timeout=args.timeout, keep=args.keep)
            _emit(result.as_dict(), args.out)
            return 0 if result.outcome == "positive" else 1
        report = shen.why_not(bundle, rules, args.relation, args.row, frozen=args.frozen,
                              max_depth=args.max_depth, max_nodes=args.max_nodes,
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
