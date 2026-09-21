"""The incumbent edge producer, and the store-parity precheck it makes possible.

Five properties, one per section.

1. **The two packs are layers, not forks.**  ``rules-static-phpstan-v1`` adds one
   primitive (``phpstan_call_edge``) and one rule (its lift into ``static_edge``);
   ``rules-static-parity-v1`` adds the reviewer's operation map and the verdicts
   it licenses.  Every declaration either pack borrows is its owner's, byte for
   byte -- including the two the closure layer owns, whose ``producer_classes``
   this unit widens from ``["scip"]`` to ``["phpstan", "scip"]`` in all three
   packs that declare them.  Widening is the point: two producers can know that
   a call graph is closed, and no third.

2. **A PHPStan report becomes the same rows a SCIP index does.**  On
   ``tests/fixtures/php_app`` -- a Laravel-shaped controller, an Eloquent read
   and write, a ``DB::`` facade with a literal table, and one ``__call`` magic
   site -- the *unchanged* ``rules-static-v1`` derives ``static_edge``,
   ``static_route_handler`` and ``static_capability_op``, and the unchanged
   closure pack derives ``static_route_reaches_table``.  Every row is classed
   ``phpstan``, and every edge carries the resolution kind that produced it, so
   a facade assumption is never read as a typed call.

3. **The witness is withheld for exactly the magic site.**  ``call_graph_closed``
   fires for a scope if and only if the report enumerated its files and none of
   them carries an unresolved site.  The ``*`` token is withheld for the one
   ``__call``; a ``document_set`` scope closes the other seven documents one at
   a time; drop the magic site and ``*`` closes.

4. **Parity is a join, and the join is licensed.**  One reviewer map, two
   indexes in one bundle: the tables both sides reach converge, the table only
   the incumbent reaches is claimed *only* under the candidate's own closure,
   and with residue in the candidate that claim becomes ``parity_blocked`` --
   naming the symbol the doubt enters through -- and ``parity_unresolved``.  An
   incumbent route a **closed** map omits is named; an open map names nothing.

5. **The recorded report is a contract until a real PHPStan runs.**  PHPStan is
   not in the devShell, so ``phpstan/report.json`` is authored against the
   collector's contract.  ``PhpstanLiveReportTest`` runs the bundled
   configuration against the fixture and asserts the committed facts are what
   comes back; it skips **by name** when ``phpstan`` is not on ``PATH`` and
   never skips to green when it is.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from capcov.claims import validate_bundle
from capcov.claims.evaluator import evaluate
from capcov.claims.ir import Bundle
from capcov.claims.static import (closure, parity, phpstan_facts, pilot, reflexion,
                                  scip_facts)
from capcov.scip import runner

try:
    from .static_rules import go_app
    from .static_rules.adapter import pack_bundle, read_json
except ImportError:  # unittest discover -s imports this directory as top-level
    from static_rules import go_app
    from static_rules.adapter import pack_bundle, read_json

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
STATIC = PACKAGE_ROOT / "src" / "capcov" / "claims" / "static"
PHP_APP = PACKAGE_ROOT / "tests" / "fixtures" / "php_app"
REPORT = PHP_APP / "phpstan" / "report.json"
NEON = PACKAGE_ROOT / "phpstan" / "phpstan-capcov.neon"
COLLECTOR = PACKAGE_ROOT / "phpstan" / "CapcovCallCollector.php"

#: The fixture's one magic site: `$this->bridge->purge($id)` on a class whose
#: only method is `__call`.  PHPStan types the receiver and not the method.
MAGIC_SITE = ("app/Support/LegacyGateway.php", 20)
#: The incumbent's route the map covers, and the one it leaves out.
SURFACE = "http:GET /jobs/{id}"
UNMAPPED_SURFACE = "http:GET /jobs"
OPERATION = "job.show"
#: The store only the incumbent reaches: the facade names it as a literal and
#: the Go candidate has no such table.
INCUMBENT_ONLY_TABLE = "audit_trail"
#: One unresolved call site in the candidate, the closure test's own.
CANDIDATE_RESIDUE = [{"file": "internal/service/service.go", "line": 12,
                      "callee": "h.dispatch", "kind": "unresolved"}]
#: The candidate symbol that residue sits on.
CANDIDATE_VIA = ("scip-go gomod github.com/example/jobsvc . "
                 "`github.com/example/jobsvc/internal/service`/Service#Fetch().")
ANALYSER_VERSION = "2.1.17"

_HAVE_SOUFFLE = shutil.which(os.environ.get("SOUFFLE") or "souffle") is not None
_PHPSTAN = shutil.which("phpstan")


def _facts(drop_magic: bool = False) -> tuple[dict, ...]:
    facts = phpstan_facts.load_report(REPORT)
    if not drop_magic:
        return facts
    return tuple(fact for fact in facts
                 if not (fact["fact"] == "unresolved"
                         and (fact["path"], fact["line"]) == MAGIC_SITE))


def _incumbent(facts=None, scope=None):
    facts = _facts() if facts is None else facts
    result = phpstan_facts.export_bundle(
        facts, source_root=PHP_APP, analyser_version=ANALYSER_VERSION, scope=scope,
        observe_tree=True)
    assert result.status == phpstan_facts.STATUS_COMPLETE, result.messages
    return result


def _incumbent_bundle(facts=None, scope=None, packs: bool = True):
    facts = _facts() if facts is None else facts
    export = _incumbent(facts, scope).bundle
    extra = (phpstan_facts.pack_bundle(), pack_bundle()) if packs else ()
    return phpstan_facts.attach(export, facts, *extra)


def _candidate(residue=()) -> tuple[Bundle, list[Bundle]]:
    """The go_app SCIP export, its closure fragment and its tree observation."""
    raw = go_app.golden_raw()
    ast = go_app.ast_raw()
    ast["scip_residue"] = [dict(entry) for entry in residue]
    result = scip_facts.export_bundle(
        go_app.normalized(raw), ast_raw=ast, source_root=go_app.GO_APP, language="go",
        index_digest=go_app.json_file_digest(raw), index_digest_kind=runner.INDEX_DIGEST_JSON)
    assert result.status == scip_facts.STATUS_COMPLETE, result.messages
    tree = dict(dict(result.bundle.metadata)["tree"])["digest"]
    atom, record = pilot.source_tree_observation(
        {decl.name: decl for decl in result.bundle.relations}, tree)
    observed = Bundle(result.bundle.relations, facts=(atom,), evidence=(record,))
    return result.bundle, [closure.closure_bundle(result.bundle, ast), observed]


def _model(closed: bool = True, operations=None) -> parity.OperationMap:
    document = {"schema_version": 1,
                "operations": operations or {OPERATION: [SURFACE, SURFACE]}}
    if closed:
        document["closed"] = True
    return parity.model_from_document(document)


def _parity_bundle(*, residue=(), model=None, facts=None):
    facts = _facts() if facts is None else facts
    incumbent = _incumbent(facts).bundle
    candidate, extras = _candidate(residue)
    return parity.attach(incumbent, candidate, model if model is not None else _model(),
                         phpstan_facts.closure_fragment(incumbent, facts), *extras,
                         phpstan_facts.pack_bundle(), pack_bundle(), reflexion.pack_bundle())


def _derived(bundle: Bundle) -> dict[str, list[list]]:
    report = evaluate(bundle)
    assert report.status.value == "complete", report.message
    return {name: sorted(list(row) for row in rows) for name, rows in report.relations}


def _payload(relations: dict[str, list[list]], name: str) -> list[list]:
    """The rows of ``name`` with the index/context column dropped."""
    return sorted(row[1:] for row in relations.get(name, ()))


def _rows(bundle: Bundle, relation: str) -> list[list]:
    return sorted([term.value for term in fact.terms][1:]
                  for fact in bundle.facts if fact.relation == relation)


class PacksAreLayersTests(unittest.TestCase):
    def test_both_packs_validate_alone(self) -> None:
        self.assertEqual(validate_bundle(phpstan_facts.pack_bundle()), ())
        self.assertEqual(validate_bundle(parity.pack_bundle()), ())

    def test_the_borrowed_declarations_are_their_owners_declarations(self) -> None:
        owners: dict[str, dict] = {}
        for pack in (read_json(PACKAGE_ROOT / "experiments" / "claim-semantics" / "static"
                               / "rules-static-v1.json"),
                     closure.load_pack(), reflexion.load_pack()):
            for section in ("primitives", "supplementary_primitives", "derived"):
                for item in pack.get(section, []):
                    owners.setdefault(item["name"], item)
        for pack in (phpstan_facts.load_pack(), parity.load_pack()):
            for item in pack["borrowed_declarations"]:
                with self.subTest(pack=pack["id"], relation=item["name"]):
                    self.assertIn(item["name"], owners)
                    self.assertEqual(item, owners[item["name"]])

    def test_the_closure_relations_admit_both_producers_in_every_pack(self) -> None:
        """Two producers can know a call graph is closed; a third cannot say so."""
        seen = 0
        for pack in (closure.load_pack(), reflexion.load_pack(),
                     json.loads((STATIC / "rules-static-cha-v1.json").read_text()),
                     parity.load_pack()):
            for section in ("primitives", "borrowed_declarations", "derived"):
                for item in pack.get(section, []):
                    if item["name"] in (closure.UNRESOLVED_RELATION, closure.CLOSED_RELATION):
                        self.assertEqual(item["producer_classes"], ["phpstan", "scip"],
                                         f"{pack['id']}.{item['name']}")
                        seen += 1
        self.assertGreaterEqual(seen, 5, "the widened declarations were not all found")

    def test_the_lift_is_the_only_rule_the_phpstan_pack_adds(self) -> None:
        pack = phpstan_facts.load_pack()
        self.assertEqual([rule["head"]["relation"] for rule in pack["rules"]], ["static_edge"])
        self.assertEqual([item["name"] for item in pack["primitives"]],
                         [phpstan_facts.EDGE_RELATION])

    def test_the_edge_relation_carries_the_resolution_kind(self) -> None:
        [edge] = [item for item in phpstan_facts.load_pack()["primitives"]
                  if item["name"] == phpstan_facts.EDGE_RELATION]
        self.assertEqual(edge["producer_classes"], ["phpstan"])
        self.assertIn("kind", [column["name"] for column in edge["columns"]])

    def test_the_parity_witness_names_what_it_licenses(self) -> None:
        """The cross-index join is licensed by one compatibility witness, by name."""
        [witness] = [item for item in parity.load_pack()["primitives"]
                     if item["name"] == parity.DESCRIBES_RELATION]
        self.assertEqual(witness["modality"], "compatibility")
        self.assertEqual(witness["compatibility_context_indices"], ["incumbent", "candidate"])
        self.assertIn("static_route_reaches_table", witness["compatibility_targets"])
        self.assertEqual(witness["producer_classes"], ["reviewer"])


class TheReportBecomesTheSameRowsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.facts = _facts()
        self.export = _incumbent(self.facts).bundle

    def test_messages_that_are_not_the_collectors_are_ignored(self) -> None:
        document = json.loads(REPORT.read_text(encoding="utf-8"))
        noisy = {"files": {**document["files"], "app/Models/Job.php": {
            "errors": 1,
            "messages": [{"message": "Access to an undefined property.", "line": 7}]}}}
        self.assertEqual(len(phpstan_facts.read_report(noisy)),
                         len(phpstan_facts.read_report(document))
                         - len([f for f in self.facts
                                if f["path"] == "app/Models/Job.php"]))

    def test_the_unchanged_packs_derive_the_capability(self) -> None:
        relations = _derived(_incumbent_bundle(self.facts))
        self.assertEqual(_payload(relations, "static_route_handler"),
                         [[UNMAPPED_SURFACE, "App\\Http\\Controllers\\JobController::listJobs"],
                          [SURFACE, "App\\Http\\Controllers\\JobController::getJob"]])
        self.assertEqual(
            _payload(relations, "static_capability_op"),
            [[SURFACE, "App\\Models\\AuditLog", "create"],
             [SURFACE, "App\\Models\\Job", "read"],
             [SURFACE, INCUMBENT_ONLY_TABLE, "create"]])
        self.assertEqual(_payload(relations, "static_route_reaches_table"),
                         [[SURFACE, "audit_logs"], [SURFACE, INCUMBENT_ONLY_TABLE],
                          [SURFACE, "jobs"]])

    def test_the_facade_chain_is_resolved_and_labelled_an_assumption(self) -> None:
        """scip-php's blind spot, typed -- and never passed off as a typed call."""
        kinds = {(row[1], row[4]) for row in _rows(self.export, phpstan_facts.EDGE_RELATION)}
        self.assertIn(("Illuminate\\Database\\Query\\Builder::insert",
                       phpstan_facts.KIND_FACADE), kinds)
        self.assertIn(("Illuminate\\Database\\Eloquent\\Builder::where",
                       phpstan_facts.KIND_MODEL_FORWARD), kinds)
        self.assertIn(("App\\Repositories\\JobRepository::get", phpstan_facts.KIND_DIRECT), kinds)
        for _callee, kind in kinds:
            self.assertIn(kind, phpstan_facts.EDGE_KINDS)

    def test_the_magic_site_is_enumerated_with_its_reason(self) -> None:
        self.assertEqual([row[:2] for row in _rows(self.export, "scip_unresolved_site")],
                         [list(MAGIC_SITE)])
        [site] = _rows(self.export, "scip_unresolved_site")
        self.assertEqual(site[3], phpstan_facts.REASON_MAGIC)

    def test_every_emitted_row_is_attributed_to_this_producer(self) -> None:
        self.assertTrue(self.export.evidence)
        for record in self.export.evidence:
            if record.atom.relation == "source_tree_observed":
                continue  # the claim-time observation, named as such
            with self.subTest(evidence=record.id):
                self.assertEqual(record.source.split(" ", 1)[0], phpstan_facts.PRODUCER_CLASS)
                self.assertTrue(record.depends_on,
                                "a row with no provenance is not evidence")

    def test_an_unknown_resolution_kind_is_refused_rather_than_read_as_direct(self) -> None:
        facts = [dict(fact, kind="larastan-telepathy") if fact["fact"] == "call" else fact
                 for fact in self.facts]
        result = phpstan_facts.export_bundle(facts, source_root=PHP_APP,
                                             analyser_version=ANALYSER_VERSION)
        self.assertEqual(result.status, phpstan_facts.STATUS_INVALID_INPUT)
        self.assertIn("larastan-telepathy", result.messages[0])

    def test_a_report_of_another_tree_is_refused(self) -> None:
        facts = (*self.facts, {"fact": "analysed", "path": "app/Nothing.php"})
        result = phpstan_facts.export_bundle(facts, source_root=PHP_APP,
                                             analyser_version=ANALYSER_VERSION)
        self.assertEqual(result.status, phpstan_facts.STATUS_INVALID_INPUT)
        self.assertIn("app/Nothing.php", result.messages[0])

    def test_the_identity_is_the_content_and_the_report_digest_is_a_receipt(self) -> None:
        again = _incumbent(tuple(reversed(self.facts))).bundle
        self.assertEqual(dict(self.export.metadata)["index_digest"],
                         dict(again.metadata)["index_digest"])
        self.assertEqual(scip_facts.bundle_digest(self.export), scip_facts.bundle_digest(again))
        self.assertEqual(dict(self.export.metadata)["index_file_digest"],
                         phpstan_facts.report_digest(self.facts))

    def test_the_analyser_version_is_part_of_the_identity(self) -> None:
        other = phpstan_facts.export_bundle(self.facts, source_root=PHP_APP,
                                            analyser_version="1.10.0", observe_tree=True)
        self.assertNotEqual(dict(other.bundle.metadata)["index_digest"],
                            dict(self.export.metadata)["index_digest"])

    def test_a_report_naming_no_analysed_file_is_refused(self) -> None:
        result = phpstan_facts.export_bundle(
            [f for f in self.facts if f["fact"] != "analysed"], source_root=PHP_APP,
            analyser_version=ANALYSER_VERSION)
        self.assertEqual(result.status, phpstan_facts.STATUS_INVALID_INPUT)
        self.assertIn("census", result.messages[0])


