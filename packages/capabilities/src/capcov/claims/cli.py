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
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .ir import BundleIngestionError, bundle_from_json
from .validation import ValidationError
from . import shen
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
    args = parser.parse_args(argv)

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
