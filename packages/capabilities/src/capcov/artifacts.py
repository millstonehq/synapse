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
import os
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .cas import FilesystemCAS, IntegrityError, sha256_bytes

SCHEMA_VERSION = 1

# The source glob set a tree hash is taken over when nothing else is declared.
DEFAULT_PATTERNS = ("**/*.py",)
LANGUAGE_PATTERNS = {
    "python": "**/*.py",
    "go": "**/*.go",
    "php": "**/*.php",
}

TREE_CACHE_VERSION = 1
MAX_TREE_CACHE_BYTES = 32 * 1024 * 1024
MAX_TREE_CACHE_ENTRIES = 500_000

# `derived_from` describes the RUN -- when it happened and against which exact
# bytes. `--check` asks a different question: has what the system can do changed?
# Diffing the provenance too would fail the check on every reformatted line,
# which teaches people to regenerate without reading, and a check nobody reads
# is the thing this framework exists to replace.
#
# The hash still does its job. `reconcile` uses it to refuse a static run and a
# runtime run taken from different trees, which is a comparison across two
# systems dressed up as a finding.
VOLATILE = ("derived_from", "timing")


def language_pattern(language: object) -> str:
    """A safe source default for a configured language.

    Unknown or absent languages retain the historic Python default.  In
    particular they never become an empty pattern set (whose shared empty digest
    would make unrelated sources appear identical).
    """
    return LANGUAGE_PATTERNS.get(str(language or "python").lower(), DEFAULT_PATTERNS[0])


def _patterns(patterns: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(str(pattern) for pattern in patterns if pattern))
    return normalized or DEFAULT_PATTERNS


def _default_cache_dir() -> Path:
    base = os.environ.get("XDG_CACHE_HOME")
    if base:
        return Path(base) / "capcov" / "tree-manifests-v1"
    return Path.home() / ".cache" / "capcov" / "tree-manifests-v1"


