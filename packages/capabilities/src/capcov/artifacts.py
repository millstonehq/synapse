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
import shutil
import stat as stat_module
import tempfile
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1

# The source glob set a tree hash is taken over when nothing else is declared.
DEFAULT_PATTERNS = ("**/*.py",)
# Every language the tree-sitter discovery path can actually parse. A language
# outside this table has no honest default glob, so `language_pattern` refuses
# rather than hashing some other language's files under its name.
LANGUAGE_PATTERNS = {
    "python": "**/*.py",
    "go": "**/*.go",
    "php": "**/*.php",
    "javascript": "**/*.js",
    "typescript": "**/*.ts",
    "tsx": "**/*.tsx",
}

# Set to an affirmative value to bind every digest to exact bytes, at the cost
# of the incremental fast path. The verification walks are always exact.
ENV_NO_CACHE = "CAPCOV_NO_CACHE"

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
    """The source default for a configured language.

    An absent language retains the historic Python default. A NAMED language
    this table does not know is refused: silently handing it `**/*.py` hashed
    one language's tree and called it another's, which is a false provenance
    claim, and it never becomes an empty pattern set (whose shared empty digest
    would make unrelated sources appear identical).
    """
    if language is None or str(language).strip() == "":
        return DEFAULT_PATTERNS[0]
    name = str(language).strip().lower()
    try:
        return LANGUAGE_PATTERNS[name]
    except KeyError:
        raise ValueError(
            f"no source glob default for language {name!r}; "
            f"declare 'globs' or 'files' explicitly "
            f"(known: {', '.join(sorted(LANGUAGE_PATTERNS))})"
        ) from None


def normalise_patterns(patterns: tuple[str, ...]) -> tuple[str, ...]:
    """The one glob-set normalization: de-duplicated, empties dropped.

    Public because callers that COMPARE a recorded pattern set against a
    snapshot's must normalize both sides, or a harmless duplicate reads as a
    stale inventory.
    """
    normalized = tuple(dict.fromkeys(str(pattern) for pattern in patterns if pattern))
    return normalized or DEFAULT_PATTERNS


# Historic private spelling, kept for in-module call sites.
_patterns = normalise_patterns


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


def _cache_dir_is_private(directory: Path) -> bool:
    """A cache is only usable when nobody else can write the digests we trust.

    On a first run nothing under the cache root exists yet, so the nearest
    existing ancestor is what decides whether it is safe to create it there.
    """
    candidate = directory if directory.is_absolute() else directory.absolute()
    for path in (candidate, *candidate.parents):
        try:
            info = path.stat()
        except OSError:
            continue
        if info.st_uid != os.getuid():
            return False
        return not info.st_mode & (stat_module.S_IWGRP | stat_module.S_IWOTH)
    return False


