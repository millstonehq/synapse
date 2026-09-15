"""The pluggable probe interface: a registry, one env contract, shared carriers.

A probe is not a Python ABC. It is a process (or an in-process driver) bound to a
fixed env contract and a single artifact: it runs the target's own exercises,
observes what they actually touched, and writes one ``observed`` artifact. The
default ``pytest`` probe is exactly today's behaviour; ``browser``, ``load`` and
``har`` are the other reality-side observers.

This module is the sibling of ``capcov.adapters``. The adapter registry names the
static (declared) readers; this registry names the runtime (actual) observers.
Together they feed the one reconcile and the one gate.

What lives here:

* ``REGISTRY`` / ``resolve`` / ``load`` -- name -> lazy dotted path, mirroring the
  adapter registry. ``resolve`` returns the dotted path WITHOUT importing (so a
  probe module that another task ships can be referenced before it exists);
  ``load`` imports it. An unknown probe RAISES -- a probe that does not exist must
  not resolve to an empty, green observation.
* The unified observe env contract (``ENV_*``) every probe reads.
* The shared ``observed`` honest-denominator carriers (``excluded_surfaces`` /
  ``unresolved``) -- defaulted and normalised, so a probe's own saw-but-filtered
  and could-not-resolve material reaches coverage -> gate instead of silently
  shrinking N (design §2 step 5).
* ``FreshnessGuard`` -- the strong stale-evidence guard (unlink + nonce +
  before/after source recheck) the browser and load probes share.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from types import ModuleType

# Lazy dotted paths, mirroring capcov.adapters.REGISTRY. Never import a probe
# module at registry-load time: `browser` is shipped by a separate task and may
# not be importable here, and `load`/`browser` pull in the target's own drivers
# which `capcov gate` must never pay for.
REGISTRY = {
    "pytest": "capcov.probes.pytest_probe",
    "browser": "capcov.probes.browser_probe",
    "load": "capcov.probes.load_probe",
    "har": "capcov.probes.har_probe",
}

# The unified observe env contract (design §1.3). `cmd_observe` sets these; every
# probe reads them. CAPCOV_NONCE and CAPCOV_ONLY are new for the four-cell path;
# the first four are exactly today's `cmd_observe` contract, so the default pytest
# probe is unchanged.
ENV_OBSERVE = "CAPCOV_OBSERVE"
ENV_OUT = "CAPCOV_OUT"
ENV_SOURCE_ROOT = "CAPCOV_SOURCE_ROOT"
ENV_TARGET = "CAPCOV_TARGET"
ENV_NONCE = "CAPCOV_NONCE"
ENV_ONLY = "CAPCOV_ONLY"

# An observed envelope with no runtime-side excluded surfaces still carries the
# key, explicitly empty. Absent-defaults-to-dropped is the Property-3 regression.
EMPTY_EXCLUDED_SURFACES: dict = {"count": 0, "surfaces": []}


def resolve(name: str) -> str:
    """Name -> dotted path, WITHOUT importing. Unknown probe raises."""
    if name not in REGISTRY:
        raise SystemExit(
            f"unknown probe {name!r}; have: {', '.join(sorted(REGISTRY))}"
        )
    return REGISTRY[name]


def load(name: str) -> ModuleType:
    """Name -> imported probe module. Unknown probe raises."""
    import importlib

    return importlib.import_module(resolve(name))


def _canonical(item: object) -> str:
    return json.dumps(item, sort_keys=True, default=str)


def excluded_surfaces_carrier(surfaces: list[dict] | None) -> dict:
    """Normalise a probe's saw-but-filtered surfaces into the carrier shape.

    Mirrors ``flows/discovery`` and the discovery-side carrier: ``{count,
    surfaces}`` with a stable order, so the field is comparable across runs and
    the narrowing stays visible rather than folded into a number.
    """
    items = list(surfaces or [])
    return {"count": len(items), "surfaces": sorted(items, key=_canonical)}


def observed_carriers(
    *,
    excluded_surfaces: list[dict] | None = None,
    unresolved: list[dict] | None = None,
) -> dict:
    """The two runtime-side honest-denominator carriers, defaulted + normalised.

    Every probe folds this into its observed envelope (design §1.3, §2 step 5):

    * ``excluded_surfaces`` -- exercises/candidates the probe SAW and dropped as
      out of scope (a diagnostic-scope browser run, a filtered scenario). Visible,
      never silent.
    * ``unresolved`` -- what the probe could not attribute or evaluate (an
      assertion it could not judge, a load sample it could not map, a driver not
      yet implemented). Named, never dropped.

    ``None`` defaults to explicit empty, so an observed artifact ALWAYS carries
    both keys and reconcile never has to guess whether an absent field meant
    "empty" or "the probe forgot".
    """
    return {
        "excluded_surfaces": excluded_surfaces_carrier(excluded_surfaces),
        "unresolved": sorted(list(unresolved or []), key=_canonical),
    }


class FreshnessGuard:
    """Reject stale output and a source change mid-exercise (design §3 / R4).

    The strong guard the browser and load probes share, distilled from
    ``flows run`` and ``outcomes.execute``:

    1. ``begin`` unlinks any stale ``out``, snapshots the source tree, and mints
       (or adopts) a nonce for this run.
    2. the probe drives its exercise, which must write FRESH evidence carrying
       that exact nonce.
    3. ``verify`` refuses evidence whose nonce does not match, or evidence
       produced against a source tree that changed while the exercise ran.

    The weak ``cmd_observe`` guard has neither a nonce nor a before/after recheck,
    so it trusts yesterday's ``--out``; a probe that drives an external runner
    must not. The nonce goes in the probe's PRIVATE run evidence, not in the final
    ``observed`` artifact -- the observed schema has no nonce field.
    """

    def __init__(
        self, out: Path | str, source_root: Path | str, *, patterns: tuple[str, ...] = ("**/*.py",)
    ) -> None:
        self.out = Path(out)
        self.source_root = Path(source_root)
        self.patterns = patterns
        self.nonce: str | None = None
        self._before: str | None = None

    def _tree(self) -> str:
        from ..artifacts import tree_sha256

        return tree_sha256(self.source_root, self.patterns)[0]

    def begin(self, nonce: str | None = None) -> str:
        """Unlink stale output, snapshot the source tree, fix the nonce."""
        self.out.unlink(missing_ok=True)
        self._before = self._tree()
        self.nonce = nonce or uuid.uuid4().hex
        return self.nonce

    def verify(self, evidence: dict) -> dict:
        """Refuse stale-nonce evidence or a source change during the run."""
        if self.nonce is None:
            raise ValueError("freshness guard: begin() was not called")
        if evidence.get("nonce") != self.nonce:
            raise ValueError(
                "freshness guard: evidence nonce does not match this run "
                "(a stale or reused artifact, not fresh observation)"
            )
        if self._tree() != self._before:
            raise ValueError(
                "freshness guard: source changed during execution; "
                "the observation describes a tree that no longer exists"
            )
        return evidence

    def verify_output(self, path: Path | str | None = None) -> dict:
        """Read the run's private evidence and verify it. Missing == not fresh."""
        evidence_path = Path(path) if path is not None else self.out
        if not evidence_path.exists():
            raise ValueError(
                "freshness guard: the exercise wrote no fresh evidence "
                f"({evidence_path})"
            )
        return self.verify(json.loads(evidence_path.read_text()))
