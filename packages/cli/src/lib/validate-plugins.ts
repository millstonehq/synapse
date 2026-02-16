import fsExtra from "fs-extra";
import * as path from "path";
import glob from "fast-glob";
import Ajv, { ErrorObject } from "ajv";
import addFormats from "ajv-formats";
import { parseDocument } from "./markdown.js";

const fs = fsExtra;

// ============================================================================
// Types and Interfaces
// ============================================================================

export interface PluginValidationIssue {
  type: "error" | "warning";
  code: string;
  message: string;
  file?: string;
  line?: number;
  field?: string;
}

export interface PluginValidationResult {
  success: boolean;
  issues: PluginValidationIssue[];
  pluginsValidated: number;
  componentsValidated: {
    commands: number;
    agents: number;
    skills: number;
    hooks: number;
    mcpServers: number;
  };
}

interface MarketplaceManifest {
  name: string;
  owner: { name: string };
  version: string;
  description: string;
  repository: { type: string; url: string };
  plugins: Array<{
    name: string;
    description: string;
    source: string;
    tags: string[];
  }>;
  maintainers?: Array<{ name: string; email?: string }>;
  license: string;
}

interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: { name: string; email?: string };
  repository: string;
  license: string;
}

// Valid tool names for agents and skills
const VALID_TOOLS = [
  "Read",
  "Write",
  "Edit",
  "Bash",
  "Grep",
  "Glob",
  "Task",
  "WebFetch",
  "WebSearch",
  "BashOutput",
  "KillShell",
  "Skill",
  "SlashCommand",
  "MultiEdit",
  "LS",
  "TodoWrite",
  "NotebookEdit",
  "AskUserQuestion",
  "ExitPlanMode",
];

// Valid hook types
const VALID_HOOK_TYPES = [
  "pre-commit",
  "post-commit",
  "pre-push",
  "post-push",
  "user-prompt-submit",
  "tool-call",
  "error",
];

// Valid model types
const VALID_MODELS = ["sonnet", "opus", "haiku"];

// ============================================================================
// Schema Validation Utilities
// ============================================================================

async function loadJsonSchema(schemaPath: string): Promise<any> {
  try {
    const content = await fs.readFile(schemaPath, "utf-8");
    return JSON.parse(content);
  } catch (error) {
    throw new Error(`Failed to load schema from ${schemaPath}: ${error}`);
  }
}

