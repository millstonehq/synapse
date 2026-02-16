# Synapse Plugin Marketplace

The Synapse Plugin Marketplace provides a collection of specialized Claude Code plugins for documentation and software delivery workflows.

## Marketplace Structure

```
synapse/ (the marketplace)
├── .claude-plugin/
│   └── marketplace.json               # Marketplace manifest listing all plugins
├── plugins/
│   └── docs/                         # Documentation authoring
├── packages/
│   ├── cli/                          # Synapse CLI tool
│   └── context-mcp/                  # Context MCP server
└── content/                          # Documentation content
```

## Available Plugins

### Documentation Framework Plugin

**Status:** Complete

Comprehensive documentation authoring with Obsidian vault optimization, content curation, and knowledge graph management.

**Features:**
- 7 specialized agents (connection, content-curator, metadata, MOC, review, tag, vault-optimizer)
- 2 skills (data-model-visualizer, system-mapper)
- Base + custom directory structure

**Best For:** Technical writers, documentation leads, knowledge managers

**Installation:**
```bash
/plugin install docs@synapse
```

## Installation

### Setting Up the Marketplace

```bash
# Add Synapse as a marketplace
/plugin marketplace add https://github.com/millstonehq/synapse

# Or for private repos
/plugin marketplace add git@github.com:your-org/synapse.git
```

### Installing Plugins

```bash
# Install the docs plugin
/plugin install docs@synapse
```

### Local Development

When working directly in the Synapse repo, plugins are automatically available from the local `.claude/` directory or from the `plugins/` structure.

## Plugin Architecture

### Plugin Manifest Structure

Each plugin has a `.claude-plugin/plugin.json` manifest:

```json
{
  "id": "plugin-id",
  "name": "Plugin Name",
  "version": "1.0.0",
  "description": "Plugin description",
  "dependencies": {
    "plugins": []
  },
  "components": {
    "agents": { "base": [], "custom": [] },
    "skills": { "base": [], "custom": [] },
    "hooks": [],
    "mcp": []
  }
}
```

### Base vs Custom Components

Each plugin separates components into:

- **base/**: Version-controlled, maintained by Synapse
- **custom/**: Gitignored, for organization-specific extensions

This allows you to:
1. Pull upstream updates without losing customizations
2. Share base components across teams
3. Keep proprietary patterns private

### Customization Workflow

```bash
# Custom directories are created automatically:
plugins/
  └── docs/
      ├── agents/
      │   ├── base/          # Version controlled
      │   └── custom/        # Your custom agents (gitignored)
      └── skills/
          ├── base/          # Version controlled
          └── custom/        # Your custom skills (gitignored)

# Add your custom agent
cat > plugins/docs/agents/custom/my-company-agent.md <<'EOF'
---
name: my-company-agent
description: Company-specific documentation patterns
tools: Read, Write, Edit
---
[Your custom agent content]
EOF

# Custom agents are automatically discovered
```

## Contributing

We welcome contributions! Priority areas:

1. **Add skills** for automation and code generation
2. **Create custom agent templates** for common patterns
3. **Improve documentation** and examples
4. **Build new plugins** for your stack

See individual plugin READMEs for specific contribution opportunities.

## Support

- **Issues:** https://github.com/millstonehq/synapse/issues
- **Discussions:** https://github.com/millstonehq/synapse/discussions

## License

MIT - See LICENSE file for details
