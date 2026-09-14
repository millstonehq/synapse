"""T2 CLI engine plumbing: adapter XOR adapters, merge, probe select, carriers.

Pins the four T2 guarantees (design §1.1, §2 step 2):

* a single ``adapter`` string produces BYTE-IDENTICAL capabilities.json to
  origin/main -- the python-fastapi-sqlalchemy back-compat floor. The test
  regenerates the baseline from origin/main's own ``cli.py`` (git blob) run
  against the CURRENT package, and diffs, so this is genuinely "both ways", not a
  frozen golden file;
* ``[[adapters]]`` runs each adapter and MERGES their core dicts; a duplicate
  obligation id across adapters RAISES rather than one silently clobbering the
  other; ``adapter`` and ``adapters`` are XOR;
* ``observe`` selects the probe via the T3 registry -- the default ``pytest``
  probe is command-driven and byte-identical to today's observe env, an
  in-process probe (``load``) self-drives, an unknown probe raises;
* the honest-denominator carriers (``excluded_surfaces`` / ``unresolved``) land
  in capabilities.json for a route/contract adapter and stay ABSENT on the python
  path (the scip_* conditional pattern -> backward compatible).

The treesitter multi-adapter case RUNS (not skips) under ``--extra treesitter``.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from capcov import cli

from .support import APP, Project

_HERE = Path(__file__).resolve()
_CAP_ROOT = _HERE.parents[1]  # packages/capabilities
_SRC = _CAP_ROOT / "src"
_REPO = _CAP_ROOT.parents[1]  # the git repo root

_HAVE_TS = (
    importlib.util.find_spec("tree_sitter") is not None
    and importlib.util.find_spec("tree_sitter_language_pack") is not None
)

# A Go bare-call route query capturing the string literal as @path -- the same
# shape the promoted-adapter tests use.
GO_QUERY = (
    "((call_expression function: (identifier) @fn (#eq? @fn \"handle\") "
    "arguments: (argument_list (interpreted_string_literal) @path)))"
)

_OPENAPI = json.dumps({"openapi": "3.1.0", "paths": {"/items": {"get": {}, "post": {}}}})


def _origin_main_cli_source() -> str:
    """origin/main's cli.py, from git. The byte-identical baseline is that code."""
    for ref in ("origin/main", "7801732"):
        try:
            done = subprocess.run(
                ["git", "-C", str(_REPO), "show",
                 f"{ref}:packages/capabilities/src/capcov/cli.py"],
                capture_output=True, text=True, check=True,
            )
            return done.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    raise unittest.SkipTest("origin/main baseline cli.py is not reachable via git")


def _shadow_src_with_baseline_cli(tmp: Path) -> Path:
    """A copy of the current src with ONLY cli.py replaced by origin/main's.

    Everything else (the python adapter, fixpoint, artifacts) is the current
    package, unchanged since origin/main on the python path -- so this runs
    origin/main's discover logic against exactly the code the new cli shares.
    """
    shadow = tmp / "baseline_src"
    shutil.copytree(_SRC, shadow)
    (shadow / "capcov" / "cli.py").write_text(_origin_main_cli_source())
    return shadow


def _run_capcov(src_dir: Path, argv: list[str], extra_env: dict | None = None) -> subprocess.CompletedProcess:
    import os

    env = {**os.environ, "PYTHONPATH": str(src_dir)}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "capcov", *argv],
        capture_output=True, text=True, env=env,
    )


def _mask_volatile(doc: dict) -> dict:
    """Drop only extracted_at: everything else (incl. artifact_sha256, extractor)
    must match for a genuine byte-identity claim, not merely normalise()'s
    provenance-blind compare."""
    clone = json.loads(json.dumps(doc))
    clone.get("derived_from", {}).pop("extracted_at", None)
    return clone


def _write_project(root: Path, capcov_toml: str, files: dict[str, str]) -> None:
    (root / "capcov.toml").write_text(capcov_toml)
    src = root / "src"
    src.mkdir(exist_ok=True)
    for name, body in files.items():
        path = src / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)


