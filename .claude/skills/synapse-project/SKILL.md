---
name: synapse-project
description: Set up and manage Synapse documentation projects. Handles npm-based project initialization, schema cascade configuration, mode detection, versioning, and CI/CD publishing.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Synapse Project Management

Set up, configure, and manage Synapse documentation projects. Covers the full lifecycle from project initialization to npm publishing.

## When to Use

- Setting up a new Synapse documentation project from npm
- Configuring schema cascade (custom schemas overriding base)
- Managing versioning and publishing of Synapse packages
- Understanding the monorepo structure

## Project Setup

### New Project

```bash
mkdir my-docs && cd my-docs
npm init -y
npm install @millstone/synapse-cli

# Create content directories
npx synapse scaffold --type meeting --title "Kickoff Meeting"

# Validate
npx synapse validate
```

The resulting `package.json`:
```json
{
  "private": true,
  "type": "module",
  "scripts": {
    "validate": "synapse validate",
    "scaffold": "synapse scaffold"
  },
  "dependencies": {
    "@millstone/synapse-cli": "^2.0.0"
  }
}
```

## Schema Cascade

The CLI resolves schemas in priority order:

1. **Local custom** — `schemas/frontmatter/custom/*.json`, `schemas/body-grammars/custom/*.json`
2. **Local base** — `schemas/frontmatter/*.json`, `schemas/body-grammars/*.json`
3. **@millstone/synapse-schemas package** — `node_modules/@millstone/synapse-schemas/`

### Adding Custom Schemas

To override a base schema (e.g., add a custom document type):

```bash
mkdir -p schemas/frontmatter/custom
```

Create `schemas/frontmatter/custom/my-type.frontmatter.schema.json`:
```json
{
  "$id": "my-type.frontmatter",
  "type": "object",
  "properties": {
    "type": { "const": "my-type" },
    "title": { "type": "string" }
  },
  "required": ["type", "title"]
}
```

Custom schemas take priority over base schemas with the same filename.

### Adding Custom Body Grammars

Create `schemas/body-grammars/custom/my-type.body-grammar.json`:
```json
{
  "type": "my-type",
  "displayName": "My Custom Type",
  "sections": [
    {
      "id": "overview",
      "title": "Overview",
      "required": true,
      "order": 1,
      "shape": {
        "type": "flow",
        "allowedNodes": ["paragraph", "list", "heading"]
      }
    }
  ]
}
```

## Monorepo Structure

The Synapse monorepo contains four publishable packages:

```
packages/
  cli/          → @millstone/synapse-cli        (main CLI tool)
  schemas/      → @millstone/synapse-schemas    (frontmatter + body-grammar schemas)
  context-mcp/  → @millstone/synapse-context-mcp (MCP server for context)
  site/         → @millstone/synapse-site       (static site generator)
```

All packages use lock-step versioning — same version number across all four.

### Version Bumping

```bash
./scripts/bump-version.sh <new-version>
```

Updates version in all four `package.json` files plus root.

### Publishing

The GitHub Actions workflow (`.github/workflows/publish.yml`) publishes packages in dependency order:
1. `@millstone/synapse-schemas` (no deps)
2. `@millstone/synapse-cli` (depends on schemas)
3. `@millstone/synapse-context-mcp`
4. `@millstone/synapse-site`

Triggered by version tags (`v*.*.*`) or manual workflow_dispatch with dry-run option.

## Configuration

### synapse.config.json

```json
{
  "branding": {
    "siteName": "My Documentation",
    "displayName": "My Documentation",
    "baseUrl": "https://docs.example.com"
  },
  "schemas": {
    "customDir": "schemas/custom",
    "loadBase": true
  }
}
```

## Troubleshooting

### "Cannot find @millstone/synapse-schemas"
The schemas package isn't installed. Run `npm install` or check that `@millstone/synapse-cli` is in your dependencies.

### Validation works locally but not in CI
Ensure CI runs `npm install` before `synapse validate`. The schemas package must be installed.

### Custom schema not being picked up
Check file location: must be in `schemas/frontmatter/custom/` or `schemas/body-grammars/custom/`. The filename must match the pattern `<type>.frontmatter.schema.json` or `<type>.body-grammar.json`.

