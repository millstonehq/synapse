"""`--judge` is opt-in: the default path is upstream's, byte for byte and import for import.

Six properties, one per section below.

1. **Nothing is imported unless asked.**  `capcov.cli` -- and a whole default
   `reconcile`/`gate` run through it -- must leave `sys.modules` free of every
   `capcov.claims` module.  The claims judge is behind a lazy import inside the
   branch `--judge claims` selects, the same way `capcov experiment` is behind a
   lazy import inside `main`.

2. **Asking incoherently is a usage error, not a verdict.**  `--judge claims`
   with no `--receipt`, an unknown engine in `capcov.toml`, a `--receipt` that
   is not a receipt directory, and `--receipt` without `--judge claims` all exit
   2 with a named message.  Exit 2 is argparse's code for "your command line
   does not name a run"; it is never a claim about the system under test.

3. **An optional kernel is asked for by name, and named when it is absent.**
   `--judge claims` alone judges with the stdlib Python evaluator and needs no
   tool at all; `--evaluator souffle` (or `souffle-compiled`, or the capcov.toml
   key) with the interpreter off PATH exits 2 with a message naming the binary,
   where it was looked for, how to install it and the flag that needs nothing --
   the shape `capcov discover --resolver scip` uses for a missing indexer -- and
   writes no judge artifacts.  A judge that ran one kernel says so in
   judge.json (`kernels: ["python"]`, `differential: not-run (single
   evaluator)`) rather than reporting a differential it did not run.

4. **A producer profile runs only when it is named.**  ``--model shen:DIR``
   runs Stage D's typed checker over the model before judging and writes its
   certificate and ``model_well_formed.json`` into the receipt; without the flag
   nothing under ``capcov.claims.modelcheck`` or ``capcov.claims.shen`` is
   imported, the judge reads whatever ``model_*`` files the receipt already has,
   and a receipt with none is *judged* -- unresolved, with the model premises
   named as missing -- rather than refused.  Asking for the profile where
   shen-go is absent is the same named exit 2 an absent Souffle gets.

5. **The judge adds a verdict; it never replaces the artifact's.**  `gate` runs
   the four-cell gate under either judge and passes only when both pass, and
   `reconcile`/`gate` record the artifact they judged -- by digest, with its
   source snapshot and its own verdict -- in judge.json.  A receipt names a run
   of the system under test and a coverage artifact names a source tree; nothing
   binds them, so a supported receipt must not turn a failing artifact green and
   judge.json must not read as a verdict about a tree it never saw.

6. **The judge never writes into the evidence, and never reads its own output as
   evidence.**  `replay.join.write_artifacts` writes a `receipt.json` of the
   judge's own into `--judge-out`, so a `--judge-out` at or inside `--receipt` is
   exit 2 before any judging, and a previous `--judge-out` handed back as
   `--receipt` is a named contract finding rather than a `KeyError` traceback.

The default-path byte-identity of the *artifacts* is pinned separately, against
upstream's own output, in tests/claim_semantics/test_upstream_golden.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC = PACKAGE_ROOT / "src"
GOLDEN = PACKAGE_ROOT / "tests" / "claim_semantics" / "fixtures" / "upstream_golden"
PYTHON_APP = GOLDEN / "python_app"
RECEIPT = (PACKAGE_ROOT / "tests" / "claim_semantics" / "fixtures"
           / "replay_receipt_target_go_qualified")
FIXTURES = PACKAGE_ROOT / "tests" / "claim_semantics" / "fixtures"
MIN_RECEIPT = FIXTURES / "replay_receipt_min"
MODEL_MIN = FIXTURES / "model_min"
#: Explains every unexplained row in the golden python_app coverage artifact, so
#: the four-cell gate over it PASSES.  A test whose subject is the claims judge's
#: verdict passes this, because `--judge claims` only ADDS a verdict: a gate over
#: an artifact that fails its own judge is exit 1 whatever the receipt says, and
#: `TheGateStillGatesTheArtifactTests` below is where that is pinned.
EXEMPTIONS = FIXTURES / "python_app_exemptions.toml"
#: The model digest ``replay_receipt_min`` was hand-built around, and the digest
#: the committed ``model_min`` sources actually hash to.  ``_receipt_for_model_min``
#: rewrites the first into the second so the receipt names the model that is in
#: the tree; nothing else about the fixture changes.
MIN_RECEIPT_MODEL = "5f0d985d02df45b3790e120f9809e5d4af85edef8079b84b08f5bfdf8439e156"


def _shen_go_reason() -> str | None:
    """Why ``--model shen`` cannot run here, or None.  Uses the CLI's own probe."""
    from capcov import cli as capcov_cli

    if shutil.which("bifrost") is None:
        return "bifrost is not on PATH"
    if capcov_cli._shen_go_binary() is None:
        return "shen-go is not on PATH, $SHEN_GO or $BIFROST_SHEN_GO"
    return None


SHEN_GO_REASON = _shen_go_reason()
if SHEN_GO_REASON and os.environ.get("CAPCOV_SHEN_REQUIRED"):
    raise RuntimeError("CAPCOV_SHEN_REQUIRED is set but " + SHEN_GO_REASON)
MS = re.compile(rb'("[A-Za-z0-9_]*_ms":\s*)\d+')


def _env(**extra: str) -> dict[str, str]:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    env.update(extra)
    return env


def _capcov(*argv: str, cwd: Path | None = None, env: dict[str, str] | None = None):
    return subprocess.run([sys.executable, "-m", "capcov", *argv], text=True,
                          capture_output=True, cwd=str(cwd) if cwd else None,
                          env=env or _env())


