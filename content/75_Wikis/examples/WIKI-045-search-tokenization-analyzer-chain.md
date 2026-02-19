---
id: WIKI-045
type: wiki
title: Search Tokenization - Analyzer Chain
status: approved
owner: Search Team
created: '2024-05-31T17:02:25.506Z'
updated: '2025-06-15T04:25:12.682Z'
tags:
  - wiki
  - search-platform
summary: Search Tokenization - Analyzer Chain
source_repo: https://git.example.com/acme/search-tokenization
commit_sha: 167de92db67f72da6994fe003a3dea84e8179ca7
generated_at: '2025-10-02T08:24:44.003Z'
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
importance: low
example: true
---

## Overview

This page documents the Elasticsearch analyzer chain configuration used by the Search Platform to tokenize and normalize document content and search queries. The analyzer chain determines how raw text is broken into indexable terms, which directly affects which queries match which documents.

We maintain multiple named analyzers for different content types and languages. All analyzers follow the same three-stage pipeline: character filtering, tokenization, and token filtering. The configuration is version-controlled in the `search-indexing-pipeline` repository under `config/elasticsearch/analyzers/`.

## Analyzer Architecture

### The Three-Stage Pipeline

Every Elasticsearch analyzer consists of three stages applied in sequence:

1. **Character filters** — Transform the raw character stream before tokenization. Used to strip HTML tags, normalize Unicode, and handle custom character substitutions.
2. **Tokenizer** — Splits the character stream into individual tokens (terms). The tokenizer choice is the most impactful decision in analyzer design.
3. **Token filters** — Transform the individual tokens after tokenization. Applied in order; the output of each filter is the input to the next.

### Named Analyzers

The Search Platform defines the following named analyzers in the `search_content_v3` index template:

| Analyzer Name | Used For | Tokenizer | Key Token Filters |
|--------------|----------|-----------|-------------------|
| `search_english` | English-language body and title fields (indexing + querying) | `standard` | lowercase, stop (English), english stemmer, synonym_graph |
| `search_english_exact` | `.keyword` sub-fields for exact-match sorting and faceting | `keyword` | lowercase, trim |
| `search_code` | Code snippet fields (no stemming, no stop words) | `whitespace` | lowercase, word_delimiter_graph |
| `search_suggest` | Autocomplete suggestion field (edge n-gram) | `standard` | lowercase, stop (English), edge_ngram (min=1, max=20) |
| `search_multilingual` | Documents with detected non-English language | `icu_tokenizer` | icu_folding, icu_normalizer |

## Detailed Configuration

### `search_english` Analyzer

This is the primary analyzer for body and title fields. It produces stemmed, stop-word-filtered, synonym-expanded terms optimized for BM25 relevance scoring.

```json
{
  "search_english": {
    "type": "custom",
    "char_filter": ["html_strip"],
    "tokenizer": "standard",
    "filter": [
      "lowercase",
      "english_stop",
      "english_possessive_stemmer",
      "english_stemmer",
      "search_synonym_graph"
    ]
  }
}
```

**Character filter: `html_strip`** — Removes HTML tags from the input. Necessary because documents ingested from the CMS sometimes contain residual HTML markup in the body field.

**Tokenizer: `standard`** — Unicode-aware tokenizer that splits on whitespace and punctuation. Handles accented characters and CJK characters correctly at the tokenizer level.

**Token filter: `english_stop`** — Removes high-frequency English stop words ("the", "is", "at", etc.) that add noise to BM25 scoring without contributing to relevance discrimination.

**Token filters: `english_possessive_stemmer` + `english_stemmer`** — Two-stage stemming. The possessive stemmer removes trailing `'s` (e.g., "document's" → "document"). The English stemmer (Porter2 algorithm) reduces inflected word forms to their stem (e.g., "indexing" → "index", "searches" → "search").

**Token filter: `search_synonym_graph`** — Applies the synonym dictionary at query time only (using `updateable: true` in ES 8.x so the synonym list can be updated without reindexing). The synonym dictionary is stored in `config/synonyms/search_synonyms.txt` and contains 1,240 entries organized by domain group (product names, technical terms, topic aliases).

