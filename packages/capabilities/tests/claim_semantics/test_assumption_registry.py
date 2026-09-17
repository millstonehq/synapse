"""The assumption registry (A1/A2) and invalidation (A3) over the target-go replay join.

Assumption-kind evidence carries run-scoped ids, so "the same reviewed
assumption" is not expressible across two runs.  ``claims/assumptions.py``
gives each one a content-and-producer id, lists what it carries, and answers
what happens when it is withdrawn.  These cases run on the committed qualified
receipt fixture, so they need no replay environment -- only Soufflé, like the
rest of the receipt suite.

The fixture is staged with a **test-local synthetic Stage D certificate**
(``_with_synthetic_certificate``).  The committed real receipts carry none --
the typed checker has not been built, and a placeholder there would be a
fabricated observation satisfying the gate ``op_qualified_rt`` imposes
(``tests/claim_semantics/README.md``) -- so without one every ``op_qualified``
here would be unresolved and there would be no supported claim whose
assumptions could be registered or withdrawn.  What this module asserts is the
*support structure* of a qualified claim, so it supplies the premise it is not
about, in a temporary copy, and says so.  Nothing it writes goes back into the
committed fixture.

Three results here are worth reading before changing an expectation, because
each one is a fact about the fixture's support structure rather than a choice:

1. The reviewer's scope exclusions are *not* leaves of ``op_qualified``.  They
   work by keeping a table out of ``undeclared_write``, and ``op_qualified``
   rests on ``undeclared_any`` being **absent**, so they carry only
   ``exclusion_applied``.  ``ground.impact`` reads positive leaves, so it
   cannot predict that withdrawing one unresolves ``op_qualified``: only the
   re-evaluation finds it, which is the point of the operation.
2. Withdrawing an exclusion moves the open ``undeclared_write`` claim from
   unresolved to *supported* -- the table the exclusion used to cover is now
   an undeclared write.  A drop is a missing premise, never a refutation, but
   it may legitimately reveal a row.
3. A certificate is bound to its bundle digest, so withdrawing *any* record --
   even one nothing rests on -- rewrites every certificate's ``bundle_digest``.
   The derivations are what stay identical.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from capcov.claims import Evidence, OutputTemplate, canonical_json
from capcov.claims import assumptions
from capcov.claims.assumptions import InvalidationError

try:
    from .target_go import replay_join
except ImportError:  # unittest discover -s imports this directory as top-level
    from target_go import replay_join

FIXTURE = replay_join.COMMITTED_RECEIPT_DIR
MODEL = "08380c9c336dc3f8e693aeea0589a60cfe808836a75bf2b815fa7cd8b39f0e7b"
#: The synthetic certificate this module stages (see the module docstring).  It is
#: the corpus fixture's placeholder pair, never a real checker's output.
SYNTHETIC_CHECKER = ("stage-d-typecheck", "0.1-pending")
SYNTHETIC_CERTIFICATE = hashlib.sha256(b"pending: checker not yet built").hexdigest()
QUALIFIED = "claim-qualified-delete-issue"
CONSTRAINS = "claim-corpus-constrains-delete-issue"
APPLIED = "claim-exclusions-applied-delete-issue"
UNDECLARED = "claim-undeclared-write-delete-issue"

#: Contract A1 is a published id: these are pinned so a change to the payload
#: (or to a reviewed row) has to be an explicit edit here, not a silent drift.
#: One id per exclusion of ``model_scope_exclusions.json`` against model 08380c9c.
PINNED_EXCLUSION_IDS = {
    "authentication": "asm:90415bcde921ad551e273f1e328b8bf4c24d00a2facc794688a3c336e1410992",
    "jobs_statuses": "asm:a9fb3a121eb54bcb8b6febe9bd2a892c6ad2c7e8e9303ceac4a1e8d3bc4e9f39",
    "redis": "asm:49642fc6067a1b2e2208d5f0a64e86d5c186c6c8ea0d7041cd3f6010e441dedc",
    "go_issue_outbox": "asm:19b263a1498799695ee58224a587617f3bd97db7623587d9f3edc3ce7fdaecb3",
}


def _with_synthetic_certificate(source: Path, destination: Path) -> Path:
    """Copy ``source`` and add the Stage D certificate the real receipt does not carry.

    The premise is positive and has no closure, so without it ``op_qualified``
    is unresolved on every real receipt and this module would have no supported
    claim to register assumptions for.  The certificate is made up, lives only
    in a temporary directory, and is never evidence about the port.
    """
    shutil.copytree(source, destination)
    return _add_synthetic_certificate(destination)


def _add_synthetic_certificate(destination: Path) -> Path:
    """Write the synthetic ``model_well_formed`` / ``model_checkers`` pair into a staged copy."""
    model = json.loads((destination / "receipt.json").read_text())["model"]
    checker, version = SYNTHETIC_CHECKER
    (destination / "model_well_formed.json").write_text(json.dumps(
        {"producer": f"modelcheck {checker} {version} model:{model[:12]}",
         "rows": [{"model": model, "checker": checker, "checker_version": version,
                   "certificate": SYNTHETIC_CERTIFICATE}]}, indent=1, sort_keys=True) + "\n")
    (destination / "model_checkers.json").write_text(json.dumps(
        {"producer": "reviewer synthetic test-local admitted model checkers",
         "rows": [{"checker": checker, "checker_version": version}]}, indent=1, sort_keys=True) + "\n")
    return destination


def _souffle() -> None:
    if shutil.which("souffle") is None:
        raise unittest.SkipTest("souffle must be on PATH: run inside the nix devShell")


class _EvaluatedFixture(unittest.TestCase):
    """One evaluated baseline join, shared by every case (both kernels run once)."""

    join = None
    replay_root = None

    @classmethod
    def setUpClass(cls) -> None:
        _souffle()
        cls.replay_root = tempfile.mkdtemp(prefix="capcov-assumption-registry-")
        cls.staged = Path(tempfile.mkdtemp(prefix="capcov-assumption-registry-receipt-"))
        cls.join = replay_join.build(_with_synthetic_certificate(FIXTURE, cls.staged / "receipt"))
        if cls.join.bundle is None:
            raise AssertionError("CONTRACT FINDING: " + "; ".join(cls.join.contract_findings))
        replay_join.evaluate_join(cls.join, cls.replay_root)
        if cls.join.mismatch is not None:
            raise AssertionError(f"kernels disagree; replay bundle: {cls.join.mismatch.replay_path}")
        cls.registry = replay_join.assumption_registry(cls.join)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.replay_root, ignore_errors=True)
        shutil.rmtree(cls.staged, ignore_errors=True)

    def entry(self, relation: str, key: str | None = None) -> dict:
        """The registry entry for a relation, optionally keyed by row[1] (a table or op)."""
        matches = [item for item in self.registry["assumptions"]
                   if item["relation"] == relation and (key is None or item["row"][1] == key)]
        self.assertEqual(len(matches), 1, f"{relation}/{key}: {len(matches)} entries")
        return matches[0]

    def record(self, relation: str, key: str | None = None) -> Evidence:
        matches = [r for r in assumptions.assumption_records(self.join.bundle)
                   if r.atom.relation == relation and (key is None or r.atom.terms[1].value == key)]
        self.assertEqual(len(matches), 1)
        return matches[0]


class IdStabilityTest(_EvaluatedFixture):
    """A1: the id is the producer class plus the row content, and nothing else."""

    def test_id_is_producer_plus_content(self) -> None:
        records = assumptions.assumption_records(self.join.bundle)
        self.assertEqual(len(records), 6)
        for record in records:
            producer = record.source.split(" ", 1)[0]
            row = [term.value for term in record.atom.terms]
            expected = "asm:" + hashlib.sha256(
                canonical_json([producer, record.atom.relation, row]).encode("utf-8")).hexdigest()
            self.assertEqual(assumptions.assumption_id(record), expected)
            self.assertEqual(assumptions.content_digest(record),
                             hashlib.sha256(canonical_json([record.atom.relation, row]).encode("utf-8")).hexdigest())

    def test_id_carries_no_run_scope(self) -> None:
        """The evidence id's replay segment must not appear in the assumption id."""
        replay12 = self.record("model_scope_exclusion", "authentication").id.split(":")[1]
        self.assertRegex(replay12, r"^[0-9a-f]{12}$")
        for record in assumptions.assumption_records(self.join.bundle):
            identifier = assumptions.assumption_id(record)
            self.assertNotIn(replay12, identifier)
            self.assertNotIn(self.join.run, identifier)
            self.assertRegex(identifier, r"^asm:[0-9a-f]{64}$")

    def test_two_builds_agree(self) -> None:
        """A second export of the same receipt registers the same ids."""
        other = replay_join.build(FIXTURE)
        self.assertIsNotNone(other.bundle)
        mine = sorted(assumptions.assumption_id(r) for r in assumptions.assumption_records(self.join.bundle))
        theirs = sorted(assumptions.assumption_id(r) for r in assumptions.assumption_records(other.bundle))
        self.assertEqual(mine, theirs)

    def test_exclusion_ids_are_pinned(self) -> None:
        """The reviewed rows against model 08380c9c keep the ids other runs must reproduce."""
        for table, pinned in PINNED_EXCLUSION_IDS.items():
            record = self.record("model_scope_exclusion", table)
            self.assertEqual(record.atom.terms[0].value, MODEL)
            self.assertEqual(assumptions.assumption_id(record), pinned)

    def test_review_provenance_is_parsed_and_excluded_from_the_id(self) -> None:
        """``reviewed_against`` keeps the reviewer and date the id deliberately drops."""
        entry = self.entry("model_scope_exclusion", "authentication")
        self.assertEqual(entry["reviewed_against"],
                         {"model": "08380c9c336d", "run": self.join.run,
                          "reviewed_at": "2026-09-16", "reviewer": "Reuben Brooks"})
        self.assertIsNone(self.entry("op_declared")["reviewed_against"],
                          "a claim-time assumption names no review")
        # a second reviewer signing the identical row lands on the identical id
        record = self.record("model_scope_exclusion", "authentication")
        twin = Evidence(id="reviewer:other:model_scope_exclusion:0", atom=record.atom,
                        source="reviewer A Nother 2027-01-02 model:08380c9c336d run:zzzzzzzzzzzz",
                        kind="assumption")
        self.assertEqual(assumptions.assumption_id(twin), assumptions.assumption_id(record))
        self.assertNotEqual(assumptions.reviewed_against(twin), entry["reviewed_against"])


