import sys
import unittest

sys.path.insert(0, "packages/capabilities/src")

from capcov.claims import (Atom, Bundle, Claim, Column, Constant, Context,
                           Modality, RelationDecl, Rule, TypeName, Variable,
                           Aggregation, validate_bundle)
from capcov.claims.souffle import (MAX_OUTPUT_BYTES, run_bundle,
                                   translate_bundle)


def R(name, *columns, **kwargs):
    return RelationDecl(name, tuple(Column(*column) for column in columns), **kwargs)


class SouffleBackendTests(unittest.TestCase):
    def test_recursive_transitive_closure_and_digests_are_deterministic(self):
        edge = R("edge", ("left", TypeName.SYMBOL), ("right", TypeName.SYMBOL))
        path = R("path", ("left", TypeName.SYMBOL), ("right", TypeName.SYMBOL))
        rules = (
            Rule(Atom("path", (Variable("x"), Variable("y"))),
                 (Atom("edge", (Variable("x"), Variable("y"))),)),
            Rule(Atom("path", (Variable("x"), Variable("z"))),
                 (Atom("path", (Variable("x"), Variable("y"))),
                  Atom("edge", (Variable("y"), Variable("z"))))),
        )
        bundle = Bundle((edge, path), facts=(
            Atom("edge", (Constant("a"), Constant("b"))),
            Atom("edge", (Constant("b"), Constant("c"))),
        ), rules=rules)
        one = run_bundle(bundle)
        two = run_bundle(bundle)
        self.assertEqual(one.relations["path"], (("a", "b"), ("a", "c"), ("b", "c")))
        self.assertEqual(one.program_digest, two.program_digest)
        self.assertEqual(one.output_digest, two.output_digest)

    def test_negation_requires_and_uses_completeness(self):
        observed = R("observed", ("item", TypeName.SYMBOL))
        complete = R("observed_closed", ("item", TypeName.SYMBOL),
                     modality=Modality.COMPLETENESS, completes="observed")
        missing = R("missing", ("item", TypeName.SYMBOL))
        bundle = Bundle((observed, complete, missing),
                        facts=(Atom("observed_closed", (Constant("x"),)),),
                        rules=(Rule(Atom("missing", (Variable("x"),)),
                                    (Atom("observed_closed", (Variable("x"),)),
                                     Atom("observed", (Variable("x"),), negated=True))),))
        self.assertFalse(validate_bundle(bundle))
        self.assertEqual(run_bundle(bundle).relations["missing"], (("x",),))

    def test_count_aggregation_is_translated_and_bounded(self):
        source = R("source", ("tenant", TypeName.SYMBOL, True), ("n", TypeName.INTEGER), context_indices=("tenant",))
        total = R("total", ("tenant", TypeName.SYMBOL, True), ("n", TypeName.INTEGER), context_indices=("tenant",))
        domain = R("tenants", ("tenant", TypeName.SYMBOL, True), finite=True, nonempty=True, context_indices=("tenant",))
        closed = R("tenants_closed", ("tenant", TypeName.SYMBOL, True), modality=Modality.COMPLETENESS, completes="tenants", context_indices=("tenant",))
        aggregation = Aggregation("number", "source", ("tenant",), "n", "count", "tenants", "tenants_closed")
        rule = Rule(Atom("total", (Variable("t"), Variable("n"))),
                    (Atom("source", (Variable("t"), Variable("n"))),
                     Atom("tenants", (Variable("t"),)),
                     Atom("tenants_closed", (Variable("t"),))), aggregation=aggregation)
        bundle = Bundle((source, total, domain, closed), facts=(
            Atom("source", (Constant("t"), Constant(1))), Atom("source", (Constant("t"), Constant(2))),
            Atom("tenants", (Constant("t"),)), Atom("tenants_closed", (Constant("t"),))), rules=(rule,))
        self.assertFalse(validate_bundle(bundle))
        self.assertEqual(run_bundle(bundle).relations["total"], (("t", 2),))

    def test_context_columns_are_emitted_in_declared_order(self):
        relation = R("contextual", ("tenant", TypeName.SYMBOL, True), ("run", TypeName.SYMBOL, True), ("value", TypeName.INTEGER), context_indices=("tenant", "run"))
        bundle = Bundle((relation,), facts=(Atom("contextual", (Constant("t"), Constant("r"), Constant(7))),))
        program = translate_bundle(bundle).program
        self.assertIn(".decl contextual(tenant:symbol, run:symbol, value:number)", program)
        self.assertEqual(run_bundle(bundle).relations["contextual"], (("t", "r", 7),))

    def test_output_limit_is_reported(self):
        relation = R("items", ("item", TypeName.SYMBOL))
        bundle = Bundle((relation,), facts=tuple(Atom("items", (Constant(str(i)),)) for i in range(4)))
        with self.assertRaises(OverflowError):
            run_bundle(bundle, max_output_bytes=1)

    def test_timeout_is_reported(self):
        relation = R("items", ("item", TypeName.SYMBOL))
        bundle = Bundle((relation,), facts=(Atom("items", (Constant("x"),)),))
        with self.assertRaises(TimeoutError):
            run_bundle(bundle, timeout=0.001)

    def test_sanitized_column_names_do_not_collide(self):
        relation = R("values", ("a-b", TypeName.SYMBOL), ("a_b", TypeName.SYMBOL))
        bundle = Bundle((relation,), facts=(Atom("values", (Constant("x"), Constant("y"))),))
        program = translate_bundle(bundle).program
        self.assertIn("a_b:symbol, a_b_2:symbol", program)
        self.assertEqual(run_bundle(bundle).relations["values"], (("x", "y"),))

    def test_nonprimitive_facts_are_rejected(self):
        derived = R("derived", ("x", TypeName.SYMBOL), primitive=False)
        with self.assertRaises(ValueError):
            translate_bundle(Bundle((derived,), facts=(Atom("derived", (Constant("x"),)),)))

    def test_json_metadata_round_trips_without_hashing_mapping(self):
        relation = R("metadata", ("payload", TypeName.JSON_METADATA_ONLY))
        bundle = Bundle((relation,), facts=(Atom("metadata", (Constant({"x": [1, 2]}, TypeName.JSON_METADATA_ONLY),)),))
        self.assertEqual(run_bundle(bundle).relations["metadata"], (({"x": [1, 2]},),))

    def test_forall_requires_every_finite_domain_member(self):
        domain = R("domain", ("x", TypeName.SYMBOL), finite=True, nonempty=True)
        covered = R("covered", ("value", TypeName.SYMBOL))
        claims = (Claim("covered", (Variable("x"),), quantifier="forall", domain="domain"),)
        bundle = Bundle((domain, covered), facts=(Atom("domain", (Constant("a"),)), Atom("domain", (Constant("b"),)), Atom("covered", (Constant("a"),))), claims=claims)
        result = run_bundle(bundle)
        self.assertEqual(result.claims[0].semantic.value, "unresolved")

    def test_any_and_all_compile_to_boolean_rows(self):
        source = R("source", ("tenant", TypeName.SYMBOL, True), ("value", TypeName.BOOLEAN), context_indices=("tenant",))
        out = R("out", ("tenant", TypeName.SYMBOL, True), ("value", TypeName.BOOLEAN), context_indices=("tenant",))
        domain = R("domain", ("tenant", TypeName.SYMBOL, True), finite=True, nonempty=True, context_indices=("tenant",))
        closed = R("closed", ("tenant", TypeName.SYMBOL, True), modality=Modality.COMPLETENESS, completes="domain", context_indices=("tenant",))
        aggregation = Aggregation("any", "source", ("tenant",), "value", "any", "domain", "closed")
        rule = Rule(Atom("out", (Variable("tenant"), Variable("value"))), (Atom("source", (Variable("tenant"), Variable("value"))), Atom("domain", (Variable("tenant"),)), Atom("closed", (Variable("tenant"),))), aggregation=aggregation)
        bundle = Bundle((source, out, domain, closed), facts=(Atom("source", (Constant("t"), Constant(True))), Atom("domain", (Constant("t"),)), Atom("closed", (Constant("t"),))), rules=(rule,))
        self.assertFalse(validate_bundle(bundle))
        self.assertEqual(run_bundle(bundle).relations["out"], (("t", True),))

    def test_boolean_aggregates_count_truth_values_not_rows(self):
        def evaluate(operator, values):
            source = R("source", ("tenant", TypeName.SYMBOL, True), ("value", TypeName.BOOLEAN), context_indices=("tenant",))
            out = R("out", ("tenant", TypeName.SYMBOL, True), ("value", TypeName.BOOLEAN), context_indices=("tenant",))
            domain = R("domain", ("tenant", TypeName.SYMBOL, True), finite=True, nonempty=True, context_indices=("tenant",))
            closed = R("closed", ("tenant", TypeName.SYMBOL, True), modality=Modality.COMPLETENESS, completes="domain", context_indices=("tenant",))
            aggregate = Aggregation(operator, "source", ("tenant",), "value", operator, "domain", "closed")
            rule = Rule(Atom("out", (Variable("tenant"), Variable("value"))), (Atom("source", (Variable("tenant"), Variable("value"))), Atom("domain", (Variable("tenant"),)), Atom("closed", (Variable("tenant"),))), aggregation=aggregate)
            facts = tuple(Atom("source", (Constant("t"), Constant(value))) for value in values)
            facts += (Atom("domain", (Constant("t"),)), Atom("closed", (Constant("t"),)))
            return run_bundle(Bundle((source, out, domain, closed), facts=facts, rules=(rule,))).relations["out"]
        self.assertEqual(evaluate("any", (False,)), ())
        self.assertEqual(evaluate("any", (False, True)), (("t", True),))
        self.assertEqual(evaluate("all", (True, True)), (("t", True),))
        self.assertEqual(evaluate("all", (True, False)), ())
        self.assertEqual(evaluate("all", ()), ())

    def test_boolean_aggregates_support_global_zero_group(self):
        def bundle(operator, values):
            source = R("source", ("value", TypeName.BOOLEAN))
            out = R("out", ("value", TypeName.BOOLEAN))
            domain = R("domain", ("scope", TypeName.SYMBOL), finite=True, nonempty=True)
            closed = R("closed", ("scope", TypeName.SYMBOL), modality=Modality.COMPLETENESS, completes="domain")
            aggregate = Aggregation(operator, "source", (), "value", operator, "domain", "closed")
            rule = Rule(Atom("out", (Variable("value"),)), (Atom("source", (Variable("value"),)), Atom("domain", (Constant("global"),)), Atom("closed", (Constant("global"),))), aggregation=aggregate)
            facts = tuple(Atom("source", (Constant(value),)) for value in values)
            facts += (Atom("domain", (Constant("global"),)), Atom("closed", (Constant("global"),)))
            return Bundle((source, out, domain, closed), facts=facts, rules=(rule,))
        for operator in ("any", "all"):
            program = translate_bundle(bundle(operator, (True,))).program
            self.assertIn(".decl __capcov_agg_", program)
            self.assertNotIn("(, n_true", program)

    def test_claim_context_filters_rows_and_negative_polarity_is_evidence(self):
        rel = R("rejected", ("tenant", TypeName.SYMBOL, True), ("actor", TypeName.SYMBOL), polarity="negative", context_indices=("tenant",))
        claim = Claim("rejected", (Variable("tenant"), Constant("actor")), Context.from_mapping({"tenant": "t1"}))
        bundle = Bundle((rel,), facts=(Atom("rejected", (Constant("t1"), Constant("actor"))), Atom("rejected", (Constant("t2"), Constant("actor")))), claims=(claim,))
        result = run_bundle(bundle)
        self.assertEqual(result.claims[0].semantic.value, "supported")
        wrong_context = Claim("rejected", (Variable("tenant"), Constant("actor")), Context.from_mapping({"tenant": "missing"}))
        result = run_bundle(Bundle((rel,), facts=bundle.facts, claims=(wrong_context,)))
        self.assertEqual(result.claims[0].semantic.value, "unresolved")


if __name__ == "__main__":
    unittest.main()