function validateAgainstSchema(
  data: any,
  schema: any,
  filePath: string
): PluginValidationIssue[] {
  const issues: PluginValidationIssue[] = [];
  const ajv = new Ajv({ allErrors: true, strict: false, validateSchema: false });
  addFormats(ajv);

  const validate = ajv.compile(schema);
  const valid = validate(data);

  if (!valid && validate.errors) {
    for (const error of validate.errors) {
      const field = error.instancePath
        ? error.instancePath.substring(1).replace(/\//g, ".")
        : error.params.missingProperty || "root";

      let message = "";
      switch (error.keyword) {
        case "required":
          message = `Missing required field "${error.params.missingProperty}"`;
          break;
        case "pattern":
          message = `Field "${field}" does not match required pattern ${error.params.pattern}`;
          break;
        case "type":
          message = `Field "${field}" should be ${error.params.type}`;
          break;
        case "minLength":
          message = `Field "${field}" is too short (minimum ${error.params.limit} characters)`;
          break;
        case "maxLength":
          message = `Field "${field}" is too long (maximum ${error.params.limit} characters)`;
          break;
        case "format":
          message = `Field "${field}" has invalid format (expected ${error.params.format})`;
          break;
        case "enum":
          message = `Field "${field}" must be one of: ${error.params.allowedValues.join(", ")}`;
          break;
        default:
          message = error.message || "Unknown validation error";
      }

      issues.push({
        type: "error",
        code: `SCHEMA_${error.keyword.toUpperCase()}`,
        message,
        file: filePath,
        field,
      });
    }
  }

  return issues;
}

// ============================================================================
// Kebab-case Validation
// ============================================================================

function isKebabCase(str: string): boolean {
  return /^[a-z0-9]+(-[a-z0-9]+)*$/.test(str);
}

function toKebabCase(str: string): string {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/_/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// ============================================================================
// Marketplace Manifest Validation
// ============================================================================

async function validateMarketplaceManifest(
  marketplacePath: string,
  schemaDir: string
): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];

  // Check file exists
  if (!(await fs.pathExists(marketplacePath))) {
    issues.push({
      type: "error",
      code: "MARKETPLACE_NOT_FOUND",
      message: "Marketplace manifest not found",
      file: marketplacePath,
    });
    return issues;
  }

  // Parse JSON
  let manifest: MarketplaceManifest;
  try {
    const content = await fs.readFile(marketplacePath, "utf-8");
    manifest = JSON.parse(content);
  } catch (error) {
    issues.push({
      type: "error",
      code: "MARKETPLACE_INVALID_JSON",
      message: `Invalid JSON: ${error}`,
      file: marketplacePath,
    });
    return issues;
  }

  // Schema validation
  const schemaPath = path.join(schemaDir, "marketplace.schema.json");
  if (await fs.pathExists(schemaPath)) {
    const schema = await loadJsonSchema(schemaPath);
    const schemaIssues = validateAgainstSchema(manifest, schema, marketplacePath);
    issues.push(...schemaIssues);
  }

  // Check plugin sources exist
  // Plugin sources are relative to project root (parent of .claude-plugin/)
  const projectRoot = path.dirname(path.dirname(marketplacePath));
  for (const plugin of manifest.plugins || []) {
    const pluginPath = path.join(
      projectRoot,
      plugin.source.replace(/^\.\//,"")
    );
    if (!(await fs.pathExists(pluginPath))) {
      issues.push({
        type: "error",
        code: "PLUGIN_SOURCE_NOT_FOUND",
        message: `Plugin source path does not exist: ${plugin.source}`,
        file: marketplacePath,
        field: `plugins[${manifest.plugins.indexOf(plugin)}].source`,
      });
    }
  }

  return issues;
}

// ============================================================================
// Plugin Manifest Validation
// ============================================================================

async function validatePluginManifest(
  pluginDir: string,
  expectedName: string,
  schemaDir: string
): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];
  const manifestPath = path.join(pluginDir, ".claude-plugin/plugin.json");

  // Check file exists
  if (!(await fs.pathExists(manifestPath))) {
    issues.push({
      type: "error",
      code: "PLUGIN_MANIFEST_NOT_FOUND",
      message: "Plugin manifest not found",
      file: manifestPath,
    });
    return issues;
  }

  // Parse JSON
  let manifest: PluginManifest;
  try {
    const content = await fs.readFile(manifestPath, "utf-8");
    manifest = JSON.parse(content);
  } catch (error) {
    issues.push({
      type: "error",
      code: "PLUGIN_INVALID_JSON",
      message: `Invalid JSON: ${error}`,
      file: manifestPath,
    });
    return issues;
  }

  // Schema validation
  const schemaPath = path.join(schemaDir, "plugin.schema.json");
  if (await fs.pathExists(schemaPath)) {
    const schema = await loadJsonSchema(schemaPath);
    const schemaIssues = validateAgainstSchema(manifest, schema, manifestPath);
    issues.push(...schemaIssues);
  }

  // Check name matches marketplace entry
  if (manifest.name !== expectedName) {
    issues.push({
      type: "error",
      code: "PLUGIN_NAME_MISMATCH",
      message: `Plugin name "${manifest.name}" does not match marketplace entry "${expectedName}"`,
      file: manifestPath,
      field: "name",
    });
  }

  return issues;
}

// ============================================================================
// Command Validation
// ============================================================================

