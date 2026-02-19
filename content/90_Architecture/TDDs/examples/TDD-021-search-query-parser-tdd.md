---
id: TDD-021
type: tdd
title: Search Query Parser TDD
status: approved
owner: Senior Engineer
created: '2024-11-10T11:59:38.758Z'
updated: '2025-04-13T16:51:35.244Z'
tags:
  - tdd
  - search-platform
summary: Search Query Parser TDD
related_adrs:
  - ADR-0019
  - ADR-0018
example: true
---

## Summary

Design a query parser that accepts raw user input strings and produces a structured query AST suitable for translation into Elasticsearch Query DSL. The parser handles boolean operators, phrase queries, field-scoped queries, and wildcard syntax. It integrates with the query rewrite layer for synonym expansion and field boosting, as decided in [[ADR-0018|ADR-0018]] and [[ADR-0019|ADR-0019]].

The parser is a standalone module within the Search Query Processing Service. It is responsible for the transformation from unstructured text to a typed query representation, not for executing the query against Elasticsearch.

## Overview

The Search Query Parser converts user-typed queries into a normalized AST that downstream components can safely process. This separation of concerns means the Elasticsearch query builder never receives raw user strings, eliminating injection risks and enabling consistent synonym expansion and field boost application.

Key design principles:
- **Strict output typing**: The AST uses a discriminated union type; downstream consumers must handle every node type
- **Fail-safe parsing**: Unparseable input falls back to a simple `multi_match` query rather than returning an error
- **Pluggable rewrite pipeline**: Synonym expansion, stopword removal, and field boosts are applied as separate rewrite passes on the AST, not within the parser itself

## Architecture

- **Lexer**: Tokenizes the raw query string into a flat token stream. Handles quoted strings, parentheses, field-colon syntax (`title:foo`), and boolean operators (`AND`, `OR`, `NOT`).
- **Parser**: Applies a recursive descent grammar to the token stream, producing an AST. Grammar supports: term nodes, phrase nodes, boolean nodes (AND/OR/NOT), field-scoped nodes, and group nodes (parenthesized sub-expressions).
- **AST Normalizer**: Flattens redundant boolean nesting, removes empty nodes, and applies precedence rules (NOT > AND > OR).
- **Rewrite Pipeline**: An ordered sequence of AST visitors that apply synonym expansion, stopword removal, and field boost annotations. Each visitor is independently configurable via the DynamoDB `search-query-config` table.
- **Query DSL Builder**: Translates the rewritten AST into Elasticsearch Query DSL JSON. Separate builder implementations exist for keyword queries and hybrid queries (including the kNN vector query).

## Information Model

- **ASTNode** (abstract): Base type with a `type` discriminant. Subtypes: `TermNode`, `PhraseNode`, `BooleanNode`, `FieldNode`, `GroupNode`, `WildcardNode`
- **TermNode**: `{ type: 'term', value: string, boost?: number, field?: string }`
- **PhraseNode**: `{ type: 'phrase', tokens: string[], slop: number, field?: string }`
- **BooleanNode**: `{ type: 'boolean', operator: 'AND' | 'OR' | 'NOT', operands: ASTNode[] }`
- **ParseResult**: `{ ast: ASTNode, raw: string, parseWarnings: string[], fallback: boolean }`

## Interfaces

- `parseQuery(rawQuery: string, config: QueryParserConfig): ParseResult` — main entry point
- `rewriteAST(ast: ASTNode, pipeline: RewritePass[]): ASTNode` — applies rewrite passes
- `buildQueryDSL(ast: ASTNode, options: QueryBuildOptions): ElasticsearchQuery` — produces ES Query DSL
- `buildHybridQueryDSL(ast: ASTNode, vector: number[], options: QueryBuildOptions): ElasticsearchQuery` — hybrid variant with kNN clause
- Config loaded from DynamoDB `search-query-config` at Lambda cold start and refreshed every 5 minutes

## Files and Layout

```
src/
  parser/
    lexer.ts          - Tokenization of raw query strings
    parser.ts         - Recursive descent parser producing AST
    normalizer.ts     - AST normalization (precedence, deduplication)
    types.ts          - ASTNode discriminated union types
  rewrite/
    synonyms.ts       - Synonym expansion rewrite pass
    stopwords.ts      - Stopword removal rewrite pass
    field-boost.ts    - Field boost annotation pass
  builder/
    keyword.ts        - Elasticsearch keyword Query DSL builder
    hybrid.ts         - Hybrid (keyword + kNN) Query DSL builder
  config/
    loader.ts         - DynamoDB config loader with refresh logic
  index.ts            - Public module interface
tests/
  parser.test.ts
  rewrite.test.ts
  builder.test.ts
  integration/
    query-roundtrip.test.ts
```

## Work Plan

1. **Phase 1 (Week 1)**: Implement lexer and parser; unit tests for all AST node types including edge cases (empty input, unbalanced parens, all-boolean query)
2. **Phase 2 (Week 2)**: Implement AST normalizer and rewrite pipeline infrastructure; synonym and stopword passes
3. **Phase 3 (Week 3)**: Implement keyword Query DSL builder; integration tests against Elasticsearch test cluster
4. **Phase 4 (Week 4)**: Implement hybrid Query DSL builder with kNN clause; validate against ADR-0019 RRF fusion approach
5. **Phase 5 (Week 5)**: Integrate into Search Query Processing Service Lambda; load test at 800 QPS

## Risks and Mitigations

- **Risk**: Complex boolean queries produce deeply nested Elasticsearch queries that time out. **Mitigation**: Add AST depth limit (max depth 5); queries exceeding limit fall back to simple multi_match.
- **Risk**: Synonym expansion produces excessively large queries, degrading performance. **Mitigation**: Cap synonym expansion to 5 synonyms per term; measure query size impact during load testing.
- **Risk**: Config reload during Lambda execution causes inconsistent rewrite behavior. **Mitigation**: Load config at cold start; refresh only between invocations using a background timer.