class CrossRunIdStabilityTest(unittest.TestCase):
    """The point of A1: a second run of the same reviewed model keeps the same ids.

    A copy of the fixture receipt with a different run id is exported for real
    (the strict exporter accepts it), so this is the cross-run property itself
    and not a restatement of the hash.  Needs no kernel: export only.
    """

    OTHER_RUN = "abc123def456"

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="capcov-assumption-rerun-"))
        cls.directory = cls.tmp / "rerun"
        shutil.copytree(FIXTURE, cls.directory)
        cls.baseline = replay_join.build(FIXTURE)
        # rglob, not iterdir: the learn campaign's rows are scoped to the replay run too,
        # and a learn row naming another run is stale exactly like any other row
        for path in sorted(cls.directory.rglob("*.json")):
            path.write_text(path.read_text(encoding="utf-8").replace(cls.baseline.run, cls.OTHER_RUN),
                            encoding="utf-8")
        cls.join = replay_join.build(cls.directory)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _ids(self, join) -> dict[tuple[str, str], str]:
        out = {}
        for record in assumptions.assumption_records(join.bundle):
            row = [term.value for term in record.atom.terms]
            out[(record.atom.relation, row[1])] = assumptions.assumption_id(record)
        return out

    def test_the_second_run_exports(self) -> None:
        self.assertEqual(self.join.contract_findings, [])
        self.assertIsNotNone(self.join.bundle)
        self.assertEqual(self.join.run, self.OTHER_RUN)
        self.assertNotEqual(self.join.run, self.baseline.run)

    def test_reviewed_exclusions_keep_their_ids_across_runs(self) -> None:
        now, before = self._ids(self.join), self._ids(self.baseline)
        for table, pinned in PINNED_EXCLUSION_IDS.items():
            key = ("model_scope_exclusion", table)
            self.assertEqual(now[key], pinned, table)
            self.assertEqual(now[key], before[key], table)
        # the census assumption is keyed by index and op, so it is run-independent too
        self.assertEqual(now[("op_declared", "delete-issue")], before[("op_declared", "delete-issue")])

    def test_a_row_carrying_the_run_gets_a_new_id(self) -> None:
        """``index_describes_replay(index, run)`` is about *this* run and must move."""
        now, before = self._ids(self.join), self._ids(self.baseline)
        self.assertEqual(
            [key for key in now if now[key] != before.get(key)],
            [("index_describes_replay", self.OTHER_RUN)])
        self.assertNotIn(("index_describes_replay", self.OTHER_RUN), before)

    def test_the_evidence_ids_did_move(self) -> None:
        """Proving the ids above are stable *despite* the run-scoped evidence ids changing."""
        mine = {r.atom.relation: r.id for r in assumptions.assumption_records(self.join.bundle)}
        theirs = {r.atom.relation: r.id for r in assumptions.assumption_records(self.baseline.bundle)}
        self.assertNotEqual(mine["model_scope_exclusion"], theirs["model_scope_exclusion"],
                            "the run-scoped evidence id changes even where the assumption id does not")


