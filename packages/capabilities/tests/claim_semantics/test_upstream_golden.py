"""With no flag and no optional tool, this branch reproduces upstream main byte for byte.

`fixtures/upstream_golden/` was produced by upstream main (commit 649be7f) from
a separate read-only checkout, with the optional toolchain hidden from PATH and
no extras installed -- see its README.md.  This test replays the same
`generate.py` against THIS tree, through the same `normalize.py`, and requires
the result to be identical.  It is the assertion the whole optional-profiles
direction rests on: every addition is reachable only through an explicit flag or
a capcov.toml key, so the default path is not ours to move.

What is compared: `discover` on the go fixture (which needs an extra it does not
have, and says so), the full `discover -> observe -> reconcile -> gate -> report`
pipeline on the python fixture, `discover` on an OpenAPI document, `flows
coverage`/`gate`, `features validate`, and every `--help`.  Artifacts, stdout,
and exit codes, all byte-identical after the golden's own `<root>`/timestamp
normalization.

Two documented exceptions, each with its own test rather than a silent skip:

* **The last line of a failing run, not its traceback.**  `normalize.py` writes
  a `.error_line` beside every non-empty `.stderr` precisely because the frames
  above it carry `cli.py` line numbers that move with any edit.  The `.stderr`
  files that have an `.error_line` are compared through it; the rest are
  compared whole.
The class states its two preconditions rather than assuming them: the golden was
recorded on host CPython 3.13 with no extras installed, and on any other
interpreter it skips with a message naming what it found and where to re-run it
(the devShell's python312 wraps argparse's subcommand list differently, which
would read as "our branch moved upstream's default path" when it is nothing of
the kind).  Two tests outside the class keep those constants tied to the
fixture's own README, so a skip can never quietly become permanent.

* **`reconcile --help` and `gate --help` list the new opt-in flags.**  A flag
  that exists appears in its command's help -- upstream's own
  `discover --help` lists `--resolver` for exactly this reason.
  `test_reconcile_and_gate_help_gains_only_the_judge_flags` pins the delta to
  exactly `--judge`, `--receipt`, `--judge-out`, `--evaluator`, `--model`: no
  upstream option lost, no sixth option gained.
"""
from __future__ import annotations

import hashlib
import json
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).resolve().parent / "fixtures" / "upstream_golden"
GENERATE = GOLDEN / "generate.py"
NORMALIZE = GOLDEN / "normalize.py"
#: The fixture's own metadata, by path from the golden root: what records
#: the run rather than being part of it.  Not basenames -- see
#: `_relative_golden_files`.
META = {"README.md", "MANIFEST.json", "generate.py", "normalize.py"}
# the two commands that gained the opt-in --judge flags; pinned by their own test
HELP_WITH_JUDGE = {"cli/help_reconcile.stdout", "cli/help_gate.stdout"}
#: Every option the two commands gained, and the whole of it: the judge itself,
#: what it judges, where it writes, which kernels run and which producer profile
#: runs before it.  Growing this set is a deliberate act -- an opt-in flag lands
#: with its entry here or the golden comparison fails.
JUDGE_FLAGS = {"--judge", "--receipt", "--judge-out", "--evaluator", "--model"}


#: The golden was recorded with **no extras installed** (README: "installed
#: extras: none"), and the recorded runs depend on that: go_app/discover exits 1
#: precisely because the treesitter extra is absent, and the python_app probe
#: output is pytest's absence.  PATH can be hidden from a subprocess; an
#: importable package cannot, so an interpreter that has one of these is not the
#: interpreter this fixture describes, and the comparison would fail as an opaque
#: byte-diff rather than as the precondition it is.
GOLDEN_EXTRAS = ("tree_sitter", "pytest", "yaml")


def _installed_extras() -> list[str]:
    return [name for name in GOLDEN_EXTRAS if importlib.util.find_spec(name) is not None]


INSTALLED_EXTRAS = _installed_extras()

#: The interpreter that recorded the golden, from its README's own table:
#: CPython 3.13.  argparse's help formatter wraps a subcommand list differently
#: between feature releases, so `cli/help.stdout` and every other recorded
#: `--help` is a 3.13 artifact, not a capcov artifact.  Run the class on the
#: pinned devShell's python312 and it fails on that wrapping alone -- an opaque
#: byte diff that says "our branch moved upstream's default path" about a
#: difference upstream's own code would produce too.  Skipped by name instead,
#: exactly like the extras precondition above: this is a statement about which
#: interpreter the fixture describes, never a verdict about the branch.
GOLDEN_PYTHON = (3, 13)
INSTALLED_WHEEL_ENV = "CAPCOV_TEST_INSTALLED_WHEEL"


def _wrong_interpreter() -> str:
    if sys.version_info[:2] == GOLDEN_PYTHON:
        return ""
    recorded = ".".join(str(part) for part in GOLDEN_PYTHON)
    running = ".".join(str(part) for part in sys.version_info[:2])
    return (f"the golden records CPython {recorded}'s argparse help output; this is "
            f"CPython {running} -- re-run it on host python3 ({recorded}.x)")