class SingleAdapterBackCompatTests(unittest.TestCase):
    """A lone `adapter` string is byte-identical to origin/main (R7)."""

    def test_python_path_byte_identical_to_origin_main(self) -> None:
        project = Project(APP)  # the full python-fastapi-sqlalchemy fixture
        self.addCleanup(project.close)
        (project.root / "capcov.toml").write_text(
            '[capcov]\nadapter = "python-fastapi-sqlalchemy"\nsource = "src"\n'
        )
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        shadow = _shadow_src_with_baseline_cli(work)

        base_out = work / "baseline.json"
        new_out = work / "new.json"
        base = _run_capcov(
            shadow,
            ["discover", "--target", str(project.root), "--out", str(base_out), "--quiet"],
        )
        new = _run_capcov(
            _SRC,
            ["discover", "--target", str(project.root), "--out", str(new_out), "--quiet"],
        )
        self.assertEqual(base.returncode, 0, base.stderr)
        self.assertEqual(new.returncode, 0, new.stderr)

        baseline = json.loads(base_out.read_text())
        current = json.loads(new_out.read_text())
        self.assertEqual(_mask_volatile(baseline), _mask_volatile(current))
        # The python path emits no route carriers -> the new keys are ABSENT, so
        # even the exact top-level key set is unchanged (the scip_* pattern).
        self.assertNotIn("excluded_surfaces", current)
        self.assertNotIn("unresolved", current)
        self.assertEqual(
            current["derived_from"]["extractor"], "capcov python-fastapi-sqlalchemy"
        )