class ClaimsIsNotImportedUnlessAskedTests(unittest.TestCase):
    """The production CLI must not pay for -- or even load -- the experiment."""

    def test_importing_capcov_cli_imports_nothing_under_capcov_claims(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-c",
             "import sys, capcov.cli; "
             "assert not any(m.startswith('capcov.claims') for m in sys.modules), "
             "sorted(m for m in sys.modules if m.startswith('capcov.claims')); "
             "print('clean')"],
            text=True, capture_output=True, env=_env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "clean")

    def test_a_default_reconcile_and_gate_import_nothing_under_capcov_claims(self) -> None:
        """Not just the import: the whole default run leaves capcov.claims unloaded."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "coverage.json"
            script = (
                "import sys\n"
                "from capcov.cli import main\n"
                f"main(['reconcile', {str(PYTHON_APP / 'capabilities.json')!r}, "
                f"{str(PYTHON_APP / 'observed.json')!r}, '--out', {str(out)!r}, '--quiet'])\n"
                f"main(['gate', {str(out)!r}, '--quiet'])\n"
                "loaded = sorted(m for m in sys.modules if m.startswith('capcov.claims'))\n"
                "print('LOADED', loaded)\n"
            )
            proc = subprocess.run([sys.executable, "-c", script], text=True,
                                  capture_output=True, env=_env())
            self.assertIn("LOADED []", proc.stdout, proc.stdout + proc.stderr)

    def test_the_claims_branch_does_import_it(self) -> None:
        """The negative control: the property above is about the default, not about a dead branch."""
        probe = Path(tempfile.mkdtemp(prefix="capcov-judge-probe-"))
        self.addCleanup(shutil.rmtree, probe, ignore_errors=True)
        script = (
            "import sys\n"
            "from capcov.cli import main\n"
            "try:\n"
            f"    main(['gate', {str(PYTHON_APP / 'coverage.json')!r}, '--judge', 'claims', "
            f"'--receipt', {str(RECEIPT)!r}, '--judge-out', {str(probe / 'out')!r}])\n"
            # an absent souffle exits here; the import under test already happened
            "except SystemExit:\n"
            "    pass\n"
            "print('LOADED', bool([m for m in sys.modules if m.startswith('capcov.claims')]))\n"
        )
        proc = subprocess.run([sys.executable, "-c", script], text=True,
                              capture_output=True, env=_env())
        self.assertIn("LOADED True", proc.stdout, proc.stdout + proc.stderr)


class ExperimentNamespaceIsLazyTests(unittest.TestCase):
    """`capcov experiment claims ...` stays reachable -- and stays invisible to production."""

    def test_the_experiment_namespace_still_runs(self) -> None:
        proc = _capcov("experiment", "claims", "--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for subcommand in ("shen", "assumptions", "modelcheck"):
            self.assertIn(subcommand, proc.stdout)

    def test_the_production_help_does_not_mention_it(self) -> None:
        """`main` routes `experiment` before argparse, so it registers no subparser."""
        proc = _capcov("--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("experiment", proc.stdout)
        self.assertNotIn("claims", proc.stdout)

    def test_every_producer_profile_is_registered(self) -> None:
        """Including the advisory one, which is registered without being imported."""
        proc = _capcov("experiment", "claims", "--help")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for subcommand in ("shen", "assumptions", "modelcheck", "static", "jev"):
            self.assertIn(subcommand, proc.stdout)
        self.assertIn("advisory", proc.stdout)

    def test_building_the_parser_imports_no_profile(self) -> None:
        """`--help` answers for every profile without loading any of them."""
        script = (
            "import sys\n"
            "from capcov.claims.cli import main\n"
            "try:\n"
            "    main(['claims', '--help'])\n"
            "except SystemExit:\n"
            "    pass\n"
            "print('LOADED', sorted(m for m in sys.modules if m.startswith('capcov.claims.shen') "
            "or m.startswith('capcov.claims.jev') or m.startswith('capcov.claims.modelcheck') "
            "or m.startswith('capcov.claims.static')))\n"
        )
        proc = subprocess.run([sys.executable, "-c", script], text=True,
                              capture_output=True, env=_env())
        self.assertIn("LOADED []", proc.stdout, proc.stdout + proc.stderr)

    def test_naming_one_profile_does_not_import_the_others(self) -> None:
        """Stage D runs; the shen workbench and the advisory profile stay unloaded."""
        script = (
            "import sys\n"
            "from capcov.claims.cli import main\n"
            f"main(['claims', 'modelcheck', '--model', {str(MODEL_MIN)!r}])\n"
            "print('LOADED', sorted(m for m in sys.modules "
            "if m.startswith('capcov.claims.shen') or m.startswith('capcov.claims.jev')))\n"
        )
        proc = subprocess.run([sys.executable, "-c", script], text=True,
                              capture_output=True, env=_env(PATH="", BIFROST_SHEN_GO=""))
        self.assertIn("LOADED []", proc.stdout, proc.stdout + proc.stderr)

    def test_the_advisory_profile_answers_by_name_when_it_is_not_here(self) -> None:
        """A valid advisory subcommand names a missing optional module, without eager imports."""
        script = (
            "import importlib\n"
            "from capcov.claims import cli\n"
            "original = importlib.import_module\n"
            "def unavailable(name, package=None):\n"
            "    if name == 'capcov.claims.jev':\n"
            "        raise ModuleNotFoundError('simulated absent Jev profile')\n"
            "    return original(name, package)\n"
            "importlib.import_module = unavailable\n"
            "try:\n"
            "    status = cli.main(['claims', 'jev', 'assess', '--request', '/unused/request.json'])\n"
            "finally:\n"
            "    importlib.import_module = original\n"
            "assert status == 3\n"
        )
        proc = subprocess.run([sys.executable, "-c", script], text=True,
                              capture_output=True, env=_env())
        self.assertEqual(proc.returncode, 0, proc.stderr)
        document = json.loads(proc.stdout)
        self.assertEqual(document.get("operational_failure"), "profile-unavailable")
        self.assertTrue(document["advisory"])
        self.assertIn("capcov.claims.jev", document["error"])


class JudgeUsageRefusalTests(unittest.TestCase):
    """Every incoherent ask is exit 2 with a named message, and judges nothing."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-judge-usage-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_claims_without_a_receipt_exits_two_on_gate(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("pass --receipt DIR", proc.stderr)
        self.assertIn("capcov gate --judge claims", proc.stderr)

    def test_claims_without_a_receipt_exits_two_on_reconcile(self) -> None:
        proc = _capcov("reconcile", str(PYTHON_APP / "capabilities.json"),
                       str(PYTHON_APP / "observed.json"),
                       "--out", str(self.tmp / "coverage.json"), "--judge", "claims")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("pass --receipt DIR", proc.stderr)
        # refused before any work: reconcile did not write its artifact either
        self.assertFalse((self.tmp / "coverage.json").exists())

    def test_an_unknown_engine_in_capcov_toml_exits_two(self) -> None:
        (self.tmp / "capcov.toml").write_text('[judge]\nengine = "hand-waving"\n')
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), cwd=self.tmp)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("unknown judge engine 'hand-waving'", proc.stderr)
        self.assertIn("four-cell, claims", proc.stderr)

    def test_an_unknown_engine_on_the_flag_exits_two(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "hand-waving")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("invalid choice", proc.stderr)

    def test_the_capcov_toml_key_selects_the_claims_judge(self) -> None:
        """The key is read, not decorative: with no --receipt it produces the claims refusal."""
        (self.tmp / "capcov.toml").write_text('[judge]\nengine = "claims"\n')
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), cwd=self.tmp)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("--judge claims", proc.stderr)
        self.assertIn("pass --receipt DIR", proc.stderr)

    def test_a_directory_that_is_not_a_receipt_exits_two(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"),
                       "--judge", "claims", "--receipt", str(self.tmp))
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("is not a replay receipt directory", proc.stderr)

    def test_a_receipt_without_the_claims_judge_is_refused_not_ignored(self) -> None:
        """A flag that silently does nothing is how a gate goes green for the wrong reason."""
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--receipt", str(RECEIPT))
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("--receipt is only meaningful with --judge claims", proc.stderr)

    def test_a_judge_out_without_the_claims_judge_is_refused(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"),
                       "--judge-out", str(self.tmp / "j"))
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("--judge-out is only meaningful with --judge claims", proc.stderr)


