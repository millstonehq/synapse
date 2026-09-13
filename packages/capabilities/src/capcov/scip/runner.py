"""Run a SCIP indexer over a target tree and read the resulting index as JSON.

Two tools do two jobs and this module is the seam between them.

  * an INDEXER walks a source tree and emits a binary ``index.scip``:
    ``scip-python`` (Pyright-based) for Python, ``scip-go`` (go/packages) for Go;
  * the ``scip`` CLI's ``print --json`` turns that binary back into JSON, so
    capcov never links a protobuf runtime.

``read_scip_index`` normalizes the CLI's JSON into the one shape capcov consumes:
a list of documents, each carrying its symbols and its occurrences. Every
occurrence records whether it is a definition (from the SCIP symbol-role bitset)
and, for a definition, the line span (``enclosing_range``) that a caller of that
definition falls inside -- which is how a reference is attributed to the function
it sits in.

Tool requirements:

  * ``scip-python``: ``npm install -g @sourcegraph/scip-python``. Does NOT need
    the target's dependencies installed or a clean type-check; it degrades
    gracefully.
  * ``scip-go``: ``go install github.com/scip-code/scip-go/cmd/scip-go@latest``
    (the module MOVED off ``sourcegraph/``; the old import path no longer
    builds). Needs a buildable Go module in the target directory.
  * the ``scip`` CLI, located via the ``SCIP_CLI`` environment variable, a
    ``scip`` binary placed next to this package (see ``_BUNDLED_SCIP``), or
    ``scip`` on ``PATH``. Build it with::

        git clone --depth 1 https://github.com/sourcegraph/scip.git
        cd scip && go build -o scip ./cmd/scip
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

# name of the index the indexer writes and the reader consumes, in the target
# directory. Both indexers below are told to write exactly this.
_INDEX_FILENAME = "index.scip"

# language -> (executable, install hint). The hint rides in the exception text
# because a missing indexer is an operator problem whose fix is one line they
# should not have to look up.
_INDEXERS = {
    "python": ("scip-python", "npm install -g @sourcegraph/scip-python"),
    "go": (
        "scip-go",
        "go install github.com/scip-code/scip-go/cmd/scip-go@latest",
    ),
}

# A built ``scip`` binary dropped next to this package is picked up with nothing
# configured. Kept out of the wheel by default; SCIP_CLI overrides it.
_BUNDLED_SCIP = Path(__file__).resolve().parent / "vendor" / "scip"

# SCIP SymbolRole bitset: bit 0x1 is Definition; every other bit (import,
# write/read access, generated, test, ...) is orthogonal to it.
_DEFINITION_ROLE = 0x1

# A symbol whose kind the indexer left unset. scip-python emits none of these;
# scip-go populates a string like "Struct"/"Field"/"Function". For an unset
# kind we fall back to parsing the descriptor suffix.
_UNSPECIFIED_KIND = frozenset({None, "", 0, "UnspecifiedKind", "UnspecifiedSymbolKind"})


class IndexerNotFound(RuntimeError):
    """A required SCIP indexer (scip-python / scip-go) is not on PATH."""


class ScipCliNotFound(RuntimeError):
    """The ``scip`` CLI needed to read an index as JSON could not be located."""


def _index_command(language: str, output: str) -> list[str]:
    """The argv for indexing the current working directory, per language.

    Split out so the exact command can be asserted without a tool installed.
    Both indexers are pointed at ``output`` and run with the target directory as
    their cwd (see ``run_scip_index``), so a relative ``index.scip`` lands there.
    """
    if language == "python":
        return [
            "scip-python", "index",
            "--project-name", "spike",
            "--project-version", "0.0.1",
            "--output", output,
            ".",
        ]
    if language == "go":
        return ["scip-go", "--output", output]
    raise ValueError(
        f"unsupported language {language!r}; expected one of {sorted(_INDEXERS)}"
    )


def run_scip_index(
    target_dir: str | os.PathLike[str], language: str, *, timeout: int = 600
) -> Path:
    """Index ``target_dir`` and return the path to the written ``index.scip``.

    ``language`` is ``"python"`` or ``"go"``. Raises ``IndexerNotFound`` naming
    the missing tool and how to install it when the indexer is absent, and
    ``ValueError`` for an unsupported language.
    """
    if language not in _INDEXERS:
        raise ValueError(
            f"unsupported language {language!r}; expected one of {sorted(_INDEXERS)}"
        )
    executable, install_hint = _INDEXERS[language]
    if shutil.which(executable) is None:
        raise IndexerNotFound(
            f"{executable!r} is required to index a {language} project but was "
            f"not found on PATH. Install it with: {install_hint}"
        )

    target = Path(target_dir)
    command = _index_command(language, _INDEX_FILENAME)
    result = subprocess.run(
        command,
        cwd=str(target),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    index_path = target / _INDEX_FILENAME
    # scip-python degrades gracefully and can exit non-zero while still writing a
    # usable index, so the index's existence is the real success signal -- but a
    # non-zero exit with no index is a hard failure worth surfacing loudly.
    if not index_path.exists():
        raise RuntimeError(
            f"{executable} exited {result.returncode} and wrote no {_INDEX_FILENAME} "
            f"in {target}.\nstderr:\n{result.stderr}"
        )
    return index_path


def _locate_scip_cli() -> str:
    """Find the ``scip`` CLI: SCIP_CLI, then the bundled path, then PATH."""
    override = os.environ.get("SCIP_CLI")
    if override:
        candidate = Path(override)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
        raise ScipCliNotFound(
            f"SCIP_CLI={override!r} is not an executable file"
        )
    if _BUNDLED_SCIP.is_file() and os.access(_BUNDLED_SCIP, os.X_OK):
        return str(_BUNDLED_SCIP)
    found = shutil.which("scip")
    if found:
        return found
    raise ScipCliNotFound(
        "the `scip` CLI is required to read an index as JSON, but none was "
        f"found. Set SCIP_CLI to a built binary, drop one at {_BUNDLED_SCIP}, "
        "or put `scip` on PATH. Build it with: git clone --depth 1 "
        "https://github.com/sourcegraph/scip.git && cd scip && "
        "go build -o scip ./cmd/scip"
    )


def _run_scip_print(
    index_path: str | os.PathLike[str], scip_cli: str, *, timeout: int = 120
) -> str:
    result = subprocess.run(
        [scip_cli, "print", "--json", str(index_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"`scip print --json {index_path}` exited {result.returncode}: "
            f"{result.stderr}"
        )
    return result.stdout


def read_scip_index(index_path: str | os.PathLike[str]) -> dict:
    """Read ``index_path`` via ``scip print --json`` and return normalized dict.

    Shape::

        {"documents": [
            {"path": str,
             "symbols": [{"symbol", "kind", "display_name"}],
             "occurrences": [{"symbol", "is_definition", "start_line",
                              "start_col", "enclosing_start_line",
                              "enclosing_end_line"}]}
        ]}

    Raises ``ScipCliNotFound`` when the ``scip`` CLI cannot be located.
    """
    scip_cli = _locate_scip_cli()
    raw = _run_scip_print(index_path, scip_cli)
    return normalize_scip_json(json.loads(raw))


def _first(mapping: dict, *keys: str, default: object = None) -> object:
    """Return the first present key's value -- tolerates snake_case (what the
    scip CLI emits) and camelCase (protojson's default) for the same field."""
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


def _kind_from_suffix(symbol: str) -> str | None:
    """Derive a symbol's kind from its SCIP descriptor suffix.

    The suffix encodes the kind: ``#`` a type/class, ``().`` a method/function,
    a trailing ``.`` a term/field. Used for scip-python, which leaves kind unset.
    """
    stripped = symbol.rstrip()
    if stripped.endswith("#"):
        return "type"
    if stripped.endswith("()."):
        return "method"
    if stripped.endswith("."):
        return "term"
    return None


def _normalize_symbol(symbol: dict) -> dict:
    name = symbol["symbol"]
    raw_kind = _first(symbol, "kind")
    kind = raw_kind if raw_kind not in _UNSPECIFIED_KIND else _kind_from_suffix(name)
    return {
        "symbol": name,
        "kind": kind,
        "display_name": _first(symbol, "display_name", "displayName"),
    }


def _range_start(rng: list | None) -> tuple[int | None, int | None]:
    """Start (line, col) of a SCIP range. A range is either
    ``[startLine, startCol, endCol]`` (one line) or
    ``[startLine, startCol, endLine, endCol]``; both start the same way."""
    if not rng:
        return None, None
    return rng[0], rng[1]


def _enclosing_span(rng: list | None) -> tuple[int | None, int | None]:
    """(start_line, end_line) of an enclosing range, tolerating the one-line
    three-element form."""
    if not rng:
        return None, None
    end_line = rng[2] if len(rng) >= 4 else rng[0]
    return rng[0], end_line


def _normalize_occurrence(occ: dict) -> dict:
    roles = _first(occ, "symbol_roles", "symbolRoles", default=0) or 0
    start_line, start_col = _range_start(_first(occ, "range"))
    enc_start, enc_end = _enclosing_span(
        _first(occ, "enclosing_range", "enclosingRange")
    )
    return {
        "symbol": occ.get("symbol"),
        "is_definition": bool(roles & _DEFINITION_ROLE),
        "start_line": start_line,
        "start_col": start_col,
        "enclosing_start_line": enc_start,
        "enclosing_end_line": enc_end,
    }


def normalize_scip_json(doc: dict) -> dict:
    """Normalize a ``scip print --json`` document into capcov's shape.

    Pure over its input: no filesystem, no tools -- which is what lets the test
    suite exercise it against a checked-in sample.
    """
    documents = []
    for document in doc.get("documents", []):
        documents.append(
            {
                "path": _first(document, "relative_path", "relativePath", "path"),
                "symbols": [
                    _normalize_symbol(s) for s in document.get("symbols", [])
                ],
                "occurrences": [
                    _normalize_occurrence(o)
                    for o in document.get("occurrences", [])
                ],
            }
        )
    return {"documents": documents}
