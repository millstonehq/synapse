"""Propagate entity references backwards along call edges to the entry points.

A handler almost never touches a table itself. It calls a service, which calls a
repository, which holds the query -- so an analyser that looks only at the
handler body binds 3 entities of 12 and reports that as the answer. Following
calls until nothing new appears is the difference between 3 and 10.

This is a per-root breadth-first traversal rather than a global worklist,
because the distance falls out of it. That distance is two things at once: the
per-hop convergence history (does this method still find more at 4 hops than at
3?) and the evidence chain attached to every binding, so a reader can check the
claim by following the calls rather than trusting the tool.
"""

from __future__ import annotations

from collections import deque


def distances(
    root: str, calls: dict[str, set[str]], max_hops: int = 64
) -> dict[str, int]:
    """Shortest call distance from `root` to every node it can reach."""
    seen = {root: 0}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        hop = seen[node]
        if hop >= max_hops:
            continue
        for callee in sorted(calls.get(node, ())):
            if callee not in seen:
                seen[callee] = hop + 1
                queue.append(callee)
    return seen


def bind(
    roots: list[str], calls: dict[str, set[str]], direct: dict[str, set[str]]
) -> tuple[dict[str, dict[str, int]], list[int]]:
    """roots -> {entity: hops at which it was first reached}, plus the history.

    history[k] is the number of distinct entities bound across ALL roots using
    call chains of at most k hops. history[0] is the direct-reference-only
    answer. It converges by construction; a history that is still climbing at
    the last hop means the traversal was truncated, and the caller should say so
    rather than present the number as final.
    """
    per_root: dict[str, dict[str, int]] = {}
    depth = 0
    for root in roots:
        reach = distances(root, calls)
        bound: dict[str, int] = {}
        for node, hop in reach.items():
            for entity in direct.get(node, ()):
                if entity not in bound or hop < bound[entity]:
                    bound[entity] = hop
            depth = max(depth, hop)
        per_root[root] = bound

    history = []
    for k in range(depth + 1):
        found = {
            entity
            for bound in per_root.values()
            for entity, hop in bound.items()
            if hop <= k
        }
        history.append(len(found))
        if k >= 2 and history[-1] == history[-2] == history[-3]:
            break
    return per_root, history


def chain(
    root: str,
    entity: str,
    calls: dict[str, set[str]],
    direct: dict[str, set[str]],
) -> list[str]:
    """The shortest call path from `root` to a node that references `entity`."""
    if entity in direct.get(root, ()):
        return [root]
    parent: dict[str, str] = {root: ""}
    queue = deque([root])
    while queue:
        node = queue.popleft()
        for callee in sorted(calls.get(node, ())):
            if callee in parent:
                continue
            parent[callee] = node
            if entity in direct.get(callee, ()):
                path = [callee]
                while parent[path[-1]]:
                    path.append(parent[path[-1]])
                return list(reversed(path))
            queue.append(callee)
    return []