class MultiAdapterMergeTests(unittest.TestCase):
    def _discover(self, capcov_toml: str, files: dict[str, str], *, extra_ts: bool = False) -> dict:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_project(root, capcov_toml, files)
        out = root / "capabilities.json"
        rc = cli.main(["discover", "--target", str(root), "--out", str(out), "--quiet"])
        self.assertEqual(rc, 0)
        return json.loads(out.read_text())

    def test_two_structured_spec_adapters_merge(self) -> None:
        capabilities = self._discover(
            '[capcov]\nsource = "src"\n'
            '[[adapters]]\nname = "structured-spec"\ndocument = "a.json"\nprefix = "/api"\n'
            '[[adapters]]\nname = "structured-spec"\ndocument = "b.json"\nprefix = "/svc"\n',
            {
                "a.json": json.dumps({"openapi": "3.1.0", "paths": {"/items": {"get": {}}}}),
                "b.json": json.dumps({"openapi": "3.1.0", "paths": {"/orders": {"get": {}}}}),
            },
        )
        self.assertEqual(
            {s["id"] for s in capabilities["surfaces"]},
            {"http:GET /api/items", "http:GET /svc/orders"},
        )
        # both docs' capabilities are present, self-bound at hop 0.
        caps = {(c["entity"], c["surface"]) for c in capabilities["capabilities"]}
        self.assertEqual(
            caps,
            {("http:GET /api/items", "http:GET /api/items"),
             ("http:GET /svc/orders", "http:GET /svc/orders")},
        )
        # The merged extractor names both adapters.
        self.assertEqual(
            capabilities["derived_from"]["extractor"],
            "capcov structured-spec+structured-spec",
        )
        # Both adapters' honest limits survive the merge -- N is not shrunk.
        self.assertIn("unresolved", capabilities)
        self.assertTrue(any(u["kind"] == "boundary" for u in capabilities["unresolved"]))

    def test_duplicate_obligation_id_across_adapters_raises(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_project(
            root,
            '[capcov]\nsource = "src"\n'
            '[[adapters]]\nname = "structured-spec"\ndocument = "a.json"\n'
            '[[adapters]]\nname = "structured-spec"\ndocument = "a.json"\n',
            {"a.json": json.dumps({"openapi": "3.1.0", "paths": {"/items": {"get": {}}}})},
        )
        out = root / "capabilities.json"
        with self.assertRaises(SystemExit) as caught:
            cli.main(["discover", "--target", str(root), "--out", str(out), "--quiet"])
        self.assertIn("duplicate obligation IDs", str(caught.exception))

    def test_adapter_and_adapters_are_xor(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_project(
            root,
            '[capcov]\nsource = "src"\nadapter = "python-fastapi-sqlalchemy"\n'
            '[[adapters]]\nname = "structured-spec"\ndocument = "a.json"\n',
            {"a.json": "{}"},
        )
        out = root / "capabilities.json"
        with self.assertRaises(SystemExit) as caught:
            cli.main(["discover", "--target", str(root), "--out", str(out), "--quiet"])
        self.assertIn("XOR", str(caught.exception))

    @unittest.skipUnless(_HAVE_TS, "treesitter extra not installed")
    def test_treesitter_and_structured_spec_merge(self) -> None:
        capabilities = self._discover(
            '[capcov]\nsource = "src"\n'
            '[[adapters]]\nname = "structured-spec"\ndocument = "openapi.json"\n'
            '[[adapters]]\nname = "treesitter-routes"\nlanguage = "go"\n'
            'globs = ["*.go"]\n'
            "query = '" + GO_QUERY + "'\n",
            {
                "openapi.json": json.dumps({"openapi": "3.1.0", "paths": {"/items": {"get": {}}}}),
                "svc.go": 'package main\nfunc f() {\n\thandle("POST /ask", h)\n}\n',
            },
        )
        self.assertEqual(
            {s["id"] for s in capabilities["surfaces"]},
            {"http:GET /items", "http:POST /ask"},
        )
        self.assertEqual(
            capabilities["derived_from"]["extractor"],
            "capcov structured-spec+treesitter-routes",
        )


class DiscoverCarriersTests(unittest.TestCase):
    """excluded_surfaces / unresolved land in capabilities.json (design §2)."""

    def test_route_adapter_writes_carriers(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_project(
            root,
            '[capcov]\nadapter = "structured-spec"\nsource = "src"\n'
            'document = "openapi.json"\nprofile = "openapi"\n',
            {"openapi.json": _OPENAPI},
        )
        out = root / "capabilities.json"
        rc = cli.main(["discover", "--target", str(root), "--out", str(out), "--quiet"])
        self.assertEqual(rc, 0)
        capabilities = json.loads(out.read_text())
        # Both carriers are first-class top-level keys.
        self.assertIn("excluded_surfaces", capabilities)
        self.assertIn("unresolved", capabilities)
        self.assertEqual(capabilities["excluded_surfaces"], {"count": 0, "surfaces": []})
        # The document boundaries reach the denominator, never dropped.
        self.assertTrue(any(u["kind"] == "boundary" for u in capabilities["unresolved"]))

    def test_empty_openapi_has_no_green_denominator(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_project(
            root,
            '[capcov]\nadapter = "structured-spec"\nsource = "src"\n'
            'document = "openapi.json"\n',
            {"openapi.json": json.dumps({"openapi": "3.1.0", "paths": {}})},
        )
        out = root / "capabilities.json"
        rc = cli.main(["discover", "--target", str(root), "--out", str(out), "--quiet"])
        self.assertEqual(rc, 0)
        capabilities = json.loads(out.read_text())
        self.assertEqual(capabilities["capabilities"], [])
        # An empty spec is not silently green: its limits are named in unresolved.
        self.assertTrue(capabilities["unresolved"])


# A fake exercise command: dump the CAPCOV_* env it received to a sidecar and
# write a (minimal) observed.json to CAPCOV_OUT -- the pytest11 plugin's role,
# faked so the observe env contract can be compared without a real pytest run.
_FAKE_EXERCISE = (
    "import os, json;"
    "cap={k:v for k,v in os.environ.items() if k.startswith('CAPCOV_') "
    "and k!='CAPCOV_ENVDUMP'};"
    "open(os.environ['CAPCOV_ENVDUMP'],'w').write(json.dumps(cap));"
    "open(os.environ['CAPCOV_OUT'],'w').write("
    "json.dumps({'schema_version':1,'kind':'observed'}))"
)


class ObservePytestBackCompatTests(unittest.TestCase):
    """probe=pytest (default) reproduces today's command-driven observe."""

    def _project(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_project(
            root,
            '[capcov]\nadapter = "python-fastapi-sqlalchemy"\nsource = "src"\n',
            {"app.py": "x = 1\n"},
        )
        return root

    def test_default_probe_env_matches_origin_main(self) -> None:
        root = self._project()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        work = Path(tmp.name)
        shadow = _shadow_src_with_baseline_cli(work)

        base_dump = work / "env_base.json"
        new_dump = work / "env_new.json"
        obs = work / "obs.json"  # same --out -> CAPCOV_OUT is identical by design
        base = _run_capcov(
            shadow,
            ["observe", "--target", str(root), "--out", str(obs),
             "--", sys.executable, "-c", _FAKE_EXERCISE],
            extra_env={"CAPCOV_ENVDUMP": str(base_dump)},
        )
        new = _run_capcov(
            _SRC,
            ["observe", "--target", str(root), "--out", str(obs),
             "--", sys.executable, "-c", _FAKE_EXERCISE],
            extra_env={"CAPCOV_ENVDUMP": str(new_dump)},
        )
        self.assertEqual(base.returncode, 0, base.stderr)
        self.assertEqual(new.returncode, 0, new.stderr)

        base_env = json.loads(base_dump.read_text())
        new_env = json.loads(new_dump.read_text())
        # CAPCOV_NONCE is deliberately fresh per invocation.  A live origin/main
        # may already contain the nonce behavior, so compare its contract rather
        # than two independently generated values.
        base_nonce = base_env.pop("CAPCOV_NONCE", None)
        new_nonce = new_env.pop("CAPCOV_NONCE", None)
        self.assertRegex(new_nonce or "", r"^[0-9a-f]{32}$")
        if base_nonce is not None:
            self.assertRegex(base_nonce, r"^[0-9a-f]{32}$")
        self.assertEqual(base_env, new_env)
        # Apart from that freshness token, the observed environment is unchanged
        # whether the pinned baseline predates the nonce or live origin/main has it.
        self.assertEqual(base_env["CAPCOV_OBSERVE"], "1")

    def test_default_probe_requires_a_command(self) -> None:
        root = self._project()
        with self.assertRaises(SystemExit) as caught:
            cli.main(["observe", "--target", str(root)])
        self.assertIn("give the command after --", str(caught.exception))


class ObserveProbeSelectionTests(unittest.TestCase):
    def _project(self, capcov_toml: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        _write_project(root, capcov_toml, {"app.py": "x = 1\n"})
        return root

    def test_in_process_probe_self_drives_without_a_command(self) -> None:
        # The load probe reads the unified env and drives itself in-process; no
        # command after -- is needed, unlike the command-driven pytest probe.
        root = self._project(
            '[capcov]\nadapter = "python-fastapi-sqlalchemy"\nsource = "src"\n'
            'probe = "load"\n'
        )
        out = root / "observed.json"
        rc = cli.main(["observe", "--target", str(root), "--out", str(out)])
        self.assertEqual(rc, 0)
        observed = json.loads(out.read_text())
        self.assertEqual(observed["kind"], "observed")
        self.assertEqual(observed["bindings"], [])
        # The stub names its missing driver -> it never masquerades as clean-empty.
        self.assertTrue(any(u["kind"] == "driver" for u in observed["unresolved"]))

    def test_flag_overrides_config_probe(self) -> None:
        # config says pytest (command-driven); --probe load selects the in-process
        # probe, which needs no command.
        root = self._project(
            '[capcov]\nadapter = "python-fastapi-sqlalchemy"\nsource = "src"\n'
            'probe = "pytest"\n'
        )
        out = root / "observed.json"
        rc = cli.main(["observe", "--target", str(root), "--out", str(out), "--probe", "load"])
        self.assertEqual(rc, 0)
        self.assertTrue(out.exists())

    def test_unknown_probe_raises(self) -> None:
        root = self._project(
            '[capcov]\nadapter = "python-fastapi-sqlalchemy"\nsource = "src"\n'
        )
        with self.assertRaises(SystemExit) as caught:
            cli.main(["observe", "--target", str(root), "--probe", "nope"])
        self.assertIn("unknown probe", str(caught.exception))

    def test_observe_leaves_environment_untouched(self) -> None:
        import os

        root = self._project(
            '[capcov]\nadapter = "python-fastapi-sqlalchemy"\nsource = "src"\n'
        )
        before = dict(os.environ)
        out = root / "observed.json"
        cli.main(["observe", "--target", str(root), "--out", str(out), "--probe", "load"])
        # The in-process probe path sets and RESTORES the env contract.
        self.assertEqual(dict(os.environ), before)


if __name__ == "__main__":
    unittest.main()