class TheWitnessIsWithheldForTheMagicSiteTests(unittest.TestCase):
    def test_the_whole_index_is_not_closed_while_one_call_is_magic(self) -> None:
        bundle = _incumbent_bundle(packs=False)
        self.assertEqual(_rows(bundle, closure.UNRESOLVED_RELATION),
                         [[MAGIC_SITE[0], MAGIC_SITE[1], "App\\Support\\LegacyBridge->purge"]])
        self.assertEqual(_rows(bundle, closure.CLOSED_RELATION), [])

    def test_dropping_the_magic_site_closes_the_index(self) -> None:
        bundle = _incumbent_bundle(_facts(drop_magic=True), packs=False)
        self.assertEqual(_rows(bundle, closure.CLOSED_RELATION), [[closure.SCOPE_TOKEN_ALL]])

    def test_a_document_set_scope_is_closed_one_document_at_a_time(self) -> None:
        facts = _facts()
        documents = sorted({fact["path"] for fact in facts if fact["fact"] == "analysed"})
        bundle = _incumbent_bundle(facts, scope=scip_facts.Scope.document_set(documents),
                                   packs=False)
        self.assertEqual([row[0] for row in _rows(bundle, closure.CLOSED_RELATION)],
                         [path for path in documents if path != MAGIC_SITE[0]])

    def test_the_witness_and_the_residue_carry_this_producers_class(self) -> None:
        bundle = _incumbent_bundle(_facts(drop_magic=True), packs=False)
        emitted = [record for record in bundle.evidence
                   if record.atom.relation in (closure.UNRESOLVED_RELATION,
                                               closure.CLOSED_RELATION)]
        self.assertTrue(emitted)
        for record in emitted:
            with self.subTest(evidence=record.id):
                self.assertEqual(record.source.split(" ", 1)[0], phpstan_facts.PRODUCER_CLASS)

    def test_the_two_readings_of_the_census_agree(self) -> None:
        """The export's own unresolved rows and the closure fragment's are one census."""
        bundle = _incumbent_bundle(packs=False)
        self.assertEqual([row[:2] for row in _rows(bundle, "scip_unresolved_site")],
                         [row[:2] for row in _rows(bundle, closure.UNRESOLVED_RELATION)])

    def test_a_report_whose_census_omits_its_own_residue_is_refused(self) -> None:
        """The guard reads the census, so a residue row outside it would close the index."""
        facts = tuple(fact for fact in _facts()
                      if not (fact["fact"] == "analysed" and fact["path"] == MAGIC_SITE[0]))
        self.assertIn(MAGIC_SITE, [(path, line) for path, line, _callee
                                   in phpstan_facts.unresolved_rows(facts)],
                      "the magic site is still enumerated; it is the census that lost the file")
        result = phpstan_facts.export_bundle(facts, source_root=PHP_APP,
                                             analyser_version=ANALYSER_VERSION,
                                             observe_tree=True)
        self.assertEqual(result.status, phpstan_facts.STATUS_INVALID_INPUT)
        self.assertIn(MAGIC_SITE[0], result.messages[0])
        self.assertIsNone(result.bundle,
                          "no bundle may carry that residue row together with the witness")

    def test_a_fact_set_the_export_was_not_built_from_is_refused(self) -> None:
        """The witness is about the census the index was hashed from, or about nothing."""
        export = _incumbent().bundle
        other = _facts(drop_magic=True)
        with self.assertRaises(phpstan_facts.ReportInputError) as caught:
            phpstan_facts.closure_fragment(export, other)
        message = str(caught.exception)
        self.assertIn(str(dict(export.metadata)["index_file_digest"]), message)
        self.assertIn(phpstan_facts.report_digest(other), message)
        with self.assertRaises(phpstan_facts.ReportInputError):
            phpstan_facts.attach(export, other, phpstan_facts.pack_bundle())