class DefaultJudgeIsTodaysBehaviorTests(unittest.TestCase):
    """`--judge four-cell` is the default, and naming it changes nothing."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-judge-default-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _reconcile(self, name: str, *extra: str):
        out = self.tmp / name
        proc = _capcov("reconcile", str(PYTHON_APP / "capabilities.json"),
                       str(PYTHON_APP / "observed.json"), "--out", str(out), *extra)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # only the wall-clock timings differ between two runs of the same reconcile
        return proc.stdout, MS.sub(rb"\g<1>0", out.read_bytes())

    def test_naming_the_default_engine_is_byte_identical_to_not_naming_it(self) -> None:
        bare_stdout, bare = self._reconcile("bare.json")
        named_stdout, named = self._reconcile("named.json", "--judge", "four-cell")
        self.assertEqual(bare, named)
        self.assertEqual(bare_stdout, named_stdout)
        self.assertNotIn("judge", json.loads(bare))

    def test_a_capcov_toml_with_no_judge_block_is_the_four_cell_judge(self) -> None:
        (self.tmp / "capcov.toml").write_text('[capcov]\nadapter = "python-fastapi-sqlalchemy"\n')
        out = self.tmp / "from-config.json"
        proc = _capcov("reconcile", str(PYTHON_APP / "capabilities.json"),
                       str(PYTHON_APP / "observed.json"), "--out", str(out), cwd=self.tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        _, bare = self._reconcile("bare2.json")
        self.assertEqual(MS.sub(rb"\g<1>0", out.read_bytes()), bare)

    def test_a_capcov_toml_that_does_not_parse_does_not_break_the_default_run(self) -> None:
        """reconcile/gate never read capcov.toml before --judge existed; a broken one
        must not turn a working default run into a failure."""
        (self.tmp / "capcov.toml").write_text("this is not = = toml\n")
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), cwd=self.tmp)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("capcov gate: FAIL -- 4 unexplained", proc.stdout)

    def test_a_capcov_toml_that_does_not_parse_says_so_on_stderr(self) -> None:
        """Passed over, but not in silence.

        A team that opted in with `[judge] engine = "claims"` and then broke an
        unrelated line of that same file would otherwise see the four-cell
        gate's usual output and nothing at all saying the judge they believe is
        gating never ran.  The exit code and stdout above are unchanged; this is
        the one line that says which file could not be read and what decided.
        """
        (self.tmp / "capcov.toml").write_text("this is not = = toml\n")
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), cwd=self.tmp)
        self.assertIn("capcov.toml could not be parsed", proc.stderr)
        self.assertIn("four-cell", proc.stderr)
        # a note about the config, never a verdict: stdout is the gate's alone
        self.assertNotIn("could not be parsed", proc.stdout)

    def test_the_unreadable_config_is_named_once_however_many_keys_are_read(self) -> None:
        """`engine`, `evaluator` and `model` are three lookups of one file."""
        (self.tmp / "capcov.toml").write_text("this is not = = toml\n")
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(self.tmp / "out"),
                       cwd=self.tmp, env=_env(PATH=""))
        self.assertEqual(proc.stderr.count("could not be parsed"), 1, proc.stderr)

    def test_a_readable_capcov_toml_says_nothing_about_parsing(self) -> None:
        """The two paths every default run actually takes stay silent."""
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), cwd=self.tmp)
        self.assertNotIn("could not be parsed", proc.stderr)
        (self.tmp / "capcov.toml").write_text('[capcov]\nadapter = "python"\n')
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), cwd=self.tmp)
        self.assertNotIn("could not be parsed", proc.stderr)

    def test_an_explicit_flag_is_never_lost_to_an_unreadable_capcov_toml(self) -> None:
        (self.tmp / "capcov.toml").write_text("this is not = = toml\n")
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       cwd=self.tmp)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("pass --receipt DIR", proc.stderr)

    def test_the_default_gate_is_the_four_cell_gate(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"))
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("capcov gate: FAIL -- 4 unexplained", proc.stdout)


@unittest.skipIf(shutil.which("souffle") is not None,
                 "this pins the message when souffle is ABSENT; it is on PATH here")
class AbsentToolIsNamedTests(unittest.TestCase):
    """The `--resolver scip` convention: name the tool, name the fix, judge nothing.

    Only for an evaluator that was *asked for*.  The default judge is the stdlib
    Python kernel, which is why `DefaultEvaluatorNeedsNoToolTests` below judges
    the same receipt in this very environment and gets an answer.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-judge-absent-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _refusal(self, *extra: str, out: Path | None = None):
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(out or self.tmp / "judge"),
                       *extra)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("capcov gate --judge claims:", proc.stderr)
        self.assertIn("Install it with:", proc.stderr)
        self.assertIn("or use --evaluator python", proc.stderr)
        return proc

    def test_gate_names_souffle_and_writes_no_judge_artifacts(self) -> None:
        out = self.tmp / "judge"
        proc = self._refusal("--evaluator", "souffle", out=out)
        self.assertIn("--evaluator souffle needs the Souffle 2.5 executable", proc.stderr)
        self.assertIn("not on PATH or $SOUFFLE", proc.stderr)
        self.assertFalse(out.exists(), "a refused judge must leave no artifacts behind")

    def test_the_compiled_evaluator_names_the_same_binary(self) -> None:
        proc = self._refusal("--evaluator", "souffle-compiled")
        self.assertIn("--evaluator souffle-compiled needs the Souffle 2.5 executable",
                      proc.stderr)

    def test_a_comma_list_is_refused_on_the_first_evaluator_that_is_absent(self) -> None:
        proc = self._refusal("--evaluator", "python,souffle-compiled")
        self.assertIn("--evaluator souffle-compiled needs", proc.stderr)

    def test_the_capcov_toml_evaluator_key_is_refused_the_same_way(self) -> None:
        (self.tmp / "capcov.toml").write_text('[judge]\nevaluator = "souffle"\n')
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(self.tmp / "judge"),
                       cwd=self.tmp)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--evaluator souffle needs", proc.stderr)

    def test_all_is_never_refused_for_an_absent_tool(self) -> None:
        """`all` means every evaluator that is here, so here it means python alone."""
        out = self.tmp / "all"
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(out),
                       "--evaluator", "all")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["kernels"], ["python"])

    def test_reconcile_still_wrote_its_own_artifact_before_the_judge_refused(self) -> None:
        """reconcile is the producer of coverage.json under either judge."""
        coverage = self.tmp / "coverage.json"
        proc = _capcov("reconcile", str(PYTHON_APP / "capabilities.json"),
                       str(PYTHON_APP / "observed.json"), "--out", str(coverage),
                       "--judge", "claims", "--receipt", str(RECEIPT),
                       "--evaluator", "souffle", "--judge-out", str(self.tmp / "judge"))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--evaluator souffle needs", proc.stderr)
        # the refusal is a command-line refusal, raised before reconcile does its
        # own work: nothing is written, not even the artifact reconcile produces
        self.assertFalse(coverage.exists())


