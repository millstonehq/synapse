import json
import math
import sys
import unittest

sys.path.insert(0, "packages/capabilities/src")

from capcov.claims import (Aggregation, Atom, Bundle, Claim, Column, Comparison,
    Constant, Context, Modality, RelationDecl, Rule, TypeName, Variable,
    bundle_from_json, canonical_json, validate_bundle)


def R(name, cols, **kw):
    return RelationDecl(name, tuple(Column(n, t, context=c) for n, t, c in cols), **kw)


class ContractReviewTests(unittest.TestCase):
    def test_values_are_frozen_and_unsupported_values_rejected(self):
        value = {"x": [1, {"y": 2}]}
        c = Constant(value, TypeName.JSON)
        value["x"].append(3)
        self.assertEqual(canonical_json(c), '{"type":"json","value":{"x":[1,{"y":2}]}}')
        with self.assertRaises(TypeError): Constant({1: "bad"})
        with self.assertRaises(ValueError): Constant(math.nan)
        with self.assertRaises(TypeError): canonical_json({"bad": {1: 2}})

    def test_fact_rule_claim_and_comparison_types_are_checked(self):
        rels = (R("a", (("tenant", TypeName.STRING, True), ("n", TypeName.INTEGER, False))),
                R("b", (("tenant", TypeName.STRING, True), ("n", TypeName.INTEGER, False))))
        bad_fact = Atom("a", (Constant("t"), Constant("not-int")))
        bad_rule = Rule(Atom("b", (Variable("t"), Variable("x"))),
                        (Atom("a", (Variable("t"), Variable("x"))),
                         Comparison(Variable("x"), "=", Constant("wrong"))))
        bad_claim = Claim("a", (Constant(4), Constant(3)), Context.from_mapping({"tenant": "t"}))
        codes = {i.code for i in validate_bundle(Bundle(rels, facts=(bad_fact,), rules=(bad_rule,), claims=(bad_claim,)))}
        self.assertIn("type-mismatch", codes)

    def test_completeness_witness_names_target_and_matches_scope(self):
        obs = R("obs", (("tenant", TypeName.STRING, True), ("event", TypeName.STRING, False)), context_indices=("tenant",))
        done = R("done", (("tenant", TypeName.STRING, True), ("event", TypeName.STRING, False)), context_indices=("tenant",))
        complete = R("complete", (("tenant", TypeName.STRING, True), ("event", TypeName.STRING, False)), modality=Modality.COMPLETENESS, completes="obs", context_indices=("tenant",))
        rule = Rule(Atom("done", (Variable("t"), Variable("e"))), (Atom("complete", (Variable("t"), Variable("e"))), Atom("obs", (Variable("u"), Variable("e")), negated=True)))
        self.assertIn("missing-completeness", {i.code for i in validate_bundle(Bundle((obs, done, complete), rules=(rule,)))})

    def test_negated_variables_cannot_introduce_bindings(self):
        a = R("a", (("x", TypeName.STRING, False),))
        b = R("b", (("x", TypeName.STRING, False),))
        rule = Rule(Atom("b", (Variable("x"),)), (Atom("a", (Variable("y"),), negated=True),))
        self.assertIn("unsafe-negation", {i.code for i in validate_bundle(Bundle((a, b), rules=(rule,)))})

    def test_aggregation_domain_closure_source_and_recursion(self):
        source = R("src", (("tenant", TypeName.STRING, True), ("n", TypeName.INTEGER, False)), context_indices=("tenant",))
        head = R("total", (("tenant", TypeName.STRING, True), ("n", TypeName.INTEGER, False)), context_indices=("tenant",))
        domain = R("tenants", (("tenant", TypeName.STRING, True),), modality=Modality.ASSUMPTION, finite=True, nonempty=True, context_indices=("tenant",))
        closure = R("tenants_closed", (("tenant", TypeName.STRING, True),), modality=Modality.COMPLETENESS, completes="tenants", context_indices=("tenant",))
        agg = Aggregation("sum", "src", ("tenant",), "n", operator="sum", domain="tenants", closure_witness="tenants_closed")
        valid = Bundle((source, head, domain, closure), rules=(Rule(Atom("total", (Variable("t"), Variable("n"))), (Atom("src", (Variable("t"), Variable("n"))),), aggregation=agg),))
        self.assertNotIn("aggregation-domain", {i.code for i in validate_bundle(valid)})
        bad = Bundle((source, head, domain, closure), rules=(Rule(Atom("total", (Variable("t"), Variable("n"))), (Atom("src", (Variable("t"), Variable("n"))),), aggregation=Aggregation("x", "missing", (), "n", domain="tenants", closure_witness="wrong")),))
        self.assertTrue({i.code for i in validate_bundle(bad)} & {"aggregation-source", "aggregation-closure"})

    def test_forall_requires_finite_explicitly_nonempty_domain(self):
        claim_rel = R("ok", (("tenant", TypeName.STRING, True),), context_indices=("tenant",))
        empty = R("tenants", (("tenant", TypeName.STRING, True),), finite=True, nonempty=False, context_indices=("tenant",))
        claim = Claim("ok", (Constant("t"),), Context.from_mapping({"tenant": "t"}), quantifier="forall", domain="tenants")
        self.assertIn("forall-domain", {i.code for i in validate_bundle(Bundle((claim_rel, empty), claims=(claim,)))})

    def test_cross_context_join_needs_compatibility_witness(self):
        a = R("a", (("tenant", TypeName.STRING, True), ("x", TypeName.STRING, False)), context_indices=("tenant",))
        b = R("b", (("tenant", TypeName.STRING, True), ("x", TypeName.STRING, False)), context_indices=("tenant",))
        out = R("out", (("tenant", TypeName.STRING, True), ("x", TypeName.STRING, False)), context_indices=("tenant",))
        rule = Rule(Atom("out", (Variable("t"), Variable("x"))), (Atom("a", (Variable("t"), Variable("x"))), Atom("b", (Variable("u"), Variable("x")))))
        self.assertIn("missing-compatibility", {i.code for i in validate_bundle(Bundle((a, b, out), rules=(rule,)))})

    def test_json_ingestion_rejects_unknown_fields_and_bad_version(self):
        base = {"schema_version": 1, "relations": [], "facts": [], "rules": [], "claims": [], "metadata": {}}
        self.assertEqual(bundle_from_json(json.dumps(base)).schema_version, 1)
        bad = dict(base); bad["extra"] = True
        with self.assertRaises(ValueError): bundle_from_json(bad)
        with self.assertRaises(ValueError): bundle_from_json('{"schema_version":1,"relations":[],"facts":[],"rules":[],"claims":[],"metadata":{},"x":NaN}')
        bad = dict(base); bad["schema_version"] = 2
        with self.assertRaises(ValueError): bundle_from_json(bad)


if __name__ == "__main__": unittest.main()
