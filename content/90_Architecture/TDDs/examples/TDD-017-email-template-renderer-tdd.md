---
id: TDD-017
type: tdd
title: Email Template Renderer TDD
status: approved
owner: Principal Engineer
created: '2024-01-14T09:37:43.979Z'
updated: '2025-01-27T02:42:43.552Z'
tags:
  - tdd
  - notification-service
summary: Email Template Renderer TDD
related_adrs:
  - ADR-0017
  - ADR-0014
example: true
---

## Summary

Design the Email Template Renderer — a TypeScript library embedded in the Email Delivery Service that compiles and renders Handlebars notification templates into production-ready HTML and plain-text email bodies. The renderer must support template versioning per [[ADR-0017|ADR-0017: Implement Template Versioning System]], locale fallback, variable validation, and a compile-time AST cache to keep render latency under 10ms per message.

The renderer is integrated with the RabbitMQ-based job processing pipeline described in [[ADR-0014|ADR-0014: Choose RabbitMQ for Notification Queue]].

## Overview

The renderer is a library (not a standalone service) consumed by the Email Delivery Service worker process. It handles the transformation from a `(templateSlug, version, locale, variableMap)` tuple into a `RenderedEmail { html, text, subject }` output.

Key design principles:
- **Compile-time caching**: Template parsing (AST generation) is expensive; the compiled AST is cached in an LRU cache keyed on `(slug, version, locale)`. Rendering from a cached AST is the common case and must be fast.
- **Strict variable validation**: Missing required variables cause a render failure with a structured error listing missing fields. Partial rendering of templates with missing variables is not allowed.
- **Locale fallback chain**: If the requested locale is not found, the renderer falls back through `(lang-REGION) → (lang) → (en-US)` before failing.
- **Version pinning**: Templates are referenced as `slug@majorVersion`. The renderer resolves the latest published minor/patch within the major version from the template store.

## Architecture

- **TemplateStore**: Reads compiled templates from PostgreSQL by `(slug, version, locale)`. Implements the locale fallback chain. Emits a `TEMPLATE_NOT_FOUND` error if no fallback succeeds.
- **TemplateCompiler**: Parses Handlebars source into an AST and extracts the required variable schema. Wraps the LRU cache.
- **TemplateRenderer**: Accepts a compiled AST and a `VariableMap`. Walks the AST, resolves variable references, and emits HTML and plain-text outputs using separate rendering paths.
- **VariableValidator**: Pre-render check that all variables declared as required in the template schema are present in the `VariableMap`. Returns structured errors on failure.
- **HelperRegistry**: Provides built-in Handlebars helpers: `{{formatDate}}`, `{{currency}}`, `{{pluralize}}`, `{{t}}` (i18n lookup), `{{#if-env}}` (conditional by send environment).

## Information Model

- **Template**: `slug`, `majorVersion`, `minorVersion`, `locale`, `status` (draft|published|deprecated), `source`, `schema` (required variables and their types), `createdBy`, `publishedAt`
- **CompiledTemplate**: `slug`, `version`, `locale`, `ast` (opaque compiled representation), `schema`, `compiledAt`
- **RenderedEmail**: `subject`, `html`, `text`, `templateVersion`, `locale`, `renderedAt`
- **RenderError**: `code` (MISSING_VARIABLE|TEMPLATE_NOT_FOUND|COMPILE_ERROR), `details` (list of offending fields or error message)

## Interfaces

- `TemplateRenderer.render(slug, version, locale, variableMap) → RenderedEmail | RenderError`
- `TemplateStore.load(slug, version, locale) → Template | null` (with locale fallback)
- `TemplateCompiler.compile(template) → CompiledTemplate` (cached)
- `VariableValidator.validate(schema, variableMap) → ValidationResult`

## Files and Layout

```
src/
  template-store.ts           - PostgreSQL template loader with locale fallback
  template-compiler.ts        - Handlebars parser and LRU cache
  template-renderer.ts        - AST walker, HTML/text output generator
  variable-validator.ts       - Required variable schema checker
  helpers/
    format-date.helper.ts
    currency.helper.ts
    pluralize.helper.ts
    i18n.helper.ts
  types/
    template.types.ts         - Template, CompiledTemplate, RenderedEmail types
    error.types.ts            - RenderError types
tests/
  template-renderer.test.ts   - Unit tests for render pipeline
  variable-validator.test.ts  - Schema validation edge cases
  helpers/                    - Unit tests per helper
```

## Work Plan

1. **Phase 1 - Types and Store (Week 1)**: Define all types, implement TemplateStore with locale fallback and PostgreSQL integration
2. **Phase 2 - Compiler and Cache (Week 2)**: Implement TemplateCompiler with LRU cache, validate cache hit/miss behavior under concurrent load
3. **Phase 3 - Renderer and Helpers (Week 3)**: Implement TemplateRenderer, VariableValidator, and all built-in helpers
4. **Phase 4 - Integration (Week 4)**: Wire renderer into the Email Delivery Service worker, integration tests with real templates
5. **Phase 5 - Performance Validation (Week 5)**: Benchmark render latency under load, tune LRU cache size, confirm < 10ms p95 for cache-hit path

## Risks and Mitigations

- **Risk**: Handlebars template injection if variable values contain Handlebars syntax. **Mitigation**: Escape all variable values before rendering; use Handlebars triple-stash `{{{var}}}` only for known-safe HTML fields.
- **Risk**: LRU cache eviction under high template diversity causes repeated compilation overhead. **Mitigation**: Monitor cache hit rate; increase LRU size if hit rate drops below 90%.
- **Risk**: Locale fallback chain causes incorrect language rendering if template data is inconsistent. **Mitigation**: Add integration tests for every supported locale confirming correct fallback behavior.
