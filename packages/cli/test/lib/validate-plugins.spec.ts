import * as path from "path";
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fsExtra from "fs-extra";
import { jest } from '@jest/globals';
import { validatePluginMarketplace } from "../../src/lib/validate-plugins.js";

const fs = fsExtra;

// ESM __dirname replacement
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe("Plugin Validation", () => {
  const fixturesDir = path.join(__dirname, "../fixtures/plugins");
  const schemasDir = path.resolve(__dirname, "../../schemas/plugins");
  
  beforeEach(async () => {
    // Clean up fixtures directory
    await fs.remove(fixturesDir);
    await fs.ensureDir(fixturesDir);
  });

  afterEach(async () => {
    // Clean up after tests
    await fs.remove(fixturesDir);
  });

  describe("validatePluginMarketplace", () => {
    it("should validate a valid marketplace with all plugin components", async () => {
      // Create a valid marketplace structure
      const testDir = path.join(fixturesDir, "valid-marketplace");
      await fs.ensureDir(testDir);

      // Create marketplace.json
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));
      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace for plugin validation",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "A test plugin for validation",
            source: "./plugins/test-plugin",
            tags: ["test", "validation"]
          }
        ],
        license: "MIT"
      });

      // Create plugin structure
      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));

      // Plugin manifest
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "A test plugin for validation testing",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      // Command
      await fs.ensureDir(path.join(pluginDir, "commands"));
      await fs.writeFile(
        path.join(pluginDir, "commands/test-command.md"),
        `---
description: A test command for validation
---

# Test Command

This is a test command.
`
      );

      // Agent
      await fs.ensureDir(path.join(pluginDir, "agents/base"));
      await fs.writeFile(
        path.join(pluginDir, "agents/base/test-agent.md"),
        `---
name: test-agent
description: A test agent for validation
tools: Read, Write, Edit
---

# Test Agent

This is a test agent.
`
      );

      // Skill
      await fs.ensureDir(path.join(pluginDir, "skills/test-skill"));
      await fs.writeFile(
        path.join(pluginDir, "skills/test-skill/SKILL.md"),
        `---
name: test-skill
description: A test skill for validation
---

# Test Skill

This is a test skill.
`
      );

      // Hook
      await fs.ensureDir(path.join(pluginDir, "hooks"));
      await fs.writeJson(path.join(pluginDir, "hooks/test-hook.json"), {
        hook: "pre-commit",
        name: "Test Hook",
        description: "A test hook for validation",
        command: "echo test",
        blocking: true
      });

      // MCP config
      await fs.writeJson(path.join(pluginDir, ".mcp.json"), {
        mcpServers: {
          "test-server": {
            command: "node",
            args: ["server.js"],
            metadata: {
              name: "Test MCP Server",
              description: "A test MCP server",
              version: "1.0.0"
            }
          }
        }
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(true);
      expect(result.issues).toHaveLength(0);
      expect(result.pluginsValidated).toBe(1);
      expect(result.componentsValidated.commands).toBe(1);
      expect(result.componentsValidated.agents).toBe(1);
      expect(result.componentsValidated.skills).toBe(1);
      expect(result.componentsValidated.hooks).toBe(1);
      expect(result.componentsValidated.mcpServers).toBe(1);
    });

    it("should report error when marketplace manifest is missing", async () => {
      const testDir = path.join(fixturesDir, "no-marketplace");
      await fs.ensureDir(testDir);

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "MARKETPLACE_NOT_FOUND"
        })
      );
    });

    it("should report error for invalid JSON in marketplace", async () => {
      const testDir = path.join(fixturesDir, "invalid-json");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));
      await fs.writeFile(
        path.join(testDir, ".claude-plugin/marketplace.json"),
        "{ invalid json"
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "MARKETPLACE_INVALID_JSON"
        })
      );
    });

    it("should report error when plugin source does not exist", async () => {
      const testDir = path.join(fixturesDir, "missing-plugin");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace with missing plugin",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "missing-plugin",
            description: "This plugin doesn't exist",
            source: "./plugins/missing-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "PLUGIN_SOURCE_NOT_FOUND"
        })
      );
    });

    it("should report error when plugin name doesn't match marketplace", async () => {
      const testDir = path.join(fixturesDir, "name-mismatch");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "expected-name",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "wrong-name",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "PLUGIN_NAME_MISMATCH"
        })
      );
    });

    it("should report error for command missing description", async () => {
      const testDir = path.join(fixturesDir, "invalid-command");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "commands"));
      await fs.writeFile(
        path.join(pluginDir, "commands/bad-command.md"),
        `---
title: Bad Command
---

# Bad Command

Missing description field.
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "COMMAND_MISSING_DESCRIPTION"
        })
      );
    });

    it("should report error for agent with non-kebab-case name", async () => {
      const testDir = path.join(fixturesDir, "invalid-agent");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/BadAgentName.md"),
        `---
name: BadAgentName
description: Agent with camelCase name
tools: Read, Write
---

# Bad Agent

This agent has a non-kebab-case name.
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "AGENT_INVALID_NAME"
        })
      );
    });

    it("should report error for skill not named SKILL.md", async () => {
      const testDir = path.join(fixturesDir, "invalid-skill-name");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "skills/test-skill"));
      await fs.writeFile(
        path.join(pluginDir, "skills/test-skill/skill.md"),
        `---
name: test-skill
description: Test skill with wrong filename
---

# Bad Skill

Should be named SKILL.md
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "SKILL_INVALID_FILENAME"
        })
      );
    });

    it("should accept supporting markdown beside and beneath SKILL.md", async () => {
      // The skills spec encourages supporting files: reference material sits
      // either next to SKILL.md or under references/, scripts/, examples/.
      // Flagging those as "misnamed skills" broke every skill shipping docs.
      const testDir = path.join(fixturesDir, "skill-with-references");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "skills/test-skill/references"));
      await fs.writeFile(
        path.join(pluginDir, "skills/test-skill/SKILL.md"),
        `---
name: test-skill
description: A test skill that ships reference material
---

# Test Skill

See [the checklist](references/checklist.md) and [notes](notes.md).
`
      );
      // Supporting file in a subdirectory.
      await fs.writeFile(
        path.join(pluginDir, "skills/test-skill/references/checklist.md"),
        "# Checklist\n\n- item\n"
      );
      // Supporting file directly beside SKILL.md.
      await fs.writeFile(
        path.join(pluginDir, "skills/test-skill/notes.md"),
        "# Notes\n\nExtended reference.\n"
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.issues).not.toContainEqual(
        expect.objectContaining({ code: "SKILL_INVALID_FILENAME" })
      );
      expect(result.success).toBe(true);
      // The skill is counted once, not once per markdown file.
      expect(result.componentsValidated.skills).toBe(1);
    });

    it("should report error for invalid hook type", async () => {
      const testDir = path.join(fixturesDir, "invalid-hook");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "hooks"));
      await fs.writeJson(path.join(pluginDir, "hooks/bad-hook.json"), {
        hook: "invalid-hook-type",
        name: "Bad Hook",
        description: "Hook with invalid type",
        command: "echo test"
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "HOOK_INVALID_TYPE"
        })
      );
    });

    it("should report error for MCP server missing command field", async () => {
      const testDir = path.join(fixturesDir, "invalid-mcp");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.writeJson(path.join(pluginDir, ".mcp.json"), {
        mcpServers: {
          "bad-server": {
            args: ["server.js"]
            // Missing command field
          }
        }
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "MCP_MISSING_COMMAND"
        })
      );
    });

    it("should report warning for MCP server missing metadata", async () => {
      const testDir = path.join(fixturesDir, "mcp-no-metadata");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.writeJson(path.join(pluginDir, ".mcp.json"), {
        mcpServers: {
          "test-server": {
            command: "node",
            args: ["server.js"]
            // Missing metadata (should warn)
          }
        }
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "warning",
          code: "MCP_MISSING_METADATA"
        })
      );
    });

    it("should warn for command with short description", async () => {
      const testDir = path.join(fixturesDir, "short-desc");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "commands"));
      await fs.writeFile(
        path.join(pluginDir, "commands/short.md"),
        `---
description: Short
---

# Short Description

This command has a very short description.
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "warning",
          code: "COMMAND_SHORT_DESCRIPTION"
        })
      );
    });

    it("should validate agents with valid model types", async () => {
      const testDir = path.join(fixturesDir, "valid-models");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/sonnet-agent.md"),
        `---
name: sonnet-agent
description: Agent using sonnet model
tools: Read, Write
model: sonnet
---

# Sonnet Agent
`
      );

      await fs.writeFile(
        path.join(pluginDir, "agents/haiku-agent.md"),
        `---
name: haiku-agent
description: Agent using haiku model
tools: Read
model: haiku
---

# Haiku Agent
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(true);
      expect(result.componentsValidated.agents).toBe(2);
    });

    it("should report error for agent with invalid model", async () => {
      const testDir = path.join(fixturesDir, "invalid-model");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/bad-model.md"),
        `---
name: bad-model
description: Agent with invalid model
tools: Read
model: gpt-4
---

# Bad Model
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "AGENT_INVALID_MODEL"
        })
      );
    });

    it("should report warning for agent with unknown tool", async () => {
      const testDir = path.join(fixturesDir, "unknown-tool");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/test-agent.md"),
        `---
name: test-agent
description: Agent with unknown tool
tools: Read, UnknownTool
---

# Test Agent
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "warning",
          code: "AGENT_UNKNOWN_TOOL"
        })
      );
    });

    it("should handle agent with tools as array", async () => {
      const testDir = path.join(fixturesDir, "tools-array");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      // Create agent with frontmatter that has tools as array (YAML array)
      await fs.writeFile(
        path.join(pluginDir, "agents/array-agent.md"),
        `---
name: array-agent
description: Agent with tools as array
tools:
  - Read
  - Write
  - Edit
---

# Array Agent
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(true);
      expect(result.componentsValidated.agents).toBe(1);
    });

    it("should report error for agent missing required fields", async () => {
      const testDir = path.join(fixturesDir, "agent-missing-fields");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/incomplete-agent.md"),
        `---
name: incomplete-agent
---

# Incomplete Agent

Missing description and tools.
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues.filter(i => i.code === "AGENT_MISSING_FIELD").length).toBeGreaterThanOrEqual(2);
    });

    it("should report error for skill missing required fields", async () => {
      const testDir = path.join(fixturesDir, "skill-missing-fields");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "skills/incomplete-skill"));
      await fs.writeFile(
        path.join(pluginDir, "skills/incomplete-skill/SKILL.md"),
        `---
name: incomplete-skill
---

# Incomplete Skill

Missing description.
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "SKILL_MISSING_FIELD"
        })
      );
    });

    it("should validate wildcard tools", async () => {
      const testDir = path.join(fixturesDir, "wildcard-tools");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/all-tools.md"),
        `---
name: all-tools
description: Agent with all tools
tools: "*"
---

# All Tools Agent
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(true);
    });

    it("should report error for invalid plugin JSON", async () => {
      const testDir = path.join(fixturesDir, "invalid-plugin-json");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeFile(
        path.join(pluginDir, ".claude-plugin/plugin.json"),
        "{ invalid json"
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "PLUGIN_INVALID_JSON"
        })
      );
    });

    it("should report error for command with invalid description type", async () => {
      const testDir = path.join(fixturesDir, "invalid-desc-type");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "commands"));
      // Create command with description as empty string
      await fs.writeFile(
        path.join(pluginDir, "commands/bad-desc.md"),
        `---
description: ""
---

# Bad Description
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      // Empty string is still invalid - should be caught
      expect(result.issues.some(i =>
        i.code === "COMMAND_INVALID_DESCRIPTION" ||
        i.code === "COMMAND_SHORT_DESCRIPTION" ||
        i.code === "COMMAND_MISSING_DESCRIPTION"
      )).toBe(true);
    });

    it("should report error for agent with no frontmatter", async () => {
      const testDir = path.join(fixturesDir, "agent-no-frontmatter");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/no-fm.md"),
        `# No Frontmatter Agent

This agent has no frontmatter.
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      // When frontmatter is missing, it reports missing fields
      expect(result.issues.filter(i => i.code === "AGENT_MISSING_FIELD").length).toBeGreaterThanOrEqual(2);
    });

    it("should report error for MCP server with invalid args type", async () => {
      const testDir = path.join(fixturesDir, "mcp-invalid-args");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.writeJson(path.join(pluginDir, ".mcp.json"), {
        mcpServers: {
          "bad-server": {
            command: "node",
            args: "not-an-array"
          }
        }
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "MCP_INVALID_ARGS"
        })
      );
    });

    it("should report error for hooks with invalid timeout", async () => {
      const testDir = path.join(fixturesDir, "hook-invalid-timeout");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "hooks"));
      await fs.writeJson(path.join(pluginDir, "hooks/bad-timeout.json"), {
        hook: "pre-commit",
        name: "Bad Timeout",
        description: "Hook with invalid timeout",
        command: "echo test",
        settings: {
          timeout: -5
        }
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "HOOK_INVALID_TIMEOUT"
        })
      );
    });

    it("should warn for agent filename mismatch", async () => {
      const testDir = path.join(fixturesDir, "agent-filename-mismatch");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "agents"));
      await fs.writeFile(
        path.join(pluginDir, "agents/wrong-filename.md"),
        `---
name: correct-name
description: Agent with mismatched filename
tools: Read
---

# Mismatched
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "warning",
          code: "AGENT_FILENAME_MISMATCH"
        })
      );
    });

    it("should warn for skill directory name mismatch", async () => {
      const testDir = path.join(fixturesDir, "skill-dir-mismatch");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.ensureDir(path.join(pluginDir, "skills/wrong-dir-name"));
      await fs.writeFile(
        path.join(pluginDir, "skills/wrong-dir-name/SKILL.md"),
        `---
name: correct-skill-name
description: Skill with mismatched directory
---

# Skill
`
      );

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "warning",
          code: "SKILL_DIR_MISMATCH"
        })
      );
    });

    it("should report error for MCP missing mcpServers", async () => {
      const testDir = path.join(fixturesDir, "mcp-no-servers");
      await fs.ensureDir(testDir);
      await fs.ensureDir(path.join(testDir, ".claude-plugin"));

      await fs.writeJson(path.join(testDir, ".claude-plugin/marketplace.json"), {
        name: "test-marketplace",
        owner: { name: "Test Owner" },
        version: "1.0.0",
        description: "A test marketplace",
        repository: { type: "git", url: "https://github.com/test/test" },
        plugins: [
          {
            name: "test-plugin",
            description: "Test plugin",
            source: "./plugins/test-plugin",
            tags: ["test"]
          }
        ],
        license: "MIT"
      });

      const pluginDir = path.join(testDir, "plugins/test-plugin");
      await fs.ensureDir(pluginDir);
      await fs.ensureDir(path.join(pluginDir, ".claude-plugin"));
      await fs.writeJson(path.join(pluginDir, ".claude-plugin/plugin.json"), {
        name: "test-plugin",
        version: "1.0.0",
        description: "Test plugin",
        author: { name: "Test Author" },
        repository: "https://github.com/test/test",
        license: "MIT"
      });

      await fs.writeJson(path.join(pluginDir, ".mcp.json"), {
        someOtherField: "value"
      });

      const result = await validatePluginMarketplace(testDir, schemasDir);

      expect(result.success).toBe(false);
      expect(result.issues).toContainEqual(
        expect.objectContaining({
          type: "error",
          code: "MCP_MISSING_SERVERS"
        })
      );
    });
  });
});