class EvaluatorUsageRefusalTests(unittest.TestCase):
    """Naming a kernel that does not exist, or naming one where it says nothing."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-evaluator-usage-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_an_unknown_evaluator_exits_two_and_lists_the_choices(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--evaluator", "datalog-by-hand")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("unknown evaluator 'datalog-by-hand'", proc.stderr)
        self.assertIn("python, souffle, souffle-compiled", proc.stderr)
        self.assertIn("(--evaluator)", proc.stderr)

    def test_all_cannot_be_combined_with_a_name(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--evaluator", "all,python")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("already means every available evaluator", proc.stderr)

    def test_an_evaluator_without_the_claims_judge_is_refused_not_ignored(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--evaluator", "python")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--evaluator is only meaningful with --judge claims", proc.stderr)

    def test_an_unknown_evaluator_in_capcov_toml_names_the_key(self) -> None:
        (self.tmp / "capcov.toml").write_text('[judge]\nevaluator = "prolog"\n')
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), cwd=self.tmp)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("unknown evaluator 'prolog'", proc.stderr)
        self.assertIn("[judge] evaluator in capcov.toml", proc.stderr)


class DefaultEvaluatorNeedsNoToolTests(unittest.TestCase):
    """The claims judge with no `--evaluator` judges with the standard library alone.

    This runs wherever the suite runs -- souffle present or not -- because that
    is the property: the default path of an opt-in feature must not need the
    opt-in tool.  What it must NOT do is pretend a differential happened.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-evaluator-default-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _judge(self, *extra: str, out: str = "judge"):
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(self.tmp / out), *extra,
                       env=_env(PATH=""))
        return proc, json.loads((self.tmp / out / "judge.json").read_text())

    def test_the_default_judge_runs_the_python_kernel_with_no_tool_on_path(self) -> None:
        """PATH is emptied: nothing but the interpreter already running is available."""
        proc, document = self._judge()
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(document["kernels"], ["python"])
        self.assertEqual(document["verdict"], "pending-premise")
        self.assertEqual(document["exit_code"], 5)

    def test_a_single_evaluator_is_never_recorded_as_a_passed_differential(self) -> None:
        _, document = self._judge(out="single")
        self.assertEqual(document["differential"], "not-run (single evaluator)")
        self.assertIsNone(document["compiled"])
        self.assertEqual(sorted(document["differential_report"]),
                         ["closure_digest_equal", "compiled_seconds", "failures",
                          "interpreter_seconds", "matched", "python_digest", "python_seconds"])
        # no digest is claimed for a kernel that did not run
        self.assertNotIn("souffle_digest", document["differential_report"])

    def test_the_capcov_toml_key_selects_the_evaluator(self) -> None:
        (self.tmp / "capcov.toml").write_text('[judge]\nevaluator = "python"\n')
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(self.tmp / "keyed"),
                       cwd=self.tmp)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        document = json.loads((self.tmp / "keyed" / "judge.json").read_text())
        self.assertEqual(document["kernels"], ["python"])

    def test_the_stdout_line_names_the_kernels_and_the_differential(self) -> None:
        proc, _ = self._judge(out="stdout")
        self.assertIn("kernels python", proc.stdout)
        self.assertIn("differential not-run (single evaluator)", proc.stdout)

    def test_quiet_silences_everything_the_judge_adds_to_stdout(self) -> None:
        """`--quiet` governs the opt-in judge exactly as it governs the rest.

        `gate` prints its own four-cell verdict whether or not `--quiet` was
        passed -- that is upstream's behaviour and not ours to move -- so what
        `--quiet` must do here is leave the command's stdout exactly what it is
        without `--judge claims` at all: the per-op summary and the closing
        verdict line are the judge's, and a quiet run prints neither.  Nothing
        is lost by the silence: judge.json still carries the verdict, the
        kernels and the judge's own exit code, and the process exit code is the
        one the loud run returned.
        """
        loud, _ = self._judge(out="loud")
        quiet, document = self._judge("--quiet", out="quiet")
        plain = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--quiet",
                        env=_env(PATH=""))
        self.assertIn("--judge claims:", loud.stdout)
        self.assertNotIn("--judge claims:", quiet.stdout)
        self.assertEqual(quiet.stdout, plain.stdout)
        self.assertEqual(quiet.returncode, loud.returncode)
        self.assertEqual(document["verdict"], "pending-premise")
        self.assertEqual(document["kernels"], ["python"])