async function validateCommand(filePath: string): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];

  try {
    const content = await fs.readFile(filePath, "utf-8");
    const { frontmatter } = parseDocument(content);

    // Check required fields
    if (!frontmatter || typeof frontmatter !== "object") {
      issues.push({
        type: "error",
        code: "COMMAND_NO_FRONTMATTER",
        message: "Command file must have YAML frontmatter",
        file: filePath,
      });
      return issues;
    }

    // Check description exists
    if (!frontmatter.description) {
      issues.push({
        type: "error",
        code: "COMMAND_MISSING_DESCRIPTION",
        message: 'Missing required frontmatter field "description"',
        file: filePath,
        field: "description",
      });
    } else if (
      typeof frontmatter.description !== "string" ||
      frontmatter.description.length === 0
    ) {
      issues.push({
        type: "error",
        code: "COMMAND_INVALID_DESCRIPTION",
        message: "Description must be a non-empty string",
        file: filePath,
        field: "description",
      });
    } else if (frontmatter.description.length < 10) {
      issues.push({
        type: "warning",
        code: "COMMAND_SHORT_DESCRIPTION",
        message: `Description is very short (${frontmatter.description.length} chars, recommend at least 10)`,
        file: filePath,
        field: "description",
      });
    }
  } catch (error) {
    issues.push({
      type: "error",
      code: "COMMAND_READ_ERROR",
      message: `Failed to read command file: ${error}`,
      file: filePath,
    });
  }

  return issues;
}

// ============================================================================
// Agent Validation
// ============================================================================

async function validateAgent(filePath: string): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];

  try {
    const content = await fs.readFile(filePath, "utf-8");
    const { frontmatter } = parseDocument(content);

    if (!frontmatter || typeof frontmatter !== "object") {
      issues.push({
        type: "error",
        code: "AGENT_NO_FRONTMATTER",
        message: "Agent file must have YAML frontmatter",
        file: filePath,
      });
      return issues;
    }

    // Check required fields
    const requiredFields = ["name", "description", "tools"];
    for (const field of requiredFields) {
      if (!frontmatter[field]) {
        issues.push({
          type: "error",
          code: "AGENT_MISSING_FIELD",
          message: `Missing required frontmatter field "${field}"`,
          file: filePath,
          field,
        });
      }
    }

    // Validate name is kebab-case
    if (frontmatter.name && !isKebabCase(frontmatter.name)) {
      const suggested = toKebabCase(frontmatter.name);
      issues.push({
        type: "error",
        code: "AGENT_INVALID_NAME",
        message: `Agent name must be kebab-case (got: "${frontmatter.name}", expected: "${suggested}")`,
        file: filePath,
        field: "name",
      });
    }

    // Validate tools
    if (frontmatter.tools) {
      let tools: string[] = [];
      if (typeof frontmatter.tools === "string") {
        tools = frontmatter.tools.split(/,\s*/).map((t: string) => t.trim());
      } else if (Array.isArray(frontmatter.tools)) {
        tools = frontmatter.tools;
      }

      for (const tool of tools) {
        if (!VALID_TOOLS.includes(tool) && tool !== "*") {
          issues.push({
            type: "warning",
            code: "AGENT_UNKNOWN_TOOL",
            message: `Unknown tool "${tool}" (valid tools: ${VALID_TOOLS.join(", ")}, or "*")`,
            file: filePath,
            field: "tools",
          });
        }
      }
    }

    // Validate model if present
    if (frontmatter.model && !VALID_MODELS.includes(frontmatter.model)) {
      issues.push({
        type: "error",
        code: "AGENT_INVALID_MODEL",
        message: `Invalid model "${frontmatter.model}" (valid: ${VALID_MODELS.join(", ")})`,
        file: filePath,
        field: "model",
      });
    }

    // Check filename matches agent name
    const filename = path.basename(filePath, ".md");
    if (frontmatter.name && filename !== frontmatter.name) {
      issues.push({
        type: "warning",
        code: "AGENT_FILENAME_MISMATCH",
        message: `Filename "${filename}.md" does not match agent name "${frontmatter.name}"`,
        file: filePath,
      });
    }
  } catch (error) {
    issues.push({
      type: "error",
      code: "AGENT_READ_ERROR",
      message: `Failed to read agent file: ${error}`,
      file: filePath,
    });
  }

  return issues;
}

