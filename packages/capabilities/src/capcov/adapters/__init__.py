"""Adapters know about a language and a stack. Nothing below this package does.

An adapter answers four questions and nothing else: where are the entities,
where are the surfaces, where are the entry points, and what calls what. The
core does the fixpoint, the reconciliation and the gate against the artifact an
adapter emits, which is what makes a second stack a day's work rather than a
fork.
"""

from __future__ import annotations

from types import ModuleType

REGISTRY = {"python-fastapi-sqlalchemy": "capcov.adapters.python_fastapi_sqlalchemy"}


def load(name: str) -> ModuleType:
    import importlib

    if name not in REGISTRY:
        raise SystemExit(
            f"unknown adapter {name!r}; have: {', '.join(sorted(REGISTRY))}"
        )
    return importlib.import_module(REGISTRY[name])