GOLDEN_PRECONDITION = _wrong_interpreter() or (
    ("the golden records a run with NO extras installed; this interpreter can import "
     + ", ".join(INSTALLED_EXTRAS)
     + " -- re-run it on a bare interpreter (the pinned devShell's python, or host "
       "python3)") if INSTALLED_EXTRAS else "")


def _hidden_path() -> str:
    """The golden's PATH: this interpreter's bindir first, then the system dirs.

    No indexer, no souffle, no go, no node -- whatever is installed on the host,
    the run under test cannot see it.  The interpreter's own bindir goes first so
    `python3` is not the macOS system 3.9.
    """
    return os.pathsep.join([str(Path(sys.executable).parent), "/usr/bin", "/bin",
                            "/usr/sbin", "/sbin"])


def _options(help_text: str) -> set[str]:
    """Every long option argparse printed, regardless of how it wrapped the column.

    Help *prose* names options too ("...writes it into --receipt. Needs..."), so
    the sentence punctuation an option name can never contain is stripped;
    without that a help string that ends a sentence on an option invents a flag
    that does not exist and the delta below is wrong in both directions.
    """
    return {token.strip("(),.;:'`\"[]")
            for token in help_text.replace("\n", " ").split()
            if token.startswith("--") and len(token) > 2}