class RegistryTest(_EvaluatedFixture):
    """A2: every assumption, what it carries, and what it shares."""

    def test_registry_lists_every_assumption_with_carriers(self) -> None:
        entries = self.registry["assumptions"]
        self.assertEqual(len(entries), 6)
        self.assertEqual([e["assumption_id"] for e in entries],
                         sorted(e["assumption_id"] for e in entries), "entries sort by assumption id")
        by_relation = {}
        for entry in entries:
            by_relation.setdefault(entry["relation"], []).append(entry)
        self.assertEqual(len(by_relation["model_scope_exclusion"]), 4)
        self.assertEqual(len(by_relation["op_declared"]), 1)
        self.assertEqual(len(by_relation["index_describes_replay"]), 1)
        self.assertEqual(self.registry["unreferenced"], [])
        self.assertEqual(self.registry["registry_version"], "capcov-assumption-registry-v1")
        self.assertEqual(self.registry["run"], self.join.run)
        self.assertRegex(self.registry["combined_bundle_digest"], r"^[0-9a-f]{64}$")

    def test_census_assumptions_carry_the_qualification(self) -> None:
        for relation in ("op_declared", "index_describes_replay"):
            entry = self.entry(relation)
            self.assertEqual(sorted({c["claim_id"] for c in entry["carried_by"]}), [QUALIFIED])
            self.assertEqual(entry["impact"]["fallen"], [QUALIFIED])
            self.assertIn(CONSTRAINS, entry["impact"]["survived"])
        self.assertEqual(self.entry("op_declared")["producer_class"], "php-census")
        self.assertEqual(self.entry("index_describes_replay")["producer_class"], "reviewer")

    def test_exclusions_carry_only_the_applied_claim(self) -> None:
        """Finding 1: an exclusion guards ``op_qualified`` through a negated atom,
        so it is not a positive leaf of it and leaf impact cannot see the link."""
        qualified_certificate = self.join.certificates[QUALIFIED]
        for table in PINNED_EXCLUSION_IDS:
            entry = self.entry("model_scope_exclusion", table)
            self.assertEqual(sorted({c["claim_id"] for c in entry["carried_by"]}), [APPLIED])
            self.assertEqual(entry["impact"]["fallen"], [APPLIED])
            self.assertIn(QUALIFIED, entry["impact"]["survived"])
            self.assertNotIn(entry["evidence_id"], qualified_certificate["leaves"])
        self.assertIn({"relation": "undeclared_any", "row": [self.join.run, "delete-issue"]},
                      [{"relation": a["relation"], "row": list(a["row"])} for a in qualified_certificate["absent"]],
                      "op_qualified rests on undeclared_any being absent")

    def test_carried_by_names_the_certificate_it_is_a_leaf_of(self) -> None:
        entry = self.entry("model_scope_exclusion", "authentication")
        carried = [c for c in entry["carried_by"] if c["claim_id"] == APPLIED]
        self.assertEqual(len(carried), 1)
        self.assertEqual(carried[0]["relation"], "exclusion_applied")
        self.assertEqual(carried[0]["row"], [self.join.run, "delete-issue", "authentication"])
        matching = [c for c in self.join.row_certificates[APPLIED]
                    if assumptions.certificate_sha256(c) == carried[0]["certificate_sha256"]]
        self.assertEqual(len(matching), 1, "the digest names a certificate the join actually holds")
        self.assertIn(entry["evidence_id"], matching[0]["leaves"])

    def test_two_producers_sharing_one_heuristic(self) -> None:
        groups = {g["heuristic"]: g for g in self.registry["shared_assumptions"]}
        index_key = f"external:index:{replay_join.SYNTHETIC_INDEX}"
        self.assertIn(index_key, groups)
        self.assertEqual(groups[index_key]["producer_classes"], ["php-census", "reviewer"])
        self.assertEqual(sorted(groups[index_key]["assumption_ids"]),
                         sorted([self.entry("op_declared")["assumption_id"],
                                 self.entry("index_describes_replay")["assumption_id"]]))
        self.assertEqual(groups[index_key]["claims"], [QUALIFIED])
        model_key = f"external:model:{MODEL}"
        self.assertEqual(groups[model_key]["producer_classes"], ["reviewer"])
        self.assertEqual(len(groups[model_key]["assumption_ids"]), 4)

    def test_shared_across_intersects_positive_support(self) -> None:
        qualified = self.join.certificates[QUALIFIED]
        applied = [c for c in self.join.row_certificates[APPLIED]
                   if assumptions.conclusion_of(c)[1][2] == "authentication"]
        self.assertEqual(len(applied), 1)
        self.assertEqual(assumptions.shared_across(self.join.bundle, [qualified]),
                         sorted([self.entry("op_declared")["assumption_id"],
                                 self.entry("index_describes_replay")["assumption_id"]]))
        self.assertEqual(assumptions.shared_across(self.join.bundle, [applied[0]]),
                         [PINNED_EXCLUSION_IDS["authentication"]])
        # finding 1 again, stated as an intersection: no positive support is shared
        self.assertEqual(assumptions.shared_across(self.join.bundle, [qualified, applied[0]]), [])

    def test_registry_document_is_written_without_local_paths(self) -> None:
        out = Path(tempfile.mkdtemp(prefix="capcov-assumption-artifacts-"))
        try:
            document = replay_join.write_artifacts(self.join, out)
            written = (out / "assumptions.json")
            self.assertTrue(written.is_file())
            registry = json.loads(written.read_text(encoding="utf-8"))
            self.assertEqual(len(registry["assumptions"]), 6)
            self.assertEqual(registry["unreferenced"], [])
            self.assertEqual(document["assumptions"]["registry"], "assumptions.json")
            text = "\n".join(p.read_text(encoding="utf-8") for p in out.iterdir())
            for needle in ("/Users/", "/home/", str(FIXTURE)):
                self.assertNotIn(needle, text)
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_summary_keeps_the_evidence_id_list_and_adds_the_registry(self) -> None:
        summary = replay_join.summary(self.join)
        self.assertEqual(summary["assumption_ids"], list(self.join.assumption_ids))
        self.assertEqual(len(summary["assumption_ids"]), 1 + len(self.join.ops))
        self.assertEqual(summary["assumptions"], self.registry["assumptions"])
        self.assertEqual(summary["shared_assumptions"], self.registry["shared_assumptions"])


