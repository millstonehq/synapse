"""Inventory literal SQLite table declarations without executing target code.

This is deliberately declaration discovery, not SQL data-flow analysis. Calls
remain diagnostics until a query/receiver adapter can bind them honestly.
"""

from __future__ import annotations

import ast
import re

# Keep strings/comments as indivisible tokens: CREATE TABLE inside either is
# data, not a declaration. Quoted identifiers retain their token type.
_TOKEN = re.compile(
    r"(?P<space>\s+)|(?P<comment>--[^\n]*|/\*[\s\S]*?\*/)"
    r"|(?P<string>'(?:''|[^'])*')"
    r'|(?P<quoted>"(?:""|[^"])*"|`(?:``|[^`])*`|\[[^\]]*\])'
    r"|(?P<word>[A-Za-z_][A-Za-z_0-9]*)|(?P<other>.)",
    re.DOTALL,
)


def tables(sql: str) -> list[str]:
    """Read CREATE [TEMP] TABLE [IF NOT EXISTS] name (...) statements only.

    Attached schemas are retained: collapsing main.items and audit.items would
    silently merge two entities. SQLite's accepted single-quoted table names
    are intentionally unsupported rather than confusing data with identifiers.
    """
    tokens = [
        (m.lastgroup, m.group()) for m in _TOKEN.finditer(sql)
        if m.lastgroup not in {"space", "comment"}
    ]
    out = []
    statements: list[list[tuple[str, str]]] = [[]]
    for token in tokens:
        if token == ("other", ";"):
            statements.append([])
        else:
            statements[-1].append(token)
    for statement in statements:
        index = 0

        def keyword(value: str) -> bool:
            nonlocal index
            if (index < len(statement) and statement[index][0] == "word"
                    and statement[index][1].upper() == value):
                index += 1
                return True
            return False

        def identifier() -> str | None:
            nonlocal index
            if index >= len(statement):
                return None
            kind, value = statement[index]
            if kind not in {"word", "quoted"}:
                return None
            index += 1
            if kind == "quoted":
                quote = value[0]
                value = value[1:-1]
                if quote in {'"', '`'}:
                    value = value.replace(quote * 2, quote)
            return value

        if not keyword("CREATE"):
            continue
        if not keyword("TEMP"):
            keyword("TEMPORARY")
        if not keyword("TABLE"):
            continue
        if keyword("IF") and not (keyword("NOT") and keyword("EXISTS")):
            continue
        name = identifier()
        if name is None:
            continue
        if index < len(statement) and statement[index] == ("other", "."):
            index += 1
            table = identifier()
            if table is None:
                continue
            name += "." + table
        if index < len(statement) and statement[index] == ("other", "("):
            out.append(name)
    return out


def inspect_call(node: ast.Call) -> tuple[list[str], str] | None:
    if not isinstance(node.func, ast.Attribute) or node.func.attr not in {
        "execute", "executemany", "executescript",
    }:
        return None
    sql = node.args[0] if node.args else next(
        (kw.value for kw in node.keywords if kw.arg in {"sql", "sql_script"}), None
    )
    if isinstance(sql, ast.Constant) and isinstance(sql.value, str):
        return tables(sql.value), "literal_sql_unbound"
    return [], "computed_sql_or_expression"
