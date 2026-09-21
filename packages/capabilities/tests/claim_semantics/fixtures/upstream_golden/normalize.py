#!/usr/bin/env python3
"""Normalize capcov CLI artifacts so two runs on two checkouts compare byte-for-byte.

Usage:  normalize.py RAW_DIR OUT_DIR  [SUBST ...]

Every SUBST is ``literal=token``: the literal prefix (an absolute path from the
producing machine) is replaced by the token everywhere it appears.  Longer
literals are applied first so nested prefixes cannot shadow each other.

Beyond paths, exactly three classes of value are volatile between runs and are
rewritten in place (formatting, key order and whitespace are otherwise
preserved byte-for-byte -- this is a textual pass, never a JSON re-dump):

* ``"extracted_at": "<iso8601>"``  -> ``"extracted_at": "<timestamp>"``
* any ``"<name>_ms": <int>``       -> ``"<name>_ms": 0``   (wall-clock timings)
* ``"duration_ms": <int>``         -> covered by the ``_ms`` rule

Nothing else is touched.  In particular ``artifact_sha256`` / ``source_snapshot``
are NOT normalized: they proved stable across runs and are part of the contract.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

TS = re.compile(r'("extracted_at":\s*")[^"]*(")')
MS = re.compile(r'("[A-Za-z0-9_]*_ms":\s*)\d+')
BIN = {".scip"}


def normalize_text(text: str, substitutions: list[tuple[str, str]]) -> str:
    for literal, token in substitutions:
        text = text.replace(literal, token)
    text = TS.sub(r"\1<timestamp>\2", text)
    text = MS.sub(r"\g<1>0", text)
    return text


def main(argv: list[str]) -> int:
    raw, out = Path(argv[1]), Path(argv[2])
    subs = [tuple(a.split("=", 1)) for a in argv[3:]]
    subs.sort(key=lambda pair: -len(pair[0]))
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for path in sorted(raw.rglob("*")):
        if not path.is_file():
            continue
        target = out / path.relative_to(raw)
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix in BIN:
            shutil.copy2(path, target)
            continue
        target.write_text(normalize_text(path.read_text(), subs))
        # The stable half of a failing run is its final message, not the
        # traceback (whose line numbers move with any edit above them).
        if path.suffix == ".stderr" and path.read_text().strip():
            last = [ln for ln in target.read_text().splitlines() if ln.strip()][-1]
            target.with_suffix(".error_line").write_text(last + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
