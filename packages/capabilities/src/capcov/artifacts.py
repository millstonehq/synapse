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

# The source glob set a tree hash is taken over when nothing else is declared.
DEFAULT_PATTERNS = ("**/*.py",)

# Per-language glob sets. The default stays the Python set so every artifact
# written before this table existed keeps hashing identically; a Go or PHP tree
# hashed over the Python default is the empty manifest (zero files), which is a
# digest that means nothing and, worse, agrees across every Go tree -- so a
# language-scoped consumer (the SCIP fact exporter's ``scip_index_tree``) asks
# for its own pattern set through ``patterns_for``.
LANGUAGE_PATTERNS: dict[str, tuple[str, ...]] = {
    "python": DEFAULT_PATTERNS,
    "go": ("**/*.go",),
    "php": ("**/*.php",),
}

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


def patterns_for(language: str) -> tuple[str, ...]:
    """The glob set a tree of ``language`` is hashed over.

    Raises ``KeyError`` for a language with no pattern set rather than falling
    back to the Python default: hashing a Go tree as ``**/*.py`` yields the
    empty manifest, a digest that would agree across every Go tree.
    """
    return LANGUAGE_PATTERNS[language]


def tree_manifest(
    root: Path, patterns: tuple[str, ...] = DEFAULT_PATTERNS
) -> list[tuple[str, str]]:
    """The sorted, deduplicated ``(tree-relative posix path, sha256)`` manifest
    ``tree_sha256`` hashes -- exposed so a consumer that needs the file list
    itself (which files *should* have been indexed) walks the tree exactly once
    and exactly the way the digest did."""
    entries: set[tuple[str, str]] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.add((path.relative_to(root).as_posix(), digest))
    return sorted(entries)


def tree_sha256(root: Path, patterns: tuple[str, ...] = DEFAULT_PATTERNS) -> tuple[str, int]:
    """Hash a source tree: sha256 over a sorted manifest of per-file hashes.

    Returns (hash, file_count). The manifest is hashed rather than the
    concatenated bytes so that a renamed file changes the hash -- a file moving
    between packages moves its surfaces, and the artifact must not claim
    otherwise. ``patterns`` defaults to the Python set; pass
    ``patterns_for(language)`` for a Go or PHP tree.
    """
    entries = tree_manifest(root, patterns)
    return manifest_sha256(entries), len(entries)


def manifest_sha256(entries: list[tuple[str, str]]) -> str:
    """The tree digest of a ``tree_manifest``: sha256 over its lines
    (``"<path> <sha256>"``), sorted as lines -- exactly the formula
    ``tree_sha256`` has always used, so a consumer holding the manifest can
    reproduce the digest without a second walk."""
    manifest = "\n".join(sorted(set(f"{rel} {digest}" for rel, digest in entries)))
    return hashlib.sha256(manifest.encode()).hexdigest()


def provenance(
    artifact: str,
    artifact_sha256: str,
    extractor: str,
    files: int,
    patterns: tuple[str, ...] | None = None,
) -> dict:
    """Describe the run: which bytes, read by whom, when -- and over which globs.

    `artifact_sha256` is only meaningful together with the pattern set it was
    taken over: the same tree hashed as `**/*.py` and as `*.go` gives two
    different, equally valid answers. Recording the patterns is what lets a LATER
    reader (`capcov outcomes`) recompute the same hash instead of silently
    recomputing a different one and calling the inventory stale. Omitted for an
    artifact written over the Python default, so old artifacts keep reading.
    """
    doc = {
        "artifact": artifact,
        "artifact_sha256": artifact_sha256,
        "artifact_files": files,
        "extractor": extractor,
        "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    if patterns is not None and tuple(patterns) != DEFAULT_PATTERNS:
        doc["source_patterns"] = list(patterns)
    return doc


def source_patterns_of(derived_from: dict) -> tuple[str, ...]:
    """The globs an artifact's `artifact_sha256` was taken over.

    An artifact written before provenance carried the field, or written over the
    Python default, has none -- that is the default, not an error.
    """
    return tuple(derived_from.get("source_patterns") or DEFAULT_PATTERNS)


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
