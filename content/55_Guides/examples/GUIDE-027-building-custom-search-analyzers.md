---
id: GUIDE-027
type: guide
title: Building Custom Search Analyzers
status: review
owner: Developer Experience
created: '2025-07-19T07:03:15.935Z'
updated: '2026-07-14T09:35:32.765Z'
tags:
  - guide
  - search-platform
summary: Building Custom Search Analyzers
audience: customer
related_systems:
  - SYSTEM-022
  - SYSTEM-023
related_sops:
  - SOP-050
  - SOP-049
example: true
---

## Why Custom Analyzers

Elasticsearch's built-in analyzers (standard, english, whitespace) cover common cases well, but domain-specific content often requires custom analysis chains. Product catalogs with part numbers, medical records with clinical terminology, or multilingual content with code-switching all benefit from analyzers tuned for their specific token patterns. A poorly chosen analyzer is one of the most common causes of poor recall and precision in search.

## Anatomy of an Analyzer

An Elasticsearch analyzer is a pipeline of three components:

1. **Character filters** - Transform the raw text before tokenization (e.g., strip HTML tags, normalize unicode, replace custom patterns)
2. **Tokenizer** - Split the text into tokens (e.g., standard word-boundary tokenizer, whitespace tokenizer, n-gram tokenizer)
3. **Token filters** - Transform tokens after splitting (e.g., lowercase, stemmer, synonym filter, stop word removal)

Custom analyzers are defined in the index settings and referenced by field mappings. A custom analyzer defined at index creation time cannot be modified without a full reindex — plan your analyzer chain carefully before creating a production index.

## Defining a Custom Analyzer

Here is an example custom analyzer for technical documentation with stemming and synonym support:

```json
{
  "settings": {
    "analysis": {
      "filter": {
        "tech_synonyms": {
          "type": "synonym",
          "synonyms_path": "analysis/tech-synonyms.txt"
        },
        "english_stemmer": {
          "type": "stemmer",
          "language": "english"
        }
      },
      "analyzer": {
        "tech_docs_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "tech_synonyms", "english_stemmer"]
        }
      }
    }
  }
}
```

## Testing Your Analyzer

Always test your analyzer before deploying to a production index. Use the Analyze API to verify tokenization output:

```
POST /_analyze
{
  "analyzer": "tech_docs_analyzer",
  "text": "Kubernetes cluster configuration"
}
```

Review the output tokens and verify they match what you expect queries to produce. Pay special attention to how edge cases are handled: numbers, hyphenated terms, and mixed-language strings.

## Common Pitfalls

- **Using different analyzers for indexing and querying**: The `analyzer` setting applies at both index time and query time. If you want different analysis at query time (e.g., no stemming at query time), use a separate `search_analyzer` field mapping property.
- **Overly aggressive stemming causing false positives**: English stemmers can collapse unrelated words (e.g., "universe" and "universal" share a stem). Test your stemmed results against a representative query set before deploying.
- **Forgetting to update the search analyzer when adding synonyms**: After updating a synonyms file, reload the search analyzers with `POST /<index>/_reload_search_analyzers` to apply changes without a reindex.
