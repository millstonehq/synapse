# Synapse Documentation Framework

Obsidian-first, Git-native documentation framework with reusable templates, realistic examples, strict validation, and self-hosted static publishing and CMS.

## Features
- Obsidian-compatible Markdown with YAML Properties
- Templates for Policies, Standards, Processes, SOPs, Runbooks, Systems, ADRs, PRDs, Capabilities, and TDDs
- Strict validation (schemas, cross-links, naming/placement)
- Quartz 4 static site (graph, backlinks, tags)
- Decap CMS (self-hosted) for non-technical editing
- Formatting and validation commands

## Quick Start

### Prerequisites
- Node 20+
- Git

### Option A: npm install (recommended)

```bash
# Scaffold a new Synapse documentation project
npx @millstone/synapse-cli scaffold --type adr --title "My First ADR"

# Or set up a full project with package.json
npm init -y
npm install @millstone/synapse-cli

# Create documents
npx synapse scaffold --type policy --title "Security Policy" --owner "Security Team"
npx synapse scaffold --type sop --title "Deployment Procedure"

# Validate and format
npx synapse validate
npx synapse format --write
```

### Daily Usage

1. **Create documents**: Use `synapse scaffold` to create new documents from templates
```bash
npx synapse scaffold --type adr --title "Use React for Frontend"
```

2. **Validate**: Run before committing
```bash
npx synapse validate
```

3. **Format**: Auto-format document body sections
```bash
npx synapse format --write
```

### Pro Tips

1. **Run validation before committing**: `npx synapse validate` catches schema, naming, and cross-link errors
2. **Use strict mode**: Enabled by default; use `--no-strict` to allow filename/title mismatches
3. **Check examples**: Look in `content/*/examples/` for valid document samples
4. **Format automatically**: `npx synapse format --write` fixes body section structure

## Packages

This monorepo contains the following packages:

| Package | Description |
|---------|-------------|
| [@millstone/synapse-cli](packages/cli/) | CLI for validation, formatting, scaffolding, and PDF generation |
| [@millstone/synapse-schemas](packages/schemas/) | JSON Schema definitions for frontmatter, body grammars, and plugins |
| [@millstone/synapse-site](packages/site/) | Quartz 4 static site generator configuration |
| [@millstone/synapse-context-mcp](packages/context-mcp/) | MCP server for AI-assisted documentation |
| [synapse-capabilities](packages/capabilities/) | Python capability discovery, flow planning, and evidence coverage engine |

The optional [capability engine](packages/capabilities/) is a standalone Python
package maintained in this monorepo. It shares Synapse CI and GitHub release
infrastructure while retaining its own version and no Node runtime dependency.
Normal documentation validation does not run application tests. See the
[capability mapping design](content/90_Architecture/TDDs/capability-mapping-and-model-based-testing.md)
for package boundaries and evidence limits.

## Configuration

Synapse uses `synapse.config.json` at the repository root for project customization.

### Folder Structure Override

By default, documents are organized in predefined folders:
- Policies -> `content/10_Policies`
- Systems -> `content/70_Systems`
- ADRs -> `content/90_Architecture/ADRs`
- etc.

You can customize folder locations:

```json
{
  "folders": {
    "system": "75_Systems",
    "policy": "15_Policies"
  }
}
```

The CLI validation automatically adapts to custom folder locations. Unmapped types continue using their default folders.

### Branding Configuration

```json
{
  "branding": {
    "siteName": "My Company Docs",
    "displayName": "My Company Documentation",
    "baseUrl": "https://docs.example.com",
    "logo": "tools/pdf/logo.png",
    "theme": {
      "lightMode": { "primary": "#1976d2" },
      "darkMode": { "primary": "#90caf9" }
    }
  }
}
```

### Decap CMS Backend

```json
{
  "decap": {
    "enabled": true,
    "backend": "github",
    "repo": "org/repo",
    "oauthProxy": "https://oauth.example.com"
  }
}
```

### Schema Resolution

The CLI resolves schemas using a cascade:

1. **Local override**: `{projectRoot}/schemas/frontmatter/*.schema.json` -- for project-specific customizations
2. **@millstone/synapse-schemas package**: Installed via npm -- the standard schema set
3. **Error**: With a helpful message explaining how to fix

This allows projects to override individual schemas while falling back to the standard set. The same cascade applies to body grammar rules.

```json
{
  "schemas": {
    "customDir": "schemas/custom",
    "loadBase": true
  }
}
```

## Decap CMS (Self-hosted)
- Serves under /admin
- Configure backend for your Git provider (GitHub/GitLab/Gitea)
- Use an OAuth proxy to exchange auth codes for tokens
- Collections mirror type folders; fields map to schema fields
- Field-level "required" and "pattern" constraints provide early feedback

## Quartz 4 Site
- contentDir: ./content
- Graph, backlinks, tags enabled
- Publish via CI to internal static hosting

## Testing

The Synapse CLI includes a comprehensive test suite using Jest with TypeScript support. Tests ensure code quality, prevent regressions, and maintain coverage above 80%.

### Running Tests

```bash
# Run all tests with coverage
npm test

# Generate detailed coverage report
npm run coverage:report
```

### Coverage Requirements

The project enforces minimum coverage thresholds of 80% for statements, branches, functions, and lines.

## Contributing
- Write tests for new features and bug fixes.
- Run `npm test` before committing.
- Ensure test coverage remains above 80%.
- Run `synapse validate` before committing or pushing.

## License

MIT
