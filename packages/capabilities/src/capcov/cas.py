"""Small stdlib-only content-addressed storage for immutable evidence.

Objects are named by the SHA-256 of their exact bytes.  Snapshot manifests are
canonical JSON objects whose own object digest is their identity; an optional
parent digest therefore participates in that identity.  Materialisation is
built in a sibling staging directory and published with one rename, so readers
never observe a partially populated snapshot.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping

SHA256_HEX_LENGTH = 64
MANIFEST_VERSION = 1


class IntegrityError(ValueError):
    """Stored bytes or a manifest do not match their content identity."""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_bytes(value: object) -> bytes:
    """The one byte representation used for manifest identity."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: str) -> str:
    if not isinstance(value, str) or len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"invalid sha256 digest: {value!r}")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"invalid sha256 digest: {value!r}")
    return value


def _relative_path(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"unsafe snapshot path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or not value or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe snapshot path: {value!r}")
    normalized = path.as_posix()
    if normalized != value or "\\" in value:
        raise ValueError(f"snapshot paths must be normalized POSIX paths: {value!r}")
    return normalized


class FilesystemCAS:
    """Exact-byte object store with atomic, no-clobber publication."""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    def object_path(self, digest: str) -> Path:
        digest = _digest(digest)
        return self.root / "objects" / "sha256" / digest[:2] / digest[2:]

    def put_bytes(self, value: bytes) -> str:
        """Publish bytes once and validate any concurrently published object."""
        digest = sha256_bytes(value)
        destination = self.object_path(digest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{digest}.", dir=destination.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                # A hard link is an atomic create-if-absent operation.  Unlike
                # replace(), it cannot overwrite an existing immutable object.
                os.link(temporary, destination)
            except FileExistsError:
                self.read_bytes(digest)
            return digest
        finally:
            temporary.unlink(missing_ok=True)

    def read_bytes(self, digest: str) -> bytes:
        digest = _digest(digest)
        value = self.object_path(digest).read_bytes()
        actual = sha256_bytes(value)
        if actual != digest:
            raise IntegrityError(
                f"CAS object {digest} failed integrity validation (found {actual})"
            )
        return value

    def put_file(self, path: Path | str) -> str:
        return self.put_bytes(Path(path).read_bytes())

    def put_manifest(
        self,
        entries: Mapping[str, str] | Iterable[tuple[str, str]],
        *,
        parent: str | None = None,
    ) -> str:
        """Store a canonical path->object manifest and return its identity."""
        if parent is not None:
            self.read_manifest(parent)
        items = entries.items() if isinstance(entries, Mapping) else entries
        normalized: dict[str, str] = {}
        for raw_path, raw_digest in items:
            path = _relative_path(str(raw_path))
            digest = _digest(str(raw_digest))
            if path in normalized and normalized[path] != digest:
                raise ValueError(f"conflicting snapshot entry: {path}")
            self.read_bytes(digest)
            normalized[path] = digest
        ordered_paths = sorted(normalized)
        if any(
            later.startswith(earlier + "/")
            for earlier, later in zip(ordered_paths, ordered_paths[1:])
        ):
            raise ValueError("snapshot paths conflict as file and directory")
        document = {
            "version": MANIFEST_VERSION,
            "parent": _digest(parent) if parent is not None else None,
            "entries": [
                {"path": path, "sha256": digest}
                for path, digest in sorted(normalized.items())
            ],
        }
        return self.put_bytes(canonical_bytes(document))

    def read_manifest(self, digest: str) -> dict:
        value = self.read_bytes(digest)
        try:
            document = json.loads(value)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise IntegrityError(f"snapshot {digest} is not valid JSON") from exc
        if not isinstance(document, dict) or document.get("version") != MANIFEST_VERSION:
            raise IntegrityError(f"snapshot {digest} has an unsupported manifest")
        parent = document.get("parent")
        if parent is not None:
            _digest(parent)
        entries = document.get("entries")
        if not isinstance(entries, list):
            raise IntegrityError(f"snapshot {digest} has malformed entries")
        previous = None
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                raise IntegrityError(f"snapshot {digest} has malformed entries")
            path = _relative_path(entry["path"])
            _digest(entry["sha256"])
            if previous is not None and path <= previous:
                raise IntegrityError(f"snapshot {digest} entries are not canonical")
            previous = path
        paths = [entry["path"] for entry in entries]
        if any(
            later.startswith(earlier + "/")
            for earlier, later in zip(paths, paths[1:])
        ):
            raise IntegrityError(f"snapshot {digest} paths conflict as file and directory")
        if canonical_bytes(document) != value:
            raise IntegrityError(f"snapshot {digest} is not canonically encoded")
        return document

    def materialize(self, manifest_digest: str, destination: Path | str) -> Path:
        """Validate and materialize a snapshot through a sibling staging tree."""
        manifest = self.read_manifest(manifest_digest)
        destination = Path(destination)
        if destination.exists():
            raise FileExistsError(f"snapshot destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}.stage-", dir=destination.parent)
        )
        try:
            for entry in manifest["entries"]:
                target = stage / entry["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(self.read_bytes(entry["sha256"]))
            os.rename(stage, destination)
        except BaseException:
            shutil.rmtree(stage, ignore_errors=True)
            raise
        return destination
