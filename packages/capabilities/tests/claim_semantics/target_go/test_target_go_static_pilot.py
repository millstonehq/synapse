"""target-go static path pilot: the section-29 machinery against an external Go checkout (section 30).

The test itself indexes a ``git archive HEAD`` copy of ``$CAPCOV_GO_FIXTURE_ROOT``
with the pinned scip-go, exports the import closure of the route handler's
package, combines it with the reviewed rule pack, runs both kernels through
``claims.differential.compare``, extracts certificates for the supported
claims from *both* closures, and records a receipt.  It skips only when the
fixture root or a tool is absent (the gate rejects "skipped"); a limit hit is
a failure that says ``resource-exhausted``, never a silently narrowed slice.

What is target-go specific is stated, not hidden:

* the route handler is a labelled ASSUMPTION (``route_handler_symbol__accepted``)
  read from the router lines named in ``ROUTE_REGISTRATION`` /
  ``HANDLER_DEFINITION``; the test re-reads those archived lines so a drift in
  target-go fails here instead of mis-declaring the binding;
* target-go issues SQL through ``database/sql`` and sends mail through its own
  ``Mailer`` implementations, so there are no ``static_op_site`` rows and the
  claims are ``static_reaches`` from the handler to named sinks;
* when ``CAPCOV_TARGET_GO_RUNTIME_RECEIPT`` names a retained receipt, the exporter
  binds its run through ``index_describes_run`` and both kernels derive the
  route observation on that exact index; this does not claim a runtime-traced
  route-to-SQL call stack;
* this external SCIP fixture has an explicit 300-second Python-kernel budget.
  A limit hit still fails as ``resource-exhausted`` and is never narrowed away.

No target-go source is written anywhere under the repository: the archive lives in
a temporary directory; the artifacts the test writes (receipt, certificates)
carry digests, counts, symbol names, paths and line numbers only.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from capcov.claims import Claim, Constant, Context, canonical_json, digest as ir_digest
from capcov.claims.differential import DifferentialMismatch, compare, run_python
from capcov.claims.evaluator import ResourceLimits
from capcov.claims.static import pilot, scip_facts
from capcov.claims.static.certificate import certify, claim_conclusions, recheck, rules_digest
from capcov.claims.static.combine import combine
from capcov.claims.static.runtime_receipt import (load_runtime_receipt, runtime_bundle)
from capcov.scip import runner

try:
    from ..static_rules.adapter import pack_bundle
except ImportError:  # unittest discover -s tests/claim_semantics imports target_go as top-level
    from static_rules.adapter import pack_bundle

FIXTURE_ROOT = os.environ.get("CAPCOV_GO_FIXTURE_ROOT")
RUNTIME_RECEIPT_PATH = os.environ.get("CAPCOV_TARGET_GO_RUNTIME_RECEIPT")
_HAVE_TOOLS = bool(FIXTURE_ROOT and shutil.which("scip-go") and shutil.which("scip") and shutil.which("go"))

MODULE = "git.internal.example/org/target-go"
LANGUAGE = "go"
HANDLER_PACKAGE = f"{MODULE}/internal/pilot"
# The route: internal/httpserver/server.go mounts the app handler at "/"
# (APP_MOUNT); cmd/target-go/main.go passes Runtime.Handler() (APP_WIRING), which
# registers, for action in {decrypt, unsubscribe, subscribe},
#   mux.HandleFunc("GET /api/cloud/notification-unsubscribe/"+action+"-email", r.recipientLinks(action))
# (ROUTE_REGISTRATION).  The three actions share one handler closure returned by
# Runtime.recipientLinks (HANDLER_DEFINITION), so one concrete surface is declared.
SURFACE = "http:GET /api/cloud/notification-unsubscribe/subscribe-email"
ROUTE_REGISTRATION = ("internal/pilot/runtime.go", 209, "r.recipientLinks(action)")
HANDLER_DEFINITION = ("internal/pilot/recipient_links.go", 14, "func (r *Runtime) recipientLinks(")
APP_MOUNT = ("internal/httpserver/server.go", 47, 'mux.Handle("/", app)')
APP_WIRING = ("cmd/target-go/main.go", 181, "httpserver.New(runtime.Handler()")
SQL_SINK_SITE = ("internal/legacyissues/subscriptions.go", 56, "tx.ExecContext(")

_P = f"scip-go gomod {MODULE} . "
HANDLER = _P + f"`{HANDLER_PACKAGE}`/Runtime#recipientLinks()."
CHANGE_SUBSCRIPTION = _P + f"`{MODULE}/internal/legacyissues`/ChangeSubscription()."
SEND_DUE_DIGESTS = _P + f"`{MODULE}/internal/legacyissues`/SendDueDigests()."

CLAIM_FIRST_PARTY = "claim-route-reaches-change-subscription"
CLAIM_SQL = "claim-route-reaches-sql-tx-exec"
CONTROL = "control-route-reaches-send-due-digests"
CLAIM_RUNTIME_SQL = "claim-runtime-route-belongs-to-index-with-terminal-sql-receipt"
CLAIM_RUNTIME_CAUSAL_SQL = "claim-runtime-route-executed-sql-on-index"
CERTIFIED_CLAIMS = (CLAIM_FIRST_PARTY, CLAIM_SQL, CLAIM_RUNTIME_SQL, CLAIM_RUNTIME_CAUSAL_SQL)

INDEX_TIMEOUT = 20 * 60
LIMITS = scip_facts.ExportLimits(documents=500, occurrences=200_000, rows=100_000)
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
COMMITTED_RECEIPT = ARTIFACTS / "receipt.json"
# static-relations-v1 identity of the archived tree under the pinned toolchain,
# keyed by target-go HEAD.  Established by two cold-cache runs from fresh nix shells
# (section 30); a warm-cache run must reproduce it byte for byte.
PINNED_IDENTITY = {
    "7e339e07dbaafe7e606a20afe644623a1f58228f": "0759ccef8fbb6024b7d215c8adc3019e93bfd277e112090acaa1304813323a3b",
}
RECORDED_DERIVED = ("static_edge", "static_root", "static_reaches", "static_route_handler", "static_index_current",
                    "scip_index_stale", "static_scope_leak", "static_scope_closed", "scip_references_closed",
                    "static_reachability_closed", "scip_duplicate_definition", "static_file_unindexed")


def stdlib_symbol(go_directive: str, package: str, member: str) -> str:
    """scip-go spells standard-library symbols under the go.mod ``go`` directive."""
    return f"scip-go gomod github.com/golang/go/src go{go_directive} `{package}`/{member}"


def _rows(bundle, relation: str):
    return [[t.value for t in f.terms] for f in bundle.facts if f.relation == relation]


def _edge_chain(node: dict, out: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Every ``static_edge`` application in a certificate derivation, in derivation order."""
    if node.get("kind") == "rule":
        if node["relation"] == "static_edge":
            out.append((node["row"][1], node["row"][2]))
        for premise in node["premises"]:
            _edge_chain(premise, out)
    return out


