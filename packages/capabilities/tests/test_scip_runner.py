"""Tests for the SCIP runner + reader.

The normalization suite runs entirely against a checked-in `scip print --json`
sample (tests/fixtures/scip_print_sample.json). It needs no network and no scip
tools: normalization is a pure function over the CLI's JSON, and the fixture is
the contract. Tests that actually shell out to an indexer or the scip CLI are
isolated in LiveToolTest and skip when the tool is absent.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from capcov.scip import runner

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "scip_print_sample.json"

_PY = "scip-python python spike 0.0.1 app/models/"
_GO = "scip-go gomod github.com/example/app v0.0.0 `app`/"


class NormalizationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(FIXTURE.read_text())
        self.out = runner.normalize_scip_json(self.raw)
        self.docs = {d["path"]: d for d in self.out["documents"]}

    def test_documents_are_keyed_by_relative_path(self) -> None:
        self.assertEqual(set(self.docs), {"app/models/job.py", "app/server.go"})

    def test_python_kind_is_derived_from_the_symbol_suffix(self) -> None:
        """scip-python leaves kind null; the descriptor suffix (`#`, `().`, `.`)
        is the only signal for whether a symbol is a type, a method or a term."""
        kinds = {
            s["display_name"]: s["kind"]
            for s in self.docs["app/models/job.py"]["symbols"]
        }
        self.assertEqual(kinds, {"Job": "type", "save": "method", "status": "term"})

    def test_go_populated_kind_is_preserved(self) -> None:
        """scip-go fills kind in; a populated kind must survive untouched rather
        than be second-guessed from the suffix."""
        kinds = {
            s["display_name"]: s["kind"]
            for s in self.docs["app/server.go"]["symbols"]
        }
        self.assertEqual(
            kinds, {"Server": "Struct", "Addr": "Field", "Start": "Function"}
        )

    def test_python_occurrences_are_fully_normalized(self) -> None:
        self.assertEqual(
            self.docs["app/models/job.py"]["occurrences"],
            [
                {
                    "symbol": _PY + "Job#",
                    "is_definition": True,
                    "start_line": 10,
                    "start_col": 6,
                    "enclosing_start_line": 10,
                    "enclosing_end_line": 40,
                },
                {
                    "symbol": _PY + "Job#",
                    "is_definition": False,
                    "start_line": 55,
                    "start_col": 4,
                    "enclosing_start_line": None,
                    "enclosing_end_line": None,
                },
                {
                    "symbol": _PY + "Job#save().",
                    "is_definition": True,
                    "start_line": 15,
                    "start_col": 8,
                    "enclosing_start_line": 15,
                    "enclosing_end_line": 22,
                },
            ],
        )

    def test_definition_bit_marks_definitions_and_references(self) -> None:
        occs = self.docs["app/models/job.py"]["occurrences"]
        self.assertEqual(
            [o["is_definition"] for o in occs], [True, False, True]
        )

    def test_missing_symbol_roles_is_not_a_definition(self) -> None:
        """The go reference occurrence carries no symbol_roles key at all; a
        missing role must default to 0, i.e. not a definition."""
        ref = self.docs["app/server.go"]["occurrences"][-1]
        self.assertFalse(ref["is_definition"])
        self.assertEqual(ref["symbol"], _GO + "Server#")

    def test_single_line_three_element_range(self) -> None:
        """A [line, startCol, endCol] range (same line) yields the start line/col
        exactly like a four-element range does."""
        start = self.docs["app/server.go"]["occurrences"][1]  # Start(), range [20,5,10]
        self.assertEqual((start["start_line"], start["start_col"]), (20, 5))
        self.assertEqual(
            (start["enclosing_start_line"], start["enclosing_end_line"]), (20, 30)
        )

    def test_definition_bit_is_masked_not_equality_checked(self) -> None:
        """A role value with additional bits set (e.g. 0x8 ReadAccess | 0x1
        Definition) is still a definition."""
        doc = {
            "documents": [
                {
                    "relative_path": "x.py",
                    "symbols": [],
                    "occurrences": [
                        {"symbol": "s", "range": [0, 0, 1], "symbol_roles": 9},
                        {"symbol": "s", "range": [1, 0, 1], "symbol_roles": 8},
                    ],
                }
            ]
        }
        occs = runner.normalize_scip_json(doc)["documents"][0]["occurrences"]
        self.assertEqual([o["is_definition"] for o in occs], [True, False])


class KindFromSuffixTest(unittest.TestCase):
    def test_suffix_grammar(self) -> None:
        self.assertEqual(runner._kind_from_suffix("pkg Thing#"), "type")
        self.assertEqual(runner._kind_from_suffix("pkg Thing#method()."), "method")
        self.assertEqual(runner._kind_from_suffix("pkg Thing#field."), "term")

    def test_unknown_suffix_is_none(self) -> None:
        self.assertIsNone(runner._kind_from_suffix("pkg param(x)"))


class RunIndexTest(unittest.TestCase):
    def test_missing_python_indexer_names_the_tool(self) -> None:
        with patch("capcov.scip.runner.shutil.which", return_value=None):
            with self.assertRaises(runner.IndexerNotFound) as ctx:
                runner.run_scip_index("/some/dir", "python")
        self.assertIn("scip-python", str(ctx.exception))

    def test_missing_go_indexer_names_the_tool_and_the_moved_module(self) -> None:
        with patch("capcov.scip.runner.shutil.which", return_value=None):
            with self.assertRaises(runner.IndexerNotFound) as ctx:
                runner.run_scip_index("/some/dir", "go")
        message = str(ctx.exception)
        self.assertIn("scip-go", message)
        # the module moved off sourcegraph/; the install hint must reflect that.
        self.assertIn("scip-code/scip-go", message)

    def test_unknown_language_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            runner.run_scip_index("/some/dir", "ruby")

    def test_python_command_shape(self) -> None:
        self.assertEqual(
            runner._index_command("python", "index.scip"),
            [
                "scip-python", "index",
                "--project-name", "spike",
                "--project-version", "0.0.1",
                "--output", "index.scip",
                ".",
            ],
        )

    def test_go_command_shape(self) -> None:
        self.assertEqual(
            runner._index_command("go", "index.scip"),
            ["scip-go", "--output", "index.scip"],
        )

    def test_run_index_invokes_indexer_in_target_dir_and_returns_path(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            recorded = {}

            def fake_run(command, **kwargs):
                recorded["command"] = command
                recorded["cwd"] = kwargs.get("cwd")
                (Path(kwargs["cwd"]) / "index.scip").write_bytes(b"\x00")
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with (
                patch("capcov.scip.runner.shutil.which", return_value="/usr/bin/scip-python"),
                patch("capcov.scip.runner.subprocess.run", fake_run),
            ):
                out = runner.run_scip_index(d, "python")

            self.assertEqual(out, Path(d) / "index.scip")
            self.assertEqual(recorded["cwd"], str(Path(d)))
            self.assertEqual(recorded["command"][0], "scip-python")

    def test_run_index_raises_when_indexer_writes_no_index(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            def fake_run(command, **kwargs):
                return SimpleNamespace(returncode=1, stdout="", stderr="boom")

            with (
                patch("capcov.scip.runner.shutil.which", return_value="/usr/bin/scip-python"),
                patch("capcov.scip.runner.subprocess.run", fake_run),
            ):
                with self.assertRaises(RuntimeError) as ctx:
                    runner.run_scip_index(d, "python")
            self.assertIn("boom", str(ctx.exception))


class ReadIndexTest(unittest.TestCase):
    def test_scip_cli_not_located_raises_named_error(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("capcov.scip.runner._BUNDLED_SCIP", Path("/no/such/scip")),
            patch("capcov.scip.runner.shutil.which", return_value=None),
        ):
            with self.assertRaises(runner.ScipCliNotFound) as ctx:
                runner.read_scip_index("index.scip")
        self.assertIn("SCIP_CLI", str(ctx.exception))

    def test_scip_cli_env_var_takes_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            cli = Path(d) / "scip"
            cli.write_text("#!/bin/sh\n")
            cli.chmod(0o755)
            with patch.dict(os.environ, {"SCIP_CLI": str(cli)}):
                self.assertEqual(runner._locate_scip_cli(), str(cli))

    def test_read_uses_the_cli_and_normalizes_its_output(self) -> None:
        raw_text = FIXTURE.read_text()
        with tempfile.TemporaryDirectory() as d:
            cli = Path(d) / "scip"
            cli.write_text("#!/bin/sh\n")
            cli.chmod(0o755)
            captured = {}

            def fake_run(command, **kwargs):
                captured["command"] = command
                return SimpleNamespace(returncode=0, stdout=raw_text, stderr="")

            with (
                patch.dict(os.environ, {"SCIP_CLI": str(cli)}),
                patch("capcov.scip.runner.subprocess.run", fake_run),
            ):
                out = runner.read_scip_index(Path(d) / "index.scip")

            self.assertEqual(captured["command"][0], str(cli))
            self.assertEqual(captured["command"][1:3], ["print", "--json"])
            self.assertEqual(
                {doc["path"] for doc in out["documents"]},
                {"app/models/job.py", "app/server.go"},
            )


# Live tests actually shell out to a real tool. They verify the wiring the
# mocked tests cannot, and skip cleanly wherever the tool is not installed.
_HAVE_SCIP_PYTHON = shutil.which("scip-python") is not None


def _have_scip_cli() -> bool:
    try:
        runner._locate_scip_cli()
        return True
    except runner.ScipCliNotFound:
        return False


class LiveToolTest(unittest.TestCase):
    @unittest.skipUnless(_HAVE_SCIP_PYTHON, "scip-python not installed")
    def test_scip_python_indexes_a_tiny_project(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "m.py").write_text(
                "class C:\n    def f(self):\n        return 1\n"
            )
            out = runner.run_scip_index(d, "python")
            self.assertEqual(out, Path(d) / "index.scip")
            self.assertTrue(out.exists() and out.stat().st_size > 0)

    @unittest.skipUnless(
        _HAVE_SCIP_PYTHON and _have_scip_cli(),
        "needs both scip-python and the scip CLI (set SCIP_CLI)",
    )
    def test_end_to_end_index_then_read(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "m.py").write_text(
                "class C:\n    def f(self):\n        return 1\n"
            )
            index = runner.run_scip_index(d, "python")
            result = runner.read_scip_index(index)
            self.assertIn("documents", result)
            definitions = [
                occ
                for doc in result["documents"]
                for occ in doc["occurrences"]
                if occ["is_definition"]
            ]
            self.assertTrue(definitions, "a class + method must yield definitions")


if __name__ == "__main__":
    unittest.main()
