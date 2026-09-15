"""The `har` probe: runtime bindings harvested from an existing browser run.

Some targets have no Python test suite to hook and no planner flow models yet,
but they already run browser suites -- Playwright can record every request of a
run as a HAR file. This probe reads those HARs and projects each request onto
the static surface it reached:

    request METHOD + URL path  -> surface   (matched against the static
                                            inventory's path templates)
    the same surface           -> entity    (route readers self-bind, so the
                                            entity IS the surface id)
    HTTP verb                  -> operation (GET=read, POST=create, PUT/PATCH=
                                            update, DELETE=delete -- weak but
                                            declared, as the browser probe does)
    HAR file name              -> test      (the exercise that produced it)

Honesty: a request no static surface matches is reported as an `unresolved`
entry (`gating: False`, runtime-side, counted with samples), never dropped.
Static surfaces the run never reached are simply absent, and land in
`static_only` at reconcile -- which is the point.

The static inventory is ``<target>/capcov.capabilities.json`` unless
``[capcov] har_surfaces`` in ``capcov.toml`` names another file; ``[capcov]
har_strip_prefixes`` strips a leading path prefix (a deployment mount such as
``/v2``) before matching. The tree hash uses the same default patterns
``capcov discover`` uses, so ``reconcile`` accepts the pair as one tree.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from .. import artifacts
from .probe_registry import (
    ENV_NONCE,
    ENV_ONLY,
    ENV_OUT,
    ENV_SOURCE_ROOT,
    ENV_TARGET,
    FreshnessGuard,
    observed_carriers,
)

# HTTP verb -> CRUD. Same weak-but-declared map the browser probe uses, widened
# with the read-only verbs a browser emits on its own (HEAD, OPTIONS preflight).
VERB_TO_OP = {
    "GET": "read",
    "HEAD": "read",
    "OPTIONS": "read",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

# A path parameter in either template dialect: `{id}` (OpenAPI, Laravel) or
# `:id` (Express, Rails). Exactly one path segment each.
_PARAM = re.compile(r"\{[^/{}]+\}|:[A-Za-z_][A-Za-z0-9_]*")

# How many distinct unmatched requests an `unresolved` entry names verbatim.
# The count is always exact; the samples are the legible part.
SAMPLE_LIMIT = 25


def template_regex(path: str) -> re.Pattern[str]:
    """`/jobs/{id}` and `/jobs/:id` both match exactly one non-empty segment."""
    out: list[str] = []
    last = 0
    for match in _PARAM.finditer(path):
        out.append(re.escape(path[last:match.start()]))
        out.append("[^/]+")
        last = match.end()
    out.append(re.escape(path[last:]))
    return re.compile("".join(out))


def match_surface(method: str, path: str, surfaces: list[dict]) -> str | None:
    """The surface id a request reached: a literal path wins over a template."""
    literal = None
    templated = None
    for surface in surfaces:
        if (surface.get("method") or "").upper() != method.upper():
            continue
        spath = surface.get("path") or ""
        if not spath.startswith("/"):
            spath = "/" + spath
        if spath == path:
            literal = surface["id"]
            break
        if (
            templated is None
            and _PARAM.search(spath)
            and template_regex(spath).fullmatch(path)
        ):
            templated = surface["id"]
    return literal or templated


def _request_path(url: str, strip_prefixes: list[str]) -> str:
    """The path component of a request URL, with a configured prefix removed."""
    path = urlsplit(url).path or "/"
    for prefix in strip_prefixes:
        prefix = prefix.rstrip("/")
        if prefix and path.startswith(prefix + "/"):
            path = path[len(prefix):]
            break
    return path if path.startswith("/") else "/" + path


def project_har(
    hars: dict[str, dict], surfaces: list[dict], strip_prefixes: list[str]
) -> dict:
    """`{name: har_document}` -> `{bindings, unresolved, requests}`.

    One binding per surface reached, its ``tests`` the HAR names that reached
    it. Every request is counted in ``requests``; the ones no surface matched
    are grouped into a single non-gating ``unresolved`` entry.
    """
    rows: dict[str, dict] = {}
    unmatched: list[str] = []
    requests = 0
    for name in sorted(hars):
        for entry in hars[name].get("log", {}).get("entries", []):
            request = entry.get("request") or {}
            method = str(request.get("method", "")).upper()
            path = _request_path(str(request.get("url", "")), strip_prefixes)
            requests += 1
            sid = match_surface(method, path, surfaces)
            if sid is None:
                unmatched.append(f"{method} {path}")
                continue
            row = rows.setdefault(sid, {"operations": set(), "tests": set()})
            row["operations"].add(VERB_TO_OP.get(method, method.lower()))
            row["tests"].add(name)
    bindings = [
        {
            "surface": sid,
            "entity": sid,
            "operations": sorted(row["operations"]),
            "tests": sorted(row["tests"]),
        }
        for sid, row in sorted(rows.items())
    ]
    unresolved = []
    if unmatched:
        distinct = sorted(set(unmatched))
        unresolved.append(
            {
                "adapter": "har",
                "kind": "unmatched-requests",
                "gating": False,
                "count": len(distinct),
                "samples": distinct[:SAMPLE_LIMIT],
                "reason": (
                    "requests in the run matched no static surface (assets, "
                    "third-party, or routes discovery missed)"
                ),
            }
        )
    return {"bindings": bindings, "unresolved": unresolved, "requests": requests}


def _capcov_block(target: Path) -> dict:
    """The ``[capcov]`` config block, or ``{}`` when there is no capcov.toml."""
    config = target / "capcov.toml"
    if not config.exists():
        return {}
    import tomllib

    return tomllib.loads(config.read_text()).get("capcov", {})


def _surfaces_path(target: Path) -> Path:
    override = _capcov_block(target).get("har_surfaces")
    return target / override if override else target / "capcov.capabilities.json"


def _strip_prefixes(target: Path) -> list[str]:
    return [str(p) for p in _capcov_block(target).get("har_strip_prefixes", [])]


def observe(
    *,
    source_root: Path | str,
    out: Path | str,
    target: Path | str,
    har_paths: list[Path | str],
    nonce: str | None = None,
    only: str | None = None,
) -> dict:
    """Project the named HAR files and write the ``observed`` artifact.

    Mirrors the load probe under the shared freshness guard: unlink the stale
    output, snapshot the tree, build nonce-stamped evidence, verify it, then
    write. The HARs are the exercise here (already run), so the evidence is the
    projection itself; the guard still refuses a tree that changed while it was
    being read. ``only`` is accepted for the env contract and unused: a HAR is
    one recorded run, there is no inner loop to scope.
    """
    source = Path(source_root)
    out_path = Path(out)
    target_dir = Path(target)
    surfaces_file = _surfaces_path(target_dir)
    if not surfaces_file.exists():
        raise ValueError(
            f"har probe: no static inventory at {surfaces_file}; run `capcov discover` "
            "first or set [capcov] har_surfaces in capcov.toml"
        )
    surfaces = json.loads(surfaces_file.read_text()).get("surfaces", [])
    if not har_paths:
        raise ValueError("har probe: name at least one .har file after `--`")
    hars = {Path(p).name: json.loads(Path(p).read_text()) for p in har_paths}

    guard = FreshnessGuard(out_path, source)
    run_nonce = guard.begin(nonce)
    result = project_har(hars, surfaces, _strip_prefixes(target_dir))
    guard.verify({"nonce": run_nonce, **result})

    tree_hash, files = artifacts.tree_sha256(source)
    body = {
        "bindings": result["bindings"],
        "exercises": len(hars),
        "requests": result["requests"],
        **observed_carriers(excluded_surfaces=[], unresolved=result["unresolved"]),
    }
    artifacts.write(
        out_path,
        "observed",
        artifacts.provenance(
            os.path.basename(str(source)), tree_hash, "capcov har-probe", files
        ),
        body,
    )
    return artifacts.read(out_path, "observed")


def main(argv: list[str] | None = None) -> int:
    """Entry the probe registry points at: project the HARs named in ``argv``.

    Reads the unified observe env contract (``CAPCOV_OUT`` / ``CAPCOV_SOURCE_ROOT``
    / ``CAPCOV_TARGET`` / ``CAPCOV_NONCE`` / ``CAPCOV_ONLY``). ``argv`` is what
    follows ``--`` on ``capcov observe --probe har -- a.har b.har``. Returns 0 on
    a fresh, valid observation.
    """
    har_paths = [Path(a) for a in (argv or [])]
    out = os.environ.get(ENV_OUT)
    source_root = os.environ.get(ENV_SOURCE_ROOT)
    target = os.environ.get(ENV_TARGET)
    if not out or not source_root or not target:
        print(
            f"capcov har-probe: {ENV_OUT}, {ENV_SOURCE_ROOT} and {ENV_TARGET} must be set",
            file=sys.stderr,
        )
        return 2
    if not har_paths:
        print("capcov har-probe: name at least one .har file after --", file=sys.stderr)
        return 2
    try:
        observe(
            source_root=source_root,
            out=out,
            target=target,
            har_paths=har_paths,
            nonce=os.environ.get(ENV_NONCE),
            only=os.environ.get(ENV_ONLY),
        )
    except (ValueError, OSError) as error:
        print(f"capcov har-probe: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
