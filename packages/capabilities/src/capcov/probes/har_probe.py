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
                                            declared, the browser probe's rule)
    HAR file name              -> test      (the exercise that produced it)

Honesty: a request no static surface matches is reported as an `unresolved`
entry (`gating: False`, runtime-side, counted with samples), never dropped.
Static surfaces the run never reached are simply absent, and land in
`static_only` at reconcile -- which is the point.

What the matcher models, and what it does not:

* A path parameter -- `{x}` or `:x` -- is exactly ONE required segment. An
  optional parameter (`:id?`, `{id?}`) and a `*` catch-all are not modelled:
  such a surface only matches a request with the parameter present, so a
  request that omits it is reported unmatched and the surface reads as
  `static_only`. That is the honest limit of the reading, named here rather
  than papered over with a looser regex.
* Trailing slashes are ignored on both sides (`/jobs/` is `/jobs`); a surface
  path without a leading slash is rooted (`admin/tows` is `/admin/tows`).
* A literal path beats a template. Two templates that both match one request
  (`/x/{a}` and `/{region}/zones` for `/x/zones`) bind nothing: the request is
  reported as `ambiguous-match`, because guessing would credit one route with
  evidence that may belong to the other.
* Matching uses the URL path only. `[capcov] har_strip_prefixes` removes a
  deployment mount before matching, and strips only `prefix + "/"`: a prefix of
  `/v2` does not touch `/v2beta/...`.
