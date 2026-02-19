---
id: WIKI-014
type: wiki
title: Email Template Engine - Design Notes
status: approved
owner: Notification Team
created: '2024-01-03T11:08:56.077Z'
updated: '2025-11-06T04:15:21.490Z'
tags:
  - wiki
  - notification-service
summary: Email Template Engine - Design Notes
source_repo: https://git.example.com/acme/email-template-engine
commit_sha: 236723bd2bc6649b7b2e3b98b508a772e463a198
generated_at: '2025-05-29T17:12:27.953Z'
source_files:
  - cmd/payments/main.go
  - internal/handler/payment_handler.go
  - internal/usecase/payment_usecase.go
  - internal/gateway/stripe/adapter.go
  - internal/gateway/paypal/adapter.go
  - internal/repository/payment_repository.go
  - internal/model/payment.go
generator: deepwiki
model: claude-3-sonnet
importance: medium
example: true
---

## Overview

The `email-template-engine` repository implements the template rendering subsystem used by the Email Delivery Service. It compiles Handlebars-style templates with per-locale variants, validates required variable bindings at render time, and produces fully-formed HTML and plain-text email bodies ready for provider submission.

This wiki page was auto-generated from the repository source. It covers the template compilation pipeline, variable resolution strategy, and the versioning scheme that allows notification producers to pin template versions.

## Architecture

The engine is structured as a library consumed by the Email Delivery Service worker process. Key components:

- **Template Loader**: Reads compiled templates from PostgreSQL by `(template_slug, version, locale)` key. Falls back to the `en-US` base locale if the requested locale is not found.
- **Compiler**: Parses Handlebars syntax, extracts the required variable schema, and caches the compiled AST in memory (LRU cache, max 500 entries). Template compilation is expensive; the cache eliminates recompilation on repeated sends.
- **Renderer**: Accepts a compiled template and a `VariableMap` (JSON object from the notification payload). Resolves variable references, evaluates conditionals and loops, and emits the final HTML and text bodies.
- **Validator**: At render time, checks that all required variables declared in the template's schema are present in the `VariableMap`. Returns a structured error listing missing variables rather than rendering a partial output.

## Key Packages

### `pkg/loader`

Manages template retrieval from PostgreSQL. The `TemplateLoader` struct uses a read-through cache keyed on `(slug, version, locale)`. Cache TTL is 5 minutes; explicit invalidation is triggered by template publish events consumed from RabbitMQ.

### `pkg/compiler`

Parses template source strings using a lightweight Handlebars parser. The `Compile()` function returns a `CompiledTemplate` value containing the AST and extracted variable schema. The in-process LRU cache wraps `Compile()` transparently.

### `pkg/renderer`

Accepts a `CompiledTemplate` and a `VariableMap`. Executes the AST walk, resolving variable references and evaluating helper functions (`{{formatDate}}`, `{{currency}}`, `{{t}}` for i18n). Returns separate `HTML` and `PlainText` outputs.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `TEMPLATE_CACHE_SIZE` | `500` | LRU cache entry limit |
| `TEMPLATE_CACHE_TTL_SECONDS` | `300` | Time before a cached template is re-fetched |
| `DEFAULT_LOCALE` | `en-US` | Fallback locale if requested locale is missing |
| `STRICT_VARIABLE_VALIDATION` | `true` | Fail render on missing required variables |

## Generation Notes

Generated from commit `236723b` on the `main` branch. The generator analyzed TypeScript source files, extracted exported interfaces, and summarized the compilation and rendering pipeline. Manual review recommended for accuracy.