// ============================================================================
// Skill Validation
// ============================================================================

async function validateSkill(filePath: string): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];

  // Check filename is SKILL.md
  const filename = path.basename(filePath);
  if (filename !== "SKILL.md") {
    issues.push({
      type: "error",
      code: "SKILL_INVALID_FILENAME",
      message: `Skill file must be named "SKILL.md" (found: "${filename}")`,
      file: filePath,
    });
  }

  try {
    const content = await fs.readFile(filePath, "utf-8");
    const { frontmatter } = parseDocument(content);

    if (!frontmatter || typeof frontmatter !== "object") {
      issues.push({
        type: "error",
        code: "SKILL_NO_FRONTMATTER",
        message: "Skill file must have YAML frontmatter",
        file: filePath,
      });
      return issues;
    }

    // Check required fields
    const requiredFields = ["name", "description"];
    for (const field of requiredFields) {
      if (!frontmatter[field]) {
        issues.push({
          type: "error",
          code: "SKILL_MISSING_FIELD",
          message: `Missing required frontmatter field "${field}"`,
          file: filePath,
          field,
        });
      }
    }

    // Validate name is kebab-case
    if (frontmatter.name && !isKebabCase(frontmatter.name)) {
      const suggested = toKebabCase(frontmatter.name);
      issues.push({
        type: "error",
        code: "SKILL_INVALID_NAME",
        message: `Skill name must be kebab-case (got: "${frontmatter.name}", expected: "${suggested}")`,
        file: filePath,
        field: "name",
      });
    }

    // Check parent directory name matches skill name
    const parentDir = path.basename(path.dirname(filePath));
    if (frontmatter.name && parentDir !== frontmatter.name) {
      issues.push({
        type: "warning",
        code: "SKILL_DIR_MISMATCH",
        message: `Parent directory "${parentDir}" does not match skill name "${frontmatter.name}"`,
        file: filePath,
      });
    }

    // Validate allowed-tools if present
    if (frontmatter["allowed-tools"]) {
      const toolsStr =
        typeof frontmatter["allowed-tools"] === "string"
          ? frontmatter["allowed-tools"]
          : "";
      const tools = toolsStr.split(/,\s*/).map((t) => t.trim());

      for (const tool of tools) {
        if (!VALID_TOOLS.includes(tool) && tool !== "*") {
          issues.push({
            type: "warning",
            code: "SKILL_UNKNOWN_TOOL",
            message: `Unknown tool "${tool}" (valid tools: ${VALID_TOOLS.join(", ")}, or "*")`,
            file: filePath,
            field: "allowed-tools",
          });
        }
      }
    }
  } catch (error) {
    issues.push({
      type: "error",
      code: "SKILL_READ_ERROR",
      message: `Failed to read skill file: ${error}`,
      file: filePath,
    });
  }

  return issues;
}

// ============================================================================
// Hooks Validation
// ============================================================================

