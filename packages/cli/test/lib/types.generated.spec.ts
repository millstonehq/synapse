import {
  getDocTypes,
  isKnownDocType,
  getTypeRegistry,
  getExpectedFolder,
  getDisplayLabel,
  getCmsCollection,
  clearTypeRegistryCache,
} from "../../src/lib/type-registry";

describe("type-registry module", () => {
  beforeEach(() => {
    clearTypeRegistryCache();
  });

  describe("getDocTypes", () => {
    it("should return a non-empty array of document types", () => {
      const types = getDocTypes();
      expect(Array.isArray(types)).toBe(true);
      expect(types.length).toBeGreaterThan(0);
    });

    it("should contain core document types", () => {
      const types = getDocTypes();
      // These are the stable core types that should always exist
      const coreTypes = [
        "adr",
        "capability",
        "meeting",
        "policy",
        "prd",
        "process",
        "reference",
        "runbook",
        "sop",
        "standard",
        "system",
        "tdd",
      ];

      coreTypes.forEach((type) => {
        expect(types).toContain(type);
      });
    });

    it("should return a sorted array", () => {
      const types = getDocTypes();
      const sorted = [...types].sort();
      expect(types).toEqual(sorted);
    });

    it("should return a new array each time", () => {
      const types1 = getDocTypes();
      const types2 = getDocTypes();
      expect(types1).not.toBe(types2);
      expect(types1).toEqual(types2);
    });
  });

  describe("isKnownDocType", () => {
    it("should return true for valid document types", () => {
      ["adr", "policy", "process", "sop", "runbook"].forEach((type) => {
        expect(isKnownDocType(type)).toBe(true);
      });
    });

    it("should return false for invalid strings", () => {
      ["invalid", "unknown", "", "ADR", "Policy"].forEach((type) => {
        expect(isKnownDocType(type)).toBe(false);
      });
    });
  });

  describe("getTypeRegistry", () => {
    it("should return a registry matching discovered schemas", () => {
      const registry = getTypeRegistry();
      const types = getDocTypes();
      expect(Object.keys(registry).sort()).toEqual(types);
    });

    it("should have correct metadata structure for each type", () => {
      const registry = getTypeRegistry();
      for (const [type, meta] of Object.entries(registry)) {
        expect(meta).toHaveProperty("folder");
        expect(meta).toHaveProperty("displayLabel");
        expect(meta).toHaveProperty("cmsCollection");
        expect(typeof meta.folder).toBe("string");
        expect(typeof meta.displayLabel).toBe("string");
        expect(typeof meta.cmsCollection).toBe("string");
      }
    });

    it("should return the same object on repeated calls (cached)", () => {
      const registry1 = getTypeRegistry();
      const registry2 = getTypeRegistry();
      expect(registry1).toBe(registry2);
    });

    it("should return a fresh object after clearing cache", () => {
      const registry1 = getTypeRegistry();
      clearTypeRegistryCache();
      const registry2 = getTypeRegistry();
      expect(registry1).not.toBe(registry2);
      expect(registry1).toEqual(registry2);
    });
  });

  describe("getExpectedFolder", () => {
    it("should return correct folder path for ADR", () => {
      expect(getExpectedFolder("adr")).toBe("content/90_Architecture/ADRs");
    });

    it("should return correct folder path for Process", () => {
      expect(getExpectedFolder("process")).toBe("content/30_Processes");
    });

    it("should return correct folder path for all document types", () => {
      getDocTypes().forEach((type) => {
        const folder = getExpectedFolder(type);
        expect(folder).toBeDefined();
        expect(folder).toContain("content/");
      });
    });

    it("should throw for unknown type", () => {
      expect(() => getExpectedFolder("invalid")).toThrow("Unknown document type: invalid");
    });
  });

  describe("getDisplayLabel", () => {
    it("should return correct display label for ADR", () => {
      expect(getDisplayLabel("adr")).toBe("ADR");
    });

    it("should return correct display label for Reference", () => {
      expect(getDisplayLabel("reference")).toBe("Reference");
    });

    it("should return display labels for all document types", () => {
      getDocTypes().forEach((type) => {
        const label = getDisplayLabel(type);
        expect(label).toBeDefined();
        expect(typeof label).toBe("string");
        expect(label.length).toBeGreaterThan(0);
      });
    });

    it("should throw for unknown type", () => {
      expect(() => getDisplayLabel("invalid")).toThrow("Unknown document type: invalid");
    });
  });

  describe("getCmsCollection", () => {
    it("should return correct CMS collection for ADR", () => {
      expect(getCmsCollection("adr")).toBe("adrs");
    });

    it("should return correct CMS collection for Process", () => {
      expect(getCmsCollection("process")).toBe("processes");
    });

    it("should return CMS collections for all document types", () => {
      getDocTypes().forEach((type) => {
        const collection = getCmsCollection(type);
        expect(collection).toBeDefined();
        expect(typeof collection).toBe("string");
        expect(collection.length).toBeGreaterThan(0);
      });
    });

    it("should throw for unknown type", () => {
      expect(() => getCmsCollection("invalid")).toThrow("Unknown document type: invalid");
    });
  });
});
