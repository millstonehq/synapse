import unittest

from capcov.claims import (Atom, Bundle, BundleIngestionError, Claim, Column,
    Constant, Context, DiagnosticRule, Evidence, Modality, RelationDecl, Rule,
    TypeName, Variable, assert_valid, bundle_from_json, canonical_json, digest,
    validate_bundle)


def rel(name, *cols, modality=Modality.OBSERVATION):
    return RelationDecl(name, tuple(Column(c, TypeName.SYMBOL, context=(c in {"tenant", "run"})) for c in cols), modality=modality)


class ClaimIRTests(unittest.TestCase):
    def test_canonical_json_and_digest_are_stable(self):
        one = Bundle((rel("seen", "tenant", "event"),), facts=(Atom("seen", (Constant("t"), Constant("e"))),))
        two = Bundle((rel("seen", "tenant", "event"),), facts=(Atom("seen", (Constant("t"), Constant("e"))),))
        self.assertEqual(canonical_json(one), canonical_json(two))
        self.assertEqual(digest(one), digest(two))
        self.assertEqual(len(digest(one)), 64)

    def test_bundle_rejects_non_ir_collection_members_before_canonical_replay(self):
        cases = (
            {"relations": (object(),)},
            {"relations": (), "evidence": (object(),)},
            {"relations": (), "outputs": (object(),)},
        )
        for kwargs in cases:
            with self.subTest(field=next(reversed(kwargs))):
                with self.assertRaises(TypeError):
                    Bundle(**kwargs)

    def test_validation_reports_publicly_constructed_malformed_nested_ir(self):
        relation = rel("seen", "value")
        valid_atom = Atom("seen", (Constant("v"),))
        cases = (
            (Bundle((relation,), evidence=(Evidence(
                "e", object(), source="producer"),)), "atom-type"),
            (Bundle((relation,), facts=(Atom("seen", (object(),)),)),
             "term-type"),
            (Bundle((relation,), rules=(Rule(
                object(), (valid_atom,)),)), "atom-type"),
            (Bundle((relation,), rules=(Rule(
                valid_atom, (object(),)),)), "atom-type"),
            (Bundle((relation,), diagnostics=(DiagnosticRule(
                "seen", "observation", predicate=(object(),)),)),
             "diagnostic-predicate"),
        )
        for bundle, expected in cases:
            with self.subTest(code=expected):
                self.assertIn(
                    expected,
                    {issue.code for issue in validate_bundle(bundle)},
                )

    def test_malformed_raw_members_have_a_named_ingestion_failure(self):
        for field in ("relations", "evidence", "outputs"):
            with self.subTest(field=field):
                raw = {"schema_version": 1, field: [17]}
                with self.assertRaises(BundleIngestionError) as caught:
                    bundle_from_json(raw)
                self.assertEqual(caught.exception.operational_failure,
                                 "invalid-input")

    def test_validation_defensively_reports_mutated_noncanonical_members(self):
        for field, code in (("relations", "relation-type"),
                            ("evidence", "evidence-type"),
                            ("outputs", "output-type")):
            with self.subTest(field=field):
                malformed = Bundle(())
                object.__setattr__(malformed, field, (object(),))
                self.assertIn(code, {issue.code
                                     for issue in validate_bundle(malformed)})

    def test_validation_reports_mutated_nested_ir_without_dereferencing_it(self):
        relation = rel("seen", "value")
        atom = Atom("seen", (Constant("v"),))
        evidence = Evidence("e", atom, source="producer")
        rule = Rule(atom, (atom,))
        claim = Claim("seen", (Constant("v"),), Context(), id="claim")
        diagnostic = DiagnosticRule(
            "seen", "observation", claim_id="claim")

        cases = (
            (evidence, "atom", object(), "atom-type"),
            (atom, "terms", object(), "atom-type"),
            (rule, "head", object(), "atom-type"),
            (rule, "body", object(), "rule-body"),
            (diagnostic, "predicate", (object(),), "diagnostic-predicate"),
        )
        for template, field, malformed, expected in cases:
            with self.subTest(field=f"{type(template).__name__}.{field}"):
                # Rebuild each graph because nested frozen records are shared.
                fact = Atom("seen", (Constant("v"),))
                record = Evidence("e", fact, source="producer")
                candidate_rule = Rule(fact, (fact,))
                candidate_diagnostic = DiagnosticRule(
                    "seen", "observation", claim_id="claim")
                target = {
                    Evidence: record,
                    Atom: fact,
                    Rule: candidate_rule,
                    DiagnosticRule: candidate_diagnostic,
                }[type(template)]
                bundle = Bundle(
                    (relation,), facts=(fact,), evidence=(record,),
                    rules=(candidate_rule,), claims=(claim,),
                    diagnostics=(candidate_diagnostic,))
                object.__setattr__(target, field, malformed)
                self.assertIn(
                    expected,
                    {issue.code for issue in validate_bundle(bundle)},
                )

    def test_positive_rule_is_valid_and_head_variables_are_safe(self):
        bundle = Bundle((rel("seen", "tenant", "event"), rel("done", "tenant", "event")), rules=(
            Rule(Atom("done", (Variable("t"), Variable("e"))), (Atom("seen", (Variable("t"), Variable("e"))),)),))
        assert_valid(bundle)

    def test_negation_requires_completeness_premise(self):
        without = Bundle((rel("seen", "tenant", "event"), rel("done", "tenant", "event")), rules=(
            Rule(Atom("done", (Variable("t"), Variable("e"))), (Atom("seen", (Variable("t"), Variable("e")), negated=True),)),))
        self.assertIn("missing-completeness", {x.code for x in validate_bundle(without)})
        seen = RelationDecl("seen", (Column("tenant", TypeName.SYMBOL, context=True), Column("event", TypeName.SYMBOL)), context_indices=("tenant",))
        done = RelationDecl("done", (Column("tenant", TypeName.SYMBOL, context=True), Column("event", TypeName.SYMBOL)), context_indices=("tenant",))
        complete = RelationDecl("complete", (Column("tenant", TypeName.SYMBOL, context=True), Column("event", TypeName.SYMBOL)), modality=Modality.COMPLETENESS, completes="seen", context_indices=("tenant",))
        with_ = Bundle((seen, done, complete), rules=(
            Rule(Atom("done", (Variable("t"), Variable("e"))), (Atom("complete", (Variable("t"), Variable("e"))), Atom("seen", (Variable("t"), Variable("e")), negated=True),)),))
        self.assertFalse(validate_bundle(with_))

    def test_unsafe_variable_and_recursive_negation_are_rejected(self):
        unsafe = Bundle((rel("a", "x"), rel("b", "x")), rules=(Rule(Atom("b", (Variable("missing"),)), (Atom("a", (Variable("x"),)),)),))
        self.assertIn("unsafe-variable", {x.code for x in validate_bundle(unsafe)})
        recursive = Bundle((rel("a", "x"), rel("b", "x")), rules=(
            Rule(Atom("a", (Variable("x"),)), (Atom("b", (Variable("x"),)),)),
            Rule(Atom("b", (Variable("x"),)), (Atom("a", (Variable("x"),), negated=True),)),))
        self.assertIn("recursive-negation", {x.code for x in validate_bundle(recursive)})

    def test_aggregation_needs_domain_and_closure(self):
        from capcov.claims import Aggregation
        bundle = Bundle((rel("a", "x"), rel("b", "x")), rules=(Rule(Atom("b", (Variable("x"),)), (Atom("a", (Variable("x"),)),), aggregation=Aggregation("count_a", "a", ("x",), "x")),))
        self.assertTrue({x.code for x in validate_bundle(bundle)} >= {"aggregation-domain", "aggregation-closure"})


if __name__ == "__main__": unittest.main()
