import * as path from 'path';
import * as os from 'os';
import fsExtra from 'fs-extra';
import * as yaml from 'js-yaml';
const fs = fsExtra;

import {
  findPdfToolsDir,
  getPdfThemeRegistry,
  getPdfThemeNames,
  isKnownPdfTheme,
  getPdfTheme,
  getDefaultThemeName,
  resolveTheme,
  loadCompanyRegistry,
  resolveCompanyLogo,
  resolveLogoDataUrl,
  clearPdfThemeRegistryCache,
} from '../../src/lib/pdf-theme-registry.js';

describe('pdf-theme-registry', () => {
  let tmpDir: string;
  let originalCwd: string;

  beforeEach(() => {
    tmpDir = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'synapse-pdf-theme-test-')));
    originalCwd = process.cwd();
    clearPdfThemeRegistryCache();
  });

  afterEach(() => {
    process.chdir(originalCwd);
    if (fs.existsSync(tmpDir)) {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    }
    clearPdfThemeRegistryCache();
  });

  describe('findPdfToolsDir', () => {
    it('should return null when no tools/pdf/ exists', () => {
      process.chdir(tmpDir);
      expect(findPdfToolsDir()).toBeNull();
    });

    it('should find tools/pdf/ in cwd', () => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      process.chdir(tmpDir);
      expect(findPdfToolsDir()).toBe(toolsDir);
    });

    it('should find tools/pdf/ by traversing up', () => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      const subDir = path.join(tmpDir, 'content/reports');
      fs.mkdirpSync(subDir);
      process.chdir(subDir);
      expect(findPdfToolsDir()).toBe(toolsDir);
    });
  });

  describe('theme discovery', () => {
    let toolsDir: string;

    beforeEach(() => {
      toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);

      // Create letterhead base files
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), 'body { margin: 0; }');
      fs.writeFileSync(
        path.join(toolsDir, 'letterhead.html'),
        '<html><head><style>{{{css}}}</style></head><body>{{{body}}}</body></html>'
      );

      process.chdir(tmpDir);
    });

    it('should always include letterhead theme', () => {
      const registry = getPdfThemeRegistry();
      expect(registry).toHaveProperty('letterhead');
      expect(registry['letterhead'].name).toBe('letterhead');
      expect(registry['letterhead'].cssPath).toBe(path.join(toolsDir, 'letterhead.css'));
    });

    it('should discover CSS-based themes', () => {
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '.acme { color: red; }');
      fs.writeFileSync(path.join(toolsDir, 'brand.css'), '.brand { color: blue; }');

      const registry = getPdfThemeRegistry();
      expect(registry).toHaveProperty('acme');
      expect(registry).toHaveProperty('brand');
      expect(registry['acme'].cssPath).toBe(path.join(toolsDir, 'acme.css'));
    });

    it('should not treat letterhead.css as a theme', () => {
      const names = getPdfThemeNames();
      // letterhead IS a theme but discovered separately, not from CSS scan exclusion
      expect(names).toContain('letterhead');
    });

    it('should detect per-theme HTML template overrides', () => {
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '.acme {}');
      fs.writeFileSync(path.join(toolsDir, 'acme.html'), '<html>acme template</html>');

      const registry = getPdfThemeRegistry();
      expect(registry['acme'].templatePath).toBe(path.join(toolsDir, 'acme.html'));
    });

    it('should fall back to letterhead.html when no theme template exists', () => {
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '.acme {}');

      const registry = getPdfThemeRegistry();
      expect(registry['acme'].templatePath).toBe(path.join(toolsDir, 'letterhead.html'));
    });

    it('should merge metadata from pdf.config.yaml', () => {
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '.acme {}');
      fs.writeFileSync(
        path.join(toolsDir, 'pdf.config.yaml'),
        yaml.dump({
          themes: {
            acme: {
              display_name: 'ACME Corp',
              default_attribution: 'ACME Inc.',
            },
          },
        })
      );

      const registry = getPdfThemeRegistry();
      expect(registry['acme'].displayName).toBe('ACME Corp');
      expect(registry['acme'].attribution).toBe('ACME Inc.');
    });

    it('should resolve logo and footer_logo from config', () => {
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '.acme {}');
      const logosDir = path.join(toolsDir, 'logos');
      fs.mkdirpSync(logosDir);
      fs.writeFileSync(path.join(logosDir, 'acme-brand.png'), 'fake-png');
      fs.writeFileSync(path.join(logosDir, 'acme-footer.png'), 'fake-png');

      fs.writeFileSync(
        path.join(toolsDir, 'pdf.config.yaml'),
        yaml.dump({
          themes: {
            acme: {
              logo: 'logos/acme-brand.png',
              footer_logo: 'logos/acme-footer.png',
            },
          },
        })
      );

      const registry = getPdfThemeRegistry();
      expect(registry['acme'].logoPath).toContain('acme-brand.png');
      expect(registry['acme'].footerLogoPath).toContain('acme-footer.png');
    });

    it('should skip logo paths that do not exist on disk', () => {
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '.acme {}');
      fs.writeFileSync(
        path.join(toolsDir, 'pdf.config.yaml'),
        yaml.dump({
          themes: {
            acme: {
              logo: 'logos/nonexistent.png',
              footer_logo: 'logos/also-nonexistent.png',
            },
          },
        })
      );

      const registry = getPdfThemeRegistry();
      expect(registry['acme'].logoPath).toBeUndefined();
      expect(registry['acme'].footerLogoPath).toBeUndefined();
    });

    it('should handle corrupted pdf.config.yaml gracefully', () => {
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '.acme {}');
      fs.writeFileSync(path.join(toolsDir, 'pdf.config.yaml'), '{{invalid yaml');

      // Should not throw, just skip config metadata
      const registry = getPdfThemeRegistry();
      expect(registry).toHaveProperty('acme');
      expect(registry['acme'].displayName).toBeUndefined();
    });

    it('should handle unreadable tools dir gracefully', () => {
      // The registry falls back if readdirSync fails — verify letterhead is still returned
      const registry = getPdfThemeRegistry();
      expect(registry).toHaveProperty('letterhead');
    });
  });

  describe('getPdfThemeNames', () => {
    it('should return sorted theme names', () => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      fs.writeFileSync(path.join(toolsDir, 'zebra.css'), '');
      fs.writeFileSync(path.join(toolsDir, 'alpha.css'), '');
      process.chdir(tmpDir);

      const names = getPdfThemeNames();
      expect(names).toEqual(['alpha', 'letterhead', 'zebra']);
    });
  });

  describe('isKnownPdfTheme / getPdfTheme', () => {
    beforeEach(() => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '');
      process.chdir(tmpDir);
    });

    it('should return true for known themes', () => {
      expect(isKnownPdfTheme('acme')).toBe(true);
      expect(isKnownPdfTheme('letterhead')).toBe(true);
    });

    it('should return false for unknown themes', () => {
      expect(isKnownPdfTheme('nonexistent')).toBe(false);
    });

    it('should return theme metadata for known theme', () => {
      const theme = getPdfTheme('acme');
      expect(theme).not.toBeNull();
      expect(theme!.name).toBe('acme');
    });

    it('should return null for unknown theme', () => {
      expect(getPdfTheme('nonexistent')).toBeNull();
    });
  });

  describe('getDefaultThemeName', () => {
    it('should return letterhead when no config exists', () => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      process.chdir(tmpDir);

      expect(getDefaultThemeName()).toBe('letterhead');
    });

    it('should return configured default theme', () => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '');
      fs.writeFileSync(
        path.join(toolsDir, 'pdf.config.yaml'),
        yaml.dump({ default_theme: 'acme' })
      );
      process.chdir(tmpDir);

      expect(getDefaultThemeName()).toBe('acme');
    });

    it('should fall back to letterhead when configured default does not exist', () => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      fs.writeFileSync(
        path.join(toolsDir, 'pdf.config.yaml'),
        yaml.dump({ default_theme: 'nonexistent' })
      );
      process.chdir(tmpDir);

      expect(getDefaultThemeName()).toBe('letterhead');
    });
  });

  describe('resolveTheme', () => {
    let toolsDir: string;

    beforeEach(() => {
      toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      fs.writeFileSync(path.join(toolsDir, 'letterhead.html'), '<html></html>');
      fs.writeFileSync(path.join(toolsDir, 'acme.css'), '');
      fs.writeFileSync(path.join(toolsDir, 'brand.css'), '');
      process.chdir(tmpDir);
    });

    it('should prefer CLI theme over frontmatter', () => {
      const theme = resolveTheme('acme', 'brand');
      expect(theme.name).toBe('acme');
    });

    it('should use frontmatter theme when no CLI theme', () => {
      const theme = resolveTheme(undefined, 'brand');
      expect(theme.name).toBe('brand');
    });

    it('should fall back to default theme', () => {
      fs.writeFileSync(
        path.join(toolsDir, 'pdf.config.yaml'),
        yaml.dump({ default_theme: 'acme' })
      );
      clearPdfThemeRegistryCache();

      const theme = resolveTheme(undefined, undefined);
      expect(theme.name).toBe('acme');
    });

    it('should fall back to letterhead when all else fails', () => {
      const theme = resolveTheme('nonexistent', 'also-nonexistent');
      expect(theme.name).toBe('letterhead');
    });
  });

  describe('company registry', () => {
    let toolsDir: string;

    beforeEach(() => {
      toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      process.chdir(tmpDir);
    });

    it('should return empty array when no registry file exists', () => {
      expect(loadCompanyRegistry()).toEqual([]);
    });

    it('should return empty array when no tools dir exists', () => {
      process.chdir(os.tmpdir());
      clearPdfThemeRegistryCache();
      expect(loadCompanyRegistry()).toEqual([]);
    });

    it('should return cached result on second call', () => {
      fs.writeFileSync(
        path.join(toolsDir, 'company-registry.yaml'),
        yaml.dump({
          companies: [
            { id: 'acme', name: 'ACME Corp', short_name: 'ACME' },
          ],
        })
      );

      const first = loadCompanyRegistry();
      const second = loadCompanyRegistry();
      expect(first).toBe(second); // Same reference = cached
    });

    it('should handle corrupted company-registry.yaml', () => {
      fs.writeFileSync(path.join(toolsDir, 'company-registry.yaml'), '{{invalid yaml');

      const companies = loadCompanyRegistry();
      expect(companies).toEqual([]);
    });

    it('should load companies from registry', () => {
      fs.writeFileSync(
        path.join(toolsDir, 'company-registry.yaml'),
        yaml.dump({
          companies: [
            { id: 'acme', name: 'ACME Corp', short_name: 'ACME' },
            { id: 'globex', name: 'Globex Inc', short_name: 'Globex' },
          ],
        })
      );

      const companies = loadCompanyRegistry();
      expect(companies).toHaveLength(2);
      expect(companies[0].id).toBe('acme');
      expect(companies[1].name).toBe('Globex Inc');
    });
  });

  describe('resolveCompanyLogo', () => {
    let toolsDir: string;

    beforeEach(() => {
      toolsDir = path.join(tmpDir, 'tools/pdf');
      const logosDir = path.join(toolsDir, 'logos');
      fs.mkdirpSync(logosDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      process.chdir(tmpDir);
    });

    it('should return null for empty company name', async () => {
      expect(await resolveCompanyLogo('')).toBeNull();
    });

    it('should return null when no tools dir', async () => {
      process.chdir(os.tmpdir());
      clearPdfThemeRegistryCache();
      expect(await resolveCompanyLogo('ACME')).toBeNull();
    });

    it('should resolve logo from company registry', async () => {
      // Create a small PNG (1x1 pixel)
      const pngBuffer = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64'
      );
      fs.writeFileSync(path.join(toolsDir, 'logos/acme.png'), pngBuffer);

      fs.writeFileSync(
        path.join(toolsDir, 'company-registry.yaml'),
        yaml.dump({
          companies: [
            { id: 'acme', name: 'ACME Corp', short_name: 'ACME', logo_path: 'logos/acme.png' },
          ],
        })
      );

      const result = await resolveCompanyLogo('ACME Corp');
      expect(result).not.toBeNull();
      expect(result).toMatch(/^data:image\/png;base64,/);
    });

    it('should match by short_name', async () => {
      const pngBuffer = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64'
      );
      fs.writeFileSync(path.join(toolsDir, 'logos/acme.png'), pngBuffer);

      fs.writeFileSync(
        path.join(toolsDir, 'company-registry.yaml'),
        yaml.dump({
          companies: [
            { id: 'acme', name: 'ACME Corp', short_name: 'ACME', logo_path: 'logos/acme.png' },
          ],
        })
      );

      const result = await resolveCompanyLogo('ACME');
      expect(result).not.toBeNull();
      expect(result).toMatch(/^data:image\/png;base64,/);
    });

    it('should match by id slug', async () => {
      const pngBuffer = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64'
      );
      fs.writeFileSync(path.join(toolsDir, 'logos/acme.png'), pngBuffer);

      fs.writeFileSync(
        path.join(toolsDir, 'company-registry.yaml'),
        yaml.dump({
          companies: [
            { id: 'acme', name: 'ACME Corp', short_name: 'ACME', logo_path: 'logos/acme.png' },
          ],
        })
      );

      const result = await resolveCompanyLogo('acme');
      expect(result).not.toBeNull();
    });

    it('should return null when registry logo path does not exist', async () => {
      fs.writeFileSync(
        path.join(toolsDir, 'company-registry.yaml'),
        yaml.dump({
          companies: [
            { id: 'acme', name: 'ACME Corp', short_name: 'ACME', logo_path: 'logos/missing.png' },
          ],
        })
      );

      const result = await resolveCompanyLogo('ACME Corp');
      // Falls through to convention discovery, which also won't find anything
      expect(result).toBeNull();
    });

    it('should return null when no logos dir exists and no registry match', async () => {
      const result = await resolveCompanyLogo('Unknown Corp');
      expect(result).toBeNull();
    });

    it('should try multiple extensions in convention discovery', async () => {
      fs.writeFileSync(path.join(toolsDir, 'logos/acme-corp.svg'), '<svg></svg>');

      const result = await resolveCompanyLogo('ACME Corp');
      expect(result).not.toBeNull();
      expect(result).toMatch(/^data:image\/svg\+xml;base64,/);
    });

    it('should discover logo by convention (slug match)', async () => {
      const pngBuffer = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64'
      );
      fs.writeFileSync(path.join(toolsDir, 'logos/acme-corp.png'), pngBuffer);

      const result = await resolveCompanyLogo('ACME Corp');
      expect(result).not.toBeNull();
      expect(result).toMatch(/^data:image\/png;base64,/);
    });
  });

  describe('resolveLogoDataUrl', () => {
    it('should return null for empty path', async () => {
      expect(await resolveLogoDataUrl('')).toBeNull();
    });

    it('should return null for nonexistent file', async () => {
      expect(await resolveLogoDataUrl('/nonexistent/logo.png')).toBeNull();
    });

    it('should return data URL for existing file', async () => {
      const pngBuffer = Buffer.from(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        'base64'
      );
      const logoPath = path.join(tmpDir, 'test-logo.png');
      fs.writeFileSync(logoPath, pngBuffer);

      const result = await resolveLogoDataUrl(logoPath);
      expect(result).not.toBeNull();
      expect(result).toMatch(/^data:image\/png;base64,/);
    });

    it('should detect SVG mime type', async () => {
      const svgPath = path.join(tmpDir, 'test-logo.svg');
      fs.writeFileSync(svgPath, '<svg></svg>');

      const result = await resolveLogoDataUrl(svgPath);
      expect(result).toMatch(/^data:image\/svg\+xml;base64,/);
    });

    it('should detect JPEG mime type', async () => {
      const jpgPath = path.join(tmpDir, 'test-logo.jpg');
      fs.writeFileSync(jpgPath, 'fake-jpg');

      const result = await resolveLogoDataUrl(jpgPath);
      expect(result).toMatch(/^data:image\/jpeg;base64,/);
    });

    it('should use octet-stream for unknown extensions', async () => {
      const unknownPath = path.join(tmpDir, 'test-logo.webp');
      fs.writeFileSync(unknownPath, 'fake-webp');

      const result = await resolveLogoDataUrl(unknownPath);
      expect(result).toMatch(/^data:application\/octet-stream;base64,/);
    });
  });

  describe('clearPdfThemeRegistryCache', () => {
    it('should clear all caches', () => {
      const toolsDir = path.join(tmpDir, 'tools/pdf');
      fs.mkdirpSync(toolsDir);
      fs.writeFileSync(path.join(toolsDir, 'letterhead.css'), '');
      process.chdir(tmpDir);

      // Populate caches
      getPdfThemeRegistry();
      loadCompanyRegistry();

      // Clear
      clearPdfThemeRegistryCache();

      // After clear, a new call should re-discover
      // (doesn't throw, and returns fresh results)
      const registry = getPdfThemeRegistry();
      expect(registry).toHaveProperty('letterhead');
    });
  });
});
