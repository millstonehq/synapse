---
id: claude-code-plugins
type: reference
title: "Claude Code Plugins"
status: published
owner: automation
created: "2025-10-29T00:00:00.000Z"
updated: "2025-10-29T00:00:00.000Z"
upstream_url: https://docs.claude.com/en/docs/claude-code/plugins
last_synced: "2025-10-29T00:00:00.000Z"
attribution: "Anthropic"
license: "Anthropic Documentation License"
category: documentation
tags: [reference, claude-code, plugins, marketplace]
summary: Complete guide to extending Claude Code with custom commands, agents, hooks, Skills, and MCP servers through the plugin system.
---

> Extend Claude Code with custom commands, agents, hooks, Skills, and MCP servers through the plugin system.

**Note**: For complete technical specifications and schemas, see [Plugins reference](https://docs.claude.com/en/docs/claude-code/plugins-reference). For marketplace management, see [Plugin marketplaces](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces).

Plugins let you extend Claude Code with custom functionality that can be shared across projects and teams. Install plugins from marketplaces to add pre-built commands, agents, hooks, Skills, and MCP servers, or create your own to automate your workflows.

## Quickstart

Let's create a simple greeting plugin to get you familiar with the plugin system. We'll build a working plugin that adds a custom command, test it locally, and understand the core concepts.

### Prerequisites

* Claude Code installed on your machine
* Basic familiarity with command-line tools

### Create your first plugin

**Step 1: Create the marketplace structure**

```bash
mkdir test-marketplace
cd test-marketplace
```

**Step 2: Create the plugin directory**

```bash
mkdir my-first-plugin
cd my-first-plugin
```

**Step 3: Create the plugin manifest**

```bash
mkdir .claude-plugin
cat > .claude-plugin/plugin.json << 'EOF'
{
  "name": "my-first-plugin",
  "description": "A simple greeting plugin to learn the basics",
  "version": "1.0.0",
  "author": {
    "name": "Your Name"
  }
}
EOF
```

**Step 4: Add a custom command**

```bash
mkdir commands
cat > commands/hello.md << 'EOF'
---
description: Greet the user with a personalized message
---

# Hello Command

Greet the user warmly and ask how you can help them today. Make the greeting personal and encouraging.
EOF
```

**Step 5: Create the marketplace manifest**

```bash
cd ..
mkdir .claude-plugin
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "test-marketplace",
  "owner": {
    "name": "Test User"
  },
  "plugins": [
    {
      "name": "my-first-plugin",
      "source": "./my-first-plugin",
      "description": "My first test plugin"
    }
  ]
}
EOF
```

**Step 6: Install and test your plugin**

```bash
cd ..
claude
```

```shell
/plugin marketplace add ./test-marketplace
/plugin install my-first-plugin@test-marketplace
```

Select "Install now". You'll then need to restart Claude Code in order to use the new plugin.

```shell
/hello
```

You'll see Claude use your greeting command! Check `/help` to see your new command listed.

### Plugin structure overview

Your plugin follows this basic structure:

```
my-first-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata
├── commands/                 # Custom slash commands (optional)
│   └── hello.md
├── agents/                   # Custom agents (optional)
│   └── helper.md
├── skills/                   # Agent Skills (optional)
│   └── my-skill/
│       └── SKILL.md
└── hooks/                    # Event handlers (optional)
    └── hooks.json
```

**Additional components you can add:**

* **Commands**: Create markdown files in `commands/` directory
* **Agents**: Create agent definitions in `agents/` directory
* **Skills**: Create `SKILL.md` files in `skills/` directory
* **Hooks**: Create `hooks/hooks.json` for event handling
* **MCP servers**: Create `.mcp.json` for external tool integration

## Install and manage plugins

Learn how to discover, install, and manage plugins to extend your Claude Code capabilities.

### Add marketplaces

Marketplaces are catalogs of available plugins. Add them to discover and install plugins:

```shell
/plugin marketplace add your-org/claude-plugins
```

```shell
/plugin
```

For detailed marketplace management including Git repositories, local development, and team distribution, see [Plugin marketplaces](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces).

### Install plugins

#### Via interactive menu (recommended for discovery)

```shell
/plugin
```

Select "Browse Plugins" to see available options with descriptions, features, and installation options.

#### Via direct commands (for quick installation)

```shell
# Install a specific plugin
/plugin install formatter@your-org

# Enable a disabled plugin
/plugin enable plugin-name@marketplace-name

# Disable without uninstalling
/plugin disable plugin-name@marketplace-name

# Completely remove a plugin
/plugin uninstall plugin-name@marketplace-name
```

### Verify installation

After installing a plugin:

1. **Check available commands**: Run `/help` to see new commands
2. **Test plugin features**: Try the plugin's commands and features
3. **Review plugin details**: Use `/plugin` → "Manage Plugins" to see what the plugin provides

## Set up team plugin workflows

Configure plugins at the repository level to ensure consistent tooling across your team. When team members trust your repository folder, Claude Code automatically installs specified marketplaces and plugins.

**To set up team plugins:**

1. Add marketplace and plugin configuration to your repository's `.claude/settings.json`
2. Team members trust the repository folder
3. Plugins install automatically for all team members

For complete instructions including configuration examples, marketplace setup, and rollout best practices, see [Configure team marketplaces](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces#how-to-configure-team-marketplaces).

## Develop more complex plugins

Once you're comfortable with basic plugins, you can create more sophisticated extensions.

### Add Skills to your plugin

Plugins can include Agent Skills to extend Claude's capabilities. Skills are model-invoked—Claude autonomously uses them based on the task context.

To add Skills to your plugin, create a `skills/` directory at your plugin root and add Skill folders with `SKILL.md` files. Plugin Skills are automatically available when the plugin is installed.

For complete Skill authoring guidance, see [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills).

### Organize complex plugins

For plugins with many components, organize your directory structure by functionality. For complete directory layouts and organization patterns, see [Plugin directory structure](https://docs.claude.com/en/docs/claude-code/plugins-reference#plugin-directory-structure).

### Test your plugins locally

When developing plugins, use a local marketplace to test changes iteratively.

**Step 1: Set up your development structure**

```bash
mkdir dev-marketplace
cd dev-marketplace
mkdir my-plugin
```

This creates:

```
dev-marketplace/
├── .claude-plugin/marketplace.json  (you'll create this)
└── my-plugin/                        (your plugin under development)
    ├── .claude-plugin/plugin.json
    ├── commands/
    ├── agents/
    └── hooks/
```

**Step 2: Create the marketplace manifest**

```bash
mkdir .claude-plugin
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "dev-marketplace",
  "owner": {
    "name": "Developer"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./my-plugin",
      "description": "Plugin under development"
    }
  ]
}
EOF
```

**Step 3: Install and test**

```bash
cd ..
claude
```

```shell
/plugin marketplace add ./dev-marketplace
/plugin install my-plugin@dev-marketplace
```

Test your plugin components:
* Try your commands with `/command-name`
* Check that agents appear in `/agents`
* Verify hooks work as expected

**Step 4: Iterate on your plugin**

After making changes:

```shell
/plugin uninstall my-plugin@dev-marketplace
/plugin install my-plugin@dev-marketplace
```

Repeat this cycle as you develop and refine your plugin.

### Debug plugin issues

If your plugin isn't working as expected:

1. **Check the structure**: Ensure your directories are at the plugin root, not inside `.claude-plugin/`
2. **Test components individually**: Check each command, agent, and hook separately
3. **Use validation and debugging tools**: See [Debugging and development tools](https://docs.claude.com/en/docs/claude-code/plugins-reference#debugging-and-development-tools)

### Share your plugins

When your plugin is ready to share:

1. **Add documentation**: Include a README.md with installation and usage instructions
2. **Version your plugin**: Use semantic versioning in your `plugin.json`
3. **Create or use a marketplace**: Distribute through plugin marketplaces for easy installation
4. **Test with others**: Have team members test the plugin before wider distribution

## Integration with Synapse

The Synapse documentation framework implements this plugin architecture with:

* **Multiple plugin structure**: Docs and custom plugins
* **Base/custom separation**: Upstream content in `base/`, organization content in `custom/`
* **Marketplace manifest**: `.claude-plugin/marketplace.json` at repository root
* **Local development**: Test plugins in the monorepo before distribution

## See Also

* [Plugin marketplaces](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces) - Creating and managing plugin catalogs
* [Plugins reference](https://docs.claude.com/en/docs/claude-code/plugins-reference) - Technical specifications and schemas
* [Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands) - Understanding custom commands
* [Subagents](https://docs.claude.com/en/docs/claude-code/sub-agents) - Creating and using specialized agents
* [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) - Extend Claude's capabilities
* [Hooks](https://docs.claude.com/en/docs/claude-code/hooks) - Automating workflows with event handlers
* [MCP](https://docs.claude.com/en/docs/claude-code/mcp) - Connecting to external tools and services