### `search_suggest` Analyzer (Edge N-gram)

Used for the DynamoDB suggestion population side-path in the indexing pipeline. Generates prefix tokens for autocomplete matching.

```json
{
  "search_suggest": {
    "type": "custom",
    "tokenizer": "standard",
    "filter": [
      "lowercase",
      "english_stop",
      "search_edge_ngram"
    ]
  },
  "search_edge_ngram": {
    "type": "edge_ngram",
    "min_gram": 1,
    "max_gram": 20,
    "token_chars": ["letter", "digit"]
  }
}
```

The edge n-gram filter generates a token for every prefix of each term. For the term "indexing", it generates: "i", "in", "ind", "inde", "index", "indexi", "indexin", "indexing". This allows the DynamoDB-backed autocomplete endpoint to match on any prefix without requiring a full-text search query.

Note: The `search_suggest` analyzer is used only during **indexing** of the suggestion field. At query time, the Autocomplete Lambda performs prefix key scans directly against DynamoDB — the Elasticsearch suggestion field is not queried at runtime.

### `search_code` Analyzer

Used for fields containing code snippets, command-line instructions, or technical strings where stemming would be destructive (e.g., "searches" and "search" should be distinct in a code context).

```json
{
  "search_code": {
    "type": "custom",
    "tokenizer": "whitespace",
    "filter": [
      "lowercase",
      "search_word_delimiter_graph"
    ]
  },
  "search_word_delimiter_graph": {
    "type": "word_delimiter_graph",
    "split_on_case_change": true,
    "split_on_numerics": true,
    "stem_english_possessive": false,
    "preserve_original": true
  }
}
```

The `word_delimiter_graph` filter splits camelCase identifiers and numeric-alphabetic compounds into sub-tokens (e.g., `SearchQueryParser` → `Search`, `Query`, `Parser`) while preserving the original token for exact matching.

## Analyzer Selection Logic

The indexing pipeline selects an analyzer for each document based on two signals: the document's `content_type` field and the detected language (from the Transform Worker's language detection step).

```
if content_type == "code_snippet":
    use search_code
elif detected_language != "en" and detected_language != null:
    use search_multilingual
else:
    use search_english  (default)
```

The `search_suggest` analyzer is always applied to the `title` and `tags` fields as a secondary sub-field mapping to populate the autocomplete suggestion tokens during indexing.

## Synonym Dictionary Management

The synonym dictionary is stored as a plain text file in the format:
```
# Domain: AI/ML
machine learning, ml => machine learning
artificial intelligence, ai => artificial intelligence
large language model, llm, large language models => large language model
```

The file uses the Solr synonym format. Explicit mapping syntax (`a, b => c`) normalizes multiple forms to a canonical term at query time. Equivalent synonym syntax (`a, b, c`) expands each form to all others.

Synonym dictionary updates do not require a full reindex. In Elasticsearch 8.x with `updateable: true` on the synonym graph filter, a `POST /search-content-read/_reload_search_analyzers` call reloads the synonym dictionary for subsequent queries without downtime. The reload procedure is documented in SOP-041.

## Known Limitations

- **Stemmer over-stemming**: The Porter2 stemmer occasionally reduces distinct technical terms to the same stem (e.g., "Elastic" and "Elasticsearch" may collide under aggressive stemming). The current configuration mitigates this by including `title^3` boost so that exact-match signals in the title field outweigh body stem collisions.
- **Multilingual documents**: Documents with mixed English and non-English content are analyzed with `search_english` if the dominant language is English (> 60% of tokens). The `icu_tokenizer` handles edge cases better for truly multilingual content, but is 30% slower at index time.
- **Synonym graph at index time**: The synonym filter is configured for query-time only expansion. This means the `_termvectors` debug API on indexed documents will not show synonym-expanded terms — only the base stemmed terms are stored in the index.