class InvalidationTest(_EvaluatedFixture):
    """A3: what actually changes when one assumption is withdrawn."""

    def invalidate(self, identifier: str):
        return replay_join.invalidate(self.join, identifier, self.replay_root)

    def test_dropping_one_reviewer_exclusion_unresolves_op_qualified(self) -> None:
        result = self.invalidate(PINNED_EXCLUSION_IDS["authentication"])
        document = result.as_dict()
        self.assertEqual(document["invalidation_version"], "capcov-assumption-invalidation-v1")
        self.assertTrue(document["kernels"]["matched"])
        self.assertEqual(document["kernels"]["python_digest"], document["kernels"]["souffle_digest"])
        self.assertEqual(document["withdrawn"],
                         [self.entry("model_scope_exclusion", "authentication")["evidence_id"]])
        self.assertNotEqual(document["withdrawn_bundle_digest"], document["baseline_bundle_digest"])

        qualified = document["claims"][QUALIFIED]
        self.assertEqual(qualified["before"], {"semantic": "supported", "operational": "complete"})
        self.assertEqual(qualified["after"], {"semantic": "unresolved", "operational": "complete"})
        self.assertEqual(qualified["blocking_premise"], {"relation": "undeclared_any", "holds": True})
        self.assertEqual(qualified["undeclared_tables"], {"php": ["authentication"], "go": ["authentication"]})
        self.assertIsNone(qualified["certificate_sha256"], "an unresolved claim certifies no row")
        # empty, and pinned so it stays visible if it ever stops being: the
        # `model_writes` output template is built only when the *baseline* join
        # already had offending effect rows, and on this fixture it had none,
        # so no template renders the premise the drop actually removed
        self.assertEqual(qualified["missing_premise"], [])
        self.assertEqual(document["flipped"], [QUALIFIED])
        self.assertEqual(document["gained"], [UNDECLARED],
                         "the drop revealed a row: reported, never folded into flipped")

        self.assertEqual(document["claims"][CONSTRAINS]["before"], document["claims"][CONSTRAINS]["after"])
        self.assertFalse(document["claims"][CONSTRAINS]["changed"])
        # finding 2: the open claim gains the row the exclusion used to cover
        self.assertEqual(document["claims"][UNDECLARED]["before"]["semantic"], "unresolved")
        self.assertEqual(document["claims"][UNDECLARED]["after"]["semantic"], "supported")
        self.assertNotIn(UNDECLARED, document["flipped"], "gaining support is not a loss")
        for entry in document["claims"].values():
            self.assertIn(entry["after"]["semantic"], {"supported", "unresolved"})

        rows = dict(self.join.result.python.relations)
        self.assertIn((self.join.run, "delete-issue", "authentication"), list(rows.get("exclusion_applied", ())),
                      "the baseline join is untouched by an invalidation")
        after_rows = {assumptions.conclusion_of(c)[1] for c in result.row_certificates.get(APPLIED, ())}
        self.assertNotIn((self.join.run, "delete-issue", "authentication"), after_rows)
        self.assertEqual(len(after_rows), 3)

    def test_leaf_impact_cannot_predict_a_negation_guarded_fall(self) -> None:
        """Finding 1, as the prediction the operation exists to correct."""
        document = self.invalidate(PINNED_EXCLUSION_IDS["authentication"]).as_dict()
        self.assertEqual(document["flipped"], [QUALIFIED])
        self.assertEqual(document["predicted_fallen"], [APPLIED])
        self.assertFalse(document["prediction_agrees"],
                         "leaf impact misses the fall it cannot see and predicts one that did not happen")

    def test_dropping_the_census_assumption_unresolves_op_qualified(self) -> None:
        entry = self.entry("op_declared")
        result = self.invalidate(entry["assumption_id"])
        document = result.as_dict()
        self.assertEqual(document["withdrawn"], [entry["evidence_id"]])
        qualified = document["claims"][QUALIFIED]
        self.assertEqual(qualified["before"]["semantic"], "supported")
        self.assertEqual(qualified["after"]["semantic"], "unresolved")
        self.assertEqual(qualified["blocking_premise"], {"relation": "op_declared", "holds": False})
        self.assertNotIn("undeclared_tables", qualified, "nothing was written that the model does not declare")
        for claim_id in (CONSTRAINS, APPLIED, UNDECLARED):
            self.assertFalse(document["claims"][claim_id]["changed"], claim_id)
        # this one *is* a positive leaf, so the static prediction gets it right
        self.assertEqual(document["predicted_fallen"], [QUALIFIED])
        self.assertEqual(document["flipped"], [QUALIFIED])
        self.assertEqual(document["gained"], [])
        self.assertTrue(document["prediction_agrees"])
        # the drop must remove *only* the census premise: the runtime
        # qualification `op_qualified_rt` (php/go agreement, no undeclared
        # write) does not rest on the census and must survive.  If a change to
        # `closed_revocation` or to the census assumption's `depends_on` also
        # took `index_describes_replay` -- they share one external heuristic --
        # every other assertion here would still pass while the withdrawal had
        # silently over-reached.
        rows = dict(result.relations)
        row = (replay_join.SYNTHETIC_INDEX, self.join.run, "delete-issue")
        self.assertIn(row, list(rows.get("op_qualified_rt", ())),
                      "op_qualified_rt is not a dependant of the census assumption")
        self.assertEqual(list(rows.get("op_qualified", ())), [],
                         "the claim relation itself is empty, which is why the claim is unresolved")

    def test_an_evidence_id_names_the_same_assumption(self) -> None:
        entry = self.entry("index_describes_replay")
        document = self.invalidate(entry["evidence_id"]).as_dict()
        self.assertEqual(document["assumption_id"], entry["assumption_id"])
        self.assertEqual(document["claims"][QUALIFIED]["after"]["semantic"], "unresolved")
        self.assertEqual(document["claims"][QUALIFIED]["blocking_premise"],
                         {"relation": "index_describes_replay", "holds": False})

    def test_invalidations_are_recorded_and_written(self) -> None:
        result = self.invalidate(PINNED_EXCLUSION_IDS["redis"])
        self.assertIs(self.join.invalidations[result.assumption_id], result)
        out = Path(tempfile.mkdtemp(prefix="capcov-assumption-artifacts-"))
        try:
            document = replay_join.write_artifacts(self.join, out)
            name = document["assumptions"]["invalidations"][result.assumption_id]
            self.assertEqual(name, f"invalidation-{result.short_id}.json")
            self.assertEqual(json.loads((out / name).read_text())["assumption_id"], result.assumption_id)
            self.assertTrue(any(p.name.startswith(f"invalidation-{result.short_id}-certificate-")
                                for p in out.iterdir()))
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_new_certificates_recheck_against_the_withdrawn_bundle(self) -> None:
        """``certify_claims`` already cross-checks both closures; this rechecks the result."""
        from capcov.claims.ir import digest
        from capcov.claims.static.certificate import recheck

        result = self.invalidate(PINNED_EXCLUSION_IDS["jobs_statuses"])
        self.assertTrue(result.row_certificates)
        checked = 0
        for claim_id, certificates in result.row_certificates.items():
            for certificate in certificates:
                self.assertEqual(certificate["bundle_digest"], digest(result.bundle),
                                 "a certificate is bound to the bundle it was drawn from")
                self.assertTrue(recheck(result.bundle, certificate).ok, claim_id)
                checked += 1
        self.assertGreaterEqual(checked, 3)
        self.assertEqual(result.claims[QUALIFIED]["after"]["semantic"], "unresolved")