async function validateHooks(filePath: string): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];

  try {
    const content = await fs.readFile(filePath, "utf-8");
    let hookConfig: any;

    try {
      hookConfig = JSON.parse(content);
    } catch (error) {
      issues.push({
        type: "error",
        code: "HOOK_INVALID_JSON",
        message: `Invalid JSON: ${error}`,
        file: filePath,
      });
      return issues;
    }

    // Check required fields
    const requiredFields = ["hook", "name", "description", "command"];
    for (const field of requiredFields) {
      if (!hookConfig[field]) {
        issues.push({
          type: "error",
          code: "HOOK_MISSING_FIELD",
          message: `Missing required field "${field}"`,
          file: filePath,
          field,
        });
      }
    }

    // Validate hook type
    if (hookConfig.hook && !VALID_HOOK_TYPES.includes(hookConfig.hook)) {
      issues.push({
        type: "error",
        code: "HOOK_INVALID_TYPE",
        message: `Invalid hook type "${hookConfig.hook}" (valid: ${VALID_HOOK_TYPES.join(", ")})`,
        file: filePath,
        field: "hook",
      });
    }

    // Validate command is non-empty
    if (
      hookConfig.command &&
      (typeof hookConfig.command !== "string" || hookConfig.command.trim() === "")
    ) {
      issues.push({
        type: "error",
        code: "HOOK_INVALID_COMMAND",
        message: "Command must be a non-empty string",
        file: filePath,
        field: "command",
      });
    }

    // Validate install structure if present
    if (hookConfig.install) {
      if (typeof hookConfig.install !== "object") {
        issues.push({
          type: "error",
          code: "HOOK_INVALID_INSTALL",
          message: "Install field must be an object",
          file: filePath,
          field: "install",
        });
      }
    }

    // Validate settings.timeout if present
    if (hookConfig.settings?.timeout !== undefined) {
      const timeout = hookConfig.settings.timeout;
      if (typeof timeout !== "number" || timeout <= 0) {
        issues.push({
          type: "error",
          code: "HOOK_INVALID_TIMEOUT",
          message: "Timeout must be a positive number",
          file: filePath,
          field: "settings.timeout",
        });
      }
    }

    // Validate blocking is boolean if present
    if (
      hookConfig.blocking !== undefined &&
      typeof hookConfig.blocking !== "boolean"
    ) {
      issues.push({
        type: "error",
        code: "HOOK_INVALID_BLOCKING",
        message: "Blocking must be a boolean",
        file: filePath,
        field: "blocking",
      });
    }
  } catch (error) {
    issues.push({
      type: "error",
      code: "HOOK_READ_ERROR",
      message: `Failed to read hooks file: ${error}`,
      file: filePath,
    });
  }

  return issues;
}

// ============================================================================
// MCP Config Validation
// ============================================================================

async function validateMcpConfig(filePath: string): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];

  try {
    const content = await fs.readFile(filePath, "utf-8");
    let mcpConfig: any;

    try {
      mcpConfig = JSON.parse(content);
    } catch (error) {
      issues.push({
        type: "error",
        code: "MCP_INVALID_JSON",
        message: `Invalid JSON: ${error}`,
        file: filePath,
      });
      return issues;
    }

    // Check top-level mcpServers object exists
    if (!mcpConfig.mcpServers) {
      issues.push({
        type: "error",
        code: "MCP_MISSING_SERVERS",
        message: 'Missing required top-level field "mcpServers"',
        file: filePath,
        field: "mcpServers",
      });
      return issues;
    }

    if (typeof mcpConfig.mcpServers !== "object") {
      issues.push({
        type: "error",
        code: "MCP_INVALID_SERVERS",
        message: "mcpServers must be an object",
        file: filePath,
        field: "mcpServers",
      });
      return issues;
    }

    // Validate each server
    for (const [serverName, serverConfig] of Object.entries(
      mcpConfig.mcpServers
    )) {
      const server = serverConfig as any;

      // Check server name is kebab-case
      if (!isKebabCase(serverName)) {
        issues.push({
          type: "warning",
          code: "MCP_SERVER_NAME_NOT_KEBAB",
          message: `Server name "${serverName}" should be kebab-case`,
          file: filePath,
          field: `mcpServers.${serverName}`,
        });
      }

      // Check required fields
      if (!server.command) {
        issues.push({
          type: "error",
          code: "MCP_MISSING_COMMAND",
          message: `Server "${serverName}" missing required field "command"`,
          file: filePath,
          field: `mcpServers.${serverName}.command`,
        });
      }

      if (!server.args) {
        issues.push({
          type: "error",
          code: "MCP_MISSING_ARGS",
          message: `Server "${serverName}" missing required field "args"`,
          file: filePath,
          field: `mcpServers.${serverName}.args`,
        });
      }

      // Validate command is string
      if (server.command && typeof server.command !== "string") {
        issues.push({
          type: "error",
          code: "MCP_INVALID_COMMAND",
          message: `Server "${serverName}" command must be a string`,
          file: filePath,
          field: `mcpServers.${serverName}.command`,
        });
      }

      // Validate args is array
      if (server.args && !Array.isArray(server.args)) {
        issues.push({
          type: "error",
          code: "MCP_INVALID_ARGS",
          message: `Server "${serverName}" args must be an array`,
          file: filePath,
          field: `mcpServers.${serverName}.args`,
        });
      }

      // Warn if metadata is missing
      if (!server.metadata) {
        issues.push({
          type: "warning",
          code: "MCP_MISSING_METADATA",
          message: `Server "${serverName}" should include metadata (name, description, version)`,
          file: filePath,
          field: `mcpServers.${serverName}.metadata`,
        });
      }
    }
  } catch (error) {
    issues.push({
      type: "error",
      code: "MCP_READ_ERROR",
      message: `Failed to read MCP config: ${error}`,
      file: filePath,
    });
  }

  return issues;
}

