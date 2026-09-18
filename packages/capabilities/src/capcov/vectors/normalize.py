"""Compare-time normalization: a versioned policy for what is volatile.

Recorded vectors stay raw. When replay compares a candidate's result with the
recorded one it applies THIS policy to both sides, so a timestamp the oracle
emitted at record time and the one the candidate emits at replay time compare
equal, and so a change to the policy never forces a re-record. The version is
stamped into artifacts by the recorder so a reader knows which policy a
comparison used.

Three rules, in order:

1. Keys that Mongo-style document encoders add (``_id``, ``$oid``, ``$date``)
   are dropped: they are generated per insert and carry no behaviour.
2. A value under a volatile KEY NAME (timestamps, tokens, expiries, generated
   transaction ids: ``VOLATILE_KEY``) is replaced by ``<volatile>``, unless it
   is empty (``None``, ``""``, ``0``) -- an empty timestamp against a filled
   one is a real difference and stays visible.
3. A string VALUE shaped like a datetime (``DATETIME``) is replaced by
   ``<volatile-datetime>`` wherever it appears, because systems emit timestamps
   under names no key pattern anticipates.

The policy is idempotent: normalizing a normalized value changes nothing, which
is what lets both sides be normalized without worrying whether one already was.
Callers add exact key names with ``extra_volatile_keys`` for a consumer's own
generated fields; the built-in pattern is not widened per consumer.
"""

from __future__ import annotations

import re

NORMALIZATION_VERSION = "v2"

VOLATILE_KEY = re.compile(
    r"(_at$|_date$|^date|modified|created$|updated|timestamp|expires|token|^transaction$)", re.I
)
DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)
DROPPED_KEYS = frozenset({"_id", "$oid", "$date"})

MASK_VOLATILE = "<volatile>"
MASK_DATETIME = "<volatile-datetime>"


def is_volatile_key(key: object, extra_volatile_keys: tuple[str, ...] | frozenset[str] = ()) -> bool:
    """Whether a dict key names a volatile value under this policy."""
    if not isinstance(key, str):
        return False
    return bool(VOLATILE_KEY.search(key)) or key in extra_volatile_keys


def normalize(value, extra_volatile_keys=()):
    """Apply the policy to ``value`` recursively; returns a new structure."""
    extra = frozenset(extra_volatile_keys)
    return _normalize(value, extra)


def _normalize(value, extra: frozenset):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if key in DROPPED_KEYS:
                continue
            if is_volatile_key(key, extra) and item not in (None, "", 0):
                out[key] = MASK_VOLATILE
            else:
                out[key] = _normalize(item, extra)
        return out
    if isinstance(value, list):
        return [_normalize(item, extra) for item in value]
    if isinstance(value, tuple):
        return [_normalize(item, extra) for item in value]
    if isinstance(value, str) and DATETIME.match(value):
        return MASK_DATETIME
    return value