class UnreferencedAssumptionTest(unittest.TestCase):
    """A fifth reviewed exclusion nothing rests on: registered, withdrawable, inert.

    The extra row goes into a temp copy; the committed fixture is never edited.
    """

    @classmethod
    def setUpClass(cls) -> None:
        _souffle()
        cls.tmp = Path(tempfile.mkdtemp(prefix="capcov-assumption-unreferenced-"))
        cls.directory = cls.tmp / FIXTURE.name
        shutil.copytree(FIXTURE, cls.directory)
        path = cls.directory / "model_scope_exclusions.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["rows"].append({"model": MODEL, "table": "never_written_table",
                                 "reason": "a reviewed exclusion for a table no side writes"})
        path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _add_synthetic_certificate(cls.directory)  # the premise this module is not about
        cls.replay_root = tempfile.mkdtemp(prefix="capcov-assumption-unreferenced-diff-")
        cls.join = replay_join.build(cls.directory)
        if cls.join.bundle is None:
            raise AssertionError("CONTRACT FINDING: " + "; ".join(cls.join.contract_findings))
        replay_join.evaluate_join(cls.join, cls.replay_root)
        if cls.join.mismatch is not None:
            raise AssertionError(f"kernels disagree; replay bundle: {cls.join.mismatch.replay_path}")
        cls.registry = replay_join.assumption_registry(cls.join)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)
        shutil.rmtree(cls.replay_root, ignore_errors=True)

    def test_registry_lists_it_as_unreferenced(self) -> None:
        entries = self.registry["assumptions"]
        self.assertEqual(len(entries), 7)
        spare = [e for e in entries if e["row"][1:2] == ["never_written_table"]]
        self.assertEqual(len(spare), 1)
        self.assertEqual(spare[0]["carried_by"], [])
        self.assertEqual(spare[0]["impact"]["fallen"], [])
        self.assertEqual(self.registry["unreferenced"], [spare[0]["assumption_id"]])
        # the four real exclusions keep the ids the committed fixture pins
        registered = {e["row"][1] for e in entries if e["relation"] == "model_scope_exclusion"}
        self.assertEqual(registered, set(PINNED_EXCLUSION_IDS) | {"never_written_table"})
        for table, pinned in PINNED_EXCLUSION_IDS.items():
            match = [e for e in entries if e["row"][1:2] == [table]]
            self.assertEqual(match[0]["assumption_id"], pinned)

    def test_dropping_it_changes_nothing(self) -> None:
        spare = [e for e in self.registry["assumptions"] if e["row"][1:2] == ["never_written_table"]][0]
        document = replay_join.invalidate(self.join, spare["assumption_id"], self.replay_root).as_dict()
        self.assertEqual(document["flipped"], [])
        self.assertEqual(document["predicted_fallen"], [])
        self.assertTrue(document["prediction_agrees"])
        self.assertEqual(document["withdrawn"], [spare["evidence_id"]])
        for claim_id, entry in document["claims"].items():
            self.assertEqual(entry["before"], entry["after"], claim_id)
            self.assertFalse(entry["changed"], claim_id)
        # finding 3: a certificate is bound to its bundle digest, so the digests
        # move even though every derivation is the one the baseline recorded
        self.assertNotEqual(document["withdrawn_bundle_digest"], document["baseline_bundle_digest"])
        result = self.join.invalidations[spare["assumption_id"]]
        for claim_id, baseline in self.join.row_certificates.items():
            after = result.row_certificates[claim_id]
            self.assertEqual([c["derivation"] for c in after], [c["derivation"] for c in baseline], claim_id)
            self.assertNotEqual(after[0]["bundle_digest"], baseline[0]["bundle_digest"])