def _copy_receipt(destination: Path, *, strip_models: bool = False,
                  model: str | None = None, checker: tuple[str, str] | None = None) -> Path:
    """A working copy of ``replay_receipt_min``, optionally rewritten.

    ``strip_models`` removes every ``model_*.json`` file -- the receipt keeps its
    header, which is where ``model_describes_run`` comes from, and loses every
    model observation.  ``model`` rewrites the model digest everywhere it
    appears, so a receipt can name the ``model_min`` sources that are actually
    in the tree.  ``checker`` rewrites the reviewer's admitted checker row.
    """
    shutil.copytree(MIN_RECEIPT, destination)
    if strip_models:
        for path in destination.glob("model_*.json"):
            path.unlink()
    else:
        (destination / "model_well_formed.json").unlink()
    if model is not None:
        for path in destination.rglob("*.json"):
            text = path.read_text(encoding="utf-8")
            if MIN_RECEIPT_MODEL in text:
                path.write_text(text.replace(MIN_RECEIPT_MODEL, model), encoding="utf-8")
    if checker is not None:
        path = destination / "model_checkers.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["rows"] = [{"checker": checker[0], "checker_version": checker[1]}]
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return destination


class ModelProfileUsageRefusalTests(unittest.TestCase):
    """`--model` is a producer profile, and naming it badly is exit 2, not a verdict."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-model-usage-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _refusal(self, *extra: str, judge: bool = True):
        argv = ["gate", str(PYTHON_APP / "coverage.json")]
        if judge:
            argv += ["--judge", "claims", "--receipt", str(RECEIPT),
                     "--judge-out", str(self.tmp / "judge")]
        proc = _capcov(*argv, *extra)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertFalse((self.tmp / "judge").exists(),
                         "a refused judge must leave no artifacts behind")
        return proc

    def test_a_model_without_the_claims_judge_is_refused_not_ignored(self) -> None:
        proc = self._refusal("--model", f"shen:{MODEL_MIN}", judge=False)
        self.assertIn("--model is only meaningful with --judge claims", proc.stderr)

    def test_a_model_that_does_not_name_a_profile_is_refused(self) -> None:
        proc = self._refusal("--model", str(MODEL_MIN))
        self.assertIn("names a producer profile and a directory, PROFILE:DIR", proc.stderr)

    def test_an_unknown_profile_names_the_profiles_that_exist(self) -> None:
        proc = self._refusal("--model", f"souffle:{MODEL_MIN}")
        self.assertIn("unknown model profile 'souffle'", proc.stderr)
        self.assertIn("expected one of shen", proc.stderr)

    def test_a_directory_that_is_not_there_is_refused_before_any_work(self) -> None:
        proc = self._refusal("--model", f"shen:{self.tmp / 'nowhere'}")
        self.assertIn("is not a model directory", proc.stderr)

    def test_the_capcov_toml_key_is_refused_the_same_way(self) -> None:
        (self.tmp / "capcov.toml").write_text('[judge]\nmodel = "shen"\n')
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(self.tmp / "judge"),
                       cwd=self.tmp)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("[judge] model in capcov.toml", proc.stderr)


class ModelProfileAbsentToolIsNamedTests(unittest.TestCase):
    """PATH emptied: asking for Stage D without shen-go is named, and judges nothing."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-model-absent-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_gate_names_shen_go_and_writes_no_judge_artifacts(self) -> None:
        out = self.tmp / "judge"
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(RECEIPT), "--judge-out", str(out),
                       "--model", f"shen:{MODEL_MIN}",
                       env=_env(PATH="", SHEN_GO="", BIFROST_SHEN_GO=""))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--model shen needs shen-go", proc.stderr)
        self.assertIn("bifrost launcher is not on PATH", proc.stderr)
        self.assertIn("not on PATH, $SHEN_GO or $BIFROST_SHEN_GO", proc.stderr)
        self.assertIn("Install it with:", proc.stderr)
        self.assertIn("or drop --model", proc.stderr)
        self.assertFalse(out.exists(), "a refused judge must leave no artifacts behind")

    def test_reconcile_refuses_before_it_writes_its_own_artifact(self) -> None:
        coverage = self.tmp / "coverage.json"
        proc = _capcov("reconcile", str(PYTHON_APP / "capabilities.json"),
                       str(PYTHON_APP / "observed.json"), "--out", str(coverage),
                       "--judge", "claims", "--receipt", str(RECEIPT),
                       "--model", f"shen:{MODEL_MIN}", "--judge-out", str(self.tmp / "judge"),
                       env=_env(PATH="", SHEN_GO="", BIFROST_SHEN_GO=""))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("--model shen needs shen-go", proc.stderr)
        self.assertFalse(coverage.exists())


