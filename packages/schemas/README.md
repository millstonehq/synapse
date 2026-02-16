# @millstone/synapse-schemas

JSON Schema definitions for the Synapse documentation framework.

## Installation

```bash
npm install @millstone/synapse-schemas
```

This package is also installed automatically as a dependency of `@millstone/synapse-cli`.

## Usage

### Helper functions

Import helper functions to locate schema directories on disk:

```js
import {
  getSchemaDir,
  getFrontmatterSchemaDir,
  getBodyGrammarDir,
  getPluginSchemaDir
} from '@millstone/synapse-schemas';
```

### Direct imports

Import schema files directly using subpath exports:

```js
import adrSchema from '@millstone/synapse-schemas/frontmatter/adr.schema.json' assert { type: 'json' };
import adrGrammar from '@millstone/synapse-schemas/body-grammars/adr.body-grammar.json' assert { type: 'json' };
```

## Schema Categories

### frontmatter/

Document frontmatter validation schemas. Each schema defines the required and optional YAML frontmatter fields for a document type.

Available schemas: adr, agreement, base, capability, meeting, policy, prd, process, reference, runbook, scorecard, sop, sow, standard, system, tdd.

The `base.schema.json` defines common fields (id, title, type, status, owner, created, updated, tags, summary) shared by all document types via `$ref`.

### body-grammars/

Document body structure grammar rules. Each grammar defines the required sections, their order, and content shape (paragraphs, lists, tables, milestones) for a document type's Markdown body.

Available grammars: adr, agreement, capability, meeting, policy, prd, process, reference, runbook, scorecard, sop, sow, standard, system, tdd.

### plugins/

Plugin configuration schemas for the Synapse plugin system.

Available schemas: marketplace, plugin.

## Schema Cascade Resolution

When used with `@millstone/synapse-cli`, schemas are resolved using a cascade:

1. **Local override**: `{projectRoot}/schemas/frontmatter/{name}.schema.json`
2. **This package**: Standard schemas bundled in `@millstone/synapse-schemas`
3. **Error**: With a helpful message

This allows projects to override individual schemas for customization while using the standard set as a fallback.

## License

MIT
