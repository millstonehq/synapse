"""Compare-time normalization: a versioned policy for what is volatile.

Recorded vectors stay raw. When replay compares a candidate's result with the
recorded one it applies THIS policy to both sides, so a timestamp the oracle
emitted at record time and the one the candidate emits at replay time compare
equal, and so a change to the policy never forces a re-record. Recording
provenance retains the version known at capture; the replay artifact separately
binds the exact source/config identity of the policy executed for its comparison.

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

import hashlib
import json
import re
from pathlib import Path

NORMALIZATION_VERSION = "v2"
POLICY_IDENTITY_FORMAT = "capcov-vector-comparison-policy/v1"

VOLATILE_KEY = re.compile(
    r"(_at$|_date$|^date|modified|created$|updated|timestamp|expires|token|^transaction$)", re.I
)
DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)
DROPPED_KEYS = frozenset({"_id", "$oid", "$date"})

MASK_VOLATILE = "<volatile>"
MASK_DATETIME = "<volatile-datetime>"


def _json_sha256(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def comparison_policy_identity() -> dict:
    """Exact source/config identity for the policy applied during replay.

    This is deliberately separate from ``vectors.json`` recording provenance:
    normalization runs at replay time, against both the recorded and candidate
    values. No path or private vector data is included in the identity.
    """
    config = {
        "normalization_version": NORMALIZATION_VERSION,
        "volatile_key_pattern": VOLATILE_KEY.pattern,
        "volatile_key_flags": int(VOLATILE_KEY.flags),
        "datetime_pattern": DATETIME.pattern,
        "datetime_flags": int(DATETIME.flags),
        "dropped_keys": sorted(DROPPED_KEYS),
        "mask_volatile": MASK_VOLATILE,
        "mask_datetime": MASK_DATETIME,
        "preserved_empty_volatile_values": [None, "", 0],
        "extra_volatile_keys": [],
    }
    try:
        source_bytes = Path(__file__).read_bytes()
    except OSError as exc:
        raise RuntimeError("cannot read the executed comparison-policy source") from exc
    core = {
        "format": POLICY_IDENTITY_FORMAT,
        "normalization_version": NORMALIZATION_VERSION,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "config": config,
        "config_sha256": _json_sha256(config),
    }
    return {**core, "policy_sha256": _json_sha256(core)}


def validate_comparison_policy_identity(identity) -> bool:
    """Check a replay's source/config identity for exact shape and self-consistency.

    Historical replay artifacts are not compared with today's normalizer. The
    recorded identity is a local execution disclosure, not an authenticated
    attestation of which code actually ran.
    """
    fields = {"format", "normalization_version", "source_sha256", "config",
              "config_sha256", "policy_sha256"}
    if not isinstance(identity, dict) or set(identity) != fields:
        return False
    if identity.get("format") != POLICY_IDENTITY_FORMAT:
        return False
    version = identity.get("normalization_version")
    source_digest = identity.get("source_sha256")
    config = identity.get("config")
    if (not isinstance(version, str) or not version
            or not isinstance(source_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", source_digest) is None):
        return False
    if not isinstance(config, dict) or set(config) != {
            "normalization_version", "volatile_key_pattern", "volatile_key_flags",
            "datetime_pattern", "datetime_flags", "dropped_keys", "mask_volatile",
            "mask_datetime", "preserved_empty_volatile_values", "extra_volatile_keys"}:
        return False
    if (config.get("normalization_version") != version
            or not isinstance(config.get("volatile_key_pattern"), str)
            or type(config.get("volatile_key_flags")) is not int
            or not isinstance(config.get("datetime_pattern"), str)
            or type(config.get("datetime_flags")) is not int
            or not isinstance(config.get("dropped_keys"), list)
            or any(not isinstance(item, str) for item in config["dropped_keys"])
            or not isinstance(config.get("mask_volatile"), str)
            or not isinstance(config.get("mask_datetime"), str)
            or not isinstance(config.get("preserved_empty_volatile_values"), list)
            or not isinstance(config.get("extra_volatile_keys"), list)
            or any(not isinstance(item, str) for item in config["extra_volatile_keys"])):
        return False
    config_digest = identity.get("config_sha256")
    policy_digest = identity.get("policy_sha256")
    if any(not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
           for value in (config_digest, policy_digest)):
        return False
    if _json_sha256(config) != config_digest:
        return False
    core = {key: value for key, value in identity.items() if key != "policy_sha256"}
    return _json_sha256(core) == policy_digest


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
