"""Artifact formats, provenance, and the tree hash everything is relative to.

There is no complete-in-the-abstract. What this framework asserts is
completeness *with respect to a named artifact*, so every file it writes carries
`derived_from`: the artifact, its hash, the extractor, and when. `reconcile`
refuses to compare two artifacts whose `artifact_sha256` disagree -- a static
run against one tree and a runtime run against another produce a diff that
looks authoritative and means nothing.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1

# `derived_from` describes the RUN -- when it happened and against which exact
# bytes. `--check` asks a different question: has what the system can do changed?
# Diffing the provenance too would fail the check on every reformatted line,
# which teaches people to regenerate without reading, and a check nobody reads
# is the thing this framework exists to replace.
#
# The hash still does its job. `reconcile` uses it to refuse a static run and a
# runtime run taken from different trees, which is a comparison across two
# systems dressed up as a finding.
VOLATILE = ("derived_from",)


def tree_sha256(root: Path, patterns: tuple[str, ...] = ("**/*.py",)) -> tuple[str, int]:
    """Hash a source tree: sha256 over a sorted manifest of per-file hashes.

    Returns (hash, file_count). The manifest is hashed rather than the
    concatenated bytes so that a renamed file changes the hash -- a file moving
    between packages moves its surfaces, and the artifact must not claim
    otherwise.
    """
    entries = []
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"{path.relative_to(root).as_posix()} {digest}")
    manifest = "\n".join(sorted(set(entries)))
    return hashlib.sha256(manifest.encode()).hexdigest(), len(set(entries))


def provenance(artifact: str, artifact_sha256: str, extractor: str, files: int) -> dict:
    return {
        "artifact": artifact,
        "artifact_sha256": artifact_sha256,
        "artifact_files": files,
        "extractor": extractor,
        "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def write(path: Path, kind: str, derived_from: dict, body: dict) -> None:
    doc = {"schema_version": SCHEMA_VERSION, "kind": kind, "derived_from": derived_from}
    doc.update(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")


def read(path: Path, expect_kind: str | None = None) -> dict:
    doc = json.loads(path.read_text())
    if expect_kind and doc.get("kind") != expect_kind:
        raise SystemExit(
            f"{path}: expected a {expect_kind!r} artifact, found {doc.get('kind')!r}"
        )
    if doc.get("schema_version") != SCHEMA_VERSION:
        raise SystemExit(
            f"{path}: schema_version {doc.get('schema_version')}, "
            f"this capcov speaks {SCHEMA_VERSION}"
        )
    return doc


def normalise(doc: dict) -> str:
    """Render an artifact's DERIVED CONTENT, for --check diffs."""
    clone = json.loads(json.dumps(doc))
    for field in VOLATILE:
        clone.pop(field, None)
    return json.dumps(clone, indent=2, sort_keys=True) + "\n"


def same_artifact(a: dict, b: dict) -> tuple[bool, str]:
    """Do two artifacts describe the same tree?"""
    ah = a.get("derived_from", {}).get("artifact_sha256")
    bh = b.get("derived_from", {}).get("artifact_sha256")
    if ah and bh and ah == bh:
        return True, ""
    return False, (
        f"static ran against {ah or '<none>'}, runtime against {bh or '<none>'}. "
        "Re-run both against the same tree; a diff across two trees is not a finding."
    )
