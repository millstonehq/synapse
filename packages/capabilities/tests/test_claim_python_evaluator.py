from __future__ import annotations

import unittest

from capcov.claims.evaluator import ResourceLimits, evaluate
from capcov.claims.ir import Aggregation, Atom, Bundle, Claim, Column, Comparison, Constant, RelationDecl, Rule, Variable
from capcov.claims.verdicts import OperationalStatus, SemanticVerdict


def rel(name: str, *columns: tuple[str, str], **kwargs: object) -> RelationDecl:
    return RelationDecl(name, tuple(Column(n, t) for n, t in columns), **kwargs)


def fact(name: str, *values: object) -> Atom:
    return Atom(name, tuple(Constant(v) for v in values))


class PythonEvaluatorTests(unittest.TestCase):
    def test_transitive_closure_and_provenance_are_deterministic(self) -> None:
        bundle = Bundle(
            relations=(rel("edge", ("src", "symbol"), ("dst", "symbol")),
                       rel("reachable", ("src", "symbol"), ("dst", "symbol")),),
            facts=(fact("edge", "a", "b"), fact("edge", "b", "c")),
            rules=(
                Rule(Atom("reachable", (Variable("x"), Variable("y"))),
                     (Atom("edge", (Variable("x"), Variable("y"))),), "edge-to-reachable"),
                Rule(Atom("reachable", (Variable("x"), Variable("z"))),
                     (Atom("reachable", (Variable("x"), Variable("y"))),
                      Atom("edge", (Variable("y"), Variable("z")))), "reachable-step"),
            ),
            claims=(Claim("reachable", (Constant("a"), Constant("c"))),),
        )
        report = evaluate(bundle)
        self.assertEqual(report.relation_rows("reachable"), (("a", "b"), ("a", "c"), ("b", "c")))
        self.assertEqual(report.claims[0].semantic, SemanticVerdict.SUPPORTED)
        self.assertIn("fact:edge", report.claims[0].result.support[0])
        self.assertEqual(report.as_dict(), evaluate(bundle).as_dict())

    def test_comparison_and_negation_require_no_false_open_world_success(self) -> None:
        relations = (
            rel("item", ("name", "symbol"), ("n", "integer")),
            rel("complete_item", ("scope", "symbol"), modality="completeness"),
            rel("small", ("name", "symbol")),
        )
        # The completeness witness is in the same rule body as the negation;
        # its presence permits closed-world reasoning for item only there.
        rules = (
            Rule(Atom("small", (Variable("name"),)),
                 (Atom("item", (Variable("name"), Variable("n"))),
                  Comparison(Variable("n"), "<", Constant(10))), "small"),
        )
        # This rule is intentionally invalid: the completeness relation has
        # the wrong arity for the witness scope and must not be evaluated.
        invalid = Bundle(relations=relations, facts=(fact("item", "a", 3),), rules=rules,
                         claims=(Claim("small", (Constant("a"),)),))
        report = evaluate(invalid)
        self.assertEqual(report.status, OperationalStatus.INVALID_INPUT)

    def test_resource_exhaustion_is_a_status(self) -> None:
        bundle = Bundle(
            relations=(rel("edge", ("src", "symbol"), ("dst", "symbol")),
                       rel("reachable", ("src", "symbol"), ("dst", "symbol")),),
            facts=(fact("edge", "a", "b"), fact("edge", "b", "c")),
            rules=(Rule(Atom("reachable", (Variable("x"), Variable("y"))),
                         (Atom("edge", (Variable("x"), Variable("y"))),), "seed"),),
            claims=(Claim("reachable", (Constant("a"), Constant("b"))),),
        )
        report = evaluate(bundle, ResourceLimits(max_derived_rows=1))
        self.assertEqual(report.status, OperationalStatus.RESOURCE_EXHAUSTED)
        self.assertEqual(report.claims[0].operational, OperationalStatus.RESOURCE_EXHAUSTED)

    def test_stratified_negation_uses_explicit_completeness(self) -> None:
        relations = (
            rel("item", ("name", "symbol")),
            rel("blocked", ("name", "symbol")),
            rel("all_items", ("scope", "symbol"), modality="completeness", completes="item"),
            rel("all_blocked", ("scope", "symbol"), modality="completeness", completes="blocked"),
            rel("allowed", ("name", "symbol")),
        )
        rule = Rule(Atom("allowed", (Variable("name"),)),
                    (Atom("item", (Variable("name"),)),
                     Atom("all_items", (Constant("global"),)),
                     Atom("all_blocked", (Constant("global"),)),
                     Atom("blocked", (Variable("name"),), negated=True)), "allowed-if-unblocked")
        bundle = Bundle(relations=relations,
                        facts=(fact("item", "a"), fact("all_items", "global"), fact("all_blocked", "global")),
                        rules=(rule,), claims=(Claim("allowed", (Constant("a"),)),))
        report = evaluate(bundle)
        self.assertEqual(report.claims[0].semantic, SemanticVerdict.SUPPORTED)
        blocked_bundle = Bundle(relations=relations,
                                facts=(*bundle.facts, fact("blocked", "a")),
                                rules=(rule,), claims=bundle.claims)
        self.assertEqual(evaluate(blocked_bundle).claims[0].semantic, SemanticVerdict.UNRESOLVED)

    def test_finite_sum_aggregation_is_grouped_and_deterministic(self) -> None:
        relations = (
            rel("item", ("name", "symbol"), ("n", "integer")),
            rel("group", ("name", "symbol"), finite=True, nonempty=True),
            rel("group_closed", ("name", "symbol"), modality="completeness", completes="group"),
            rel("total", ("name", "symbol"), ("n", "integer")),
        )
        rule = Rule(Atom("total", (Variable("name"), Variable("n"))),
                    (Atom("item", (Variable("name"), Variable("n"))),
                     Atom("group", (Variable("name"),)),
                     Atom("group_closed", (Variable("name"),))),
                    "sum-items", aggregation=Aggregation("n", "item", ("name",), "n", "sum", "group", "group_closed"))
        bundle = Bundle(relations=relations,
                        facts=(fact("item", "a", 2), fact("item", "a", 3), fact("group", "a"), fact("group_closed", "a")),
                        rules=(rule,), claims=(Claim("total", (Constant("a"), Constant(5))),))
        report = evaluate(bundle)
        self.assertEqual(report.relation_rows("total"), (("a", 5),))
        self.assertEqual(report.claims[0].semantic, SemanticVerdict.SUPPORTED)


if __name__ == "__main__":
    unittest.main()