class ModelProfilePreflightBoundaryTests(unittest.TestCase):
    """The explicit producer flag runs preflight before judging; no runtime is built here."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-model-boundary-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_model_flag_preflights_ill_formed_and_unavailable_results(self) -> None:
        from capcov import cli as capcov_cli
        from capcov.claims import modelcheck
        from capcov.claims.replay import judge as claims_judge

        cases = (
            ({"status": "ill-formed", "model": "a" * 64, "fact": None,
              "certificate_sha256": "b" * 64,
              "failures": [{"id": "registry-ids", "message": "type mismatch"}],
              "error": None}, 0, True),
            ({"status": "unavailable", "model": None, "fact": None,
              "certificate_sha256": None, "failures": [], "error": "mock runtime unavailable"},
             1, False),
        )
        for report, expected_status, should_judge in cases:
            with self.subTest(status=report["status"]):
                receipt = _copy_receipt(self.tmp / report["status"], strip_models=True)
                out = self.tmp / f"{report['status']}-judge"
                judge_document = {"verdict": "supported", "exit_code": 0,
                                  "ops": {}, "kernels": ["python"],
                                  "differential": "not-run (single evaluator)",
                                  "compiled": None, "differential_report": None,
                                  "contract_findings": []}
                with patch("capcov.cli._require_shen_go", return_value="/mock/shen"), \
                        patch.object(modelcheck, "preflight", return_value=report) as preflight, \
                        patch.object(claims_judge, "judge_receipt",
                                     return_value=(judge_document, [])) as judge:
                    status = capcov_cli.main([
                        "gate", str(PYTHON_APP / "coverage.json"),
                        "--exemptions", str(EXEMPTIONS), "--judge", "claims",
                        "--receipt", str(receipt), "--judge-out", str(out),
                        "--model", f"shen:{MODEL_MIN}", "--quiet"])
                self.assertEqual(status, expected_status)
                preflight.assert_called_once_with(MODEL_MIN, out_dir=receipt)
                self.assertEqual(judge.called, should_judge)
                self.assertFalse((receipt / "model_well_formed.json").exists())
                if should_judge:
                    self.assertTrue((out / "judge.json").is_file())
                else:
                    self.assertFalse(out.exists())


class NoModelProfileJudgesWhatTheReceiptCarriesTests(unittest.TestCase):
    """Without the flag: nothing is imported, nothing is run, and nothing is refused."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-model-default-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_the_claims_judge_imports_no_model_checker_unless_asked(self) -> None:
        """The judge runs in full; capcov.claims.modelcheck and .shen stay unloaded."""
        script = (
            "import sys\n"
            "from capcov.cli import main\n"
            "try:\n"
            f"    main(['gate', {str(PYTHON_APP / 'coverage.json')!r}, '--judge', 'claims', "
            f"'--receipt', {str(MIN_RECEIPT)!r}, '--judge-out', {str(self.tmp / 'out')!r}, "
            "'--quiet'])\n"
            "except SystemExit:\n"
            "    pass\n"
            "print('MODEL', sorted(m for m in sys.modules if m.startswith('capcov.claims.shen') "
            "or m.startswith('capcov.claims.modelcheck')))\n"
        )
        proc = subprocess.run([sys.executable, "-c", script], text=True,
                              capture_output=True, env=_env())
        self.assertIn("MODEL []", proc.stdout, proc.stdout + proc.stderr)
        self.assertTrue((self.tmp / "out" / "judge.json").is_file(),
                        "the judge still judged")

    def test_a_receipt_with_no_model_files_is_judged_unresolved_not_refused(self) -> None:
        """Every model_* file removed: an answer, not an error.

        Each op comes out semantically ``unresolved`` with its model premises
        named -- ``model_writes`` (no declared write set was observed) and
        ``model_well_formed`` (no typed certificate) -- and operationally
        ``complete``, because nothing failed: the evidence simply is not there.
        ``model_describes_run`` is NOT among them, and that is not an oversight:
        the receipt header still names a model, which is where that row comes
        from.  The verdict is not-supported (exit 1), never a traceback.
        """
        receipt = _copy_receipt(self.tmp / "stripped", strip_models=True)
        out = self.tmp / "stripped-judge"
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(receipt), "--judge-out", str(out))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["verdict"], "not-supported")
        self.assertEqual(document["contract_findings"], [])
        self.assertTrue(document["ops"], "the receipt was still judged op by op")
        for op, entry in document["ops"].items():
            with self.subTest(op=op):
                self.assertEqual(entry["op_qualified"]["semantic"], "unresolved")
                self.assertEqual(entry["op_qualified"]["operational"], "complete")
                self.assertIn("model_well_formed", entry["op_qualified"]["missing_premises"])
                self.assertIn("model_writes", entry["op_qualified"]["missing_premises"])

    def test_the_same_receipt_with_its_certificate_is_supported(self) -> None:
        """The control: only the model premises were missing above.

        Gated with --exemptions so the coverage artifact passes its own judge and
        the exit code is the claims judge's answer alone.
        """
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--exemptions", str(EXEMPTIONS),
                       "--receipt", str(MIN_RECEIPT), "--judge-out", str(self.tmp / "intact"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


@unittest.skipIf(SHEN_GO_REASON, f"needs shen-go through bifrost ({SHEN_GO_REASON})")
class ModelProfilePreflightTests(unittest.TestCase):
    """The present path: Stage D runs, writes into the receipt, and the judge reads it.

    The receipt is ``replay_receipt_min`` rewritten to name the ``model_min``
    sources that are committed in this tree (its hand-built digest names no
    model anyone can check) and stripped of the hand-written
    ``model_well_formed.json``.  Without the flag that receipt is *pending* the
    Stage D premise; with it the premise is a real certificate produced here.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-model-preflight-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        sys.path.insert(0, str(SRC))
        self.addCleanup(sys.path.remove, str(SRC))
        from capcov.claims import modelcheck

        self.digest = modelcheck.model_digest(MODEL_MIN)

    def _gate(self, receipt: Path, out: str, *extra: str):
        # --exemptions makes the four-cell gate over the golden artifact pass, so
        # the exit code here is the JUDGE's verdict and nothing else
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--exemptions", str(EXEMPTIONS),
                       "--receipt", str(receipt), "--judge-out", str(self.tmp / out), *extra)
        return proc, json.loads((self.tmp / out / "judge.json").read_text())

    def test_without_the_flag_the_receipt_is_pending_the_stage_d_premise(self) -> None:
        receipt = _copy_receipt(self.tmp / "pending", model=self.digest)
        proc, document = self._gate(receipt, "pending-out")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(document["verdict"], "pending-premise")
        self.assertEqual(document["exit_code"], 5)
        self.assertFalse((receipt / "model_well_formed.json").exists())

    def test_the_profile_writes_the_certificate_into_the_receipt_before_judging(self) -> None:
        receipt = _copy_receipt(self.tmp / "checked", model=self.digest)
        proc, document = self._gate(receipt, "checked-out", "--model", f"shen:{MODEL_MIN}")
        self.assertIn(f"model {self.digest[:12]} is well-formed", proc.stdout)
        certificate = json.loads((receipt / "modelcheck-certificate.json").read_text())
        self.assertEqual(certificate["verdict"], "well-formed")
        self.assertEqual(certificate["model"], self.digest)
        fact = json.loads((receipt / "model_well_formed.json").read_text())
        [row] = fact["rows"]
        self.assertEqual(row["model"], self.digest)
        self.assertEqual(row["checker"], "capcov-modelcheck")
        self.assertEqual(row["certificate"], certificate["certificate_sha256"])
        self.assertTrue((receipt / "modelcheck-transcript.txt").is_file())
        # the premise the judge was pending is now met; what it is still pending
        # is the reviewer's admission of THIS checker, which no producer may grant
        # itself -- the fixture admits a different one
        self.assertEqual(document["verdict"], "pending-premise")
        for entry in document["ops"].values():
            self.assertNotIn("model_well_formed", entry["op_qualified"]["missing_premises"])
            self.assertEqual(entry["qualification"], "pending model_checker_admitted")

    def test_with_the_checker_admitted_the_same_run_is_supported(self) -> None:
        """End to end: the reviewer admits capcov-modelcheck, Stage D runs, verdict supported."""
        receipt = _copy_receipt(self.tmp / "admitted", model=self.digest,
                                checker=("capcov-modelcheck", "1.0.0"))
        proc, document = self._gate(receipt, "admitted-out", "--model", f"shen:{MODEL_MIN}")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(document["verdict"], "supported")

    def test_a_model_the_receipt_does_not_name_is_a_contract_finding(self) -> None:
        """Fail-closed: a certificate for another model never becomes this run's premise."""
        receipt = _copy_receipt(self.tmp / "foreign")
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(receipt), "--judge-out", str(self.tmp / "foreign-out"),
                       "--model", f"shen:{MODEL_MIN}")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("contract finding", proc.stderr)
        self.assertIn("the certificate is for another model", proc.stderr)