def _cache_path(root: Path, patterns: tuple[str, ...], cache_dir: Path) -> Path:
    identity = json.dumps(
        {"root": str(root.resolve()), "patterns": list(patterns)},
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return cache_dir / f"{hashlib.sha256(identity).hexdigest()}.json"


def _read_cache(path: Path, root: Path, patterns: tuple[str, ...]) -> dict[str, dict]:
    stat = path.stat()
    if stat.st_size > MAX_TREE_CACHE_BYTES:
        raise ValueError("tree cache exceeds the read bound")
    document = json.loads(path.read_bytes())
    # The deterministic index is a mutable name; the manifest it points to is
    # an immutable CAS object.  Accept the pre-CAS inline format too, so a
    # user's existing cache is upgraded on its next successful write.
    if isinstance(document, dict) and "object_sha256" in document:
        reference_integrity = document.get("integrity_sha256")
        reference_payload = {
            key: value
            for key, value in document.items()
            if key != "integrity_sha256"
        }
        expected_reference_integrity = hashlib.sha256(
            json.dumps(
                reference_payload, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        if (
            reference_integrity != expected_reference_integrity
            or document.get("version") != TREE_CACHE_VERSION
            or document.get("root") != str(root.resolve())
            or document.get("patterns") != list(patterns)
        ):
            raise ValueError("invalid tree cache reference")
        object_value = FilesystemCAS(path.parent / "cas").read_bytes(
            document["object_sha256"]
        )
        document = json.loads(object_value)
    integrity = document.get("integrity_sha256") if isinstance(document, dict) else None
    payload = {
        key: value for key, value in document.items() if key != "integrity_sha256"
    } if isinstance(document, dict) else {}
    expected_integrity = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if (
        not isinstance(document, dict)
        or integrity != expected_integrity
        or document.get("version") != TREE_CACHE_VERSION
        or document.get("root") != str(root.resolve())
        or document.get("patterns") != list(patterns)
        or not isinstance(document.get("entries"), dict)
        or len(document["entries"]) > MAX_TREE_CACHE_ENTRIES
    ):
        raise ValueError("invalid tree cache manifest")
    entries = document["entries"]
    for relative, entry in entries.items():
        if (
            not isinstance(relative, str)
            or not relative
            or relative.startswith("/")
            or ".." in Path(relative).parts
            or "\\" in relative
            or not isinstance(entry, dict)
            or not isinstance(entry.get("sha256"), str)
            or len(entry["sha256"]) != 64
            or entry["sha256"] != entry["sha256"].lower()
        ):
            raise ValueError("invalid tree cache entry")
    return entries


def _file_identity(stat: os.stat_result) -> dict[str, int]:
    # ctime/inode/device make the size+mtime fast path conservative without
    # changing the source-bound digest, which remains path + exact-byte SHA-256.
    return {
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
        "device": stat.st_dev,
        "inode": stat.st_ino,
        "mode": stat.st_mode,
    }


def _hash_file(path: Path, before: os.stat_result) -> tuple[str, os.stat_result]:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    after = path.stat()
    if _file_identity(before) != _file_identity(after):
        raise OSError(f"source file changed while hashing: {path}")
    return digest.hexdigest(), after


def _write_cache(
    path: Path, root: Path, patterns: tuple[str, ...], entries: dict[str, dict]
) -> None:
    document = {
        "version": TREE_CACHE_VERSION,
        "root": str(root.resolve()),
        "patterns": list(patterns),
        "entries": entries,
    }
    document["integrity_sha256"] = hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    manifest_value = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    if len(manifest_value) > MAX_TREE_CACHE_BYTES:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    cas = FilesystemCAS(path.parent / "cas")
    try:
        object_digest = cas.put_bytes(manifest_value)
    except IntegrityError:
        # The source hash was freshly computed, so a corrupt cache object may
        # be repaired at this exact content-addressed path.  The cache is
        # optional; this never applies to source or evidence objects.
        cas.object_path(sha256_bytes(manifest_value)).unlink(missing_ok=True)
        object_digest = cas.put_bytes(manifest_value)
    reference = {
        "version": TREE_CACHE_VERSION,
        "root": str(root.resolve()),
        "patterns": list(patterns),
        "object_sha256": object_digest,
    }
    reference["integrity_sha256"] = hashlib.sha256(
        json.dumps(reference, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    value = json.dumps(reference, sort_keys=True, separators=(",", ":")).encode()
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class SourceSnapshot:
    """One exact tree identity plus bounded, non-secret verification metrics."""

    root: Path
    patterns: tuple[str, ...]
    digest: str
    files: int
    verification: dict
    # Per-file digests are retained only in memory.  They let consumers whose
    # declared inputs include this exact source root reuse the authoritative
    # manifest instead of opening every file a second time.  The public tree
    # hash API remains the compact ``(digest, files)`` pair.
    entries: tuple[tuple[str, str], ...] = ()

    def provenance(self, artifact: str, extractor: str) -> dict:
        return provenance(
            artifact,
            self.digest,
            extractor,
            self.files,
            self.patterns,
            snapshot=self,
        )

    def verify(self, *, cache_dir: Path | str | None = None) -> "SourceSnapshot":
        current = snapshot_tree(self.root, self.patterns, cache_dir=cache_dir)
        if current.digest != self.digest or current.files != self.files:
            raise ValueError("source changed since the source snapshot was captured")
        return current


def snapshot_tree(
    root: Path,
    patterns: tuple[str, ...] = DEFAULT_PATTERNS,
    *,
    cache_dir: Path | str | None = None,
) -> SourceSnapshot:
    """Capture an exact source manifest, reusing only metadata-matched entries.

    Cache failure is deliberately optional: a missing, corrupt, oversized, or
    unwritable cache falls back to exact content hashing.  Source read/stat
    failures still raise and therefore can never be converted into cached
    success.
    """
    started = time.perf_counter_ns()
    root = Path(root).resolve()
    patterns = _patterns(patterns)
    requested_cache = Path(cache_dir) if cache_dir is not None else _default_cache_dir()
    try:
        cache_inside_source = requested_cache.resolve().is_relative_to(root)
    except OSError:
        cache_inside_source = False
    cache_path = _cache_path(root, patterns, requested_cache)
    cached: dict[str, dict] = {}
    cache_read_error = False
    cache_enabled = not cache_inside_source
    if cache_enabled:
        try:
            cached = _read_cache(cache_path, root, patterns)
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            cache_read_error = True

    paths: dict[str, Path] = {}
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(root).as_posix()
            paths[relative] = path
    if len(paths) > MAX_TREE_CACHE_ENTRIES:
        raise ValueError(
            f"source manifest has more than {MAX_TREE_CACHE_ENTRIES} files"
        )

    fresh: dict[str, dict] = {}
    reused = 0
    hashed = 0
    manifest_entries: list[str] = []
    for relative, path in sorted(paths.items()):
        stat = path.stat()
        identity = _file_identity(stat)
        previous = cached.get(relative)
        if previous is not None and all(
            previous.get(key) == value for key, value in identity.items()
        ):
            digest = previous["sha256"]
            # Cache parsing validates shape; conversion validates hexadecimal.
            try:
                int(digest, 16)
            except ValueError:
                digest, stat = _hash_file(path, stat)
                identity = _file_identity(stat)
                hashed += 1
            else:
                reused += 1
        else:
            digest, stat = _hash_file(path, stat)
            identity = _file_identity(stat)
            hashed += 1
        fresh[relative] = {**identity, "sha256": digest}
        manifest_entries.append(f"{relative} {digest}")

    manifest = "\n".join(manifest_entries)
    digest = hashlib.sha256(manifest.encode()).hexdigest()
    cache_write_error = False
    if cache_enabled:
        try:
            _write_cache(cache_path, root, patterns, fresh)
        except OSError:
            cache_write_error = True
    if not cache_enabled:
        status = "disabled"
    elif cache_read_error or cache_write_error:
        status = "fallback"
    elif paths and reused == len(paths) and set(cached) == set(paths):
        status = "hit"
    else:
        status = "miss"
    elapsed_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)
    return SourceSnapshot(
        root=root,
        patterns=patterns,
        digest=digest,
        files=len(paths),
        verification={
            "cache": status,
            "cache_hit": status == "hit",
            "files_hashed": hashed,
            "files_reused": reused,
            "duration_ms": min(elapsed_ms, 86_400_000),
        },
        entries=tuple((relative, entry["sha256"]) for relative, entry in sorted(fresh.items())),
    )


def tree_sha256(
    root: Path,
    patterns: tuple[str, ...] = DEFAULT_PATTERNS,
    *,
    cache_dir: Path | str | None = None,
) -> tuple[str, int]:
    """Hash a source tree: sha256 over a sorted manifest of per-file hashes.

    Returns (hash, file_count). The manifest is hashed rather than the
    concatenated bytes so that a renamed file changes the hash -- a file moving
    between packages moves its surfaces, and the artifact must not claim
    otherwise.
    """
    snapshot = snapshot_tree(root, patterns, cache_dir=cache_dir)
    return snapshot.digest, snapshot.files


def provenance(
    artifact: str,
    artifact_sha256: str,
    extractor: str,
    files: int,
    patterns: tuple[str, ...] | None = None,
    *,
    snapshot: SourceSnapshot | None = None,
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
    if snapshot is not None:
        if snapshot.digest != artifact_sha256 or snapshot.files != files:
            raise ValueError("source snapshot does not match artifact provenance")
        doc["source_snapshot"] = {
            "version": 1,
            "manifest_sha256": snapshot.digest,
            "files": snapshot.files,
        }
    return doc


def source_snapshot_of(root: Path, derived_from: dict) -> SourceSnapshot:
    """Rebuild and validate a serialized provenance snapshot.

    Old artifacts have no ``source_snapshot`` and remain valid: the authoritative
    fields have always been ``artifact_sha256`` and ``artifact_files``.
    """
    patterns = source_patterns_of(derived_from)
    current = snapshot_tree(root, patterns)
    expected_digest = derived_from.get("artifact_sha256")
    expected_files = derived_from.get("artifact_files", current.files)
    optional = derived_from.get("source_snapshot")
    if optional is not None:
        if not isinstance(optional, dict) or optional.get("version") != 1:
            raise ValueError("invalid serialized source snapshot")
        if (
            optional.get("manifest_sha256") != expected_digest
            or optional.get("files") != expected_files
        ):
            raise ValueError("serialized source snapshot disagrees with derived_from")
    if current.digest != expected_digest or current.files != expected_files:
        raise ValueError("source provenance does not match the current tree")
    return current


def carried_source_snapshot(root: Path, derived_from: dict) -> SourceSnapshot:
    """Deserialize a snapshot identity without re-reading the source tree.

    This is used only for the begin-side of an observe freshness guard.  The
    guard always captures an authoritative current snapshot after the exercise
    and compares it with this identity before publishing evidence.
    """
    digest = derived_from.get("artifact_sha256")
    files = derived_from.get("artifact_files")
    if not isinstance(digest, str) or len(digest) != 64 or type(files) is not int:
        raise ValueError("source provenance lacks an exact digest and file count")
    try:
        int(digest, 16)
    except ValueError as exc:
        raise ValueError("source provenance has an invalid SHA-256 digest") from exc
    optional = derived_from.get("source_snapshot")
    if optional is not None and (
        not isinstance(optional, dict)
        or optional.get("version") != 1
        or optional.get("manifest_sha256") != digest
        or optional.get("files") != files
    ):
        raise ValueError("serialized source snapshot disagrees with derived_from")
    return SourceSnapshot(
        root=Path(root).resolve(),
        patterns=source_patterns_of(derived_from),
        digest=digest,
        files=files,
        verification={
            "cache": "carried",
            "cache_hit": True,
            "files_hashed": 0,
            "files_reused": files,
            "duration_ms": 0,
        },
        entries=(),
    )


def source_patterns_of(derived_from: dict) -> tuple[str, ...]:
    """The globs an artifact's `artifact_sha256` was taken over.

    An artifact written before provenance carried the field, or written over the
    Python default, has none -- that is the default, not an error.
    """
    return tuple(derived_from.get("source_patterns") or DEFAULT_PATTERNS)


def write(path: Path, kind: str, derived_from: dict, body: dict) -> None:
    doc = {"schema_version": SCHEMA_VERSION, "kind": kind, "derived_from": derived_from}
    doc.update(body)
    write_document(path, doc)


def write_document(path: Path, doc: dict) -> None:
    """Atomically publish a complete JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    value = (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode()
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


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
