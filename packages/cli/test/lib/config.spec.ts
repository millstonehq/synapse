import * as path from "path";
import * as os from "os";
import fsExtra from "fs-extra";
const fs = fsExtra;
import { jest } from "@jest/globals";
import {
  loadConfig,
  getExpectedFolder,
  getFolderName,
  clearConfigCache,
  type SynapseConfig,
} from "../../src/lib/config.js";

describe("config module", () => {
  let tmpDir: string;

  beforeEach(() => {
    // Create a temporary directory for each test
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "synapse-config-test-"));
    clearConfigCache();
  });

  afterEach(() => {
    // Clean up
    if (fs.existsSync(tmpDir)) {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
    clearConfigCache();
  });

  describe("loadConfig", () => {
    it("should return null when no config file exists", () => {
      const config = loadConfig(tmpDir);
      expect(config).toBeNull();
    });

    it("should load a valid config file", () => {
      const configData: SynapseConfig = {
        branding: {
          siteName: "Test Site",
          displayName: "Test Display",
        },
        folders: {
          system: "75_Systems",
        },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      const config = loadConfig(tmpDir);
      expect(config).not.toBeNull();
      expect(config?.branding?.siteName).toBe("Test Site");
      expect(config?.folders?.system).toBe("75_Systems");
    });

    it("should find config file by traversing up directories", () => {
      const configData: SynapseConfig = {
        branding: { siteName: "Root Config" },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      // Create nested directory
      const nestedDir = path.join(tmpDir, "level1", "level2", "level3");
      fs.mkdirSync(nestedDir, { recursive: true });

      // Load config from nested directory - should traverse up and find it
      const config = loadConfig(nestedDir);
      expect(config).not.toBeNull();
      expect(config?.branding?.siteName).toBe("Root Config");
    });

    it("should cache loaded config for same directory", () => {
      const configData: SynapseConfig = {
        branding: { siteName: "Cached Config" },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      // First load
      const config1 = loadConfig(tmpDir);
      expect(config1?.branding?.siteName).toBe("Cached Config");

      // Modify the file
      const modifiedData: SynapseConfig = {
        branding: { siteName: "Modified Config" },
      };
      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(modifiedData, null, 2)
      );

      // Second load - should still return cached version
      const config2 = loadConfig(tmpDir);
      expect(config2?.branding?.siteName).toBe("Cached Config");
    });

    it("should reload config when clearConfigCache is called", () => {
      const configData: SynapseConfig = {
        branding: { siteName: "Original Config" },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      // First load
      const config1 = loadConfig(tmpDir);
      expect(config1?.branding?.siteName).toBe("Original Config");

      // Clear cache
      clearConfigCache();

      // Modify the file
      const modifiedData: SynapseConfig = {
        branding: { siteName: "Cleared Cache Config" },
      };
      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(modifiedData, null, 2)
      );

      // Second load after cache clear - should read new config
      const config2 = loadConfig(tmpDir);
      expect(config2?.branding?.siteName).toBe("Cleared Cache Config");
    });

    it("should return null and warn on malformed JSON", () => {
      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        "{ invalid json here"
      );

      const consoleSpy = jest.spyOn(console, "warn").mockImplementation(() => {});

      const config = loadConfig(tmpDir);
      expect(config).toBeNull();
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Could not load synapse.config.json")
      );

      consoleSpy.mockRestore();
    });

    it("should stop traversing at root directory", () => {
      // Start at a deep nested directory with no config anywhere
      const deepDir = path.join(
        tmpDir,
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "i",
        "j",
        "k"
      );
      fs.mkdirSync(deepDir, { recursive: true });

      const config = loadConfig(deepDir);
      expect(config).toBeNull();
    });
  });

  describe("getExpectedFolder", () => {
    it("should return default folder when no config exists", () => {
      const folder = getExpectedFolder("system", tmpDir);
      expect(folder).toBe("content/70_Systems");
    });

    it("should return custom folder from config", () => {
      const configData: SynapseConfig = {
        folders: {
          system: "75_Systems",
        },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      const folder = getExpectedFolder("system", tmpDir);
      expect(folder).toBe("content/75_Systems");
    });

    it("should add content/ prefix if not present in custom folder", () => {
      const configData: SynapseConfig = {
        folders: {
          system: "80_CustomSystems",
        },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      const folder = getExpectedFolder("system", tmpDir);
      expect(folder).toBe("content/80_CustomSystems");
    });

    it("should not duplicate content/ prefix", () => {
      const configData: SynapseConfig = {
        folders: {
          system: "content/85_Systems",
        },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      const folder = getExpectedFolder("system", tmpDir);
      expect(folder).toBe("content/85_Systems");
    });

    it("should fall back to default for types not in config", () => {
      const configData: SynapseConfig = {
        folders: {
          system: "75_Systems",
        },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      // Request a type not in the config
      const folder = getExpectedFolder("policy", tmpDir);
      expect(folder).toBe("content/10_Policies");
    });
  });

  describe("getFolderName", () => {
    it("should return folder name without content/ prefix", () => {
      const folderName = getFolderName("system", tmpDir);
      expect(folderName).toBe("70_Systems");
    });

    it("should return custom folder name without content/ prefix", () => {
      const configData: SynapseConfig = {
        folders: {
          system: "75_Systems",
        },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      const folderName = getFolderName("system", tmpDir);
      expect(folderName).toBe("75_Systems");
    });

    it("should strip content/ prefix from custom folder with prefix", () => {
      const configData: SynapseConfig = {
        folders: {
          system: "content/85_Systems",
        },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      const folderName = getFolderName("system", tmpDir);
      expect(folderName).toBe("85_Systems");
    });
  });

  describe("clearConfigCache", () => {
    it("should clear the config cache", () => {
      const configData: SynapseConfig = {
        branding: { siteName: "Test Cache Clear" },
      };

      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(configData, null, 2)
      );

      // Load config to populate cache
      loadConfig(tmpDir);

      // Clear cache
      clearConfigCache();

      // Modify config file
      const newConfigData: SynapseConfig = {
        branding: { siteName: "Cache Cleared" },
      };
      fs.writeFileSync(
        path.join(tmpDir, "synapse.config.json"),
        JSON.stringify(newConfigData, null, 2)
      );

      // Load again - should get new config
      const config = loadConfig(tmpDir);
      expect(config?.branding?.siteName).toBe("Cache Cleared");
    });
  });
});
