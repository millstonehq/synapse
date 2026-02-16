/**
 * PDF Theme Registry - discovers themes and company config at runtime.
 * Scans the content repo's tools/pdf/ directory for CSS themes,
 * optional pdf.config.yaml metadata, and company-registry.yaml.
 *
 * Convention: any *.css file in tools/pdf/ (except letterhead.css) is a theme.
 * Name = filename stem (e.g., acme.css → theme "acme").
 */

import fsExtra from 'fs-extra';
import * as path from 'path';
import * as yaml from 'js-yaml';

const fs = fsExtra;

// ---------------------------------------------------------------------------
// Interfaces
// ---------------------------------------------------------------------------

export interface PdfThemeMetadata {
  name: string;
  cssPath: string;
  templatePath?: string;
  logoPath?: string;
  footerLogoPath?: string;
  attribution?: string;
  displayName?: string;
}

export interface CompanyEntry {
  id: string;
  name: string;
  short_name: string;
  logo_path?: string;
}

interface PdfConfigTheme {
  display_name?: string;
  logo?: string;
  footer_logo?: string;
  default_attribution?: string;
}

interface PdfConfig {
  themes?: Record<string, PdfConfigTheme>;
  default_theme?: string;
}

// ---------------------------------------------------------------------------
// Cache
// ---------------------------------------------------------------------------

let _themeRegistry: Record<string, PdfThemeMetadata> | null = null;
let _companyRegistry: CompanyEntry[] | null = null;
let _pdfConfig: PdfConfig | null | undefined = undefined; // undefined = not loaded
let _pdfToolsDir: string | null = null;

// ---------------------------------------------------------------------------
// Directory resolution
// ---------------------------------------------------------------------------

/**
 * Find the tools/pdf/ directory by traversing up from cwd.
 * Returns null if not found (framework default will be used).
 */