class RefusalTest(_EvaluatedFixture):
    """What the registry refuses to answer rather than answering wrongly."""

    def test_withdraw_refuses_an_unknown_id(self) -> None:
        with self.assertRaises(InvalidationError) as caught:
            assumptions.withdraw(self.join.bundle, ["reviewer:nope:model_scope_exclusion:000000000000"])
        self.assertIn("not an evidence id", str(caught.exception))
        with self.assertRaises(InvalidationError):
            assumptions.resolve(self.join.bundle, "asm:" + "0" * 64)
        # an evidence id that exists but is not an assumption is refused too
        observation = next(r for r in self.join.bundle.evidence if r.kind != "assumption")
        with self.assertRaises(InvalidationError) as caught:
            assumptions.resolve(self.join.bundle, observation.id)
        self.assertIn("not an assumption", str(caught.exception))

    def test_withdraw_never_repairs_a_reviewed_output(self) -> None:
        """A template naming the withdrawn id is a refusal, not an edit."""
        from dataclasses import replace as replace_dataclass

        record = self.record("model_scope_exclusion", "authentication")
        bundle = self.join.bundle
        poisoned = replace_dataclass(bundle, outputs=tuple(bundle.outputs) + (
            OutputTemplate("missing_premise", QUALIFIED, relation="model_writes",
                           requires_any_evidence=(record.id,), when_claim="unresolved"),))
        with self.assertRaises(InvalidationError) as caught:
            assumptions.withdraw(poisoned, [record.id])
        self.assertIn("never repaired", str(caught.exception))
        # unchanged, the same withdrawal is fine
        reduced = assumptions.withdraw(bundle, [record.id])
        self.assertNotIn(record.id, {r.id for r in reduced.evidence})

    def test_withdraw_refuses_a_template_that_excludes_the_withdrawn_id(self) -> None:
        """All three evidence fields of a reviewed template are refusals, not just the positive two.

        An ``excludes_evidence`` id would still *render* after the withdrawal --
        that is the point of the field -- and rendering it would add a missing
        premise the reviewer wrote under the assumption that the record exists.
        Deciding on the reviewer's behalf which reading they meant is the edit
        this operation does not make.
        """
        from dataclasses import replace as replace_dataclass

        record = self.record("model_scope_exclusion", "authentication")
        poisoned = replace_dataclass(self.join.bundle, outputs=tuple(self.join.bundle.outputs) + (
            OutputTemplate("missing_premise", QUALIFIED, relation="model_writes",
                           excludes_evidence=(record.id,), when_claim="unresolved"),))
        with self.assertRaises(InvalidationError) as caught:
            assumptions.withdraw(poisoned, [record.id])
        self.assertIn("never repaired", str(caught.exception))
        self.assertIn(record.id, str(caught.exception))

    def test_a_claim_already_refuted_at_the_baseline_is_not_a_refusal(self) -> None:
        """The guard is about *transitions*: a verdict the withdrawal did not cause is reported.

        Fail-closed either way, but refusing here would make the whole
        operation unusable on any bundle that already carries a refuted claim,
        which is exactly the bundle an invalidation is most worth asking about.
        """
        real_compare = assumptions.compare

        def mask(report):
            claims = [SimpleNamespace(key=c.key, semantic="refuted" if c.key == CONSTRAINS else c.semantic,
                                      operational=c.operational, missing_premises=c.missing_premises)
                      for c in report.claims]
            return SimpleNamespace(claims=claims, relations=report.relations,
                                   canonical_digest=report.canonical_digest)

        def poisoned(bundle, **kwargs):
            result = real_compare(bundle, **kwargs)
            return SimpleNamespace(python=mask(result.python), souffle=result.souffle,
                                   matched=result.matched)

        baseline = SimpleNamespace(python=mask(self.join.result.python),
                                   souffle=self.join.result.souffle, matched=True)
        assumptions.compare = poisoned
        try:
            result = assumptions.invalidate(self.join.bundle, PINNED_EXCLUSION_IDS["redis"],
                                            replay_root=self.replay_root, baseline_result=baseline,
                                            baseline_row_certificates=self.join.row_certificates)
        finally:
            assumptions.compare = real_compare
        entry = result.claims[CONSTRAINS]
        self.assertEqual(entry["before"]["semantic"], "refuted")
        self.assertEqual(entry["after"]["semantic"], "refuted")
        self.assertFalse(entry["changed"])
        self.assertNotIn(CONSTRAINS, result.flipped, "it was never supported, so nothing was lost")
        self.assertNotIn(CONSTRAINS, result.gained)

    def test_withdraw_keeps_a_fact_another_producer_still_attests(self) -> None:
        """Two producers, one row: withdrawing one leaves the fact standing."""
        from dataclasses import replace as replace_dataclass

        record = self.record("model_scope_exclusion", "authentication")
        twin = Evidence(id="reviewer:twin:model_scope_exclusion:000000000000", atom=record.atom,
                        context=record.context, source="reviewer A Nother 2027-01-02 model:08380c9c336d run:zzz",
                        depends_on=record.depends_on, kind="assumption")
        doubled = replace_dataclass(self.join.bundle, evidence=tuple(self.join.bundle.evidence) + (twin,))
        reduced = assumptions.withdraw(doubled, [record.id])
        self.assertNotIn(record.id, {r.id for r in reduced.evidence})
        self.assertIn(twin.id, {r.id for r in reduced.evidence})
        self.assertIn(record.atom, reduced.facts, "the row is still attested, so it stays")

    def test_withdraw_takes_the_dependants_with_it(self) -> None:
        """A record resting on the withdrawn one goes too (``ground.closed_revocation``)."""
        from dataclasses import replace as replace_dataclass

        record = self.record("op_declared")
        index = self.record("index_describes_replay")
        dependant = Evidence(id="reviewer:derived:index_describes_replay:000000000000", atom=index.atom,
                             context=index.context, source="reviewer derived from the census assumption",
                             depends_on=(record.id,), kind="assumption")
        extended = replace_dataclass(self.join.bundle,
                                     evidence=tuple(self.join.bundle.evidence) + (dependant,))
        reduced = assumptions.withdraw(extended, [record.id])
        remaining = {r.id for r in reduced.evidence}
        self.assertNotIn(record.id, remaining)
        self.assertNotIn(dependant.id, remaining, "a dependant goes with what it rests on")
        self.assertIn(index.id, remaining)
        self.assertIn(index.atom, reduced.facts, "the row its own producer attests still stands")
        self.assertNotIn(record.atom, reduced.facts, "nothing else attested op_declared")

    def test_transition_to_refuted_is_a_finding(self) -> None:
        """If a kernel ever reported refuted after a drop, no document is written."""
        real_compare = assumptions.compare

        def poisoned(bundle, **kwargs):
            result = real_compare(bundle, **kwargs)
            claims = [SimpleNamespace(key=c.key, semantic="refuted" if c.key == QUALIFIED else c.semantic,
                                      operational=c.operational, missing_premises=c.missing_premises)
                      for c in result.python.claims]
            python = SimpleNamespace(claims=claims, relations=result.python.relations,
                                     canonical_digest=result.python.canonical_digest)
            return SimpleNamespace(python=python, souffle=result.souffle, matched=result.matched)

        assumptions.compare = poisoned
        try:
            with self.assertRaises(InvalidationError) as caught:
                replay_join.invalidate(self.join, PINNED_EXCLUSION_IDS["go_issue_outbox"], self.replay_root)
        finally:
            assumptions.compare = real_compare
        self.assertIn("never a refutation", str(caught.exception))
        self.assertNotIn(PINNED_EXCLUSION_IDS["go_issue_outbox"], self.join.invalidations)

    def test_invalidate_withdraws_one_assumption_at_a_time(self) -> None:
        with self.assertRaises(InvalidationError):
            assumptions.invalidate(self.join.bundle, [], replay_root=self.replay_root,
                                   baseline_result=self.join.result,
                                   baseline_row_certificates=self.join.row_certificates)
        with self.assertRaises(InvalidationError) as caught:
            assumptions.invalidate(self.join.bundle,
                                   [PINNED_EXCLUSION_IDS["redis"], PINNED_EXCLUSION_IDS["authentication"]],
                                   replay_root=self.replay_root, baseline_result=self.join.result,
                                   baseline_row_certificates=self.join.row_certificates)
        self.assertIn("one invalidation withdraws one assumption", str(caught.exception))