class TheGateStillGatesTheArtifactTests(unittest.TestCase):
    """`--judge claims` ADDS a verdict; the coverage artifact keeps its own.

    The positional argument is not decorative.  A receipt names a run of the
    system under test and a coverage artifact names a source tree; nothing in
    either binds them, so a supported receipt must never turn a failing artifact
    green.  `gate` runs the four-cell gate under either judge and passes only
    when both pass, and judge.json records the artifact it was handed -- by
    digest, never by path -- so the receipt's verdict cannot be read as a verdict
    about that tree.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-judge-binding-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_a_supported_receipt_does_not_rescue_a_failing_coverage_artifact(self) -> None:
        out = self.tmp / "unrescued"
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(MIN_RECEIPT), "--judge-out", str(out))
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        # the artifact's own judge ran and said no, in the words it always used
        self.assertIn("capcov gate: FAIL -- 4 unexplained", proc.stdout)
        self.assertIn("does not replace the artifact's", proc.stderr)
        document = json.loads((out / "judge.json").read_text())
        # ... and the claims judge said yes, which is recorded and not obeyed
        self.assertEqual(document["verdict"], "supported")
        self.assertEqual(document["exit_code"], 0)
        self.assertEqual(document["gated_artifact"]["four_cell"], "fail")
        self.assertEqual(document["gated_artifact"]["four_cell_unexplained"], 4)

    def test_both_verdicts_pass_and_the_gate_passes(self) -> None:
        """The control: the same receipt over an artifact that passes its own judge."""
        out = self.tmp / "both"
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--exemptions", str(EXEMPTIONS),
                       "--receipt", str(MIN_RECEIPT), "--judge-out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("capcov gate: PASS", proc.stdout)
        document = json.loads((out / "judge.json").read_text())
        self.assertEqual(document["verdict"], "supported")
        self.assertEqual(document["gated_artifact"]["four_cell"], "pass")
        self.assertEqual(document["gated_artifact"]["four_cell_unexplained"], 0)

    def test_judge_json_names_the_artifact_by_digest_and_no_path(self) -> None:
        out = self.tmp / "named"
        _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                "--receipt", str(MIN_RECEIPT), "--judge-out", str(out))
        document = json.loads((out / "judge.json").read_text())
        gated = document["gated_artifact"]
        self.assertEqual(gated["kind"], "coverage")
        self.assertEqual(gated["sha256"], hashlib.sha256(
            (PYTHON_APP / "coverage.json").read_bytes()).hexdigest())
        coverage = json.loads((PYTHON_APP / "coverage.json").read_text())
        self.assertEqual(gated["source_snapshot"],
                         coverage["derived_from"]["source_snapshot"])
        self.assertEqual(gated["summary"], coverage["summary"])
        # the public-repo rule the other judge artifacts follow
        self.assertNotIn(str(PACKAGE_ROOT), (out / "judge.json").read_text())

    def test_reconcile_records_the_artifact_it_just_wrote(self) -> None:
        """reconcile produces the artifact, so the judge names the bytes it produced."""
        coverage = self.tmp / "coverage.json"
        out = self.tmp / "reconciled"
        proc = _capcov("reconcile", str(PYTHON_APP / "capabilities.json"),
                       str(PYTHON_APP / "observed.json"), "--out", str(coverage),
                       "--judge", "claims", "--receipt", str(MIN_RECEIPT),
                       "--judge-out", str(out))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        gated = json.loads((out / "judge.json").read_text())["gated_artifact"]
        self.assertEqual(gated["four_cell"], "reconciled")
        self.assertEqual(gated["sha256"],
                         hashlib.sha256(coverage.read_bytes()).hexdigest())


class JudgeOutIsNeverInsideTheEvidenceTests(unittest.TestCase):
    """The judge writes a receipt.json of its own, so it may not write into a receipt.

    Two ways that bites, both refused before any judging: `--judge-out` pointed at
    (or inside) `--receipt` would overwrite the evidence with the judge's summary,
    and a previous `--judge-out` passed as `--receipt` would be read as evidence.
    The second is a contract finding about the evidence -- never a traceback.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-judge-out-"))
        self.receipt = _copy_receipt(self.tmp / "receipt")
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _digest(self) -> str:
        return hashlib.sha256((self.receipt / "receipt.json").read_bytes()).hexdigest()

    def test_judge_out_equal_to_the_receipt_is_refused_and_touches_nothing(self) -> None:
        before = self._digest()
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(self.receipt), "--judge-out", str(self.receipt))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("would overwrite the evidence it judged", proc.stderr)
        self.assertEqual(self._digest(), before, "the evidence was rewritten")

    def test_judge_out_inside_the_receipt_is_refused(self) -> None:
        proc = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                       "--receipt", str(self.receipt),
                       "--judge-out", str(self.receipt / "judge"))
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("inside it", proc.stderr)
        self.assertFalse((self.receipt / "judge").exists())

    def test_a_previous_judge_out_is_not_a_receipt_it_is_a_contract_finding(self) -> None:
        out = self.tmp / "first"
        first = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                        "--receipt", str(self.receipt), "--judge-out", str(out))
        self.assertEqual(first.returncode, 1, first.stdout + first.stderr)
        self.assertTrue((out / "receipt.json").is_file(),
                        "the judge writes a receipt.json of its own -- that is the trap")
        second = _capcov("gate", str(PYTHON_APP / "coverage.json"), "--judge", "claims",
                         "--receipt", str(out), "--judge-out", str(self.tmp / "second"))
        self.assertEqual(second.returncode, 1, second.stdout + second.stderr)
        self.assertIn("contract finding", second.stderr)
        self.assertIn("is not a replay receipt directory", second.stderr)
        self.assertNotIn("Traceback", second.stderr)


