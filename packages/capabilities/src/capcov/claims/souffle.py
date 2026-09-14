"""Souffle 2.5 backend for the restricted claims IR.

The backend is intentionally a small boundary: validation and semantics live in
the IR, while this module only translates a validated bundle, executes the
generated program, and returns normalized relation/claim observations.  It
does not read corpus expectations or call another evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Mapping

from .ir import (Atom, Bundle, Comparison, Constant, Rule, Term, TypeName,
                 Variable, canonical_json, digest)
from .validation import assert_valid
from .verdicts import EvaluationResult, OperationalStatus, SemanticVerdict, verdict


MAX_SECONDS = 30.0
MAX_ROWS = 100_000
MAX_OUTPUT_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class SouffleProgram:
    bundle_digest: str
    program: str
    facts: Mapping[str, str]
    program_digest: str
    runtime: str = "souffle-2.5"


@dataclass(frozen=True)
class SouffleResult:
    bundle_digest: str
    program_digest: str
    runtime: str
    relations: Mapping[str, tuple[tuple[Any, ...], ...]]
    claims: tuple[EvaluationResult, ...]
    output_digest: str
    evidence_digest: str
    elapsed_seconds: float


def _identifier(value: str) -> str:
    out = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in value)
    return out if out and not out[0].isdigit() else "r_" + out


def _aliases(names):
    """Assign collision-free stable identifiers after Souffle sanitization."""
    result = {}
    used = set()
    for name in names:
        base = _identifier(name)
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        result[name] = candidate
    return result


def _stype(type_name: TypeName) -> str:
    if type_name in {TypeName.SYMBOL, TypeName.DIGEST, TypeName.JSON_METADATA_ONLY}:
        return "symbol"
    if type_name in {TypeName.INTEGER, TypeName.UNSIGNED, TypeName.TIMESTAMP}:
        return "number"
    if type_name is TypeName.BOOLEAN:
        return "number"
    raise ValueError(f"Souffle cannot represent {type_name.value}")


def _quote(value: Any, type_name: TypeName | None = None) -> str:
    if type_name is TypeName.BOOLEAN:
        return "1" if value else "0"
    if type_name in {TypeName.INTEGER, TypeName.UNSIGNED, TypeName.TIMESTAMP}:
        return str(int(value))
    # Souffle string literals use C-style escapes.  json's string escaping is
    # compatible for the canonical symbol values used by the IR.
    import json
    return json.dumps(canonical_json(value) if type_name is TypeName.JSON_METADATA_ONLY else str(value), ensure_ascii=False)


def _fact_field(value: Any, type_name: TypeName) -> str:
    """Serialize one TSV fact field (symbols are unquoted in Souffle facts)."""
    if type_name is TypeName.BOOLEAN:
        return "1" if value else "0"
    if type_name in {TypeName.INTEGER, TypeName.UNSIGNED, TypeName.TIMESTAMP}:
        return str(int(value))
    text = canonical_json(value) if type_name is TypeName.JSON_METADATA_ONLY else str(value)
    if any(ch in text for ch in "\t\r\n"):
        raise ValueError("symbol values containing TSV control characters are unsupported")
    return text


def _term(term: Term, columns, index: int, variable_aliases=None) -> str:
    column_type = columns[index].type
    if isinstance(term, Variable):
        return (variable_aliases or {}).get(term.name, _identifier(term.name))
    if isinstance(term, Constant):
        return _quote(term.value, column_type)
    raise TypeError(f"unsupported term {type(term).__name__}")


def _atom(atom: Atom, relation_map, relation_aliases=None, column_aliases=None, variable_aliases=None, term_overrides=None) -> str:
    relation = relation_map[atom.relation]
    relation_name = (relation_aliases or {}).get(atom.relation, _identifier(atom.relation))
    args = ", ".join((term_overrides or {}).get(i, _term(t, relation.columns, i, variable_aliases)) for i, t in enumerate(atom.terms))
    return ("!" if atom.negated else "") + relation_name + "(" + args + ")"


def _comparison(c: Comparison, variable_aliases=None) -> str:
    def simple(term):
        if isinstance(term, Variable): return (variable_aliases or {}).get(term.name, _identifier(term.name))
        if isinstance(term, Constant): return _quote(term.value, term.type)
        raise TypeError(type(term).__name__)
    return f"{simple(c.left)} {c.operator} {simple(c.right)}"


def translate_bundle(bundle: Bundle) -> SouffleProgram:
    """Translate a validated bundle into deterministic Souffle source/facts."""
    assert_valid(bundle)
    relation_map = {r.name: r for r in bundle.relations}
    relation_aliases = _aliases([r.name for r in bundle.relations])
    column_aliases = {r.name: _aliases([c.name for c in r.columns]) for r in bundle.relations}
    lines = ["// Generated by capcov.claims.souffle; do not edit."]
    extra_decls = []
    extra_rules = []
    facts: dict[str, str] = {}
    for relation in bundle.relations:
        fields = ", ".join(f"{column_aliases[relation.name][c.name]}:{_stype(c.type)}" for c in relation.columns)
        lines.append(f".decl {relation_aliases[relation.name]}({fields})")
    # Every relation has an input file.  This keeps primitive and derived
    # relations on the same deterministic representation and permits a later
    # producer to add facts without regenerating declarations.
    for relation in bundle.relations:
        lines.append(f'.input {relation_aliases[relation.name]}(IO=file, filename="facts/{relation_aliases[relation.name]}.facts")')
        lines.append(f'.output {relation_aliases[relation.name]}(IO=file, filename="outputs/{relation_aliases[relation.name]}.csv")')
    for rule in bundle.rules:
        var_names = []
        for term in [*rule.head.terms, *(t for a in rule.body if isinstance(a, Atom) for t in a.terms)]:
            if isinstance(term, Variable) and term.name not in var_names: var_names.append(term.name)
        variable_aliases = _aliases(var_names)
        head = _atom(rule.head, relation_map, relation_aliases, column_aliases, variable_aliases)
        body = [_atom(a, relation_map, relation_aliases, column_aliases, variable_aliases) if isinstance(a, Atom) else _comparison(a, variable_aliases) for a in rule.body]
        if rule.aggregation is not None:
            agg = rule.aggregation
            source = relation_map[agg.relation]
            source_atom = next((a for a in rule.body if isinstance(a, Atom) and a.relation == agg.relation and not a.negated), None)
            if source_atom is None:
                raise ValueError(f"aggregation {agg.name} has no positive source atom")
            value_index = [c.name for c in source.columns].index(agg.value_variable)
            source_text = _atom(source_atom, relation_map, relation_aliases, column_aliases, variable_aliases)
            value = variable_aliases.get(agg.value_variable, _identifier(agg.value_variable))
            if agg.operator == "count": expression = f"count : {source_text}"
            elif agg.operator in {"sum", "min", "max"}:
                op = agg.operator
                expression = f"{op} {value} : {source_text}"
            else:
                if agg.operator not in {"any", "all"}:
                    raise NotImplementedError(f"unsupported Souffle aggregation {agg.operator!r}")
                # Boolean aggregation is represented by a generated count
                # helper.  A true row is emitted only when the finite source
                # has at least one member (any), or exactly the finite domain
                # cardinality (all).  This avoids pretending Souffle's count
                # result is a Boolean value.
                helper = _identifier("__capcov_agg_" + agg.name)
                helper = _aliases([helper])[helper]
                source_columns = {column.name: column.type for column in source.columns}
                group_terms = [variable_aliases.get(name, _identifier(name)) for name in agg.group_by]
                group_types = [_stype(source_columns[name]) for name in agg.group_by]
                extra_decls.append(f".decl {helper}({', '.join(g + ':' + t for g, t in zip(group_terms, group_types))}, n:number)")
                helper_body = [x for x in body if x != source_text]
                helper_body.append(f"n = count : {source_text}")
                extra_rules.append(f"{helper}({', '.join(group_terms)}, n) :- {', '.join(helper_body)}.")
                body = [x for x in body if x != source_text]
                body.append(f"{helper}({', '.join(group_terms)}, n)")
                if agg.operator == "any":
                    body.append("n > 0")
                else:
                    # all requires the declared finite domain and compares
                    # source cardinality to that domain's cardinality.
                    domain_atom = next((a for a in rule.body if isinstance(a, Atom) and a.relation == agg.domain and not a.negated), None)
                    if domain_atom is None:
                        raise ValueError("all aggregation requires a domain atom")
                    domain_text = _atom(domain_atom, relation_map, relation_aliases, column_aliases, variable_aliases)
                    body.append(f"n = count : {domain_text}")
                target_i = [c.name for c in relation_map[rule.head.relation].columns].index(agg.value_variable)
                head = _atom(rule.head, relation_map, relation_aliases, column_aliases, variable_aliases, {target_i: "1"})
                lines.append(f"{head} :- {', '.join(body)}.")
                continue
            # Souffle's aggregate is a body constraint whose result binds the
            # head value variable.  Remove the source atom from the ordinary
            # body; the aggregate expression supplies it.
            body = [x for x in body if x != source_text]
            head_term = rule.head.terms[[c.name for c in relation_map[rule.head.relation].columns].index(agg.value_variable)]
            head_value = variable_aliases.get(head_term.name, _identifier(head_term.name)) if isinstance(head_term, Variable) else value
            body.append(f"{head_value} = {expression}")
        lines.append(f"{head} :- {', '.join(body)}.")
    lines.extend(extra_decls)
    lines.extend(extra_rules)
    program = "\n".join(lines) + "\n"
    for relation in bundle.relations:
        if not relation.primitive and any(f.relation == relation.name for f in bundle.facts):
            raise ValueError(f"facts cannot target non-primitive relation {relation.name!r}")
        rows = []
        for fact in bundle.facts:
            if fact.relation != relation.name:
                continue
            rows.append("\t".join(_fact_field(t.value, relation.columns[i].type) if isinstance(t, Constant) else "" for i, t in enumerate(fact.terms)))
        facts[relation_aliases[relation.name]] = "\n".join(sorted(rows)) + ("\n" if rows else "")
    bundle_digest = digest(bundle)
    program_digest = hashlib.sha256(program.encode()).hexdigest()
    return SouffleProgram(bundle_digest, program, facts, program_digest)


def _parse_value(raw: str, type_name: TypeName) -> Any:
    if type_name is TypeName.BOOLEAN: return bool(int(raw))
    if type_name in {TypeName.INTEGER, TypeName.UNSIGNED, TypeName.TIMESTAMP}: return int(raw)
    if type_name is TypeName.JSON_METADATA_ONLY:
        import json
        return json.loads(raw)
    return raw


def run_bundle(bundle: Bundle, *, executable: str = "souffle", timeout: float = MAX_SECONDS,
               max_rows: int = MAX_ROWS, max_output_bytes: int = MAX_OUTPUT_BYTES) -> SouffleResult:
    """Run Souffle in a bounded temporary directory and normalize outputs."""
    translated = translate_bundle(bundle)
    relation_map = {r.name: r for r in bundle.relations}
    relation_aliases = _aliases([r.name for r in bundle.relations])
    root = Path(tempfile.mkdtemp(prefix="capcov-souffle-"))
    started = time.monotonic()
    try:
        (root / "facts").mkdir(); (root / "outputs").mkdir()
        (root / "program.dl").write_text(translated.program, encoding="utf-8")
        for relation in bundle.relations:
            alias = relation_aliases[relation.name]
            (root / "facts" / f"{alias}.facts").write_text(translated.facts[alias], encoding="utf-8")
        proc = subprocess.Popen([executable, "--jobs", "1", "program.dl"], cwd=root,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.monotonic() + timeout
        while proc.poll() is None:
            output_bytes = sum(p.stat().st_size for p in (root / "outputs").glob("*") if p.is_file())
            if output_bytes > max_output_bytes:
                proc.kill(); proc.communicate()
                raise OverflowError(f"Souffle outputs exceed {max_output_bytes} bytes during execution")
            if time.monotonic() > deadline:
                proc.kill(); proc.communicate()
                raise TimeoutError(f"Souffle exceeded {timeout:.1f}s")
            time.sleep(0.005)
        stdout, stderr = proc.communicate()
        if proc.returncode:
            raise RuntimeError((stderr or stdout)[-4000:])
        output_bytes = sum(p.stat().st_size for p in (root / "outputs").glob("*") if p.is_file())
        if output_bytes > max_output_bytes:
            raise OverflowError(f"Souffle outputs exceed {max_output_bytes} bytes")
        relations: dict[str, tuple[tuple[Any, ...], ...]] = {}
        total_rows = 0
        for name, relation in relation_map.items():
            path = root / "outputs" / f"{relation_aliases[name]}.csv"
            rows = []
            if path.exists():
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line: continue
                    fields = line.split("\t")
                    if len(fields) != relation.arity: raise ValueError(f"malformed output row for {name}")
                    rows.append(tuple(_parse_value(v, c.type) for v, c in zip(fields, relation.columns)))
            total_rows += len(rows)
            if total_rows > max_rows: raise OverflowError(f"Souffle derived rows exceed {max_rows}")
            # JSON metadata values decode to mappings and are intentionally not
            # hashable.  Canonical keys preserve set semantics without mutating
            # or stringifying the public normalized values.
            unique = {canonical_json(row): row for row in rows}
            relations[name] = tuple(unique[key] for key in sorted(unique))
        output_digest = hashlib.sha256(b"".join((k + "=" + repr(v)).encode() for k, v in sorted(relations.items()))).hexdigest()
        claim_results = tuple(_claim_result(claim, relation_map[claim.relation], relations, relation_map) for claim in bundle.claims)
        runtime = next((line.strip() for line in stdout.splitlines() if line.strip().startswith("Version:")), translated.runtime)
        evidence_digest = hashlib.sha256((translated.bundle_digest + translated.program_digest + runtime + output_digest).encode()).hexdigest()
        return SouffleResult(translated.bundle_digest, translated.program_digest, runtime, relations, claim_results, output_digest, evidence_digest, time.monotonic() - started)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _claim_matches(row, terms, relation, context):
    bindings = {}
    columns = {column.name: i for i, column in enumerate(relation.columns)}
    for i, term in enumerate(terms):
        if isinstance(term, Constant):
            if row[i] != term.value:
                return False
        elif isinstance(term, Variable):
            if term.name in bindings and bindings[term.name] != row[i]:
                return False
            bindings[term.name] = row[i]
    for name, value in context.items():
        if name in columns and row[columns[name]] != value:
            return False
    return True


def _claim_result(claim, relation, relations, relation_map):
    rows = relations.get(claim.relation, ())
    if claim.quantifier.value == "forall":
        domain_decl = relation_map.get(claim.domain) if claim.domain else None
        domain = relations.get(claim.domain, ()) if claim.domain else ()
        domain_columns = {column.name: i for i, column in enumerate(domain_decl.columns)} if domain_decl else {}
        # Every finite-domain member binds variables with the corresponding
        # domain column name; claim and domain argument order need not match.
        supported = bool(domain) and all(
            any(_claim_matches(row, tuple(
                Constant(d[domain_columns[t.name]]) if isinstance(t, Variable) and t.name in domain_columns else t
                for t in claim.terms), relation, claim.context.as_dict()) for row in rows)
            for d in domain
        )
    else:
        supported = any(_claim_matches(row, claim.terms, relation, claim.context.as_dict()) for row in rows)
    semantic = verdict(supported, False)
    return EvaluationResult(semantic=semantic, operational=OperationalStatus.COMPLETE,
                            resources=(("derived_rows", sum(len(v) for v in relations.values())),))


__all__ = ["SouffleProgram", "SouffleResult", "translate_bundle", "run_bundle", "MAX_SECONDS", "MAX_ROWS", "MAX_OUTPUT_BYTES"]
