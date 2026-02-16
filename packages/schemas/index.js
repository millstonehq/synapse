import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

export function getSchemaDir() { return __dirname; }
export function getFrontmatterSchemaDir() { return join(__dirname, 'frontmatter'); }
export function getBodyGrammarDir() { return join(__dirname, 'body-grammars'); }
export function getPluginSchemaDir() { return join(__dirname, 'plugins'); }