def _read_cache(path: Path, root: Path, patterns: tuple[str, ...]) -> dict[str, dict]:
    info = path.stat()
    if info.st_uid != os.getuid() or info.st_mode & (
        stat_module.S_IWGRP | stat_module.S_IWOTH
    ):
        raise ValueError("tree cache is not private to this user")
    if info.st_size > MAX_TREE_CACHE_BYTES:
        raise ValueError("tree cache exceeds the read bound")
    document = json.loads(path.read_bytes())
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
) -> bool:
    """Replace this index in one rename. Returns False when it does not fit.

    There is exactly one live manifest per (root, patterns), it is never shared
    with a second referent, and `os.replace` is already atomic -- so the index
    IS the manifest. An indirection through a content-addressed object bought
    nothing here and leaked one orphaned object per edit, forever.
    """
    document = {
        "version": TREE_CACHE_VERSION,
        "root": str(root.resolve()),
        "patterns": list(patterns),
        "entries": entries,
    }
    document["integrity_sha256"] = hashlib.sha256(
        json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    value = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    if len(value) > MAX_TREE_CACHE_BYTES:
        return False
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    # An index written by the superseded content-addressed format leaves its
    # object store behind; drop it the first time we replace that index.
    shutil.rmtree(path.parent / "cas", ignore_errors=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


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
    # True when this identity was handed over by a driving `capcov observe`
    # rather than captured here.  The driver owns the one exact verification
    # at the publication boundary; a carried snapshot never verifies itself.
    carried: bool = False

    @property
    def exact(self) -> bool:
        """Every digest in this snapshot came from bytes read by this process.

        A cache miss and a `trust_cache=False` walk are both exact -- nothing
        was reused -- so this is a property of what happened, not of a flag.
        A carried identity is never exact: the process holding it read nothing.
        """
        return not self.carried and self.verification.get("files_reused") == 0

    def provenance(self, artifact: str, extractor: str) -> dict:
        return provenance(
            artifact,
            self.digest,
            extractor,
            self.files,
            self.patterns,
            snapshot=self,
        )

    def verify(self) -> "SourceSnapshot":
        """Re-read the tree FROM BYTES and require it to still be this tree.

        This is THE exact walk of a run, and there is one: at the publication
        boundary, in the process that publishes.  Never from the cache --
        anything running as this user can write `~/.cache`, including the
        exercise a freshness guard exists to distrust, so a cache-backed
        verification lets the observed process answer the question being
        asked about it.  The returned snapshot is exact; publish from it.
        """
        current = snapshot_tree(self.root, self.patterns, trust_cache=False)
        if current.digest != self.digest or current.files != self.files:
            raise ValueError("source changed since the source snapshot was captured")
        return current


def _cache_disabled_by_env() -> bool:
    return os.environ.get(ENV_NO_CACHE, "").strip().lower() in {"1", "true", "yes", "on"}


def snapshot_tree(
    root: Path,
    patterns: tuple[str, ...] = DEFAULT_PATTERNS,
    *,
    cache_dir: Path | str | None = None,
    trust_cache: bool = True,
) -> SourceSnapshot:
    """Capture an exact source manifest, reusing only metadata-matched entries.

    `trust_cache=False` hashes every selected file from bytes.  That is what
    every verification walk does, because the shared cache is writable by
    anything running as this user -- including the exercise a freshness guard
    exists to distrust -- so a cache-backed verification would let the observed
    process answer the question asked about it.  `CAPCOV_NO_CACHE=1` forces the
    same for every walk.

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
    cache_enabled = (
        trust_cache
        and not cache_inside_source
        and not _cache_disabled_by_env()
        and _cache_dir_is_private(requested_cache)
    )
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
    # Past the index bound the tree is still hashed exactly; only the
    # incremental index is given up.  A large tree must stay slow, not fail.
    unbounded = len(paths) > MAX_TREE_CACHE_ENTRIES
    if unbounded:
        cached = {}

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
    oversized = False
    if cache_enabled and not unbounded:
        try:
            oversized = not _write_cache(cache_path, root, patterns, fresh)
        except OSError:
            cache_write_error = True
    if unbounded:
        status = "unbounded"
    elif not cache_enabled:
        status = "disabled"
    elif oversized:
        status = "oversized"
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
            "exact": reused == 0,
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
        # `exact`: every digest was read from bytes by the publishing process.
        # `cached`: the fast path was used and this identity is PROVISIONAL --
        # it becomes authoritative only when an exact artifact over the same
        # tree agrees with it (reconcile enforces this), never on its own.
        doc["source_snapshot"] = {
            "version": 1,
            "manifest_sha256": snapshot.digest,
            "files": snapshot.files,
            "verification": "exact" if snapshot.exact else "cached",
        }
    return doc


SNAPSHOT_VERIFICATIONS = ("exact", "cached")


def snapshot_verification_of(derived_from: dict) -> str:
    """How an artifact's digest was established: ``exact`` or ``cached``.

    Artifacts written before the cache existed have no ``source_snapshot`` and
    were always hashed from bytes, so their absence reads as exact.  A snapshot
    block that does not say it was read from bytes was not: it is provisional.
    """
    optional = derived_from.get("source_snapshot")
    if optional is None:
        return "exact"
    if not isinstance(optional, dict) or optional.get("version") != 1:
        raise ValueError("invalid serialized source snapshot")
    verification = optional.get("verification", "cached")
    if verification not in SNAPSHOT_VERIFICATIONS:
        raise ValueError(f"unknown source snapshot verification {verification!r}")
    return verification


def mark_provisional(derived_from: dict) -> dict:
    """What a driver hands to a probe: an identity nobody has yet verified.

    The driver's begin-side capture may itself have been exact (a cold miss),
    but that was the tree BEFORE the exercise.  The artifact is published
    after it, in a process the driver cannot vouch for, so the identity it
    carries is provisional until the driver's own exact walk stamps it --
    otherwise a driver that dies mid-run leaves an artifact reconcile accepts.
    """
    optional = derived_from.get("source_snapshot") or {
        "version": 1,
        "manifest_sha256": derived_from.get("artifact_sha256"),
        "files": derived_from.get("artifact_files"),
    }
    return {
        **derived_from,
        "source_snapshot": {**optional, "verification": "cached"},
    }


def mark_exact(derived_from: dict, verified: SourceSnapshot) -> dict:
    """Carry an exact verification outward onto a provisional provenance.

    The one process that read the bytes stamps the artifact; a child that was
    handed a carried identity cannot, because it read nothing.
    """
    if not verified.exact:
        raise ValueError("only an exact snapshot can mark provenance exact")
    if (
        derived_from.get("artifact_sha256") != verified.digest
        or derived_from.get("artifact_files") != verified.files
    ):
        raise ValueError("exact snapshot does not match the provenance it would mark")
    optional = derived_from.get("source_snapshot") or {
        "version": 1,
        "manifest_sha256": verified.digest,
        "files": verified.files,
    }
    return {
        **derived_from,
        "source_snapshot": {**optional, "verification": "exact"},
    }


def source_snapshot_of(root: Path, derived_from: dict) -> SourceSnapshot:
    """Rebuild and validate a serialized provenance snapshot.

    Old artifacts have no ``source_snapshot`` and remain valid: the authoritative
    fields have always been ``artifact_sha256`` and ``artifact_files``.
    """
    patterns = source_patterns_of(derived_from)
    # A validation helper answers "is this exactly the tree it names", so it
    # reads bytes; a cached answer here would be the cache validating itself.
    current = snapshot_tree(root, patterns, trust_cache=False)
    expected_digest = derived_from.get("artifact_sha256")
    expected_files = derived_from.get("artifact_files")
    if type(expected_files) is not int:
        # Defaulting this to the value under test made the check vacuous.
        raise ValueError("source provenance lacks an exact file count")
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
    snapshot_verification_of(derived_from)
    return SourceSnapshot(
        root=Path(root).resolve(),
        patterns=source_patterns_of(derived_from),
        digest=digest,
        files=files,
        verification={
            # Nothing was read to build this: it is an identity handed over by
            # the driver, which verifies it from bytes before publication.
            "cache": "carried",
            "cache_hit": False,
            "files_hashed": 0,
            "files_reused": 0,
            "exact": False,
            "duration_ms": 0,
        },
        entries=(),
        carried=True,
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

# --- SCIP fact exporter helpers (experiment/claim-semantics) -----------------
# The static-claim exporter needs the file list itself (which files *should*
# have been indexed) and the tree digest, walking the tree exactly once and
# exactly the way the digest did.  Built on ``snapshot_tree`` so the incremental
# cache and the digest formula are shared, not duplicated.

def patterns_for(language: str) -> tuple[str, ...]:
    """The glob set a tree of ``language`` is hashed over.

    Raises ``KeyError`` for a language with no pattern set rather than falling
    back to the Python default: hashing a Go tree as ``**/*.py`` yields the
    empty manifest, a digest that would agree across every Go tree.
    """
    if language not in LANGUAGE_PATTERNS:
        raise KeyError(language)
    return (LANGUAGE_PATTERNS[language],)


def tree_manifest(
    root: Path, patterns: tuple[str, ...] = DEFAULT_PATTERNS, *,
    cache_dir: Path | str | None = None,
) -> list[tuple[str, str]]:
    """The sorted ``(tree-relative posix path, sha256)`` manifest ``tree_sha256``
    hashes, from one snapshot walk."""
    return list(snapshot_tree(root, patterns, cache_dir=cache_dir).entries)


def manifest_sha256(entries: list[tuple[str, str]]) -> str:
    """The tree digest of a ``tree_manifest``: sha256 over ``"<path> <sha256>"``
    lines sorted by path -- the formula ``snapshot_tree`` uses, so a consumer
    holding the manifest reproduces the digest without a second walk."""
    manifest = "\n".join(sorted(set(f"{rel} {digest}" for rel, digest in entries)))
    return hashlib.sha256(manifest.encode()).hexdigest()