class WholeAssumptionTest(_EvaluatedFixture):
    """An assumption two records attest is withdrawn only when both go.

    The A3 document is signed with an *assumption* id.  If ``invalidate`` were
    given an evidence id and withdrew only that record, the fact would still be
    attested, no claim would move, and the document would read
    ``assumption_id: asm:9041..., flipped: []`` -- publishable evidence that
    ``op_qualified`` is independent of a reviewer exclusion that is in fact
    still carrying it.  The certificates in such a document recheck cleanly, so
    nothing downstream would catch it.
    """

    def doubled(self):
        """The fixture bundle plus a second reviewer signing the identical row."""
        from dataclasses import replace as replace_dataclass

        record = self.record("model_scope_exclusion", "authentication")
        twin = Evidence(id="reviewer:twin:model_scope_exclusion:000000000000", atom=record.atom,
                        context=record.context,
                        source="reviewer A Nother 2027-01-02 model:08380c9c336d run:zzzzzzzzzzzz",
                        depends_on=record.depends_on, kind="assumption")
        self.assertEqual(assumptions.assumption_id(twin), PINNED_EXCLUSION_IDS["authentication"],
                         "the same producer class and the same row is the same assumption")
        bundle = replace_dataclass(self.join.bundle, evidence=tuple(self.join.bundle.evidence) + (twin,))
        self.assertIn(record.atom, bundle.facts,
                      "the twin attests a row the bundle already carries, so the closure is unchanged "
                      "and the evaluated baseline is still the baseline of this bundle")
        return bundle, record, twin

    def test_resolve_names_every_attestation_of_an_assumption(self) -> None:
        bundle, record, twin = self.doubled()
        resolved = assumptions.resolve(bundle, PINNED_EXCLUSION_IDS["authentication"])
        self.assertEqual(sorted(r.id for r in resolved), sorted([record.id, twin.id]))
        self.assertEqual([r.id for r in assumptions.resolve(bundle, twin.id)], [twin.id],
                         "an evidence id still names its own record")

    def test_invalidating_by_evidence_id_withdraws_every_attestation(self) -> None:
        bundle, record, twin = self.doubled()
        result = assumptions.invalidate(bundle, record.id, replay_root=self.replay_root,
                                        baseline_result=self.join.result,
                                        baseline_row_certificates=self.join.row_certificates)
        document = result.as_dict()
        self.assertEqual(document["assumption_id"], PINNED_EXCLUSION_IDS["authentication"])
        self.assertEqual(sorted(document["withdrawn"]), sorted([record.id, twin.id]),
                         "one evidence id, but the assumption is what is withdrawn")
        self.assertEqual(document["flipped"], [QUALIFIED])
        self.assertEqual(document["claims"][QUALIFIED]["after"]["semantic"], "unresolved")
        self.assertNotIn(record.atom, result.bundle.facts,
                         "nothing attests the row any more, so the fact goes too")

    def test_an_assumption_id_and_an_evidence_id_give_the_same_document(self) -> None:
        bundle, record, _ = self.doubled()
        by_evidence = assumptions.invalidate(bundle, record.id, replay_root=self.replay_root,
                                             baseline_result=self.join.result,
                                             baseline_row_certificates=self.join.row_certificates).as_dict()
        by_assumption = assumptions.invalidate(bundle, PINNED_EXCLUSION_IDS["authentication"],
                                               replay_root=self.replay_root,
                                               baseline_result=self.join.result,
                                               baseline_row_certificates=self.join.row_certificates).as_dict()
        self.assertEqual(by_evidence, by_assumption,
                         "which id names the assumption cannot change what the withdrawal says")


