"""The four-way diff. This is the product.

Static analysis enumerates paths that never run and loses the thread at dynamic
dispatch. Runtime observation follows dynamic dispatch exactly and only sees
what ran. They fail independently, so where they disagree is information rather
than noise:

    both          a capability
    static_only   a path no exercise reached -- a coverage gap
    runtime_only  the extractor missed it -- fix the adapter, or say why
    neither       declared and never touched -- dead

Three of those four are failures until someone names a reason. That is the
whole mechanism; everything else here is bookkeeping.
"""

from __future__ import annotations

CELLS = ("both", "static_only", "runtime_only", "neither")
FAILING_CELLS = ("static_only", "runtime_only", "neither")


def reconcile(capabilities: dict, observed: dict) -> dict:
    entities = [e["name"] for e in capabilities["entities"]]
    static_surfaces = {s["id"] for s in capabilities["surfaces"]}
    exercised: set[str] = set()

    static_by_entity: dict[str, dict] = {}
    for cap in capabilities["capabilities"]:
        row = static_by_entity.setdefault(
            cap["entity"], {"surfaces": set(), "ops": set()}
        )
        row["surfaces"].add(cap["surface"])
        row["ops"].update(cap["operations"])

    runtime_by_entity: dict[str, dict] = {}
    unknown_surfaces: dict[str, set[str]] = {}
    direct_from_tests: dict[str, set[str]] = {}
    for binding in observed["bindings"]:
        surface = binding["surface"]
        row = runtime_by_entity.setdefault(
            binding["entity"], {"surfaces": set(), "ops": set(), "tests": set(),
                                "via_surface": False}
        )
        row["surfaces"].add(surface)
        row["ops"].update(binding["operations"])
        row["tests"].update(binding.get("tests", []))
        if surface.startswith("test:"):
            # A test reaching past every surface into the internals. That is
            # observation, not a surface, and gating on it would fail the build
            # for every unit test in the repository. It is still worth counting:
            # an entity ONLY ever reached this way has no surface at all.
            direct_from_tests.setdefault(binding["entity"], set()).add(surface[5:])
            continue
        row["via_surface"] = True
        exercised.add(surface)
        if surface not in static_surfaces:
            unknown_surfaces.setdefault(surface, set()).add(binding["entity"])

    rows = []
    for entity in sorted(set(entities) | set(runtime_by_entity)):
        s = static_by_entity.get(entity)
        r = runtime_by_entity.get(entity)
        cell = (
            "both" if s and r
            else "static_only" if s
            else "runtime_only" if r
            else "neither"
        )
        rows.append(
            {
                "entity": entity,
                "cell": cell,
                "declared": entity in entities,
                "static_surfaces": sorted(s["surfaces"]) if s else [],
                "runtime_surfaces": sorted(r["surfaces"]) if r else [],
                "static_operations": sorted(s["ops"]) if s else [],
                "runtime_operations": sorted(r["ops"]) if r else [],
                # An operation static claims and runtime never saw is an
                # untested operation on a tested entity -- the gap the
                # entity-level cell is too coarse to show.
                "untested_operations": sorted(
                    (s["ops"] if s else set()) - (r["ops"] if r else set())
                ),
                "tests": sorted(r["tests"]) if r else [],
                # Observed only from test code reaching into the internals --
                # no route, no worker, no command. Reported, not gated: it is a
                # smell about the test suite, not a missing capability.
                "reached_only_by_tests": bool(r) and not r["via_surface"],
            }
        )

    # A test that exercised an entity nothing declares any more. This is the
    # deleted capability whose test keeps passing against something that is
    # gone, and it is invisible to every coverage number in the ordinary sense.
    orphan_tests = []
    for entity, row in sorted(runtime_by_entity.items()):
        if entity not in entities:
            for test in sorted(row["tests"]):
                orphan_tests.append({"test": test, "entity": entity})

    return {
        "rows": rows,
        "summary": {cell: sum(1 for r in rows if r["cell"] == cell) for cell in CELLS},
        "unknown_surfaces": [
            {"surface": surface, "entities": sorted(entities_)}
            for surface, entities_ in sorted(unknown_surfaces.items())
        ],
        "orphan_tests": orphan_tests,
        "reached_only_by_tests": sorted(
            entity for entity, row in runtime_by_entity.items() if not row["via_surface"]
        ),
        # A declared surface no exercise ever reached. The entity behind it is
        # usually still in the `both` cell, reached through some other route, so
        # the four cells cannot show this: an endpoint with no test hides behind
        # a well-tested table. Reported and not gated -- see the TDD.
        "unexercised_surfaces": sorted(
            s["id"] for s in capabilities["surfaces"]
            if s["id"] not in exercised and s.get("mounted", True)
        ),
        "unmounted_surfaces": sorted(
            s["id"] for s in capabilities["surfaces"] if not s.get("mounted", True)
        ),
    }