class ParityIsALicensedJoinTests(unittest.TestCase):
    def test_both_sides_reaching_a_table_converges(self) -> None:
        relations = _derived(_parity_bundle())
        self.assertEqual(_payload(relations, "static_parity"),
                         [[OPERATION, "audit_logs"], [OPERATION, "jobs"]])

    def test_a_store_only_the_incumbent_reaches_is_claimed_under_closure(self) -> None:
        relations = _derived(_parity_bundle())
        self.assertEqual(_payload(relations, "parity_static_only_incumbent"),
                         [[OPERATION, INCUMBENT_ONLY_TABLE]])
        self.assertEqual(_payload(relations, "parity_blocked"), [])
        self.assertEqual(_payload(relations, "parity_unresolved"), [])

    def test_candidate_residue_turns_the_claim_into_a_named_doubt(self) -> None:
        relations = _derived(_parity_bundle(residue=CANDIDATE_RESIDUE))
        self.assertEqual(_payload(relations, "parity_static_only_incumbent"), [],
                         "an unresolved call site is exactly what closure may not assume away")
        self.assertEqual(_payload(relations, "parity_blocked"),
                         [[OPERATION, INCUMBENT_ONLY_TABLE, CANDIDATE_VIA]])
        self.assertEqual(_payload(relations, "parity_unresolved"),
                         [[OPERATION, INCUMBENT_ONLY_TABLE]])
        self.assertEqual(_payload(relations, "static_parity"),
                         [[OPERATION, "audit_logs"], [OPERATION, "jobs"]],
                         "residue withdraws negations, never positive reaches")

    def test_a_closed_map_names_the_route_it_does_not_cover(self) -> None:
        self.assertEqual(_payload(_derived(_parity_bundle()), "parity_route_unmapped"),
                         [[UNMAPPED_SURFACE]])

    def test_an_open_map_claims_nothing_about_what_it_omits(self) -> None:
        relations = _derived(_parity_bundle(model=_model(closed=False)))
        self.assertEqual(_payload(relations, "parity_route_unmapped"), [])
        self.assertEqual(_payload(relations, "parity_static_only_incumbent"),
                         [[OPERATION, INCUMBENT_ONLY_TABLE]],
                         "the map's closure gates its own negation, not the code's")

    def test_the_two_indexes_keep_their_own_identities(self) -> None:
        bundle = _parity_bundle()
        indexes = {fact.terms[0].value for fact in bundle.facts
                   if fact.relation == "scip_index"}
        self.assertEqual(len(indexes), 2)
        self.assertEqual(len({record.id for record in bundle.evidence}),
                         len(bundle.evidence))

    def test_a_route_neither_index_declares_is_refused_by_name(self) -> None:
        incumbent = _incumbent().bundle
        candidate, _extras = _candidate()
        model = _model(operations={OPERATION: [SURFACE, "http:GET /typo"]})
        with self.assertRaises(parity.ParityInputError) as caught:
            parity.map_bundle(incumbent, candidate, model)
        self.assertIn("http:GET /typo", str(caught.exception))
        self.assertIn("candidate", str(caught.exception))

    def test_one_index_is_not_a_parity(self) -> None:
        incumbent = _incumbent().bundle
        with self.assertRaises(parity.ParityInputError):
            parity.map_bundle(incumbent, incumbent, _model())

    def test_a_merge_without_the_reflexion_pack_is_refused_not_downgraded(self) -> None:
        """``parity_blocked`` with no rule would report the doubt as the weaker row."""
        facts = _facts()
        incumbent = _incumbent(facts).bundle
        candidate, extras = _candidate(CANDIDATE_RESIDUE)
        with self.assertRaises(parity.ParityInputError) as caught:
            parity.attach(incumbent, candidate, _model(),
                          phpstan_facts.closure_fragment(incumbent, facts), *extras,
                          phpstan_facts.pack_bundle(), pack_bundle())
        self.assertIn(parity.REFLEXION_PACK_ID, str(caught.exception))

    def test_the_map_rows_are_the_reviewers_and_name_the_document(self) -> None:
        bundle = _parity_bundle()
        model_digest = _model().digest
        emitted = [record for record in bundle.evidence
                   if record.atom.relation in (parity.MAP_RELATION, parity.MAP_CLOSED_RELATION,
                                               parity.DESCRIBES_RELATION)]
        self.assertEqual(len(emitted), 3)
        for record in emitted:
            with self.subTest(evidence=record.id):
                self.assertEqual(record.source.split(" ", 1)[0], parity.PRODUCER_CLASS)
                self.assertTrue(record.source.endswith(model_digest))

    @unittest.skipUnless(_HAVE_SOUFFLE, "needs the souffle executable")
    def test_both_kernels_agree_on_the_parity_verdicts(self) -> None:
        from capcov.claims.differential import compare

        with tempfile.TemporaryDirectory() as tmp:
            for label, residue in (("closed", ()), ("residue", CANDIDATE_RESIDUE)):
                with self.subTest(candidate=label):
                    result = compare(_parity_bundle(residue=residue),
                                     replay_root=str(Path(tmp) / label))
                    self.assertTrue(result.matched, result.replay_path)