class _StubReport:
    """The one shape `judge_document` reads off a kernel report."""

    def __init__(self, backend: str, digest: str) -> None:
        self.backend, self.canonical_digest = backend, digest
        self.operational_failure = None
        self.claims: list = []


class _StubDisagreement:
    """Two kernels that ran and did not agree -- what `evaluate_join` returns as `mismatch`."""

    evaluators = ("python", "souffle")
    differential = "ran"
    closure_digest_equal = False
    timings = {"python": 0.0, "souffle": 0.0}
    reports = (_StubReport("python", "a" * 64), _StubReport("souffle", "b" * 64))


def _stub_kernel_failure(failure: str):
    """The same shape, but the second kernel never ran: it failed by name."""
    broken = _StubReport("souffle", "")
    broken.operational_failure = failure

    class _Failed(_StubDisagreement):
        reports = (_StubReport("python", "a" * 64), broken)

    return _Failed


class KernelDisagreementIsExitTwoTests(unittest.TestCase):
    """Kernels that disagree are exit 2 and no verdict -- and the gate fails.

    Nothing else in the suite reaches that branch (the kernels agree on every
    committed fixture, which is the point of them), so without this a deleted
    mismatch branch would fall through to "no op was replayed" -- exit 1, a
    claim about the receipt -- and every test would still pass.  The
    disagreement is injected rather than provoked: no souffle here.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="capcov-kernel-mismatch-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        sys.path.insert(0, str(SRC))
        self.addCleanup(sys.path.remove, str(SRC))
        from capcov.claims.replay import judge as claims_judge

        self.judge = claims_judge
        original = claims_judge.replay_join.evaluate_join

        def disagree(join, *args, **kwargs):
            join.result, join.mismatch = None, _StubDisagreement()
            join.evaluators, join.differential = _StubDisagreement.evaluators, "ran"
            return join

        claims_judge.replay_join.evaluate_join = disagree
        self.addCleanup(setattr, claims_judge.replay_join, "evaluate_join", original)

    def _patch(self, outcome) -> None:
        """Re-point the injection at another disagreement shape."""
        def disagree(join, *args, **kwargs):
            join.result, join.mismatch = None, outcome()
            join.evaluators, join.differential = outcome.evaluators, "ran"
            return join

        self.judge.replay_join.evaluate_join = disagree

    def test_the_judge_reports_kernel_mismatch_exit_two_and_judges_no_op(self) -> None:
        out = self.tmp / "mismatch"
        document, diagnostics = self.judge.judge_receipt(MIN_RECEIPT, out, [])
        self.assertEqual(document["verdict"], self.judge.VERDICT_KERNEL_MISMATCH)
        self.assertEqual(document["exit_code"], self.judge.EXIT_KERNEL)
        self.assertEqual(document["ops"], {}, "a disagreement is never a per-op verdict")
        self.assertFalse(document["differential_report"]["matched"])
        self.assertTrue(any("kernels disagree" in line for line in diagnostics), diagnostics)
        self.assertEqual(json.loads((out / "judge.json").read_text())["exit_code"],
                         self.judge.EXIT_KERNEL)

    def test_a_souffle_that_will_not_start_is_unavailable_not_a_disagreement(self) -> None:
        """Exit 4's question, not exit 2's: nothing disagreed, a kernel never ran.

        `require_evaluators` refuses an ABSENT souffle before any work; what
        reaches the differential is a souffle that is here and will not run, and
        reporting that as "the kernels disagree" claims a differential that never
        happened (with a digest for a closure nothing produced).
        """
        self._patch(_stub_kernel_failure("souffle-unavailable"))
        out = self.tmp / "unavailable"
        # the ask stays the default python kernel -- the injected outcome is what
        # carries the failed souffle, so this needs no interpreter to be here
        document, diagnostics = self.judge.judge_receipt(MIN_RECEIPT, out, [])
        self.assertEqual(document["verdict"], self.judge.VERDICT_UNAVAILABLE)
        self.assertEqual(document["exit_code"], self.judge.EXIT_UNAVAILABLE)
        self.assertIn("could not be started", document["message"])
        self.assertTrue(any("no differential ran" in line for line in diagnostics), diagnostics)

    def test_a_kernel_that_failed_some_other_way_is_still_a_kernel_failure(self) -> None:
        """Only "could not be started" is the toolchain's; the rest stay exit 2."""
        self._patch(_stub_kernel_failure("souffle-execution-failed"))
        document, _ = self.judge.judge_receipt(MIN_RECEIPT, self.tmp / "failed", [])
        self.assertEqual(document["verdict"], self.judge.VERDICT_KERNEL_MISMATCH)
        self.assertEqual(document["exit_code"], self.judge.EXIT_KERNEL)

    def test_the_cli_fails_the_gate_and_never_passes_it(self) -> None:
        """Even over an artifact whose own gate passes: the judge reached no verdict."""
        import contextlib
        import io

        from capcov.cli import main

        out = self.tmp / "cli"
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            rc = main(["gate", str(PYTHON_APP / "coverage.json"), "--exemptions",
                       str(EXEMPTIONS), "--judge", "claims", "--receipt", str(MIN_RECEIPT),
                       "--judge-out", str(out), "--quiet"])
        self.assertEqual(rc, 1, buffer.getvalue())
        self.assertEqual(json.loads((out / "judge.json").read_text())["verdict"],
                         self.judge.VERDICT_KERNEL_MISMATCH)


if __name__ == "__main__":
    unittest.main()
