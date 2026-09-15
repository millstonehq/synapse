"""Project discovered surfaces onto a FODA feature tree.

`capcov features map` is the bridge the feature layer lacked: the tree records
what a system CAN do as user-recognisable nouns, discovery records what the code
DECLARES as routes, and nothing joined them. This module joins them by rule -- a
feature claims surfaces by id glob (fnmatch over ``"http:METHOD path"``) or by
tag (carried from an OpenAPI operation) -- and emits the ``{id: {covered, total}}``
map ``features coverage`` consumes.

Three refusals keep the projection honest, in the package's usual style:

* A surface no feature claims is NOT silently outside the product. It is listed
  under ``unassigned`` (the global-denominator property: every surface discovery
  can see is assigned or named).
* A surface several features claim counts toward each and is listed under
  ``contested`` so a human resolves the overlap rather than the tool guessing.
* Without a reconciliation, nothing is covered. ``assurance`` says
  ``"static-only"`` and every ``covered`` is zero. Declared is not exercised.
"""

from __future__ import annotations

import fnmatch

from . import model as model_mod


def validate_mapping(mapping: dict, model: dict) -> None:
    """Structural validity of a mapping against its feature model.

    A rule is ``{"surfaces": [glob, ...], "tags": [tag, ...]}``; either list may be
    absent, not both. Feature ids must exist in the model.
    """
    if not isinstance(mapping, dict) or mapping.get("version") != 1:
        raise ValueError("mapping version must be 1")
    features = mapping.get("features")
    if not isinstance(features, dict) or not features:
        raise ValueError("mapping needs a nonempty 'features' map")
    known = {f["id"] for f in model["features"]}
    unknown = sorted(set(features) - known)
    if unknown:
        raise ValueError(f"mapping names unknown features: {unknown}")
    for fid, rule in features.items():
        if not isinstance(rule, dict):
            raise ValueError(f"{fid}: rule must be an object")
        patterns = rule.get("surfaces", [])
        tags = rule.get("tags", [])
        if not isinstance(patterns, list) or not isinstance(tags, list):
            raise ValueError(f"{fid}: 'surfaces' and 'tags' must be lists")
        if not all(isinstance(p, str) and p for p in patterns + tags):
            raise ValueError(f"{fid}: patterns and tags must be nonempty strings")
        if not patterns and not tags:
            raise ValueError(f"{fid}: rule claims nothing (no surfaces, no tags)")


def _matches(surface: dict, rule: dict) -> bool:
    sid = surface["id"]
    if any(fnmatch.fnmatchcase(sid, pattern) for pattern in rule.get("surfaces", [])):
        return True
    wanted = set(rule.get("tags", []))
    return bool(wanted) and bool(wanted & set(surface.get("tags") or []))


def exercised_surfaces(coverage: dict) -> set[str]:
    """Every surface a reconciliation saw reached at runtime, across all rows."""
    seen: set[str] = set()
    for row in coverage.get("rows", []):
        seen.update(row.get("runtime_surfaces", []))
    return seen


def project(
    model: dict,
    mapping: dict,
    capabilities: dict,
    coverage: dict | None = None,
) -> dict:
    """Surfaces -> per-feature obligations plus the named remainder.

    Returns ``{version, assurance, obligations, surfaces_total, assigned,
    unassigned, contested, excluded_surfaces, unresolved}``. ``obligations`` is
    exactly the map ``features.coverage.rollup`` takes.
    """
    model_mod.validate(model)
    validate_mapping(mapping, model)
    surfaces = capabilities.get("surfaces", [])
    if not surfaces:
        raise ValueError(
            "discovery inventory has no surfaces; refusing to map an empty denominator"
        )
    exercised = exercised_surfaces(coverage) if coverage is not None else set()
    rules = mapping["features"]
    obligations = {fid: {"covered": 0, "total": 0} for fid in rules}
    claims: dict[str, list[str]] = {}
    for surface in surfaces:
        sid = surface["id"]
        owners = sorted(fid for fid, rule in rules.items() if _matches(surface, rule))
        claims[sid] = owners
        for fid in owners:
            obligations[fid]["total"] += 1
            if sid in exercised:
                obligations[fid]["covered"] += 1
    unassigned = sorted(sid for sid, owners in claims.items() if not owners)
    contested = {sid: owners for sid, owners in sorted(claims.items()) if len(owners) > 1}
    excluded = capabilities.get("excluded_surfaces") or {}
    return {
        "version": 1,
        "assurance": "static+runtime" if coverage is not None else "static-only",
        "obligations": obligations,
        "surfaces_total": len(surfaces),
        "assigned": len(surfaces) - len(unassigned),
        "unassigned": unassigned,
        "contested": contested,
        "excluded_surfaces": int(excluded.get("count", 0)),
        "unresolved": len(capabilities.get("unresolved") or []),
    }