class PhpstanLiveReportTest(unittest.TestCase):
    """The committed report is a contract; one real PHPStan run is what records it."""

    @unittest.skipUnless(_PHPSTAN, "needs phpstan on PATH (the devShell has none); "
                                   "the committed report is authored against the collector "
                                   "contract until this runs")
    def test_the_committed_report_is_what_phpstan_produces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            process = subprocess.run(
                [_PHPSTAN, "analyse", "-c", str(NEON), "--error-format=json",
                 "--no-progress", "app", "routes"],
                cwd=PHP_APP, capture_output=True, text=True, timeout=300,
                env={**os.environ, "TMPDIR": tmp})
        self.assertTrue(process.stdout.strip(), process.stderr[-2000:])
        live = phpstan_facts.read_report(json.loads(process.stdout))
        self.assertEqual(list(live), list(phpstan_facts.load_report(REPORT)))


class TheBundledCollectorTravelsWithThePackageTests(unittest.TestCase):
    def test_the_collector_and_its_configuration_are_in_the_repository(self) -> None:
        self.assertTrue(COLLECTOR.is_file())
        self.assertTrue(NEON.is_file())
        text = COLLECTOR.read_text(encoding="utf-8")
        self.assertIn(phpstan_facts.FACT_PREFIX, text,
                      "the collector and the reader must agree on the message prefix")
        for kind in phpstan_facts.EDGE_KINDS:
            self.assertIn(f"'{kind}'", text, f"the collector never emits {kind}")

    def test_the_packs_ship_as_package_data(self) -> None:
        from importlib import resources

        for name in (phpstan_facts.PACK_NAME, parity.PACK_NAME):
            resource = resources.files("capcov.claims.static").joinpath(name)
            self.assertEqual(json.loads(resource.read_text(encoding="utf-8"))["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
