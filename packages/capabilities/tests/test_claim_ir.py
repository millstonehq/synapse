import pytest

from capcov.claims import (
    Atom, Bundle, Column, Comparison, Constant, RelationDecl, Rule, TypeName,
    Variable, canonical_json, digest, assert_valid, validate_bundle, ValidationError,
    Modality,
)


def rel(name, *cols, modality=Modality.OBSERVATION):
    return RelationDecl(name, tuple(Column(c, TypeName.STRING, context=(c in {"tenant", "run"})) for c in cols), modality=modality)


def test_canonical_json_and_digest_are_stable():
    one = Bundle((rel("seen", "tenant", "event"),), facts=(Atom("seen", (Constant("t"), Constant("e"))),))
    two = Bundle((rel("seen", "tenant", "event"),), facts=(Atom("seen", (Constant("t"), Constant("e"))),))
    assert canonical_json(one) == canonical_json(two)
    assert digest(one) == digest(two)
    assert len(digest(one)) == 64


def test_positive_rule_is_valid_and_head_variables_are_safe():
    bundle = Bundle(
        (rel("seen", "tenant", "event"), rel("done", "tenant", "event")),
        rules=(Rule(Atom("done", (Variable("t"), Variable("e"))),
               (Atom("seen", (Variable("t"), Variable("e"))),)),),
    )
    assert_valid(bundle)


def test_negation_requires_completeness_premise():
    without = Bundle((rel("seen", "tenant", "event"), rel("done", "tenant", "event")), rules=(
        Rule(Atom("done", (Variable("t"), Variable("e"))), (Atom("seen", (Variable("t"), Variable("e")), negated=True),)),))
    assert any(x.code == "missing-completeness" for x in validate_bundle(without))
    with_ = Bundle((rel("seen", "tenant", "event"), rel("done", "tenant", "event"),
                    rel("complete", "tenant", "event", modality=Modality.COMPLETENESS)), rules=(
        Rule(Atom("done", (Variable("t"), Variable("e"))), (
            Atom("complete", (Variable("t"), Variable("e"))),
            Atom("seen", (Variable("t"), Variable("e")), negated=True),)),))
    assert not validate_bundle(with_)


def test_unsafe_variable_and_recursive_negation_are_rejected():
    unsafe = Bundle((rel("a", "x"), rel("b", "x")), rules=(
        Rule(Atom("b", (Variable("missing"),)), (Atom("a", (Variable("x"),)),)),))
    assert any(x.code == "unsafe-variable" for x in validate_bundle(unsafe))
    recursive = Bundle((rel("a", "x"), rel("b", "x")), rules=(
        Rule(Atom("a", (Variable("x"),)), (Atom("b", (Variable("x"),)),)),
        Rule(Atom("b", (Variable("x"),)), (Atom("a", (Variable("x"),), negated=True),)),))
    assert any(x.code == "recursive-negation" for x in validate_bundle(recursive))


def test_aggregation_needs_domain_and_closure():
    from capcov.claims import Aggregation
    bundle = Bundle((rel("a", "x"), rel("b", "x")), rules=(
        Rule(Atom("b", (Variable("x"),)), (Atom("a", (Variable("x"),)),),
             aggregation=Aggregation("count_a", "a", ("x",), "x")),))
    assert {x.code for x in validate_bundle(bundle)} >= {"aggregation-domain", "aggregation-closure"}

