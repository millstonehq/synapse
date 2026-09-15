from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from capcov import artifacts, cli
from capcov.cas import FilesystemCAS, IntegrityError
from capcov.outcomes import provenance as outcome_provenance
from capcov.probes import load_probe, pytest_probe


def legacy_tree_digest(root: Path, patterns: tuple[str, ...]) -> tuple[str, int]:
    entries = []
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            entries.append(
                f"{path.relative_to(root).as_posix()} "
                f"{hashlib.sha256(path.read_bytes()).hexdigest()}"
            )
    manifest = "\n".join(sorted(set(entries)))
    return hashlib.sha256(manifest.encode()).hexdigest(), len(set(entries))


class IncrementalTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "source"
        self.cache = Path(temporary.name) / "cache"
        self.root.mkdir()
        (self.root / "a.py").write_text("x = 1\n")
        (self.root / "b.py").write_text("y = 2\n")

    def test_cold_and_warm_keep_the_exact_legacy_manifest_digest(self) -> None:
        cold = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        warm = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        self.assertEqual((cold.digest, cold.files), legacy_tree_digest(self.root, ("**/*.py",)))
        self.assertEqual((warm.digest, warm.files), (cold.digest, cold.files))
        self.assertEqual(cold.verification["cache"], "miss")
        self.assertEqual(cold.verification["files_hashed"], 2)
        self.assertEqual(warm.verification["cache"], "hit")
        self.assertEqual(warm.verification["files_reused"], 2)
        self.assertEqual(warm.verification["files_hashed"], 0)

    def test_metadata_mismatch_rehashes_even_when_content_is_unchanged(self) -> None:
        cold = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        path = self.root / "a.py"
        stat = path.stat()
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
        refreshed = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        self.assertEqual(refreshed.digest, cold.digest)
        self.assertEqual(refreshed.verification["files_hashed"], 1)
        self.assertEqual(refreshed.verification["files_reused"], 1)

    def test_same_size_content_change_with_restored_mtime_is_not_a_false_hit(self) -> None:
        before = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        path = self.root / "a.py"
        stat = path.stat()
        path.write_text("x = 9\n")
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        # ctime/inode/device are conservative identity fields in addition to the
        # required relative path + size + mtime_ns key.
        after = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        self.assertNotEqual(after.digest, before.digest)
        self.assertGreaterEqual(after.verification["files_hashed"], 1)

    def test_corrupt_cache_falls_back_to_content_and_repairs_itself(self) -> None:
        expected = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        cache_file = next(self.cache.glob("*.json"))
        cache_file.write_text("{not-json")
        fallback = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        self.assertEqual(fallback.digest, expected.digest)
        self.assertEqual(fallback.verification["cache"], "fallback")
        self.assertEqual(fallback.verification["files_hashed"], 2)
        self.assertEqual(artifacts.snapshot_tree(self.root, cache_dir=self.cache).verification["cache"], "hit")

    def test_corrupt_content_addressed_manifest_falls_back_to_content(self) -> None:
        expected = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        reference = json.loads(next(self.cache.glob("*.json")).read_text())
        object_path = FilesystemCAS(self.cache / "cas").object_path(
            reference["object_sha256"]
        )
        object_path.write_bytes(b"corrupt manifest")
        fallback = artifacts.snapshot_tree(self.root, cache_dir=self.cache)
        self.assertEqual((fallback.digest, fallback.files), (expected.digest, expected.files))
        self.assertEqual(fallback.verification["cache"], "fallback")
        self.assertEqual(fallback.verification["files_hashed"], 2)

    def test_unwritable_or_invalid_cache_location_is_optional(self) -> None:
        blocked = self.cache
        blocked.write_text("not a directory")
        snapshot = artifacts.snapshot_tree(self.root, cache_dir=blocked)
        self.assertEqual((snapshot.digest, snapshot.files), legacy_tree_digest(self.root, ("**/*.py",)))
        self.assertEqual(snapshot.verification["cache"], "fallback")

    def test_cache_inside_source_is_disabled_and_never_changes_semantics(self) -> None:
        inside = self.root / ".capcov-cache"
        snapshot = artifacts.snapshot_tree(self.root, ("**/*",), cache_dir=inside)
        self.assertEqual(snapshot.verification["cache"], "disabled")
        self.assertFalse(inside.exists())


class CASTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.cas = FilesystemCAS(self.root / "cas")

    def test_exact_objects_canonical_snapshot_parent_and_materialization(self) -> None:
        a = self.cas.put_bytes(b"alpha\x00")
        b = self.cas.put_bytes(b"beta\n")
        first = self.cas.put_manifest({"b/value": b, "a/value": a})
        reordered = self.cas.put_manifest([("a/value", a), ("b/value", b)])
        child = self.cas.put_manifest({"a/value": a}, parent=first)
        self.assertEqual(first, reordered)
        self.assertNotEqual(first, child)
        self.assertEqual(self.cas.read_manifest(child)["parent"], first)
        output = self.cas.materialize(first, self.root / "materialized")
        self.assertEqual((output / "a/value").read_bytes(), b"alpha\x00")
        self.assertEqual((output / "b/value").read_bytes(), b"beta\n")

    def test_existing_object_is_validated_and_corruption_is_never_a_hit(self) -> None:
        digest = self.cas.put_bytes(b"immutable")
        self.assertEqual(self.cas.put_bytes(b"immutable"), digest)
        self.cas.object_path(digest).write_bytes(b"corrupt")
        with self.assertRaises(IntegrityError):
            self.cas.read_bytes(digest)
        with self.assertRaises(IntegrityError):
            self.cas.put_bytes(b"immutable")

    def test_materialization_failure_never_publishes_a_partial_destination(self) -> None:
        missing = self.cas.put_bytes(b"present when snapshotted")
        manifest = self.cas.put_manifest({"missing": missing})
        self.cas.object_path(missing).unlink()
        destination = self.root / "destination"
        with self.assertRaises(FileNotFoundError):
            self.cas.materialize(manifest, destination)
        self.assertFalse(destination.exists())