* HEAD, OPTIONS and verbs outside the CRUD map bind nothing (the browser
  probe's rule); they are counted as `non-binding-verbs`. Non-http(s) URLs
  (`data:`, `blob:`, `about:`) are counted in the `unmatched-requests` entry as
  `non_http`. An entry with no URL or no method is `malformed-entries`. Nothing
  reaches the `/` surface by accident.

The static inventory is ``<target>/capcov.capabilities.json`` unless
``[capcov] har_surfaces`` in ``capcov.toml`` names another file. The tree hash
keeps the package's ``**/*.py`` default deliberately: ``capcov discover``
hashes the source the same way and ``reconcile`` refuses a pair whose hashes
differ, so a probe-local pattern would make every reconcile a drift refusal.

Scale: the inventory is indexed once (literals by exact key, templates
compiled once), and each distinct ``(method, path)`` is resolved once per run.
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

# HTTP verb -> CRUD: the SAME weak-but-declared map the browser probe uses.
# Verbs outside the set (HEAD, OPTIONS, PROPFIND, a typo) claim no operation
# rather than guess one; they are counted, not bound.
VERB_TO_OP = {
    "GET": "read",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

# A path parameter in either template dialect: `{id}` (OpenAPI, Laravel) or
# `:id` (Express, Rails). Exactly one path segment each.
_PARAM = re.compile(r"\{[^/{}]+\}|:[A-Za-z_][A-Za-z0-9_]*")

# How many distinct requests an `unresolved` entry names verbatim. The count is
# always exact; the samples are the legible part.
SAMPLE_LIMIT = 25

# The URL schemes a request can carry and still be a route the target served.
HTTP_SCHEMES = ("http", "https")

# The index `index_surfaces` builds: exact literals keyed by (METHOD, path), and
# the templated surfaces with their regex compiled once.
Index = tuple[dict[tuple[str, str], str], list[tuple[str, "re.Pattern[str]", str]]]


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


def _normalise_path(path: str) -> str:
    """Root the path and drop a trailing slash: `admin/tows/` -> `/admin/tows`."""
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/") or "/"


def index_surfaces(surfaces: list[dict]) -> Index:
    """Index the static inventory once: literals by exact key, templates compiled.

    A surface path is normalised as the matcher normalises a request path (a
    missing leading slash is added, a trailing slash dropped), so the two sides
    compare on the same footing.
    """
    literals: dict[tuple[str, str], str] = {}
    templates: list[tuple[str, re.Pattern[str], str]] = []
    for surface in surfaces:
        method = (surface.get("method") or "").upper()
        spath = _normalise_path(surface.get("path") or "")
        if _PARAM.search(spath):
            templates.append((method, template_regex(spath), surface["id"]))
        else:
            literals.setdefault((method, spath), surface["id"])
    return literals, templates


def candidates_indexed(method: str, path: str, index: Index) -> list[str]:
    """Every surface id a request could be: one literal, or all matching templates.

    A literal hit is definitive and returns alone. Otherwise every template that
    matches is returned, in inventory order, so the caller can tell one hit from
    an ambiguity instead of silently taking the first.
    """
    literals, templates = index
    method = method.upper()
    path = _normalise_path(path)
    literal = literals.get((method, path))
    if literal is not None:
        return [literal]
    return [
        sid
        for template_method, pattern, sid in templates
        if template_method == method and pattern.fullmatch(path)
    ]


def match_indexed(method: str, path: str, index: Index) -> str | None:
    """The surface id a request reached, or None when none or several match."""
    candidates = candidates_indexed(method, path, index)
    return candidates[0] if len(candidates) == 1 else None


def match_surface(method: str, path: str, surfaces: list[dict]) -> str | None:
    """One-shot form of `match_indexed`: build the index and delegate.

    Convenient for a single lookup; `project_har` builds the index once instead.
    """
    return match_indexed(method, path, index_surfaces(surfaces))


def _request_path(path: str, strip_prefixes: list[str]) -> str:
    """A request's URL path with a configured mount prefix removed.

    Strips only `prefix + "/"`, so `/v2` removes the mount from `/v2/items` and
    leaves `/v2beta/items` alone. The first prefix that applies wins.
    """
    path = path or "/"
    for prefix in strip_prefixes:
        prefix = prefix.rstrip("/")
        if prefix and path.startswith(prefix + "/"):
            path = path[len(prefix):]
            break
    return _normalise_path(path)


def _labels(hars: dict[str, dict]) -> dict[str, str]:
    """Given path -> the basename used as the `tests` label; collisions refused.

    `ci/smoke.har` and `local/smoke.har` are two different runs. Labelling both
    `smoke.har` would merge their evidence under one name, so the collision is
    an error naming both paths, not a quiet fold.
    """
    by_label: dict[str, list[str]] = {}
    for given in hars:
        by_label.setdefault(Path(given).name, []).append(given)
    clashes = {label: paths for label, paths in by_label.items() if len(paths) > 1}
    if clashes:
        detail = "; ".join(
            f"{label!r} from {', '.join(paths)}" for label, paths in sorted(clashes.items())
        )
        raise ValueError(
            f"HAR files share a basename and would be merged under one "
            f"test label: {detail}"
        )
    return {given: Path(given).name for given in hars}


def _sample(method: str, host: str, path: str) -> str:
    """`METHOD host/path`, host empty when the URL had none (a relative URL)."""
    return f"{method} {host}{path}"


def _unresolved_entry(kind: str, samples: list[str], reason: str, **extra: object) -> dict:
    distinct = sorted(set(samples))
    return {
        "adapter": "har",
        "kind": kind,
        "gating": False,
        "count": len(distinct),
        "samples": distinct[:SAMPLE_LIMIT],
        "reason": reason,
        **extra,
    }


def project_har(
    hars: dict[str, dict], surfaces: list[dict], strip_prefixes: list[str]
) -> dict:
    """`{given_path: har_document}` -> `{bindings, unresolved, requests}`.

    One binding per surface reached, its ``tests`` the HAR basenames that
    reached it. Every entry is counted in ``requests``; what did not bind is
    grouped into non-gating ``unresolved`` entries by cause: matched no surface
    (with non-http URLs counted alongside), matched several, a verb outside the
    CRUD map, or an entry with no method or URL.
    """
    labels = _labels(hars)
    index = index_surfaces(surfaces)
    memo: dict[tuple[str, str], list[str]] = {}
    rows: dict[str, dict] = {}
    unmatched: list[str] = []
    ambiguous: list[str] = []
    non_binding: list[str] = []
    malformed: list[str] = []
    non_http = 0
    requests = 0
    for given in sorted(hars):
        label = labels[given]
        for position, entry in enumerate(hars[given].get("log", {}).get("entries", [])):
            requests += 1
            request = entry.get("request") or {}
            method = str(request.get("method") or "").upper()
            url = str(request.get("url") or "")
            if not method or not url:
                malformed.append(f"{label}#{position}")
                continue
            parts = urlsplit(url)
            if parts.scheme and parts.scheme.lower() not in HTTP_SCHEMES:
                non_http += 1
                continue
            host = parts.netloc
            path = _request_path(parts.path, strip_prefixes)
            if method not in VERB_TO_OP:
                non_binding.append(_sample(method, host, path))
                continue
            key = (method, path)
            if key not in memo:
                memo[key] = candidates_indexed(method, path, index)
            candidates = memo[key]
            if not candidates:
                unmatched.append(_sample(method, host, path))
                continue
            if len(candidates) > 1:
                ambiguous.append(f"{method} {path} -> [{', '.join(candidates)}]")
                continue
            row = rows.setdefault(candidates[0], {"operations": set(), "tests": set()})
            row["operations"].add(VERB_TO_OP[method])
            row["tests"].add(label)

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
    if unmatched or non_http:
        unresolved.append(
            _unresolved_entry(
                "unmatched-requests",
                unmatched,
                "requests in the run matched no static surface (assets, third-party, "
                "or routes discovery missed); non_http counts data:/blob:/about: URLs",
                non_http=non_http,
            )
        )
    if ambiguous:
        unresolved.append(
            _unresolved_entry(
                "ambiguous-match",
                ambiguous,
                "more than one templated surface matched; nothing bound rather than "
                "credit the wrong route",
            )
        )
    if non_binding:
        unresolved.append(
            _unresolved_entry(
                "non-binding-verbs",
                non_binding,
                "HEAD, OPTIONS and verbs outside the CRUD map claim no operation "
                "and bind nothing",
            )
        )
    if malformed:
        unresolved.append(
            _unresolved_entry(
                "malformed-entries",
                malformed,
                "HAR entries with no request method or URL (named as file#index)",
            )
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
            f"no static inventory at {surfaces_file}; run `capcov discover` "
            "first or set [capcov] har_surfaces in capcov.toml"
        )
    surfaces = json.loads(surfaces_file.read_text()).get("surfaces", [])
    if not har_paths:
        raise ValueError("name at least one .har file after `--`")
    hars = {str(p): json.loads(Path(p).read_text()) for p in har_paths}

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
