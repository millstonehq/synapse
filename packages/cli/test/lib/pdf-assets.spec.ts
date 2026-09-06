import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { inlinePdfImages, renderPdfDiagrams } from '../../src/lib/pdf-assets.js';
import { markdownToHtml } from '../../src/lib/markdown.js';
import { chromium } from 'playwright-chromium';

describe('PDF assets', () => {
  let dir: string;
  beforeEach(async () => { dir = await mkdtemp(path.join(os.tmpdir(), 'pdf-assets-')); });
  afterEach(async () => { await rm(dir, { recursive: true, force: true }); });

  it('embeds parsed local images while retaining Markdown sanitization', async () => {
    await writeFile(path.join(dir, 'an image.png'), 'test-image');
    const html = await markdownToHtml('![a "quoted" label](an%20image.png "caption")\n\n<script>alert(1)</script>');
    const output = await inlinePdfImages(html, dir);
    expect(output).toContain('data:image/png;base64,dGVzdC1pbWFnZQ==');
    expect(output).toContain('alt="a &quot;quoted&quot; label"');
    expect(output).toContain('title="caption"');
    expect(output).not.toContain('<script');
  });

  it('leaves remote images and unsupported formats unchanged', async () => {
    const html = '<img src="https://example.com/a.png"><img src="//example.com/a.png"><img src="data:image/png;base64,AA=="><img src="file:///tmp/a.png"><img src="a.txt"><img src="">';
    expect(await inlinePdfImages(html, dir)).toBe(html);
  });

  it('reports missing local images instead of silently printing broken assets', async () => {
    await expect(inlinePdfImages('<img src="missing.png">', dir)).rejects.toThrow('ENOENT');
  });

  it('does not load Mermaid for documents without diagrams', async () => {
    const page = { locator: () => ({ count: async () => 0 }) };
    await expect(renderPdfDiagrams(page as any)).resolves.toBeUndefined();
  });

  it('renders diagrams locally and rejects invalid diagrams', async () => {
    const browser = await chromium.launch();
    try {
      const page = await browser.newPage();
      // No network is needed for the renderer or its dependencies.
      await page.route('**/*', route => route.abort());
      await page.setContent(await markdownToHtml('```mermaid\nflowchart LR\nA[Read & validate] --> B[Export PDF]\n```'));
      await renderPdfDiagrams(page);
      expect(await page.locator('.mermaid-diagram svg').count()).toBe(1);
      expect(await page.locator('.mermaid-diagram').textContent()).toContain('Read & validate');
      expect(await page.locator('pre code.language-mermaid').count()).toBe(0);
      await page.setContent(await markdownToHtml('```mermaid\nnot a valid diagram\n```'));
      await expect(renderPdfDiagrams(page)).rejects.toThrow();
    } finally {
      await browser.close();
    }
  }, 30000);
});