// ============================================================================
// Plugin Structure Validation
// ============================================================================

async function validatePluginStructure(
  pluginDir: string
): Promise<PluginValidationIssue[]> {
  const issues: PluginValidationIssue[] = [];

  // Check .claude-plugin directory exists
  const claudePluginDir = path.join(pluginDir, ".claude-plugin");
  if (!(await fs.pathExists(claudePluginDir))) {
    issues.push({
      type: "error",
      code: "PLUGIN_MISSING_DIR",
      message: "Plugin must have .claude-plugin directory",
      file: pluginDir,
    });
  }

  // Check component directories are at plugin root, not inside .claude-plugin
  const componentDirs = ["commands", "agents", "skills", "hooks"];
  for (const dir of componentDirs) {
    const wrongPath = path.join(claudePluginDir, dir);
    if (await fs.pathExists(wrongPath)) {
      issues.push({
        type: "error",
        code: "PLUGIN_COMPONENT_WRONG_LOCATION",
        message: `Component directory "${dir}/" must be at plugin root, not inside .claude-plugin/`,
        file: wrongPath,
      });
    }
  }

  return issues;
}

// ============================================================================
// Main Validation Entry Point
// ============================================================================

export async function validatePluginMarketplace(
  rootDir: string,
  schemaDir?: string
): Promise<PluginValidationResult> {
  const allIssues: PluginValidationIssue[] = [];
  const componentsValidated = {
    commands: 0,
    agents: 0,
    skills: 0,
    hooks: 0,
    mcpServers: 0,
  };

  // Determine schema directory
  const schemasDir =
    schemaDir ||
    path.join(rootDir, "schemas/plugins") ||
    path.resolve(process.cwd(), "schemas/plugins");

  // Validate marketplace manifest
  const marketplacePath = path.join(rootDir, ".claude-plugin/marketplace.json");
  const marketplaceIssues = await validateMarketplaceManifest(
    marketplacePath,
    schemasDir
  );
  allIssues.push(...marketplaceIssues);

  // If marketplace is invalid, return early
  if (!await fs.pathExists(marketplacePath)) {
    return {
      success: false,
      issues: allIssues,
      pluginsValidated: 0,
      componentsValidated,
    };
  }

  // Load marketplace to get plugin list
  let marketplace: MarketplaceManifest;
  try {
    const content = await fs.readFile(marketplacePath, "utf-8");
    marketplace = JSON.parse(content);
  } catch (error) {
    return {
      success: false,
      issues: allIssues,
      pluginsValidated: 0,
      componentsValidated,
    };
  }

  // Validate each plugin
  let pluginsValidated = 0;
  for (const plugin of marketplace.plugins || []) {
    const pluginPath = path.join(rootDir, plugin.source.replace(/^\.\//, ""));

    if (!(await fs.pathExists(pluginPath))) {
      continue; // Already reported in marketplace validation
    }

    pluginsValidated++;

    // Validate plugin structure
    const structureIssues = await validatePluginStructure(pluginPath);
    allIssues.push(...structureIssues);

    // Validate plugin manifest
    const manifestIssues = await validatePluginManifest(
      pluginPath,
      plugin.name,
      schemasDir
    );
    allIssues.push(...manifestIssues);

    // Validate commands
    const commandsDir = path.join(pluginPath, "commands");
    if (await fs.pathExists(commandsDir)) {
      const commandFiles = await glob("**/*.md", { cwd: commandsDir });
      for (const file of commandFiles) {
        const filePath = path.join(commandsDir, file);
        const commandIssues = await validateCommand(filePath);
        allIssues.push(...commandIssues);
        componentsValidated.commands++;
      }
    }

    // Validate agents
    const agentsDir = path.join(pluginPath, "agents");
    if (await fs.pathExists(agentsDir)) {
      const agentFiles = await glob("**/*.md", { cwd: agentsDir });
      for (const file of agentFiles) {
        const filePath = path.join(agentsDir, file);
        const agentIssues = await validateAgent(filePath);
        allIssues.push(...agentIssues);
        componentsValidated.agents++;
      }
    }

    // Validate skills
    const skillsDir = path.join(pluginPath, "skills");
    if (await fs.pathExists(skillsDir)) {
      // Find all markdown files in skills directories
      const allSkillFiles = await glob("**/*.md", { cwd: skillsDir });
      const validSkillFiles = await glob("**/SKILL.md", { cwd: skillsDir });
      
      // Report incorrectly named skill files
      for (const file of allSkillFiles) {
        const filename = path.basename(file);
        if (filename !== "SKILL.md") {
          allIssues.push({
            type: "error",
            code: "SKILL_INVALID_FILENAME",
            message: `Skill file must be named "SKILL.md" (found: "${filename}")`,
            file: path.join(skillsDir, file),
          });
        }
      }
      
      // Validate properly named skill files
      for (const file of validSkillFiles) {
        const filePath = path.join(skillsDir, file);
        const skillIssues = await validateSkill(filePath);
        allIssues.push(...skillIssues);
        componentsValidated.skills++;
      }
    }

    // Validate hooks
    const hooksDir = path.join(pluginPath, "hooks");
    if (await fs.pathExists(hooksDir)) {
      const hookFiles = await glob("**/*.json", { cwd: hooksDir });
      for (const file of hookFiles) {
        const filePath = path.join(hooksDir, file);
        const hookIssues = await validateHooks(filePath);
        allIssues.push(...hookIssues);
        componentsValidated.hooks++;
      }
    }

    // Validate MCP config
    const mcpPath = path.join(pluginPath, ".mcp.json");
    if (await fs.pathExists(mcpPath)) {
      const mcpIssues = await validateMcpConfig(mcpPath);
      allIssues.push(...mcpIssues);
      
      // Count servers
      try {
        const content = await fs.readFile(mcpPath, "utf-8");
        const mcpConfig = JSON.parse(content);
        if (mcpConfig.mcpServers) {
          componentsValidated.mcpServers += Object.keys(
            mcpConfig.mcpServers
          ).length;
        }
      } catch (error) {
        // Already reported in validation
      }
    }
  }

  const success = allIssues.filter((i) => i.type === "error").length === 0;

  return {
    success,
    issues: allIssues,
    pluginsValidated,
    componentsValidated,
  };
}