export function findPdfToolsDir(): string | null {
  if (_pdfToolsDir !== null) return _pdfToolsDir;

  let dir = process.cwd();
  for (let i = 0; i < 5; i++) {
    const candidate = path.join(dir, 'tools/pdf');
    if (fs.existsSync(candidate)) {
      _pdfToolsDir = candidate;
      return _pdfToolsDir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  return null;
}

/**
 * Get the resolved tools/pdf/ directory.
 * Falls back to the framework's own tools/pdf/ for the letterhead default.
 */
function getPdfToolsDirOrFallback(): string {
  const dir = findPdfToolsDir();
  if (dir) return dir;

  // Fallback: framework's own tools/pdf/
  const frameworkDir = path.resolve(new URL('../../..', import.meta.url).pathname, 'tools/pdf');
  if (fs.existsSync(frameworkDir)) return frameworkDir;

  throw new Error(
    'Could not find tools/pdf/ directory. Run synapse from a project root ' +
    'that contains tools/pdf/ or install the synapse framework properly.'
  );
}

// ---------------------------------------------------------------------------
// Config loading
// ---------------------------------------------------------------------------

function loadPdfConfig(toolsDir: string): PdfConfig | null {
  if (_pdfConfig !== undefined) return _pdfConfig;

  const configPath = path.join(toolsDir, 'pdf.config.yaml');
  if (!fs.existsSync(configPath)) {
    _pdfConfig = null;
    return null;
  }

  try {
    const content = fs.readFileSync(configPath, 'utf-8');
    _pdfConfig = (yaml.load(content) as PdfConfig) || null;
    return _pdfConfig;
  } catch {
    _pdfConfig = null;
    return null;
  }
}

// ---------------------------------------------------------------------------
// Theme discovery
// ---------------------------------------------------------------------------

function discoverThemes(): Record<string, PdfThemeMetadata> {
  const toolsDir = getPdfToolsDirOrFallback();
  const config = loadPdfConfig(toolsDir);
  const registry: Record<string, PdfThemeMetadata> = {};

  // Always register the letterhead fallback
  const letterheadCss = path.join(toolsDir, 'letterhead.css');
  const letterheadHtml = path.join(toolsDir, 'letterhead.html');
  if (fs.existsSync(letterheadCss)) {
    registry['letterhead'] = {
      name: 'letterhead',
      cssPath: letterheadCss,
      templatePath: fs.existsSync(letterheadHtml) ? letterheadHtml : undefined,
      displayName: 'Default Letterhead',
    };
  }

  // Scan for theme CSS files
  let files: string[];
  try {
    files = fs.readdirSync(toolsDir);
  } catch {
    return registry;
  }

  for (const file of files) {
    if (!file.endsWith('.css') || file === 'letterhead.css') continue;

    const themeName = path.basename(file, '.css');
    const cssPath = path.join(toolsDir, file);

    const theme: PdfThemeMetadata = {
      name: themeName,
      cssPath,
    };

    // Check for per-theme HTML template override
    const templatePath = path.join(toolsDir, `${themeName}.html`);
    if (fs.existsSync(templatePath)) {
      theme.templatePath = templatePath;
    } else if (fs.existsSync(letterheadHtml)) {
      theme.templatePath = letterheadHtml;
    }

    // Merge metadata from pdf.config.yaml if present
    const configTheme = config?.themes?.[themeName];
    if (configTheme) {
      if (configTheme.display_name) theme.displayName = configTheme.display_name;
      if (configTheme.default_attribution) theme.attribution = configTheme.default_attribution;
      if (configTheme.logo) {
        const logoPath = path.resolve(toolsDir, configTheme.logo);
        if (fs.existsSync(logoPath)) theme.logoPath = logoPath;
      }
      if (configTheme.footer_logo) {
        const footerPath = path.resolve(toolsDir, configTheme.footer_logo);
        if (fs.existsSync(footerPath)) theme.footerLogoPath = footerPath;
      }
    }

    registry[themeName] = theme;
  }

  return registry;
}

// ---------------------------------------------------------------------------
// Public API — Themes
// ---------------------------------------------------------------------------

export function getPdfThemeRegistry(): Record<string, PdfThemeMetadata> {
  if (!_themeRegistry) {
    _themeRegistry = discoverThemes();
  }
  return _themeRegistry;
}

export function getPdfThemeNames(): string[] {
  return Object.keys(getPdfThemeRegistry()).sort();
}

export function isKnownPdfTheme(name: string): boolean {
  return name in getPdfThemeRegistry();
}

export function getPdfTheme(name: string): PdfThemeMetadata | null {
  return getPdfThemeRegistry()[name] || null;
}

/**
 * Get the default theme name from pdf.config.yaml, or 'letterhead'.
 */
export function getDefaultThemeName(): string {
  const toolsDir = findPdfToolsDir();
  if (toolsDir) {
    const config = loadPdfConfig(toolsDir);
    if (config?.default_theme && isKnownPdfTheme(config.default_theme)) {
      return config.default_theme;
    }
  }
  return 'letterhead';
}

/**
 * Resolve the theme to use given CLI override, frontmatter, and defaults.
 * Priority: cliTheme > frontmatterTheme > config default > letterhead
 */
export function resolveTheme(
  cliTheme?: string,
  frontmatterTheme?: string,
): PdfThemeMetadata {
  const candidates = [cliTheme, frontmatterTheme, getDefaultThemeName(), 'letterhead'];

  for (const name of candidates) {
    if (name) {
      const theme = getPdfTheme(name);
      if (theme) return theme;
    }
  }

  // Should never reach here since letterhead is always registered,
  // but return a minimal fallback just in case
  const toolsDir = getPdfToolsDirOrFallback();
  return {
    name: 'letterhead',
    cssPath: path.join(toolsDir, 'letterhead.css'),
    templatePath: path.join(toolsDir, 'letterhead.html'),
    displayName: 'Default Letterhead',
  };
}

// ---------------------------------------------------------------------------
// Public API — Company Registry
// ---------------------------------------------------------------------------

export function loadCompanyRegistry(): CompanyEntry[] {
  if (_companyRegistry !== null) return _companyRegistry;

  const toolsDir = findPdfToolsDir();
  if (!toolsDir) {
    _companyRegistry = [];
    return _companyRegistry;
  }

  const registryPath = path.join(toolsDir, 'company-registry.yaml');
  if (!fs.existsSync(registryPath)) {
    _companyRegistry = [];
    return _companyRegistry;
  }

  try {
    const content = fs.readFileSync(registryPath, 'utf-8');
    const data = yaml.load(content) as any;
    _companyRegistry = (data?.companies as CompanyEntry[]) || [];
  } catch {
    _companyRegistry = [];
  }

  return _companyRegistry;
}

/**
 * Resolve a company logo to a base64 data URL.
 * Matches by name, short_name, or id. Falls back to convention: logos/{slug}.*
 */
export async function resolveCompanyLogo(companyName: string): Promise<string | null> {
  if (!companyName) return null;

  const toolsDir = findPdfToolsDir();
  if (!toolsDir) return null;

  const logosDir = path.join(toolsDir, 'logos');

  // Try company registry first
  const companies = loadCompanyRegistry();
  const slug = companyName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  const match = companies.find(
    (c) =>
      c.name === companyName ||
      c.short_name === companyName ||
      c.id === slug ||
      c.id === companyName.toLowerCase(),
  );

  if (match?.logo_path) {
    const logoPath = path.resolve(toolsDir, match.logo_path);
    if (await fs.pathExists(logoPath)) {
      return fileToDataUrl(logoPath);
    }
  }

  // Fallback: convention-based discovery in logos/ dir
  if (await fs.pathExists(logosDir)) {
    const exts = ['.png', '.svg', '.jpg', '.jpeg'];
    for (const ext of exts) {
      const candidate = path.join(logosDir, `${slug}${ext}`);
      if (await fs.pathExists(candidate)) {
        return fileToDataUrl(candidate);
      }
    }
  }

  return null;
}

/**
 * Resolve a file path (relative to tools/pdf/) to a base64 data URL.
 */
export async function resolveLogoDataUrl(logoPath: string): Promise<string | null> {
  if (!logoPath) return null;
  if (!(await fs.pathExists(logoPath))) return null;
  return fileToDataUrl(logoPath);
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function fileToDataUrl(filePath: string): Promise<string> {
  const buffer = await fs.readFile(filePath);
  const ext = path.extname(filePath).slice(1).toLowerCase();
  let mimeType: string;

  switch (ext) {
    case 'svg': mimeType = 'image/svg+xml'; break;
    case 'png': mimeType = 'image/png'; break;
    case 'jpg': case 'jpeg': mimeType = 'image/jpeg'; break;
    default: mimeType = 'application/octet-stream';
  }

  return `data:${mimeType};base64,${buffer.toString('base64')}`;
}

// ---------------------------------------------------------------------------
// Cache management
// ---------------------------------------------------------------------------

export function clearPdfThemeRegistryCache(): void {
  _themeRegistry = null;
  _companyRegistry = null;
  _pdfConfig = undefined;
  _pdfToolsDir = null;
}