class CertifyClaimsAgreementTest(_EvaluatedFixture):
    """``certify_claims`` promises the closures agree; this is that promise, tested."""

    def _result(self, souffle_relations):
        souffle = SimpleNamespace(relations=souffle_relations,
                                  canonical_digest=self.join.result.souffle.canonical_digest,
                                  claims=self.join.result.souffle.claims)
        return SimpleNamespace(python=self.join.result.python, souffle=souffle, matched=False)

    def test_a_closure_missing_a_claim_row_is_raised_not_reported(self) -> None:
        dropped = tuple((name, rows[1:] if name == "exclusion_applied" else rows)
                        for name, rows in self.join.result.souffle.relations)
        with self.assertRaises(AssertionError) as caught:
            assumptions.certify_claims(self.join.bundle, self._result(dropped))
        self.assertIn("disagree on the claim rows", str(caught.exception))

    def test_a_closure_agreeing_on_the_rows_but_not_the_support_is_raised(self) -> None:
        """Same claim rows, a support row missing: the second closure must object, not be ignored.

        The exception is the certifier's own (no rule derives the premise from
        that closure) rather than the row/certificate comparison's -- either
        way it is raised out of ``certify_claims`` and no document is written,
        which is the property: a judge with two answers has none.
        """
        from capcov.claims.static.certificate import CertificateError

        altered = tuple((name, () if name == "model_scope_exclusion" else rows)
                        for name, rows in self.join.result.souffle.relations)
        with self.assertRaises((AssertionError, CertificateError)):
            assumptions.certify_claims(self.join.bundle, self._result(altered))


class TruncatedImpactTest(_EvaluatedFixture):
    """A registry whose ``ground.impact`` query does not fit in its bounds."""

    def test_strict_refuses_and_the_embedded_copy_degrades(self) -> None:
        report = self.join.report()
        with self.assertRaises(InvalidationError) as caught:
            assumptions.registry(self.join.bundle, self.join.row_certificates,
                                 run=self.join.run, relations=report.relations, max_nodes=1)
        self.assertIn("truncated", str(caught.exception))
        degraded = assumptions.registry(self.join.bundle, self.join.row_certificates,
                                        run=self.join.run, relations=report.relations,
                                        strict_impact=False, max_nodes=1)
        self.assertEqual(len(degraded["assumptions"]), 6)
        for entry in degraded["assumptions"]:
            self.assertEqual(entry["impact"], {"truncated": True, "fallen": None, "survived": None})

    def test_the_summary_never_raises_on_a_truncated_query(self) -> None:
        """``summary`` embeds the registry, so it must degrade rather than fail."""
        summary = replay_join.summary(self.join)
        self.assertEqual(len(summary["assumptions"]), 6)
        for entry in summary["assumptions"]:
            self.assertFalse(entry["impact"]["truncated"], "the fixture fits in the default bounds")


class CommandLineTest(unittest.TestCase):
    """``claims assumptions registry|invalidate`` over the staged fixture.

    Staged, not committed: the CLI's invalidation cases turn on ``op_qualified``
    being *supported* first, which no real receipt is until the Stage D checker
    exists (module docstring).
    """

    @classmethod
    def setUpClass(cls) -> None:
        _souffle()
        cls.tmp = Path(tempfile.mkdtemp(prefix="capcov-assumption-cli-receipt-"))
        cls.receipt = _with_synthetic_certificate(FIXTURE, cls.tmp / "receipt")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def _run(self, *argv: str) -> tuple[int, str]:
        import contextlib
        import io

        from capcov.claims import cli

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = cli.main(list(argv))
        return code, buffer.getvalue()

    @staticmethod
    def _owned_replay_roots() -> set[Path]:
        return set(Path(tempfile.gettempdir()).glob("capcov-assumptions-*"))

    def test_registry_and_invalidate_roundtrip(self) -> None:
        out = Path(tempfile.mkdtemp(prefix="capcov-assumption-cli-"))
        before_roots = self._owned_replay_roots()
        try:
            code, text = self._run("claims", "assumptions", "registry",
                                   "--receipt", str(self.receipt), "--out", str(out))
            self.assertEqual(code, 0, text[:2000])
            registry = json.loads(text)["registry"]
            self.assertEqual(len(registry["assumptions"]), 6)
            self.assertEqual(registry["unreferenced"], [])
            self.assertTrue((out / "assumptions.json").is_file())

            code, text = self._run("claims", "assumptions", "invalidate", "--receipt", str(self.receipt),
                                   "--drop", PINNED_EXCLUSION_IDS["authentication"])
            self.assertEqual(code, 0, text[:2000])
            document = json.loads(text)["invalidations"]
            self.assertEqual(len(document), 1)
            self.assertEqual(document[0]["flipped"], [QUALIFIED])
            self.assertEqual(document[0]["claims"][QUALIFIED]["undeclared_tables"],
                             {"php": ["authentication"], "go": ["authentication"]})
            self.assertEqual(document[0]["gained"], [UNDECLARED])
            self.assertEqual(self._owned_replay_roots() - before_roots, set(),
                             "a replay root the CLI made itself is removed when nothing needs it")
        finally:
            shutil.rmtree(out, ignore_errors=True)

    def test_a_kernel_disagreement_on_the_claims_is_exit_3(self) -> None:
        """``certify_claims`` raises ``AssertionError``; the contract calls that 3, not a traceback."""
        from capcov.claims import cli

        module = cli._join_module()
        real = module.invalidate

        def raising(join, identifier, replay_root):
            raise AssertionError(f"{identifier}: certificates differ between closures")

        module.invalidate = raising
        before_roots = self._owned_replay_roots()
        try:
            code, text = self._run("claims", "assumptions", "invalidate", "--receipt", str(self.receipt),
                                   "--drop", PINNED_EXCLUSION_IDS["redis"])
        finally:
            module.invalidate = real
        self.assertEqual(code, 3, text[:2000])
        document = json.loads(text)
        self.assertIn("disagree", document["kernel_mismatch"])
        self.assertIn("certificates differ", document["error"])
        kept = self._owned_replay_roots() - before_roots
        self.assertEqual(len(kept), 1, "a mismatch keeps its replay root: the evidence is in it")
        self.assertEqual({str(path) for path in kept}, {document["replay"]})
        for path in kept:
            shutil.rmtree(path, ignore_errors=True)

    def test_unknown_drop_is_a_refusal(self) -> None:
        code, text = self._run("claims", "assumptions", "invalidate",
                               "--receipt", str(self.receipt), "--drop", "asm:" + "0" * 64)
        self.assertEqual(code, 2)
        self.assertIn("not an assumption", json.loads(text)["refusal"])

    def test_missing_receipt_is_a_refusal(self) -> None:
        code, text = self._run("claims", "assumptions", "registry", "--receipt", "/nonexistent-receipt-dir")
        self.assertEqual(code, 2)
        self.assertIn("no receipt directory", json.loads(text)["refusal"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
