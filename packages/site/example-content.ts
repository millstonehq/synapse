import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import yaml from 'js-yaml';

/** Public demos opt in by location AND an explicit boolean frontmatter flag.
 * Only Markdown is copied; arbitrary vault assets and symlinks are not published.
 */
export function stageExamples(source: string, destination: string): string[] {
  const approved: string[] = [];
  function visit(relative: string) {
    for (const entry of readdirSync(join(source, relative), { withFileTypes: true })) {
      const path = relative ? `${relative}/${entry.name}` : entry.name;
      if (entry.isSymbolicLink()) continue;
      if (entry.isDirectory()) { visit(path); continue; }
      if (!entry.isFile() || !path.split('/').slice(0, -1).includes('examples') || !path.endsWith('.md')) continue;
      const text = readFileSync(join(source, path), 'utf8');
      const match = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(text);
      const frontmatter = match ? yaml.load(match[1]) as Record<string, unknown> | null : null;
      if (frontmatter?.example === true && frontmatter.draft !== true) approved.push(path);
    }
  }
  visit('');
  if (!approved.length) throw new Error('Example-only publication requires at least one approved example');
  rmSync(destination, { recursive: true, force: true });
  mkdirSync(destination, { recursive: true });
  for (const path of approved.sort()) {
    mkdirSync(dirname(join(destination, path)), { recursive: true });
    cpSync(join(source, path), join(destination, path));
  }
  writeFileSync(join(destination, 'index.md'), `---\ntitle: Synapse Example Documents\n---\n\n# Synapse Example Documents\n\nThis public demonstration contains example documents for the [Synapse documentation framework](https://github.com/millstonehq/synapse). They describe fictional systems and illustrate its document types.\n\nBrowse the folders, graph, or search to explore ${approved.length} examples.\n`);
  return approved;
}
