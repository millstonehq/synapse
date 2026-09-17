"""Thin re-export of ``capcov.claims.replay.join`` plus the committed fixture receipts.

The join logic (``build`` / ``evaluate_join`` / ``summary`` / ``write_artifacts``, the
assumption registry and the why-not helpers) lives in ``src`` so ``scripts/`` can import
it without the tests on ``sys.path``; only the fixture paths and the
``CAPCOV_REPLAY_RECEIPT_DIR`` lookup stay here.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[3] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capcov.claims.replay.join import *  # noqa: E402,F401,F403
from capcov.claims.replay.join import (  # noqa: E402,F401
    _BLOCKING_ORDER, CENSUS_ASSUMPTION_SOURCE, INDEX_ASSUMPTION_SOURCE, MODEL_WITNESSES, REASONS,
    REVIEWER_SOURCE, SYNTHETIC_INDEX, UNDECLARED_REASON, ReplayJoin, assumption_registry,
    blocking_premise, build, evaluate_join, exclusions, exclusions_applied, invalidate, summary,
    undeclared_tables, well_formed_certificate, write_artifacts)

RECEIPT_DIR_ENV = "CAPCOV_REPLAY_RECEIPT_DIR"
OUT_ENV = "CAPCOV_TARGET_GO_REPLAY_OUT"

_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
COMMITTED_RECEIPT_DIR = _FIXTURES / "replay_receipt_target_go_qualified"
"""A real, conforming target-go replay receipt (run eca6e7930af3, synthetic oracle seed, local
evidence paths scrubbed) against the model that declares every business table the
systems write for delete-issue, with the reviewer's scope exclusions: the default
the receipt suite judges, so it is never skip-gated on an untracked work directory.
``CAPCOV_REPLAY_RECEIPT_DIR`` still overrides it."""
REPEAT_RECEIPT_DIR = _FIXTURES / "replay_receipt_target_go_repeat"
"""The four-request receipt (run 271d2dde86a0): owner (200), forbidden (403), missing
(404) and -- for the first time against the incumbent -- repeat (404), a second DELETE
of the issue ``owner`` soft-deleted.  Neither the selftest nor a mutant re-baseline was
run on this tape, so ``op_qualified`` is honestly unresolved at ``corpus_constrains``;
this is the receipt on which ``repeat_delete_not_found`` is judged against real rows
rather than a synthetic case."""
UNQUALIFIED_RECEIPT_DIR = _FIXTURES / "replay_receipt_target_go_unqualified"
"""The earlier real receipt (run 333072ef11f5) whose model declared only ``issue``:
with the reviewer's four exclusions applied, ``entity_statistics`` and ``mongo:issue``
stay undeclared on both sides, so delete-issue is unresolved.  Kept for the negative path."""


def receipt_dir() -> Path | None:
    value = os.environ.get(RECEIPT_DIR_ENV)
    if value:
        return Path(value)
    return COMMITTED_RECEIPT_DIR if (COMMITTED_RECEIPT_DIR / "receipt.json").is_file() else None


__all__ = ["COMMITTED_RECEIPT_DIR", "REPEAT_RECEIPT_DIR", "UNQUALIFIED_RECEIPT_DIR", "RECEIPT_DIR_ENV",
           "OUT_ENV", "SYNTHETIC_INDEX", "ReplayJoin", "receipt_dir", "build", "evaluate_join",
           "summary", "write_artifacts", "blocking_premise", "undeclared_tables", "exclusions",
           "exclusions_applied", "well_formed_certificate", "assumption_registry", "invalidate"]