class PatternAndProvenanceTests(unittest.TestCase):
    def test_language_defaults_cover_python_go_php_and_fail_safe(self) -> None:
        self.assertEqual(
            cli._source_patterns([("treesitter-routes", {"language": "go"})]),
            ("**/*.go",),
        )
        self.assertEqual(
            cli._source_patterns([("treesitter-routes", {"language": "php"})]),
            ("**/*.php",),
        )
        self.assertEqual(
            cli._source_patterns([("treesitter-routes", {"language": "unknown"})]),
            ("**/*.py",),
        )

    def test_go_and_php_defaults_count_files_and_never_use_the_empty_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.go").write_text("package main\n")
            (root / "index.php").write_text("<?php echo 1;\n")
            empty = hashlib.sha256(b"").hexdigest()
            for language, pattern in (("go", "**/*.go"), ("php", "**/*.php")):
                digest, count = artifacts.tree_sha256(root, (pattern,), cache_dir=root.parent / f"cache-{language}")
                self.assertEqual(count, 1)
                self.assertNotEqual(digest, empty)
                derived = artifacts.provenance("src", digest, "test", count, (pattern,))
                self.assertEqual(derived["source_patterns"], [pattern])

    def test_carried_provenance_is_reused_and_finally_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "pipeline.py").write_text("STAGES = []\n")
            snapshot = artifacts.snapshot_tree(source, cache_dir=root / "cache")
            derived = snapshot.provenance("src", "capcov source-snapshot")
            result = load_probe.observe(
                source_root=source,
                out=root / "observed.json",
                source_snapshot=snapshot,
                source_provenance=derived,
            )
            for key in ("artifact", "artifact_sha256", "artifact_files", "source_snapshot"):
                self.assertEqual(result["derived_from"][key], derived[key])
            self.assertEqual(result["derived_from"]["extractor"], "capcov load-probe (stub)")
            self.assertIn("observe_ms", result["timing"])
            self.assertIn("cache_hit", result["timing"]["source_verification"])

    def test_legacy_artifact_without_optional_snapshot_still_reads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "a.py").write_text("x = 1\n")
            digest, count = artifacts.tree_sha256(source, cache_dir=root / "cache")
            legacy = {
                "schema_version": 1,
                "kind": "capabilities",
                "derived_from": {
                    "artifact": "src",
                    "artifact_sha256": digest,
                    "artifact_files": count,
                    "extractor": "legacy",
                    "extracted_at": "2026-01-01T00:00:00+00:00",
                },
            }
            path = root / "legacy.json"
            path.write_text(json.dumps(legacy))
            self.assertEqual(artifacts.read(path), legacy)
            self.assertEqual(artifacts.source_snapshot_of(source, legacy["derived_from"]).digest, digest)

    def test_outcome_provenance_reuses_selected_source_file_digests(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            tests = root / "tests"
            source.mkdir()
            tests.mkdir()
            source_file = source / "a.py"
            source_file.write_text("x = 1\n")
            test_file = tests / "test_a.py"
            test_file.write_text("def test_a(): pass\n")
            snapshot = artifacts.snapshot_tree(source, cache_dir=root / "cache")
            inventory = {
                "schema_version": 1,
                "kind": "capabilities",
                "surfaces": [{"id": "GET /a"}],
                "derived_from": snapshot.provenance("src", "test"),
            }
            mapping = {
                "version": 1,
                "scope": "a",
                "environment": "fixture",
                "limitations": ["none"],
                "inputs": ["src", "tests"],
                "outcomes": [{
                    "id": "a",
                    "capability": "a",
                    "description": "a",
                    "source_refs": ["GET /a"],
                    "policy": "required",
                    "tests": ["tests/test_a.py::test_a"],
                }],
            }
            real_read_bytes = Path.read_bytes

            def reject_source_reads(path: Path) -> bytes:
                if path.resolve().is_relative_to(source.resolve()):
                    raise AssertionError(f"source was read again: {path}")
                return real_read_bytes(path)

            with patch.object(Path, "read_bytes", reject_source_reads):
                result = outcome_provenance(root, mapping, inventory, snapshot)
            self.assertEqual(
                result["input_files"]["src/a.py"],
                snapshot.entries[0][1],
            )

    def test_reconcile_aggregates_all_phase_timings_and_normalise_ignores_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            derived = {
                "artifact": "src",
                "artifact_sha256": "a" * 64,
                "artifact_files": 1,
                "extractor": "test",
                "extracted_at": "2026-01-01T00:00:00+00:00",
            }
            capabilities = {
                "schema_version": 1,
                "kind": "capabilities",
                "derived_from": derived,
                "timing": {"discover_ms": 7},
                "entities": [],
                "surfaces": [],
                "capabilities": [],
                "blind_spots": [],
                "residue": [],
            }
            observed = {
                "schema_version": 1,
                "kind": "observed",
                "derived_from": {**derived, "extractor": "probe"},
                "timing": {"observe_ms": 11},
                "bindings": [],
            }
            capabilities_path = root / "capabilities.json"
            observed_path = root / "observed.json"
            output = root / "coverage.json"
            artifacts.write_document(capabilities_path, capabilities)
            artifacts.write_document(observed_path, observed)
            self.assertEqual(
                cli.main(
                    [
                        "reconcile",
                        str(capabilities_path),
                        str(observed_path),
                        "--out",
                        str(output),
                        "--quiet",
                    ]
                ),
                0,
            )
            coverage = artifacts.read(output, "coverage")
            self.assertEqual(coverage["timing"]["discover_ms"], 7)
            self.assertEqual(coverage["timing"]["observe_ms"], 11)
            self.assertIn("reconcile_ms", coverage["timing"])
            self.assertEqual(
                coverage["timing"]["total_ms"],
                18 + coverage["timing"]["reconcile_ms"],
            )
            changed_timing = {**coverage, "timing": {"total_ms": 999999}}
            self.assertEqual(
                artifacts.normalise(coverage), artifacts.normalise(changed_timing)
            )

    def test_pytest_probe_replaces_rescan_provenance_with_carried_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "src"
            source.mkdir()
            (source / "a.py").write_text("x = 1\n")
            out = root / "observed.json"
            snapshot = artifacts.snapshot_tree(source, cache_dir=root / "cache")
            derived = snapshot.provenance("src", "capcov source-snapshot")

            def fake_dump(path, source_root, exercises, **kwargs):
                artifacts.write(path, "observed", {"artifact_sha256": "old"}, {"bindings": []})

            old_enabled, old_started = pytest_probe._ENABLED, pytest_probe._STARTED_NS
            self.addCleanup(setattr, pytest_probe, "_ENABLED", old_enabled)
            self.addCleanup(setattr, pytest_probe, "_STARTED_NS", old_started)
            pytest_probe._ENABLED = True
            pytest_probe._STARTED_NS = time.perf_counter_ns()
            with (
                patch.object(pytest_probe.python_probe, "dump", side_effect=fake_dump),
                patch.dict(
                    os.environ,
                    {
                        "CAPCOV_OUT": str(out),
                        "CAPCOV_SOURCE_ROOT": str(source),
                        "CAPCOV_SOURCE_PROVENANCE": json.dumps(derived),
                    },
                    clear=False,
                ),
            ):
                pytest_probe.pytest_sessionfinish(SimpleNamespace(), 0)
            result = artifacts.read(out, "observed")
            self.assertEqual(result["derived_from"]["artifact_sha256"], snapshot.digest)
            self.assertEqual(result["derived_from"]["extractor"], "capcov python-probe")


if __name__ == "__main__":
    unittest.main()
