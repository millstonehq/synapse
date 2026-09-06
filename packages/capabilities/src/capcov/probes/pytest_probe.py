"""pytest plugin. Dormant unless CAPCOV_OBSERVE is set.

This is the whole runtime half from the target's point of view: install capcov,
run the test suite you already run. Nothing in the application changes, no
sidecar, no agent, no network. The plugin is loaded through the pytest11 entry
point, so there is not even a conftest line.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from . import python_probe

if TYPE_CHECKING:  # pytest is present whenever this plugin loads; the guard
    # keeps the module importable by capcov's own stdlib-only test suite.
    from pytest import Config, Item, Session

_ENABLED = False
_EXERCISES = 0


def pytest_configure(config: Config) -> None:
    global _ENABLED
    if os.environ.get("CAPCOV_OBSERVE") != "1":
        return
    hooks = python_probe.install()
    _ENABLED = True
    if not any(hooks.values()):
        raise RuntimeError(
            "CAPCOV_OBSERVE=1 but neither sqlalchemy nor fastapi could be "
            "imported. A probe that cannot observe must not report an empty "
            "observation as a clean run."
        )
    # Before any test module is imported, so `from x import process_one` in a
    # test file picks up the wrapper rather than the original.
    python_probe.install_entry_points(Path(os.environ.get("CAPCOV_TARGET", ".")))


def pytest_runtest_protocol(item: Item, nextitem: Item | None) -> None:
    """Outermost per-test hook: fixture setup counts as part of the exercise."""
    if _ENABLED:
        global _EXERCISES
        _EXERCISES += 1
        python_probe.set_exercise(item.nodeid)
    return None


def pytest_sessionfinish(session: Session, exitstatus: int) -> None:
    if not _ENABLED:
        return
    out = Path(os.environ.get("CAPCOV_OUT", "observed.json"))
    source = Path(os.environ.get("CAPCOV_SOURCE_ROOT", "src"))
    python_probe.dump(out, source, _EXERCISES)