@unittest.skipIf(GOLDEN_PRECONDITION, GOLDEN_PRECONDITION)
class UpstreamGoldenTests(unittest.TestCase):
    """One generate+normalize for the whole class; the comparisons are pure."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.workspace = Path(tempfile.mkdtemp(prefix="capcov-golden-"))
        raw, cls.actual = cls.workspace / "raw", cls.workspace / "normalized"
        pythonpath = [str(PACKAGE_ROOT)]
        if os.environ.get(INSTALLED_WHEEL_ENV) != "1":
            pythonpath.insert(0, str(PACKAGE_ROOT / "src"))
        env = {
            "PATH": _hidden_path(),
            "HOME": os.environ.get("HOME", str(cls.workspace)),
            "TERM": "dumb",
            "LANG": "en_US.UTF-8",
            # The wheel proof keeps only the test support package on PYTHONPATH;
            # capcov itself must then resolve from the installed distribution.
            "PYTHONPATH": os.pathsep.join(pythonpath),
            "CAPCOV_CAP_ROOT": str(PACKAGE_ROOT),
        }
        if os.environ.get(INSTALLED_WHEEL_ENV) == "1":
            imported = subprocess.run(
                [sys.executable, "-c", "import pathlib, capcov; print(pathlib.Path(capcov.__file__).resolve())"],
                cwd=str(cls.workspace), env=env, text=True, capture_output=True,
            )
            assert imported.returncode == 0, imported.stdout + imported.stderr
            assert not imported.stdout.strip().startswith(str(PACKAGE_ROOT / "src")), (
                "installed-wheel proof imported capcov from the source checkout: "
                + imported.stdout.strip()
            )
        generated = subprocess.run([sys.executable, str(GENERATE), str(raw)],
                                   cwd=str(PACKAGE_ROOT), env=env, text=True,
                                   capture_output=True)
        assert generated.returncode == 0, generated.stdout + generated.stderr
        normalized = subprocess.run(
            [sys.executable, str(NORMALIZE), str(raw), str(cls.actual),
             f"{raw / '_work'}=<root>", f"{raw}=<out>",
             f"{PACKAGE_ROOT}=<upstream>/packages/capabilities",
             f"{env['HOME']}=<home>"],
            text=True, capture_output=True)
        assert normalized.returncode == 0, normalized.stdout + normalized.stderr

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.workspace, ignore_errors=True)

    def _relative_golden_files(self) -> list[str]:
        """Every recorded artifact: the files the generator re-derives.

        ``suite/`` is the recorded run of upstream's own unittest suite, which
        this test does not re-run; it is pinned by the manifest below like
        everything else, and excluded only from the artifact comparisons.
        """
        names = (str(path.relative_to(GOLDEN))
                 for path in GOLDEN.rglob("*") if path.is_file())
        # META is matched on the RELATIVE PATH, not the basename: the four
        # metadata files live at the root of the fixture, and a recorded
        # artifact that happens to be called README.md or generate.py inside
        # `python_app/` is an artifact and must be compared like one.
        return sorted(name for name in names
                      if name not in META and not name.startswith("suite/"))

    def test_the_golden_bytes_are_the_ones_the_manifest_names(self) -> None:
        """Prove the comparison below read upstream's committed bytes, not a re-baseline.

        Over every committed file, ``suite/`` included, and in both directions: a
        file the manifest does not name is drift, and a manifest entry with no
        file is a manifest that names something this tree does not have.
        """
        manifest = json.loads((GOLDEN / "MANIFEST.json").read_text())["sha256"]
        # every file in the fixture except the gitignored transcript (*.log): the
        # recorded artifacts, the suite/ record and the two generator scripts
        present = {str(path.relative_to(GOLDEN)) for path in GOLDEN.rglob("*")
                   if path.is_file() and not path.name.endswith(".log")}
        drifted = {
            name: hashlib.sha256((GOLDEN / name).read_bytes()).hexdigest()
            for name in sorted(manifest)
            if name in present
            and hashlib.sha256((GOLDEN / name).read_bytes()).hexdigest() != manifest[name]}
        self.assertEqual(drifted, {})
        self.assertEqual(set(self._relative_golden_files()) - set(manifest), set())
        self.assertEqual(set(manifest) - present, set(),
                         "the manifest names a file this tree does not have")

    def test_only_the_root_metadata_and_the_suite_record_are_excluded(self) -> None:
        """Nothing leaves the byte comparison by accident of its basename.

        `META` names four files at the root of the fixture.  Matching it on the
        basename instead would silently drop any recorded artifact called
        README.md, MANIFEST.json, generate.py or normalize.py from a
        subdirectory -- a real possibility for a fixture whose whole content is
        CLI output over sample projects.  This pins the exclusion set to exactly
        the four root files plus the `suite/` record.
        """
        everything = {str(path.relative_to(GOLDEN))
                      for path in GOLDEN.rglob("*") if path.is_file()}
        excluded = everything - set(self._relative_golden_files())
        self.assertEqual({name for name in excluded if not name.startswith("suite/")},
                         META)

    def test_every_default_path_artifact_is_byte_identical_to_upstream(self) -> None:
        differing, missing = [], []
        for name in self._relative_golden_files():
            if name in HELP_WITH_JUDGE:
                continue
            if name.endswith(".stderr") and (GOLDEN / name).with_suffix(".error_line").is_file():
                continue  # compared through .error_line; see the module docstring
            produced = self.actual / name
            if not produced.is_file():
                missing.append(name)
                continue
            if produced.read_bytes() != (GOLDEN / name).read_bytes():
                differing.append(name)
        self.assertEqual(missing, [], "our branch produced no counterpart for these")
        self.assertEqual(differing, [], "our branch moved upstream's default path here")

    def test_our_run_produced_no_artifact_upstream_did_not(self) -> None:
        upstream = set(self._relative_golden_files())
        ours = {str(path.relative_to(self.actual))
                for path in self.actual.rglob("*") if path.is_file()}
        self.assertEqual(sorted(ours - upstream), [])

    def test_the_final_message_of_every_failing_run_is_unchanged(self) -> None:
        """The stable half of a failing run: the last line, not the frames above it."""
        lines = [name for name in self._relative_golden_files() if name.endswith(".error_line")]
        self.assertTrue(lines, "the golden pins at least one failing run")
        for name in lines:
            with self.subTest(name):
                self.assertEqual((self.actual / name).read_bytes(),
                                 (GOLDEN / name).read_bytes())

    def test_reconcile_and_gate_help_gains_only_the_judge_flags(self) -> None:
        """The one allowed delta, and it is exactly these opt-in flags wide."""
        for name in sorted(HELP_WITH_JUDGE):
            with self.subTest(name):
                upstream = _options((GOLDEN / name).read_text())
                ours = _options((self.actual / name).read_text())
                self.assertEqual(ours - upstream, JUDGE_FLAGS)
                self.assertEqual(upstream - ours, set(),
                                 "no upstream option may disappear")
                exit_name = name.replace(".stdout", ".exit")
                self.assertEqual((self.actual / exit_name).read_bytes(),
                                 (GOLDEN / exit_name).read_bytes())

    def test_no_other_help_text_moved(self) -> None:
        """`capcov --help` still lists upstream's subcommands and no experiment namespace."""
        top = (self.actual / "cli" / "help.stdout").read_text()
        self.assertEqual(top, (GOLDEN / "cli" / "help.stdout").read_text())
        self.assertNotIn("experiment", top)
        self.assertNotIn("claims", top)


class GoldenPreconditionsAreTheOnesTheFixtureRecordsTests(unittest.TestCase):
    """The skip above is only honest while its constants match the README.

    Not skipped with the class: a precondition nobody can read back is how a
    suite quietly stops running.  These two assertions run on every
    interpreter, including the one the class skips on.
    """

    def test_the_readme_names_the_interpreter_the_skip_expects(self) -> None:
        recorded = re.search(r"CPython \*\*(\d+)\.(\d+)\.", (GOLDEN / "README.md").read_text())
        self.assertIsNotNone(recorded, "the golden README no longer names its interpreter")
        self.assertEqual((int(recorded.group(1)), int(recorded.group(2))), GOLDEN_PYTHON)

    def test_the_readme_names_the_extras_the_skip_expects(self) -> None:
        readme = (GOLDEN / "README.md").read_text()
        for name in GOLDEN_EXTRAS:
            with self.subTest(name):
                self.assertIn(name, readme)

    def test_installed_wheel_proof_cannot_skip(self) -> None:
        """CI's wheel gate must fail instead of passing only the guard tests."""
        if os.environ.get(INSTALLED_WHEEL_ENV) == "1":
            self.assertEqual(GOLDEN_PRECONDITION, "")


if __name__ == "__main__":
    unittest.main()
