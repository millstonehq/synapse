import fsExtra from 'fs-extra';
import * as path from 'path';
import { getTypeRegistry } from './type-registry.js';

const fs = fsExtra;

export interface SynapseConfig {
  branding?: {
    siteName?: string;
    displayName?: string;
    baseUrl?: string;
    logo?: string;
    theme?: {
      lightMode?: { primary: string };
      darkMode?: { primary: string };
    };
  };
  folders?: {
    [docType: string]: string;
  };
  decap?: {
    enabled?: boolean;
    backend?: 'github' | 'gitlab' | 'bitbucket';
    repo?: string;
    oauthProxy?: string;
  };
  schemas?: {
    customDir?: string;
    loadBase?: boolean;
  };
}

let cachedConfig: SynapseConfig | null = null;
let cachedConfigPath: string | null = null;

/**
 * Find synapse.config.json by traversing up from current directory
 */
function findConfigPath(startDir: string = process.cwd()): string | null {
  let currentDir = startDir;

  // Traverse up to 10 levels
  for (let i = 0; i < 10; i++) {
    const configPath = path.join(currentDir, 'synapse.config.json');
    if (fs.existsSync(configPath)) {
      return configPath;
    }

    const parentDir = path.dirname(currentDir);
    if (parentDir === currentDir) {
      // Reached root
      break;
    }
    currentDir = parentDir;
  }

  return null;
}

/**
 * Load synapse.config.json from the repository root
 * Returns null if config file doesn't exist (graceful fallback to defaults)
 */
export function loadConfig(cwd?: string): SynapseConfig | null {
  const startDir = cwd || process.cwd();

  // Return cached config if same directory
  if (cachedConfig && cachedConfigPath) {
    const currentConfigPath = findConfigPath(startDir);
    if (currentConfigPath === cachedConfigPath) {
      return cachedConfig;
    }
  }

  const configPath = findConfigPath(startDir);

  if (!configPath) {
    // No config file found - this is OK, we'll use defaults
    cachedConfig = null;
    cachedConfigPath = null;
    return null;
  }

  try {
    const configContent = fs.readFileSync(configPath, 'utf-8');
    const config = JSON.parse(configContent) as SynapseConfig;

    cachedConfig = config;
    cachedConfigPath = configPath;

    return config;
  } catch (error) {
    // Invalid JSON or read error - return null and fall back to defaults
    console.warn(`Warning: Could not load synapse.config.json: ${error}`);
    return null;
  }
}

/**
 * Get the expected folder for a document type
 * Reads from config if available, falls back to default from type registry
 */
export function getExpectedFolder(type: string, cwd?: string): string {
  const config = loadConfig(cwd);

  // Check if config has custom folder mapping
  if (config?.folders && config.folders[type]) {
    const customFolder = config.folders[type];
    // Ensure it starts with content/
    return customFolder.startsWith('content/')
      ? customFolder
      : `content/${customFolder}`;
  }

  // Fall back to default from type registry
  const registry = getTypeRegistry();
  const meta = registry[type];
  if (!meta) throw new Error(`Unknown document type: ${type}`);
  return `content/${meta.folder}`;
}

/**
 * Get the folder name (without content/ prefix) for a document type
 */
export function getFolderName(type: string, cwd?: string): string {
  const fullPath = getExpectedFolder(type, cwd);
  return fullPath.replace(/^content\//, '');
}

/**
 * Clear the config cache (useful for testing)
 */
export function clearConfigCache(): void {
  cachedConfig = null;
  cachedConfigPath = null;
}
