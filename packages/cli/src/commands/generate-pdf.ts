import fsExtra from 'fs-extra';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { inlinePdfImages, renderPdfDiagrams } from '../lib/pdf-assets.js';
import { chromium } from 'playwright-chromium';
import { registerDefaultHelpers } from '../lib/templates.js';
import { loadSchema, validateFrontmatter } from '../lib/schemas.js';
import { isKnownDocType } from '../lib/type-registry.js';
import { markdownToHtml } from '../lib/markdown.js';
import {
  resolveTheme,
  resolveCompanyLogo,
  resolveLogoDataUrl,
  findPdfToolsDir,
} from '../lib/pdf-theme-registry.js';

const fs = fsExtra;

let chalk: any;
async function getChalk() {
  if (!chalk) {
    try {
      chalk = (await import('chalk')).default;
    } catch {
      chalk = {
        green: (str: string) => str,
        red: (str: string) => str,
        yellow: (str: string) => str,
        blue: (str: string) => str,
      };
    }
  }
  return chalk;
}

interface GeneratePdfOptions {
  input: string;
  output: string;
  logo?: string;
  company?: string;
  theme?: string;
  url?: string;
  validate?: boolean;
  draft?: boolean;
}

export async function generatePdf(options: GeneratePdfOptions): Promise<void> {
  const c = await getChalk();
  registerDefaultHelpers();

  // Load markdown file with frontmatter
  console.log(c.blue(`📄 Loading data from ${options.input}`));
  const fileContent = await fs.readFile(options.input, 'utf-8');

  // Parse frontmatter and body
  const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
  const match = fileContent.match(frontmatterRegex);

  if (!match) {
    throw new Error('Invalid markdown file: missing frontmatter');
  }

  const frontmatterYaml = match[1];
  const markdownBody = match[2].trim();
  const data = yaml.load(frontmatterYaml) as Record<string, any>;

  // Validate data against schema
  if (options.validate !== false) {
    const docType = data.type;
    if (!docType) {
      throw new Error('Document type not specified in frontmatter');
    }
    if (!isKnownDocType(docType)) {
      throw new Error(`Invalid document type: ${docType}`);
    }

    console.log(c.blue(`✓ Validating against ${docType} schema`));
    const schema = await loadSchema(docType);
    const validation = validateFrontmatter(data, schema);

    if (!validation.valid) {
      console.log(c.yellow('⚠️  Validation warnings:'));
      validation.errors?.forEach(error => {
        console.log(c.yellow(`   - ${error.path}: ${error.message}`));
      });
      throw new Error('Schema validation failed');
    }
  }

  // Convert markdown to HTML
  console.log(c.blue('🔄 Converting markdown to HTML'));
  const inputDir = path.dirname(path.resolve(options.input));
  const projectRoot = path.resolve(inputDir, '../..');

  const htmlContent = await inlinePdfImages(
    await markdownToHtml(markdownBody, projectRoot), inputDir
  );

  // Resolve theme
  const theme = resolveTheme(options.theme, data.brand_theme as string | undefined);
  console.log(c.blue(`🎨 Using theme: ${theme.displayName || theme.name}`));

  // Load base CSS (letterhead.css) + theme CSS
  let baseCss = '';
  const toolsDir = findPdfToolsDir();
  if (toolsDir) {
    const letterheadCssPath = path.join(toolsDir, 'letterhead.css');
    if (await fs.pathExists(letterheadCssPath)) {
      baseCss = await fs.readFile(letterheadCssPath, 'utf-8');
    }
  }
  const themeCss = await fs.readFile(theme.cssPath, 'utf-8');
  const css = baseCss + '\n\n' + themeCss;

  // Load template
  let templateHtml: string;
  if (theme.templatePath && await fs.pathExists(theme.templatePath)) {
    templateHtml = await fs.readFile(theme.templatePath, 'utf-8');
  } else {
    throw new Error('No HTML template found for theme. Ensure tools/pdf/letterhead.html exists.');
  }

  // Resolve logos
  const companyName = (options.company || data.company) as string | undefined;
  let companyLogoDataUrl = '';
  if (companyName) {
    const resolved = await resolveCompanyLogo(companyName);
    if (resolved) {
      companyLogoDataUrl = resolved;
      console.log(c.green(`✓ Company logo: ${companyName}`));
    }
  }

  let brandLogoDataUrl = '';
  if (options.logo) {
    // CLI override
    const logoPath = path.resolve(options.logo);
    if (await fs.pathExists(logoPath)) {
      brandLogoDataUrl = (await resolveLogoDataUrl(logoPath)) || '';
    }
  } else if (theme.logoPath) {
    brandLogoDataUrl = (await resolveLogoDataUrl(theme.logoPath)) || '';
  }

  let footerLogoDataUrl = '';
  if (theme.footerLogoPath) {
    footerLogoDataUrl = (await resolveLogoDataUrl(theme.footerLogoPath)) || '';
  }

  // Detect draft status
  const isDraft = options.draft || data.status === 'draft';
  if (isDraft) {
    console.log(c.yellow('⚠️  Draft mode'));
  }

  // Compile template with Handlebars
  const Handlebars = (await import('handlebars')).default;
  const compiled = Handlebars.compile(templateHtml);

  const finalHtml = compiled({
    title: data.title || 'Document',
    body: htmlContent,
    css,
    logo: brandLogoDataUrl,
    companyLogo: companyLogoDataUrl,
    company: companyName || '',
    date: new Date().toISOString().split('T')[0],
    attribution: data.consultant_attribution ?? theme.attribution ?? '',
    footerLogo: footerLogoDataUrl,
    isDraft,
    theme: theme.name,
  });

  console.log(c.blue('🖨️  Generating PDF with Playwright'));
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.setContent(finalHtml, { waitUntil: 'load' });
    await renderPdfDiagrams(page);
    await page.evaluate('Promise.all([document.fonts.ready, ...Array.from(document.images, img => img.decode())])');

    // Ensure output directory exists
    await fs.ensureDir(path.dirname(options.output));

    await page.pdf({
      path: options.output,
      format: 'Letter',
      margin: {
        top: '0.5in',
        right: '0.75in',
        bottom: '0.5in',
        left: '0.75in',
      },
      printBackground: true,
    });
  } finally {
    await browser.close();
  }

  console.log(c.green(`✅ PDF generated: ${options.output}`));
}

export async function generatePdfCommand(args: {
  input?: string;
  output?: string;
  logo?: string;
  company?: string;
  theme?: string;
  url?: string;
  validate?: boolean;
  draft?: boolean;
}): Promise<void> {
  const c = await getChalk();

  if (!args.input) {
    console.error(c.red('Error: --input is required'));
    console.log('Usage: synapse generate-pdf --input <markdown-file> --output <pdf-file>');
    process.exit(1);
  }

  if (!args.output) {
    console.error(c.red('Error: --output is required'));
    console.log('Usage: synapse generate-pdf --input <markdown-file> --output <pdf-file>');
    process.exit(1);
  }

  try {
    await generatePdf({
      input: args.input,
      output: args.output,
      logo: args.logo,
      company: args.company,
      theme: args.theme,
      url: args.url,
      validate: args.validate,
      draft: args.draft,
    });
  } catch (error) {
    console.error(c.red('Error:'), error instanceof Error ? error.message : error);
    process.exit(1);
  }
}