@unittest.skipUnless(_HAVE_TOOLS, "needs CAPCOV_GO_FIXTURE_ROOT and scip-go, scip and go on PATH")
class FgGoStaticPilotTest(unittest.TestCase):
    blocked: str | None = None

    @classmethod
    def setUpClass(cls) -> None:
        started = time.time()
        cls.tmp = tempfile.TemporaryDirectory(prefix="capcov-target-go-pilot-")
        cls.out_dir = Path(os.environ.get("CAPCOV_TARGET_GO_PILOT_OUT") or tempfile.mkdtemp(prefix="capcov-target-go-pilot-out-"))
        cls.out_dir.mkdir(parents=True, exist_ok=True)
        cls.checkout = pilot.inspect_checkout(FIXTURE_ROOT)
        cls.runtime_receipt = cls._load_runtime_receipt()
        cls.archive = pilot.archive_head(FIXTURE_ROOT, Path(cls.tmp.name) / "target-go")
        cache_root = Path(os.environ.get("CAPCOV_GO_CACHE_ROOT") or Path(tempfile.gettempdir()) / "capcov-target-go-pilot")
        cls.go_env = pilot.index_environment(cache_root / "gomodcache", cache_root / "gocache")
        for path in (cls.go_env["GOMODCACHE"], cls.go_env["GOCACHE"]):
            Path(path).mkdir(parents=True, exist_ok=True)
        cls.saved_env = {k: os.environ.get(k) for k in cls.go_env}
        os.environ.update(cls.go_env)
        cls.tools = pilot.tool_receipt()
        cls.timings: dict[str, float] = {}
        cls.go_directive = cls.checkout.go_directive
        cls.sql_begin_tx = stdlib_symbol(cls.go_directive, "database/sql", "DB#BeginTx().")
        cls.sql_tx_exec = stdlib_symbol(cls.go_directive, "database/sql", "Tx#ExecContext().")
        # --- index -----------------------------------------------------------
        t = time.time()
        try:
            index_path = runner.run_scip_index(cls.archive, LANGUAGE, timeout=INDEX_TIMEOUT)
        except subprocess.TimeoutExpired:
            cls.blocked = f"resource-exhausted: scip-go exceeded {INDEX_TIMEOUT}s on the archived checkout"
            return
        except RuntimeError as exc:
            cls.blocked = f"indexer error: {exc}"
            return
        cls.timings["index"] = round(time.time() - t, 1)
        cls.index_sha256 = pilot.sha256_file(index_path)
        cls.index_bytes = index_path.stat().st_size
        cls.normalized = runner.read_scip_index(index_path, retain=True)
        index_path.unlink()
        # --- slice and export -------------------------------------------------
        cls.closure = pilot.package_closure(cls.normalized, MODULE, HANDLER_PACKAGE, language=LANGUAGE)
        t = time.time()
        cls.exported = scip_facts.export_bundle(
            cls.normalized, ast_raw=None, source_root=cls.archive, language=LANGUAGE,
            scope=scip_facts.Scope.document_set(cls.closure.documents), limits=LIMITS,
            index_digest=cls.normalized["index_digest"], index_digest_kind=cls.normalized["index_digest_kind"],
            commit=cls.checkout.head,
            describes_runs=(cls.runtime_receipt["run"],) if cls.runtime_receipt else ())
        cls.timings["export"] = round(time.time() - t, 1)
        if cls.exported.status != scip_facts.STATUS_COMPLETE:
            cls.blocked = (f"export {cls.exported.status}: {cls.exported.messages}; counts {cls.exported.counts}; "
                           f"limits {LIMITS} -- narrowing the slice is a recorded decision, not an automatic one")
            return
        cls.meta = dict(cls.exported.bundle.metadata)
        cls.index = cls.meta["index_digest"]
        cls.coverage = pilot.edge_coverage(cls.exported.bundle)
        # --- combine with the pack, the assumption and the claims ---------------
        pack = pack_bundle()
        decls = {d.name: d for d in (*cls.exported.bundle.relations, *pack.relations)}
        index_eid = next(e.id for e in cls.exported.bundle.evidence if e.atom.relation == "scip_index")
        declared_from = (f"{ROUTE_REGISTRATION[0]}:{ROUTE_REGISTRATION[1]} registers "
                         f"GET /api/cloud/notification-unsubscribe/<action>-email -> {ROUTE_REGISTRATION[2]}; "
                         f"handler defined at {HANDLER_DEFINITION[0]}:{HANDLER_DEFINITION[1]}; app mounted at "
                         f"{APP_MOUNT[0]}:{APP_MOUNT[1]} and wired at {APP_WIRING[0]}:{APP_WIRING[1]}")
        cls.assumption = pilot.route_handler_assumption(cls.index, SURFACE, HANDLER, declared_from=declared_from,
                                                        index_evidence_id=index_eid)
        tree_atom, tree_evidence = pilot.source_tree_observation(decls, dict(cls.meta["tree"])["digest"])
        cls.claims = [
            pilot.reaches_claim(cls.index, HANDLER, CHANGE_SUBSCRIPTION, CLAIM_FIRST_PARTY),
            pilot.reaches_claim(cls.index, HANDLER, cls.sql_tx_exec, CLAIM_SQL),
            pilot.reaches_claim(cls.index, HANDLER, SEND_DUE_DIGESTS, CONTROL),
        ]
        runtime_bundle = Bundle(())
        if cls.runtime_receipt:
            runtime_bundle = cls._runtime_bundle(decls)
            cls.claims.append(Claim(
                "runtime_route_observed_on_index",
                (Constant(cls.index, "digest"), Constant(cls.runtime_receipt["tenant"], "symbol"),
                 Constant(SURFACE, "symbol"), Constant(cls.runtime_receipt["run"], "symbol")),
                Context.from_mapping({"index": cls.index, "tenant": cls.runtime_receipt["tenant"],
                                      "surface": SURFACE, "run": cls.runtime_receipt["run"]}),
                id=CLAIM_RUNTIME_SQL))
            cls.claims.append(Claim(
                "runtime_route_reaches_sql_on_index",
                (Constant(cls.index, "digest"), Constant(cls.runtime_receipt["run"], "symbol"),
                 Constant(cls.runtime_receipt["request_id"], "symbol"), Constant(SURFACE, "symbol"),
                 Constant("git.internal.example/org/target-go/internal/legacyissues.ChangeSubscription", "symbol"),
                 Constant("change-subscription", "symbol"),
                 Constant("cancel-notification-confirmation", "symbol")),
                Context.from_mapping({"index": cls.index, "run": cls.runtime_receipt["run"],
                                      "request": cls.runtime_receipt["request_id"], "surface": SURFACE,
                                      "tx": "change-subscription"}),
                id=CLAIM_RUNTIME_CAUSAL_SQL))
        cls.claims = tuple(cls.claims)
        cls.bundle = combine(
            cls.exported.bundle, pack, cls.assumption, runtime_bundle,
            facts=[tree_atom], evidence=[tree_evidence],
            claims=cls.claims,
            metadata={"experiment": "section-30 target-go static path pilot", "surface": SURFACE,
                      "target": cls.checkout.receipt(),
                      "runtime_join": cls.runtime_receipt["run"] if cls.runtime_receipt else "none (static half only)"})
        # --- both kernels ---------------------------------------------------------
        cls.replay_root = tempfile.mkdtemp(prefix="capcov-target-go-pilot-replay-")
        cls.result = None
        cls.mismatch = None
        t = time.time()
        try:
            cls.result = compare(
                cls.bundle,
                python_runner=lambda bundle: run_python(
                    bundle, limits=ResourceLimits(max_seconds=300.0)),
                replay_root=cls.replay_root,
            )
        except DifferentialMismatch as exc:
            cls.mismatch = exc.result
        cls.timings["compare"] = round(time.time() - t, 1)
        cls.timings["total"] = round(time.time() - started, 1)
        cls.receipt = cls._write_artifacts()
        print(f"\ntarget-go pilot artifacts: {cls.out_dir} (index {cls.timings.get('index')}s, "
              f"compare {cls.timings.get('compare')}s)")

    @classmethod
    def tearDownClass(cls) -> None:
        for key, value in getattr(cls, "saved_env", {}).items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        if getattr(cls, "mismatch", None) is None and getattr(cls, "replay_root", ""):
            shutil.rmtree(cls.replay_root, ignore_errors=True)
        cls.tmp.cleanup()

    # -- receipt --------------------------------------------------------------

    @classmethod
    def _write_artifacts(cls) -> dict:
        report = cls.result.python if cls.result is not None else cls.mismatch.python
        other = cls.result.souffle if cls.result is not None else cls.mismatch.souffle
        relations = dict(report.relations)
        closure = pilot.closure_symbols(relations, cls.index, HANDLER)
        unrooted_closure = pilot.unrooted_on_closure(cls.coverage, closure)
        deep_unresolved = sum(1 for row in relations.get("static_unresolved", ()) if row[1] == "deep-unresolved")
        verdicts = {c.key: {"semantic": c.semantic, "operational": c.operational, "basis": c.basis,
                            "missing_premises": list(c.missing_premises)} for c in report.claims}
        certificates: dict[str, dict] = {}
        chain: dict[str, list[list[str]]] = {}
        if cls.result is not None:
            for claim in cls.claims:
                if claim.id not in CERTIFIED_CLAIMS:
                    continue
                rows = claim_conclusions(cls.bundle, relations, claim)
                if not rows:
                    continue
                cert = certify(cls.bundle, relations, claim.relation, rows[0])
                certificates[claim.id] = cert
                chain[claim.id] = [list(edge) for edge in _edge_chain(cert["derivation"] or {}, [])]
                (cls.out_dir / f"certificate-{claim.id}.json").write_text(
                    json.dumps(cert, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        supported = (cls.result is not None and cls.result.matched
                     and verdicts.get(CLAIM_SQL, {}).get("semantic") == "supported")
        outcome, reasons = pilot.outcome(claim_supported=supported, coverage=cls.coverage,
                                         unrooted_closure=unrooted_closure, deep_unresolved=deep_unresolved)
        unindexed = sorted(row[1] for row in relations.get("static_file_unindexed", ()))
        receipt = {
            "pilot": "EXPERIMENT-PLAN section 30 target-go static path pilot",
            "target": cls.checkout.receipt(),
            "tools": cls.tools,
            "go_environment": cls.go_env,
            "index_file": {"sha256": cls.index_sha256, "bytes": cls.index_bytes, "kind": "binary receipt, not identity",
                           "tool_name": cls.normalized["metadata"].get("tool_name"),
                           "tool_version": cls.normalized["metadata"].get("tool_version"),
                           "documents": len(cls.normalized["documents"]),
                           "occurrences": sum(len(d["occurrences"]) for d in cls.normalized["documents"])},
            "route": {"surface": SURFACE, "handler_symbol": HANDLER,
                      "declared_from": cls.assumption.evidence[0].source,
                      "assumption_evidence_id": cls.assumption.evidence[0].id,
                      "binding": "labelled assumption; no route_site / route_handler_location observation"},
            "slice": cls.closure.receipt(),
            "export": {"status": cls.exported.status, "profile": cls.meta["profile"],
                       "limits": {"documents": LIMITS.documents, "occurrences": LIMITS.occurrences, "rows": LIMITS.rows},
                       "facts": len(cls.exported.bundle.facts), "row_counts": cls.exported.counts,
                       "index_identity": cls.index, "index_identity_kind": cls.meta["index_digest_kind"],
                       "exported_bundle_digest": scip_facts.bundle_digest(cls.exported.bundle),
                       "tree": dict(cls.meta["tree"]), "messages": list(cls.exported.messages),
                       "unindexed_files": unindexed,
                       "out_of_tree_documents": [dict(e) for e in cls.meta["out_of_tree_documents"]]},
            "combined": {"bundle_digest": scip_facts.bundle_digest(cls.bundle), "ir_digest": ir_digest(cls.bundle),
                         "rules_digest": rules_digest(cls.bundle), "facts": len(cls.bundle.facts),
                         "rules": len(cls.bundle.rules), "relations": len(cls.bundle.relations)},
            "kernels": {"matched": cls.result is not None and cls.result.matched,
                        "python_digest": report.canonical_digest, "souffle_digest": other.canonical_digest,
                        "python_failure": report.operational_failure, "souffle_failure": other.operational_failure,
                        "replay_path": cls.mismatch.replay_path if cls.mismatch else None,
                        "derived_rows": {name: len(relations.get(name, ())) for name in RECORDED_DERIVED}},
            "claims": verdicts,
            "path": chain,
            # ``sha256`` binds the certificate to this run's bundle (its
            # ``bundle_digest`` is the plain IR digest, which sees the index-file
            # receipt); ``derivation_sha256`` is the run-independent part.
            "certificates": {claim_id: {"sha256": ir_digest(cert),
                                        "derivation_sha256": ir_digest({k: v for k, v in cert.items() if k != "bundle_digest"}),
                                        "steps": cert["steps"], "nodes": cert["nodes"],
                                        "leaves": len(cert["leaves"]), "truncated": cert["truncated"]}
                             for claim_id, cert in certificates.items()},
            "coverage": {**cls.coverage.receipt(), "route_closure_symbols": len(closure),
                         "unrooted_on_route_closure": unrooted_closure, "deep_unresolved": deep_unresolved},
            "outcome": outcome, "outcome_reasons": reasons,
            "runtime_join": ({"run": cls.runtime_receipt["run"], "receipt_sha256": cls.runtime_receipt_sha256,
                              "claim": CLAIM_RUNTIME_SQL} if cls.runtime_receipt else
                             "none: no retained target-go run receipt exists, so no index_describes_run row was declared"),
            "timings_seconds": cls.timings,
        }
        (cls.out_dir / "receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        return receipt

    @classmethod
    def _load_runtime_receipt(cls):
        if not RUNTIME_RECEIPT_PATH:
            cls.runtime_receipt_sha256 = None
            return None
        loaded = load_runtime_receipt(
            RUNTIME_RECEIPT_PATH,
            expected_commit=cls.checkout.head,
            expected_surface=SURFACE)
        cls.runtime_receipt_sha256 = loaded.sha256
        return loaded

    @classmethod
    def _runtime_bundle(cls, decls):
        del decls  # declarations come from the shared receipt producer
        return runtime_bundle(cls.runtime_receipt, sha256=cls.runtime_receipt_sha256)

    # -- helpers --------------------------------------------------------------

    def _ready(self) -> None:
        if self.blocked:
            self.fail(f"pilot blocked: {self.blocked}")

    def _result(self):
        self._ready()
        if self.mismatch is not None:
            r = self.mismatch
            self.fail(f"kernels disagree on target-go; replay bundle: {r.replay_path}; "
                      f"python={r.python.operational_failure!r} souffle={r.souffle.operational_failure!r} "
                      f"{r.souffle.message[:600]}")
        return self.result

    def _archived_line(self, spec: tuple[str, int, str]) -> str:
        path, line, _ = spec
        return (self.archive / path).read_text(encoding="utf-8").splitlines()[line - 1]

    # -- tests ---------------------------------------------------------------

    def test_target_receipt_is_the_pinned_indexer_over_the_declared_module(self) -> None:
        self._ready()
        meta = self.normalized["metadata"]
        self.assertEqual(meta.get("tool_name"), "scip-go")
        self.assertEqual(meta.get("tool_version"), self.tools["scip-go"]["version"])
        for name in ("scip-go", "scip", "go"):
            self.assertTrue(self.tools[name]["path"].startswith("/nix/store/"), self.tools[name])
        self.assertEqual(self.checkout.module_path, MODULE)
        self.assertRegex(self.checkout.head, r"^[0-9a-f]{40}$")
        self.assertRegex(self.index_sha256, r"^[0-9a-f]{64}$")
        self.assertEqual(self.meta["index_file_digest"], self.index_sha256)
        self.assertEqual(self.meta["index_file_digest_kind"], "binary")
        self.assertEqual(self.meta["index_digest_kind"], scip_facts.INDEX_IDENTITY)
        self.assertEqual(self.meta["commit"], self.checkout.head)
        self.assertEqual(_rows(self.exported.bundle, "scip_index_commit"), [[self.index, self.checkout.head]])
        # every rooted symbol defined in this index lives under the go.mod module path
        self.assertEqual(pilot.module_prefix_violations(self.exported.bundle, MODULE), [])
        self.assertTrue(all(record.id.split(":")[1] == self.index[:12] for record in self.exported.bundle.evidence))

    def test_router_lines_still_say_what_the_assumption_declares(self) -> None:
        self._ready()
        for spec in (ROUTE_REGISTRATION, HANDLER_DEFINITION, APP_MOUNT, APP_WIRING, SQL_SINK_SITE):
            with self.subTest(spec=spec):
                self.assertIn(spec[2], self._archived_line(spec))
        self.assertIn('"GET /api/cloud/notification-unsubscribe/"', self._archived_line(ROUTE_REGISTRATION))
        [record] = self.assumption.evidence
        self.assertEqual(record.kind, "assumption")
        self.assertTrue(record.source.startswith("human-declared from router source: internal/pilot/runtime.go:209"))
        self.assertEqual(record.id.split(":")[:3], ["static", self.index[:12], pilot.ROUTE_HANDLER_ASSUMPTION])
        # the handler symbol is a callable the index defines at the declared line
        definitions = {(p, l): s for _, p, l, s in _rows(self.exported.bundle, "scip_definition_site")}
        self.assertEqual(definitions.get((HANDLER_DEFINITION[0], HANDLER_DEFINITION[1])), HANDLER)
        self.assertNotIn("route_site", self.exported.counts)
        self.assertNotIn("route_handler_location", self.exported.counts)
        self.assertNotIn("static_op_site", self.exported.counts)

    def test_slice_is_the_handler_package_closure_within_limits(self) -> None:
        self._ready()
        self.assertEqual(self.exported.status, scip_facts.STATUS_COMPLETE)
        self.assertIn(HANDLER_PACKAGE, self.closure.packages)
        self.assertIn(f"{MODULE}/internal/legacyissues", self.closure.packages)
        self.assertTrue(all(pkg.startswith(MODULE) for pkg in self.closure.packages))
        self.assertTrue(all(not p.endswith("_test.go") for p in self.closure.documents))
        self.assertLessEqual(len(self.closure.documents), LIMITS.documents)
        self.assertLessEqual(self.closure.occurrences, LIMITS.occurrences)
        self.assertLessEqual(len(self.exported.bundle.facts), LIMITS.rows)
        self.assertEqual(sorted(self.meta["in_scope_documents"]), list(self.closure.documents))
        scope = dict(self.meta["scope"])
        self.assertEqual((scope["kind"], list(scope["values"])),
                         (scip_facts.SCOPE_DOCUMENT_SET, list(self.closure.documents)))
        self.assertEqual(self.meta["profile"], scip_facts.PROFILE_SLICE)
        go_files = sorted(str(p.relative_to(self.archive)) for p in self.archive.rglob("*.go"))
        self.assertEqual(self.exported.counts["static_source_file"], len(go_files))
        # scip-go emits Go's generated _testmain.go for each pkg.test package it
        # loads, read out of GOCACHE with a path escaping the tree; the exporter
        # keeps those out of every fact (their path is a per-run value) and
        # records them as a receipt.  One per .test package in the index.
        out_of_tree = [dict(entry) for entry in self.meta["out_of_tree_documents"]]
        test_packages = {pkg for pkg in pilot.document_packages(self.normalized).values()
                         if pkg and pkg.endswith(".test")}
        self.assertEqual(len(out_of_tree), len(test_packages))
        self.assertGreater(len(out_of_tree), 0)
        self.assertTrue(all(entry["basename"].endswith("-d") for entry in out_of_tree), out_of_tree)
        self.assertEqual(self.exported.counts["scip_document"],
                         len(self.normalized["documents"]) - len(out_of_tree))
        document_paths = [p for _, p, *_ in _rows(self.exported.bundle, "scip_document")]
        self.assertTrue(all(not p.startswith(("../", "/")) and "/../" not in p for p in document_paths))
        self.assertTrue(set(document_paths) <= set(go_files))
        # scip-go leaves build-tagged test files out; no production file is unindexed
        self.assertTrue(all(p.endswith("_test.go") for p in self.receipt["export"]["unindexed_files"]),
                        self.receipt["export"]["unindexed_files"])
        self.assertIn("static_scope_closed", self.exported.counts, "an in-slice edge landed outside the slice")
        self.assertNotIn("static_scope_leak", self.exported.counts)
        self.assertFalse(self.meta["census_available"], "no tree-sitter census was taken for target-go")
        self.assertNotIn("scip_references_closed", self.exported.counts)
        self.assertNotIn("static_reachability_closed", self.exported.counts)

    def test_kernels_agree_on_every_relation_and_claim(self) -> None:
        result = self._result()
        self.assertTrue(result.matched)
        self.assertIsNone(result.python.operational_failure)
        self.assertIsNone(result.souffle.operational_failure)
        self.assertEqual(result.python.canonical_digest, result.souffle.canonical_digest)
        self.assertEqual(dict(result.python.relations), dict(result.souffle.relations))
        self.assertEqual(result.python.claims, result.souffle.claims)

    def test_route_reaches_the_sql_sink_with_identical_certificates_from_both_closures(self) -> None:
        result = self._result()
        for report in (result.python, result.souffle):
            with self.subTest(kernel=report.backend):
                verdicts = {c.key: c.semantic for c in report.claims}
                self.assertEqual(verdicts[CLAIM_FIRST_PARTY], "supported")
                self.assertEqual(verdicts[CLAIM_SQL], "supported")
        relations = dict(result.python.relations)
        self.assertEqual(set(relations["static_route_handler"]), {(self.index, SURFACE, HANDLER)})
        self.assertEqual(set(relations["static_root"]), {(self.index, HANDLER)})
        self.assertIn((self.index, HANDLER, CHANGE_SUBSCRIPTION), set(relations["static_edge"]))
        self.assertIn((self.index, CHANGE_SUBSCRIPTION, self.sql_begin_tx), set(relations["static_edge"]))
        self.assertIn((self.index, CHANGE_SUBSCRIPTION, self.sql_tx_exec), set(relations["static_edge"]))
        self.assertEqual(set(relations["static_index_current"]), {(self.index,)})
        self.assertEqual(relations["scip_index_stale"], ())
        for claim in self.claims:
            if claim.id not in CERTIFIED_CLAIMS:
                continue
            with self.subTest(claim=claim.id):
                rows = claim_conclusions(self.bundle, relations, claim)
                self.assertEqual(len(rows), 1)
                from_python = certify(self.bundle, relations, claim.relation, rows[0])
                from_souffle = certify(self.bundle, dict(result.souffle.relations), claim.relation, rows[0])
                self.assertEqual(from_python, from_souffle)
                self.assertFalse(from_python["truncated"])
                self.assertTrue(recheck(self.bundle, from_python, relations).ok)
                self.assertTrue(recheck(self.bundle, from_souffle, dict(result.souffle.relations)).ok)
                runtime_claims = {CLAIM_RUNTIME_SQL, CLAIM_RUNTIME_CAUSAL_SQL}
                allowed = ("scip:", "static:", "runtime:") if claim.id in runtime_claims else ("scip:", "static:")
                self.assertTrue(all(leaf.startswith(allowed) for leaf in from_python["leaves"]))
                if claim.id not in runtime_claims:
                    self.assertIn(self.assumption.evidence[0].id, from_python["leaves"])
                self.assertEqual(json.loads((self.out_dir / f"certificate-{claim.id}.json").read_text()), from_python)
        # the derived path, as a symbol chain
        self.assertEqual(self.receipt["path"][CLAIM_FIRST_PARTY], [[HANDLER, CHANGE_SUBSCRIPTION]])
        self.assertEqual(self.receipt["path"][CLAIM_SQL],
                         [[HANDLER, CHANGE_SUBSCRIPTION], [CHANGE_SUBSCRIPTION, self.sql_tx_exec]])
        self.assertEqual(self.receipt["certificates"][CLAIM_SQL]["steps"], 1)

    @unittest.skipUnless(RUNTIME_RECEIPT_PATH, "needs CAPCOV_TARGET_GO_RUNTIME_RECEIPT")
    def test_runtime_receipt_joins_the_index_and_terminal_sql_in_both_kernels(self) -> None:
        result = self._result()
        expected = (self.index, self.runtime_receipt["tenant"], SURFACE,
                    self.runtime_receipt["run"])
        causal = (self.index, self.runtime_receipt["run"], self.runtime_receipt["request_id"], SURFACE,
                  "git.internal.example/org/target-go/internal/legacyissues.ChangeSubscription",
                  "change-subscription", "cancel-notification-confirmation")
        for report in (result.python, result.souffle):
            with self.subTest(kernel=report.backend):
                claims = {claim.key: claim for claim in report.claims}
                self.assertEqual(claims[CLAIM_RUNTIME_SQL].semantic, "supported")
                self.assertEqual(claims[CLAIM_RUNTIME_CAUSAL_SQL].semantic, "supported")
                self.assertIn(expected, set(dict(report.relations)["runtime_route_observed_on_index"]))
                self.assertIn(causal, set(dict(report.relations)["runtime_route_reaches_sql_on_index"]))
                self.assertIn((self.index, self.runtime_receipt["run"]),
                              set(dict(report.relations)["index_describes_run"]))
        claim = next(claim for claim in self.claims if claim.id == CLAIM_RUNTIME_SQL)
        rows = claim_conclusions(self.bundle, dict(result.python.relations), claim)
        certificate = certify(self.bundle, dict(result.python.relations), claim.relation, rows[0])
        self.assertTrue(any(leaf.startswith("runtime:") for leaf in certificate["leaves"]))
        self.assertTrue(any(":index_describes_run:" in leaf for leaf in certificate["leaves"]))
        self.assertTrue(recheck(self.bundle, certificate, dict(result.souffle.relations)).ok)
        causal_claim = next(claim for claim in self.claims if claim.id == CLAIM_RUNTIME_CAUSAL_SQL)
        rows = claim_conclusions(self.bundle, dict(result.python.relations), causal_claim)
        certificate = certify(self.bundle, dict(result.python.relations), causal_claim.relation, rows[0])
        leaf_relations = {leaf.split(":")[2] for leaf in certificate["leaves"] if leaf.startswith("runtime:")}
        self.assertTrue({"runtime_route_observed", "runtime_function_entered", "runtime_sql_executed",
                         "runtime_tx_committed", "runtime_route_completed"}
                        <= leaf_relations)
        self.assertTrue(any(":index_describes_run:" in leaf for leaf in certificate["leaves"]))
        self.assertTrue(recheck(self.bundle, certificate, dict(result.souffle.relations)).ok)

    def test_negative_control_is_unresolved_never_refuted(self) -> None:
        result = self._result()
        for report in (result.python, result.souffle):
            with self.subTest(kernel=report.backend):
                [control] = [c for c in report.claims if c.key == CONTROL]
                self.assertEqual(control.semantic, "unresolved")
                self.assertNotEqual(control.semantic, "refuted")
                self.assertEqual(control.operational, "complete")
                self.assertTrue(control.missing_premises)
        relations = dict(result.python.relations)
        self.assertNotIn((self.index, HANDLER, SEND_DUE_DIGESTS), set(relations["static_reaches"]))
        # ... and it can never be refuted here: no call-graph completeness witness exists
        self.assertEqual(relations["static_reachability_closed"], ())
        self.assertEqual(relations["scip_references_closed"], ())

    def test_coverage_and_outcome_are_recorded(self) -> None:
        result = self._result()
        coverage = self.receipt["coverage"]
        self.assertEqual(coverage["total_edges"], self.exported.counts["scip_may_reference"])
        self.assertEqual(coverage["rooted_edges"] + sum(
            1 for _, c, d, *_ in _rows(self.exported.bundle, "scip_may_reference")
            if c in self.coverage.unrooted or d in self.coverage.unrooted), coverage["total_edges"])
        self.assertEqual(coverage["unrooted_symbols"], self.exported.counts.get("scip_symbol_unrooted", 0))
        self.assertGreater(coverage["route_closure_symbols"], 1)
        self.assertEqual(coverage["deep_unresolved"], 0)
        outcome = self.receipt["outcome"]
        self.assertIn(outcome, (pilot.OUTCOME_SUPPORTED, pilot.OUTCOME_UNKNOWN))
        if coverage["ratio"] < pilot.COVERAGE_THRESHOLD or coverage["unrooted_on_route_closure"]:
            self.assertEqual(outcome, pilot.OUTCOME_UNKNOWN, self.receipt["outcome_reasons"])
            self.assertTrue(self.receipt["outcome_reasons"])
        else:
            self.assertEqual(outcome, pilot.OUTCOME_SUPPORTED, self.receipt["outcome_reasons"])
            self.assertEqual(self.receipt["outcome_reasons"], [])
        self.assertEqual(self.receipt["kernels"]["matched"], result.matched)
        if self.runtime_receipt:
            self.assertEqual(self.receipt["runtime_join"]["run"], self.runtime_receipt["run"])
            self.assertEqual(self.exported.counts["index_describes_run"], 1)
        else:
            self.assertEqual(self.receipt["runtime_join"].split(":")[0], "none")
            self.assertNotIn("index_describes_run", self.exported.counts)

    def test_identity_is_pinned_when_the_committed_receipt_names_this_head(self) -> None:
        self._ready()
        if not COMMITTED_RECEIPT.exists():
            self.fail(f"no committed receipt at {COMMITTED_RECEIPT}")
        committed = json.loads(COMMITTED_RECEIPT.read_text(encoding="utf-8"))
        same_run_inputs = (committed["target"]["head"] == self.checkout.head
                           and committed["tools"]["scip-go"]["version"] == self.tools["scip-go"]["version"]
                           and committed["tools"]["go"]["version"] == self.tools["go"]["version"])
        if not same_run_inputs:
            print(f"\ncommitted receipt is for target-go {committed['target']['head'][:12]} / "
                  f"scip-go {committed['tools']['scip-go']['version']}; this run is "
                  f"{self.checkout.head[:12]} / {self.tools['scip-go']['version']}: identity not compared")
            return
        # the static-relations-v1 identity and the receipt-free bundle digest are
        # functions of the archived tree and the indexer, not of this run
        self.assertEqual(self.receipt["export"]["index_identity"], committed["export"]["index_identity"])
        if self.checkout.head in PINNED_IDENTITY:
            self.assertEqual(self.receipt["export"]["index_identity"], PINNED_IDENTITY[self.checkout.head])
        self.assertEqual(self.receipt["export"]["exported_bundle_digest"], committed["export"]["exported_bundle_digest"])
        self.assertEqual(self.receipt["export"]["row_counts"], committed["export"]["row_counts"])
        self.assertEqual(self.receipt["combined"]["bundle_digest"], committed["combined"]["bundle_digest"])
        self.assertEqual(self.receipt["kernels"]["python_digest"], committed["kernels"]["python_digest"])
        # certificates bind to the exact bundle (receipt included); their derivations do not
        run_independent = lambda entries: {claim: {k: v for k, v in entry.items() if k != "sha256"}  # noqa: E731
                                           for claim, entry in entries.items()}
        self.assertEqual(run_independent(self.receipt["certificates"]), run_independent(committed["certificates"]))
        self.assertNotEqual(self.receipt["combined"]["ir_digest"], committed["combined"]["ir_digest"],
                            "the plain IR digest sees the index-file receipt and must differ between indexings")

    def test_artifacts_carry_no_target_go_source(self) -> None:
        self._ready()
        written = sorted(p.name for p in self.out_dir.iterdir())
        self.assertIn("receipt.json", written)
        self.assertTrue(all(name.endswith(".json") for name in written), written)
        text = "\n".join((self.out_dir / name).read_text(encoding="utf-8") for name in written)
        self.assertNotIn("package pilot", text)
        self.assertNotIn("func (r *Runtime)", text)
        self.assertNotIn(str(self.archive), canonical_json(self.bundle))
        # no fact or metadata names the Go caches (the _testmain.go documents are
        # gone from the facts and recorded by basename only)
        for needle in (self.go_env["GOCACHE"], self.go_env["GOMODCACHE"], "gocache", "gomodcache"):
            self.assertNotIn(needle, canonical_json(self.bundle))
        self.assertNotIn("../", canonical_json(self.exported.bundle))


if __name__ == "__main__":
    unittest.main()
