#!/usr/bin/env python3
"""Run a small, locked qualification measurement manifest and write private evidence.

The manifest is local input and is never copied to the report: command argv,
environment values and host paths are deliberately omitted. At most eight
samples and fifteen minutes of declared command time are accepted.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import threading
import time
from typing import Any

HERE = Path(__file__).resolve().parent
LOCK_HELPER = HERE / "with-heavy-lock.py"
MAX_SAMPLES = 8
MAX_BUDGET_SECONDS = 900
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MAX_TREE_FILES = 20_000
MAX_TREE_BYTES = 256 * 1024 * 1024
MAX_TOOLCHAIN_BINARIES = 12
MAX_TOOLCHAIN_BINARY_BYTES = 512 * 1024 * 1024
TAIL_BYTES = 16 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
PIN = re.compile(r"^(?:[0-9a-fA-F]{7,64}|not-applicable|unknown|unpinned)$")
SECRET = re.compile(
    r"(?i)(\b(?:bearer\s+|token|secret|password|cookie|authorization)\b\s*[:= ]\s*)[^\s,;]+")
ABSOLUTE_PATH = re.compile(r"(?<![A-Za-z0-9])/(?:[^\s\"'<>]+/)*[^\s\"'<>]*")


class MeasurementError(ValueError):
    pass


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_identity(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None
    root = Path(value)
    if not root.is_dir():
        return {"available": False, "sha256": None, "files": 0, "bytes": 0}
    digest = hashlib.sha256()
    count = total = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_symlink() or not path.is_file():
                continue
            size = path.stat().st_size
            count += 1
            total += size
            if count > MAX_TREE_FILES or total > MAX_TREE_BYTES:
                return {"available": True, "complete": False, "sha256": None,
                        "files": count, "bytes": total}
            relative = path.relative_to(root).as_posix().encode("utf-8", "surrogateescape")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            digest.update(size.to_bytes(8, "big"))
            digest.update(bytes.fromhex(_file_hash(path)))
    return {"available": True, "complete": True, "sha256": digest.hexdigest(),
            "files": count, "bytes": total}


def _source_identity(root_value: str) -> dict[str, Any]:
    root = Path(root_value)
    commit = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
                            capture_output=True, text=True, check=False)
    if commit.returncode:
        raise MeasurementError("source_root is not a readable git worktree")
    diff = subprocess.run(["git", "-C", str(root), "diff", "--binary", "HEAD", "--"],
                          capture_output=True, check=False)
    if diff.returncode or len(diff.stdout) > 32 * 1024 * 1024:
        raise MeasurementError("source diff failed or exceeded the 32 MiB bound")
    untracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
        capture_output=True, check=False)
    if untracked.returncode:
        raise MeasurementError("could not enumerate untracked source files")
    paths = sorted(p for p in untracked.stdout.split(b"\0") if p)
    if len(diff.stdout) > MAX_SOURCE_BYTES or len(paths) > MAX_TREE_FILES:
        raise MeasurementError("source diff exceeded the source identity bound")
    identity = hashlib.sha256()
    identity.update(b"tracked-diff\0")
    identity.update(diff.stdout)
    total = len(diff.stdout)
    for raw_path in paths:
        relative = Path(os.fsdecode(raw_path))
        path = root / relative
        if path.is_symlink():
            content = os.fsencode(os.readlink(path))
            kind = b"symlink\0"
        elif path.is_file():
            remaining = MAX_SOURCE_BYTES - total - len(raw_path)
            if path.stat().st_size > remaining:
                raise MeasurementError("untracked source files exceeded the source identity bound")
            content = path.read_bytes()
            kind = b"file\0"
        else:
            raise MeasurementError("an untracked source entry is not a regular file or symlink")
        total += len(raw_path) + len(content)
        if total > MAX_SOURCE_BYTES:
            raise MeasurementError("untracked source files exceeded the source identity bound")
        identity.update(kind)
        identity.update(len(raw_path).to_bytes(8, "big"))
        identity.update(raw_path)
        identity.update(len(content).to_bytes(8, "big"))
        identity.update(content)
    return {"commit": commit.stdout.strip(), "working_tree_sha256": identity.hexdigest(),
            "dirty": bool(diff.stdout or paths), "untracked_files": len(paths)}


def _toolchain(sample: dict[str, Any], name: str) -> dict[str, str]:
    pins = sample.get("toolchain", {})
    if not isinstance(pins, dict) or not all(isinstance(k, str) and SAFE_ID.fullmatch(k)
                                             and isinstance(v, str) and PIN.fullmatch(v)
                                             for k, v in pins.items()):
        raise MeasurementError(f"sample {name} toolchain must map safe pin names to revisions or status labels")
    return dict(sorted(pins.items()))


def _toolchain_binaries(sample: dict[str, Any], name: str) -> dict[str, dict[str, Any]]:
    binaries = sample.get("toolchain_binaries", {})
    if (not isinstance(binaries, dict) or len(binaries) > MAX_TOOLCHAIN_BINARIES or
            not all(isinstance(k, str) and SAFE_ID.fullmatch(k) and isinstance(v, str)
                    for k, v in binaries.items())):
        raise MeasurementError(f"sample {name} toolchain_binaries must map at most 12 safe ids to paths")
    result = {}
    for binary_id, path_value in sorted(binaries.items()):
        path = Path(path_value)
        if not path.is_absolute():
            raise MeasurementError(f"sample {name} toolchain binary paths must be absolute")
        try:
            resolved = path.resolve(strict=True)
            info = resolved.stat()
        except OSError as exc:
            raise MeasurementError(f"sample {name} toolchain binary {binary_id} is unavailable") from exc
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise MeasurementError(f"sample {name} toolchain binary {binary_id} is not executable")
        if info.st_size > MAX_TOOLCHAIN_BINARY_BYTES:
            raise MeasurementError(f"sample {name} toolchain binary {binary_id} exceeds the 512 MiB bound")
        result[binary_id] = {"sha256": _file_hash(resolved), "bytes": info.st_size}
    return result


def _tail_reader(stream, state: dict[str, Any]) -> None:
    tail = bytearray()
    total = 0
    while True:
        chunk = stream.read(8192)
        if not chunk:
            break
        total += len(chunk)
        tail.extend(chunk)
        if len(tail) > TAIL_BYTES:
            del tail[:-TAIL_BYTES]
    state["tail"] = bytes(tail)
    state["bytes"] = total


def _safe_tail(data: bytes, replacements: list[tuple[str, str]]) -> bytes:
    text = data.decode("utf-8", "replace")
    for value, label in sorted(replacements, key=lambda pair: len(pair[0]), reverse=True):
        if value:
            text = text.replace(value, label)
    text = SECRET.sub(r"\1<redacted>", text)
    text = ABSOLUTE_PATH.sub("<private-path>", text)
    return text.encode("utf-8")[-TAIL_BYTES:]


def _private_dir(path: Path) -> None:
    existed = path.exists()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if existed and path.stat().st_mode & 0o077:
        raise MeasurementError("private output directory must not be accessible by group or others")
    if not existed:
        path.chmod(0o700)


def _write_private(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_bytes(data)
    path.chmod(0o600)


def _sample(sample: dict[str, Any], *, index: int, planned: int, logs: Path,
            lock: Path | None, lock_timeout: float, default_timeout: float,
            remaining_budget: float) -> dict[str, Any]:
    name = sample.get("id")
    phase = sample.get("phase")
    if not isinstance(name, str) or not SAFE_ID.fullmatch(name):
        raise MeasurementError("every sample needs a safe id")
    if not isinstance(phase, str) or not SAFE_ID.fullmatch(phase):
        raise MeasurementError(f"sample {name} needs a safe phase")
    cache_state = sample.get("cache_state", "unknown")
    if cache_state not in {"cold", "warm", "not-applicable", "unknown"}:
        raise MeasurementError(f"sample {name} cache_state is not a supported label")
    kind = sample.get("sample_kind", "single")
    if kind not in {"single", "cold", "warm"}:
        raise MeasurementError(f"sample {name} sample_kind must be single, cold, or warm")
    group = sample.get("comparison_group")
    if group is not None and (not isinstance(group, str) or not SAFE_ID.fullmatch(group)):
        raise MeasurementError(f"sample {name} comparison_group must be a safe id")
    command = sample.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) for x in command):
        raise MeasurementError(f"sample {name} needs a non-empty command array")
    timeout = min(float(sample.get("timeout_seconds", default_timeout)), remaining_budget)
    if timeout <= 0:
        raise MeasurementError("the 15-minute command budget is exhausted")
    cwd = sample.get("cwd")
    env = os.environ.copy()
    additions = sample.get("env", {})
    if not isinstance(additions, dict) or not all(isinstance(k, str) and isinstance(v, str)
                                                   for k, v in additions.items()):
        raise MeasurementError(f"sample {name} env must be a string map")
    env.update(additions)
    source = _source_identity(str(sample["source_root"]))
    input_identity = _tree_identity(sample.get("input_root"))
    cache_before = _tree_identity(sample.get("cache_dir"))
    if cache_state == "cold" and cache_before and cache_before.get("files", 0) != 0:
        raise MeasurementError(f"sample {name} claimed cold cache but it was not empty")
    if cache_state == "warm" and (not cache_before or cache_before.get("files", 0) == 0):
        raise MeasurementError(f"sample {name} claimed warm cache but no cache files were present")
    output_root = Path(sample["output_root"]) if sample.get("output_root") else None
    if output_root is not None and output_root.is_symlink():
        raise MeasurementError(f"sample {name} output_root may not be a symlink")
    if output_root is not None and output_root.exists() and any(output_root.iterdir()):
        raise MeasurementError(f"sample {name} output_root must be empty")
    if output_root is not None:
        _private_dir(output_root)

    timing_path = logs / f"{name}.lock-timing.json"
    wrapper = [sys.executable, str(LOCK_HELPER), "--timeout", str(lock_timeout),
               "--label", name, "--timing-json", str(timing_path)]
    if lock is not None:
        wrapper.extend(["--lock", str(lock)])
    wrapper.extend(["--", *command])
    started = time.monotonic()
    proc = subprocess.Popen(wrapper, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, start_new_session=True)
    stdout_state: dict[str, Any] = {}
    stderr_state: dict[str, Any] = {}
    readers = [threading.Thread(target=_tail_reader, args=(proc.stdout, stdout_state), daemon=True),
               threading.Thread(target=_tail_reader, args=(proc.stderr, stderr_state), daemon=True)]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        # The lock wrapper can exit after its direct child exits while a
        # grandchild remains in the owned process group. Always kill the group
        # after the grace period, even if the leader has already been reaped.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        if proc.poll() is None:
            proc.wait()
    for reader in readers:
        reader.join(timeout=5)
    elapsed = time.monotonic() - started
    replacements = [(str(Path(v)), "<private-path>") for v in
                    (sample.get("source_root"), sample.get("input_root"),
                     sample.get("output_root"), sample.get("cache_dir"), str(timing_path),
                     str(lock) if lock else None, cwd) if v]
    replacements.extend((value, "<private-arg>") for value in command if value)
    replacements.extend((value, "<private-env>") for value in additions.values() if value)
    stdout_tail = _safe_tail(stdout_state.get("tail", b""), replacements)
    stderr_tail = _safe_tail(stderr_state.get("tail", b""), replacements)
    _write_private(logs / f"{name}.stdout.tail", stdout_tail)
    _write_private(logs / f"{name}.stderr.tail", stderr_tail)
    try:
        timing = json.loads(timing_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        timing = {"lock_acquired": False, "lock_wait_seconds": None, "command_seconds": None}
    output_identity = _tree_identity(str(output_root) if output_root is not None else None)
    cache_after = _tree_identity(sample.get("cache_dir"))
    go_target = {"required": bool(sample.get("require_go_target", False)), "ran": None}
    if go_target["required"]:
        case_name = sample.get("shake_case")
        try:
            text = stdout_tail.decode("utf-8")
            start = text.find("{")
            report_doc, _ = json.JSONDecoder().raw_decode(text, start)
            case = report_doc["cases"][case_name]
            status = case["impls"]["shen-go"]["status"]
            available = report_doc.get("available", [])
            ran = (status == "PASS" and available == ["shen-go"] and
                   "BYTE-IDENTICAL across 1 targets (shen-go)" in case.get("detail", ""))
        except (KeyError, TypeError, json.JSONDecodeError):
            ran = False
        go_target.update({"case": case_name if isinstance(case_name, str) else None, "ran": ran})
    group = sample.get("comparison_group")
    result = {
        "id": name, "phase": phase, "sample_kind": kind,
        "comparison_group": group,
        "cache_state": cache_state,
        "toolchain": _toolchain(sample, name),
        "resolved_toolchain_binaries": _toolchain_binaries(sample, name),
        "source": source, "input_identity": input_identity,
        "output_identity": output_identity,
        "native_cache_before": cache_before, "native_cache_after": cache_after,
        "lock_acquired": timing.get("lock_acquired"),
        "lock_wait_seconds": timing.get("lock_wait_seconds"),
        "exec_seconds": timing.get("command_seconds"),
        "elapsed_seconds": round(elapsed, 6),
        "exit_code": proc.returncode, "timed_out": timed_out,
        "stdout_bytes": stdout_state.get("bytes", 0), "stderr_bytes": stderr_state.get("bytes", 0),
        "log_tails": {"stdout": f"{name}.stdout.tail", "stderr": f"{name}.stderr.tail"},
        "required_go_target": go_target,
    }
    if result["lock_acquired"] is False:
        result["status"] = "blocked"
    elif proc.returncode != 0 or timed_out or result["lock_acquired"] is not True or go_target["ran"] is False:
        result["status"] = "failed"
    else:
        result["status"] = "complete"
    return result


def _comparisons(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for sample in samples:
        group = sample.get("comparison_group")
        if group and sample["sample_kind"] in {"cold", "warm"}:
            groups[group][sample["sample_kind"]] = sample
    result = []
    for group, pair in sorted(groups.items()):
        cold, warm = pair.get("cold"), pair.get("warm")
        cold_hash = (cold.get("output_identity") or {}).get("sha256") if cold else None
        warm_hash = (warm.get("output_identity") or {}).get("sha256") if warm else None
        same = bool(isinstance(cold_hash, str) and isinstance(warm_hash, str)
                    and cold_hash == warm_hash)
        result.append({"group": group, "cold_present": bool(cold), "warm_present": bool(warm),
                       "output_identity_matches": same,
                       "cold_sha256": cold_hash, "warm_sha256": warm_hash})
    return result


def _summary(report: dict[str, Any]) -> str:
    lines = [f"Qualification measurement: {report['sample_count']}/{report['planned_samples']} samples; "
             f"status={report['status']}"]
    for sample in report["samples"]:
        lines.append(f"- {sample['phase']} [{sample['sample_kind']}]: {sample['status']}, "
                     f"exec={sample['exec_seconds']}, lock_wait={sample['lock_wait_seconds']}, "
                     f"exit={sample['exit_code']}, output={((sample.get('output_identity') or {}).get('sha256') or 'unavailable')[:12]}")
    for pair in report["cold_warm_comparisons"]:
        lines.append(f"- {pair['group']} cold/warm output identities match: {pair['output_identity_matches']}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", required=True, type=Path, help="private JSON report path")
    parser.add_argument("--logs", type=Path, help="private bounded log-tail directory")
    parser.add_argument("--lock", type=Path, default=None, help="override the shared heavy-lock path")
    parser.add_argument("--lock-timeout", type=float, default=0,
                        help="seconds to wait; default 0 preserves a busy producer's priority")
    parser.add_argument("--command-timeout", type=float, default=300)
    parser.add_argument("--budget-seconds", type=float, default=MAX_BUDGET_SECONDS)
    args = parser.parse_args(argv)
    if not 0 <= args.lock_timeout <= 60 or not 1 <= args.command_timeout <= 300:
        parser.error("lock timeout must be 0..60s and command timeout 1..300s")
    if not 1 <= args.budget_seconds <= MAX_BUDGET_SECONDS:
        parser.error("budget must be 1..900 seconds")
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        samples = manifest.get("samples") if manifest.get("schema") == "capcov-qualification-measurement-v1" else None
        if not isinstance(samples, list) or not samples or len(samples) > MAX_SAMPLES:
            raise MeasurementError("manifest must contain 1..8 samples and use the supported schema")
        if not all(isinstance(s, dict) for s in samples):
            raise MeasurementError("each sample must be a JSON object")
        declared = sum(float(s.get("timeout_seconds", args.command_timeout)) for s in samples)
        if declared > args.budget_seconds:
            raise MeasurementError("declared sample time exceeds the 15-minute budget")
        report_path = args.report
        logs = args.logs or report_path.parent / (report_path.stem + "-logs")
        if report_path.is_symlink() or report_path.with_suffix(".md").is_symlink():
            raise MeasurementError("report paths may not be symlinks")
        if report_path.exists() or report_path.with_suffix(".md").exists():
            raise MeasurementError("report paths must not already exist")
        if logs.exists() and any(logs.iterdir()):
            raise MeasurementError("logs directory must be empty")
        _private_dir(logs)
        started = time.monotonic()
        outcomes: list[dict[str, Any]] = []
        status = "complete"
        for index, sample in enumerate(samples):
            remaining = args.budget_seconds - (time.monotonic() - started)
            if remaining <= 0:
                status = "budget-exhausted"
                break
            outcome = _sample(sample, index=index, planned=len(samples), logs=logs,
                              lock=args.lock, lock_timeout=args.lock_timeout,
                              default_timeout=args.command_timeout, remaining_budget=remaining)
            outcomes.append(outcome)
            if outcome["status"] != "complete":
                status = outcome["status"]
                break
        report = {
            "schema": "capcov-qualification-measurement-report-v1",
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "host": {"system": platform.system(), "machine": platform.machine(),
                     "python": platform.python_version()},
            "status": status, "planned_samples": len(samples), "sample_count": len(outcomes),
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "samples": outcomes, "cold_warm_comparisons": _comparisons(outcomes),
        }
        _write_private(report_path, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
        markdown = _summary(report).encode()
        _write_private(report_path.with_suffix(".md"), markdown)
        print(_summary(report), end="")
        return 0 if status == "complete" else (75 if status == "blocked" else 1)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, MeasurementError) as exc:
        print(f"measurement refused: {str(exc)[:300]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
