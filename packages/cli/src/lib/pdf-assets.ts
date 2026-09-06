import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { createRequire } from 'node:module';
import { parseFragment, serialize, type DefaultTreeAdapterMap } from 'parse5';
import type { Page } from 'playwright-chromium';

const require = createRequire(import.meta.url);
const imageTypes: Record<string, string> = {
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp',
};

/** Embed images after Markdown sanitization, preserving parsed alt/title attributes. */
export async function inlinePdfImages(html: string, inputDir: string): Promise<string> {
  const fragment = parseFragment(html);
  async function embed(node: DefaultTreeAdapterMap['node']): Promise<void> {
    if ('tagName' in node && node.tagName === 'img') {
      const attribute = node.attrs.find(attr => attr.name === 'src');
      const src = attribute?.value;
      if (src && !/^(?:[a-z][a-z\d+.-]*:|\/\/)/i.test(src)) {
        const file = path.resolve(inputDir, decodeURIComponent(src.split(/[?#]/)[0]));
        const mime = imageTypes[path.extname(file).toLowerCase()];
        if (mime) {
          const bytes = await readFile(file);
          attribute!.value = `data:${mime};base64,${bytes.toString('base64')}`;
        }
      }
    }
    if ('childNodes' in node) {
      for (const child of node.childNodes) await embed(child);
    }
  }
  await embed(fragment);
  return serialize(fragment);
}

/** Render with the installed Mermaid bundle; no CDN or global executable is needed. */
export async function renderPdfDiagrams(page: Page): Promise<void> {
  if (await page.locator('pre code.language-mermaid').count() === 0) return;
  await page.addScriptTag({
    path: path.join(path.dirname(require.resolve('mermaid')), 'mermaid.min.js'),
  });
  await page.addStyleTag({ content: '.mermaid-diagram { display:flex; justify-content:center; margin:1.5rem 0; } .mermaid-diagram svg { max-width:100%; height:auto; }' });
  await page.evaluate(`(async () => {
    mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'default' });
    const blocks = Array.from(document.querySelectorAll('pre code.language-mermaid'));
    for (const [index, block] of blocks.entries()) {
      const { svg } = await mermaid.render('synapse-diagram-' + index, block.textContent);
      const container = document.createElement('div');
      container.className = 'mermaid-diagram';
      container.innerHTML = svg;
      block.parentElement.replaceWith(container);
    }
  })()`);
}
