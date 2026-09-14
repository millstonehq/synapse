import unittest

from capcov.claims import (Atom, Bundle, Column, Constant, Modality,
    RelationDecl, Rule, TypeName, Variable, assert_valid, canonical_json,
    digest, validate_bundle)


def rel(name, *cols, modality=Modality.OBSERVATION):
    return RelationDecl(name, tuple(Column(c, TypeName.SYMBOL, context=(c in {"tenant", "run"})) for c in cols), modality=modality)


class ClaimIRTests(unittest.TestCase):
    def test_canonical_json_and_digest_are_stable(self):
        one = Bundle((rel("seen", "tenant", "event"),), facts=(Atom("seen", (Constant("t"), Constant("e"))),))
        two = Bundle((rel("seen", "tenant", "event"),), facts=(Atom("seen", (Constant("t"), Constant("e"))),))
        self.assertEqual(canonical_json(one), canonical_json(two))
        self.assertEqual(digest(one), digest(two))
        self.assertEqual(len(digest(one)), 64)

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
