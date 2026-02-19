/**
 * Deterministic synthetic document generation.
 *
 * Reads a titles.json manifest, scaffolds documents using existing examples
 * as templates, and patches frontmatter with cross-references, dates, and
 * type-specific fields. No LLM calls — body content is placeholder.
 */

import fsExtra from 'fs-extra';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { getTypeRegistry, getExpectedFolder, getDisplayLabel } from './type-registry.js';

const fs = fsExtra;

// ============================================================================
// Types
// ============================================================================

export interface TitleEntry {
  type: string;
  title: string;
  domain: string;
}

export interface ManifestEntry extends TitleEntry {
  id: string;
  filepath: string;
}

export interface GenerateOptions {
  titles: string;
  dir: string;
  force: boolean;
}

// ============================================================================
// Constants
// ============================================================================

const OWNER_POOLS: Record<string, string[]> = {
  policy: ['CTO', 'VP Engineering', 'CISO'],
  standard: ['Head of Engineering', 'Security Lead', 'Compliance Officer'],
  process: ['Engineering Manager', 'Platform Lead', 'Director of Engineering'],
  sop: ['Release Manager', 'SRE Lead', 'DevOps Lead'],
  runbook: ['On-Call Engineer'],
  guide: ['Engineering Team', 'Developer Experience'],
  meeting: ['Principal Engineer', 'Engineering Manager', 'Product Manager'],
  system: ['$DOMAIN Engineering'],
  wiki: ['$DOMAIN Team'],
  report: ['$DOMAIN Tech Lead'],
  postmortem: ['On-Call Engineer', 'Incident Commander'],
  adr: ['Principal Engineer', 'Tech Lead', 'Staff Engineer'],
  tdd: ['Principal Engineer', 'Tech Lead', 'Senior Engineer'],
  prd: ['Head of Product', 'Product Manager', 'Senior PM'],
  flow: ['QA Lead', 'QA Engineer'],
  capability: ['Head of Engineering', 'VP Engineering'],
  reference: ['Security Team', 'Platform Team', 'Engineering Team'],
};

const STATUS_WEIGHTS: [string, number][] = [
  ['approved', 55],
  ['accepted', 10],
  ['draft', 15],
  ['review', 10],
  ['deprecated', 5],
  ['proposed', 5],
];

const RUNTIME_POOL = [
  'Kubernetes / Node.js 20 / PostgreSQL 16',
  'Kubernetes / Go 1.22 / PostgreSQL 15 / Redis 7',
  'Kubernetes / Python 3.12 / PostgreSQL 16 / RabbitMQ 3.13',
  'ECS Fargate / Java 21 / Aurora PostgreSQL / ElastiCache',
  'Kubernetes / Rust 1.75 / ScyllaDB / Redis 7',
  'Lambda / Node.js 20 / DynamoDB',
  'Kubernetes / .NET 8 / SQL Server 2022',
  'Kubernetes / Go 1.22 / ClickHouse / Kafka',
  'ECS Fargate / Python 3.12 / OpenSearch / Redis 7',
  'Kubernetes / TypeScript / PostgreSQL 16 / Redis 7',
];

const SEVERITY_POOL = ['SEV-1', 'SEV-2', 'SEV-3', 'SEV-4'];
const AUDIENCE_POOL: string[] = ['internal', 'customer', 'partner'];
const REPORT_TYPE_POOL: string[] = ['company', 'portfolio', 'analytics'];
const REFERENCE_CATEGORY_POOL: string[] = [
  'documentation', 'api-reference', 'blog-post',
  'standard', 'specification', 'tutorial', 'other',
];
const HEALTH_POOL: string[] = ['excellent', 'good', 'fair', 'poor'];
const CONFIDENCE_POOL: string[] = ['high', 'medium', 'low'];
const DURATION_POOL: string[] = ['~15 minutes', '~30 minutes', '~1 hour', '~2 hours', '~4 hours'];
const ATTRIBUTION_POOL: string[] = [
  'OWASP Foundation', 'NIST', 'Cloud Native Computing Foundation',
  'ISO', 'IEEE', 'W3C', 'IETF', 'Linux Foundation',
];

// ============================================================================
// Helpers
// ============================================================================

function toKebabCase(str: string): string {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

/** Simple seeded PRNG for deterministic output. */
function seededRandom(seed: number): number {
  const x = Math.sin(seed * 9301 + 49297) * 233280;
  return x - Math.floor(x);
}

function pick<T>(arr: readonly T[], seed: number): T {
  return arr[Math.floor(seededRandom(seed) * arr.length)];
}

function pickN<T>(arr: readonly T[], n: number, seed: number): T[] {
  const shuffled = [...arr];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(seededRandom(seed + i) * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled.slice(0, Math.min(n, shuffled.length));
}

function randomDate(startYear: number, endYear: number, seed: number): string {
  const start = new Date(startYear, 0, 1).getTime();
  const end = new Date(endYear, 11, 31).getTime();
  return new Date(start + seededRandom(seed) * (end - start)).toISOString();
}

function randomMonth(startYear: number, endYear: number, seed: number): string {
  const year = startYear + Math.floor(seededRandom(seed) * (endYear - startYear + 1));
  const month = 1 + Math.floor(seededRandom(seed + 1) * 12);
  return `${year}-${String(month).padStart(2, '0')}`;
}

function randomHexSha(seed: number): string {
  let sha = '';
  for (let i = 0; i < 40; i++) {
    sha += Math.floor(seededRandom(seed + i) * 16).toString(16);
  }
  return sha;
}

// ============================================================================
// Frontmatter Parsing
// ============================================================================

function parseFrontmatterAndBody(content: string): {
  frontmatter: Record<string, any>;
  body: string;
} {
  const lines = content.split('\n');
  let startLine = -1;
  let endLine = -1;

  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === '---') {
      if (startLine === -1) startLine = i;
      else { endLine = i; break; }
    }
  }

  if (startLine === -1 || endLine === -1) {
    return { frontmatter: {}, body: content };
  }

  const fmString = lines.slice(startLine + 1, endLine).join('\n');
  const body = lines.slice(endLine + 1).join('\n');
  return {
    frontmatter: (yaml.load(fmString) as Record<string, any>) || {},
    body,
  };
}

function serializeDocument(frontmatter: Record<string, any>, body: string): string {
  const fmYaml = yaml.dump(frontmatter, {
    lineWidth: -1,
    quotingType: "'",
    forceQuotes: false,
  }).trim();
  return `---\n${fmYaml}\n---\n${body}`;
}

// ============================================================================
// ID Generation
// ============================================================================

function generateId(type: string, counter: number): string {
  if (type === 'adr') {
    // ADR-0001 exists as hand-written example; start from 0002
    return `ADR-${String(counter + 1).padStart(4, '0')}`;
  }
  const prefix = getDisplayLabel(type).toUpperCase().replace(/\s+/g, '-');
  return `${prefix}-${String(counter).padStart(3, '0')}`;
}

// ============================================================================
// Example File Resolution
// ============================================================================

async function findExampleFile(type: string, cwd: string): Promise<string> {
  const registry = getTypeRegistry();
  const meta = registry[type];
  if (!meta) throw new Error(`Unknown document type: "${type}"`);

  const examplesDir = path.join(cwd, 'content', meta.folder, 'examples');
  if (!await fs.pathExists(examplesDir)) {
    throw new Error(`No examples directory for type "${type}" at ${examplesDir}`);
  }

  const files = (await fs.readdir(examplesDir)).filter((f: string) => f.endsWith('.md'));
  if (files.length === 0) {
    throw new Error(`No example .md files for type "${type}" in ${examplesDir}`);
  }

  // Prefer hand-written examples (prefixed with "example-")
  const handWritten = files.find((f: string) => f.startsWith('example-'));
  return path.join(examplesDir, handWritten || files[0]);
}

// ============================================================================
// Scaffold One Document (inline — no console output)
// ============================================================================

async function scaffoldOne(
  type: string,
  title: string,
  id: string,
  cwd: string,
  force: boolean,
): Promise<string> {
  const examplePath = await findExampleFile(type, cwd);
  const exampleContent = await fs.readFile(examplePath, 'utf-8');
  const { frontmatter, body } = parseFrontmatterAndBody(exampleContent);

  // Core frontmatter updates (mirrors scaffold.ts logic)
  const now = new Date().toISOString();
  frontmatter.id = id;
  frontmatter.title = title;
  frontmatter.status = 'draft';
  frontmatter.created = now;
  frontmatter.updated = now;
  delete frontmatter.example;

  // Strip type-name-only tags
  if (Array.isArray(frontmatter.tags)) {
    frontmatter.tags = frontmatter.tags.filter((t: string) => t !== type);
    if (frontmatter.tags.length === 0) delete frontmatter.tags;
  }

  // Build output path
  const kebabTitle = toKebabCase(title);
  const filename = `${id}-${kebabTitle}.md`;
  const folder = getExpectedFolder(type);
  const outputDir = path.join(cwd, folder, 'examples');
  const outputPath = path.join(outputDir, filename);

  if ((await fs.pathExists(outputPath)) && !force) {
    return outputPath;
  }

  await fs.ensureDir(outputDir);
  await fs.writeFile(outputPath, serializeDocument(frontmatter, body), 'utf-8');
  return outputPath;
}

// ============================================================================
// Domain Lookup for Cross-References
// ============================================================================

type DomainLookup = Map<string, Map<string, ManifestEntry[]>>;

function buildDomainLookup(manifest: ManifestEntry[]): DomainLookup {
  const lookup: DomainLookup = new Map();
  for (const doc of manifest) {
    if (!lookup.has(doc.domain)) lookup.set(doc.domain, new Map());
    const byType = lookup.get(doc.domain)!;
    if (!byType.has(doc.type)) byType.set(doc.type, []);
    byType.get(doc.type)!.push(doc);
  }
  return lookup;
}

function docsOfType(lookup: DomainLookup, domain: string, type: string): ManifestEntry[] {
  return lookup.get(domain)?.get(type) || [];
}

// ============================================================================
// Frontmatter Patching (second pass — cross-refs + type-specific fields)
// ============================================================================

async function patchDocument(
  doc: ManifestEntry,
  index: number,
  lookup: DomainLookup,
): Promise<void> {
  const raw = await fs.readFile(doc.filepath, 'utf-8');
  const { frontmatter, body } = parseFrontmatterAndBody(raw);
  const seed = index * 997; // prime multiplier avoids clustering

  // --- Common patches ---
  frontmatter.example = true;
  frontmatter.summary = doc.title;

  // Status (reference type has its own allowed values)
  if (doc.type === 'reference') {
    const refStatuses: [string, number][] = [['published', 70], ['draft', 20], ['archived', 10]];
    const refRoll = seededRandom(seed + 1) * 100;
    let refCum = 0;
    for (const [status, weight] of refStatuses) {
      refCum += weight;
      if (refRoll < refCum) { frontmatter.status = status; break; }
    }
  } else {
    const roll = seededRandom(seed + 1) * 100;
    let cum = 0;
    for (const [status, weight] of STATUS_WEIGHTS) {
      cum += weight;
      if (roll < cum) { frontmatter.status = status; break; }
    }
  }

  // Owner
  const pool = OWNER_POOLS[doc.type] || ['Engineering Team'];
  frontmatter.owner = pick(pool, seed + 2)
    .replace('$DOMAIN', doc.domain.split(' ')[0]);

  // Dates
  frontmatter.created = randomDate(2024, 2025, seed + 3);
  frontmatter.updated = randomDate(2025, 2026, seed + 4);

  // Tags
  frontmatter.tags = [doc.type, toKebabCase(doc.domain)];

  // --- Type-specific patches ---
  patchTypeSpecific(doc, frontmatter, index, seed, lookup);

  await fs.writeFile(doc.filepath, serializeDocument(frontmatter, body), 'utf-8');
}

function patchTypeSpecific(
  doc: ManifestEntry,
  fm: Record<string, any>,
  index: number,
  seed: number,
  lookup: DomainLookup,
): void {
  const d = doc.domain;

  switch (doc.type) {
    case 'policy': {
      const stds = docsOfType(lookup, d, 'standard');
      if (stds.length) fm.related_standards = pickN(stds, 2, seed + 10).map(s => s.id);
      break;
    }
    case 'standard': {
      const pols = docsOfType(lookup, d, 'policy');
      const sys = docsOfType(lookup, d, 'system');
      if (pols.length) fm.related_policies = pickN(pols, 2, seed + 10).map(p => p.id);
      if (sys.length) fm.related_systems = pickN(sys, 2, seed + 11).map(s => s.id);
      break;
    }
    case 'process': {
      const stds = docsOfType(lookup, d, 'standard');
      const sops = docsOfType(lookup, d, 'sop');
      const sys = docsOfType(lookup, d, 'system');
      if (stds.length) fm.related_standards = pickN(stds, 2, seed + 10).map(s => s.id);
      if (sops.length) fm.related_sops = pickN(sops, 2, seed + 11).map(s => s.id);
      if (sys.length) fm.related_systems = pickN(sys, 1, seed + 12).map(s => s.id);
      break;
    }
    case 'sop': {
      const procs = docsOfType(lookup, d, 'process');
      const sys = docsOfType(lookup, d, 'system');
      fm.related_process = procs.length ? pick(procs, seed + 10).id : 'placeholder-process';
      if (sys.length) fm.related_systems = pickN(sys, 1, seed + 11).map(s => s.id);
      break;
    }
    case 'guide': {
      fm.audience = pick(AUDIENCE_POOL, seed + 10);
      const sys = docsOfType(lookup, d, 'system');
      const sops = docsOfType(lookup, d, 'sop');
      if (sys.length) fm.related_systems = pickN(sys, 2, seed + 11).map(s => s.id);
      if (sops.length) fm.related_sops = pickN(sops, 2, seed + 12).map(s => s.id);
      break;
    }
    case 'meeting': {
      fm.company = doc.domain.replace(/\s+/g, '');
      fm.topic = doc.title;
      fm.meeting_date = randomDate(2024, 2026, seed + 10);
      fm.our_attendees = ['Principal Engineer', 'Tech Lead', 'Product Manager'];
      fm.their_attendees = ['Engineering Manager', 'QA Lead'];
      break;
    }
    case 'system': {
      fm.owner_team = `${doc.domain.split(' ')[0]} Engineering`;
      fm.runtime = pick(RUNTIME_POOL, seed + 10);
      fm.repos = [`https://git.example.com/acme/${toKebabCase(doc.title)}`];
      fm.sla = pick(['99.9% monthly uptime', '99.95% monthly uptime', '99.99% monthly uptime'], seed + 11);
      const deps = docsOfType(lookup, d, 'system').filter(s => s.id !== doc.id);
      if (deps.length) fm.dependencies = pickN(deps, 2, seed + 12).map(s => s.title);
      const rbs = docsOfType(lookup, d, 'runbook');
      if (rbs.length) fm.runbooks = pickN(rbs, 2, seed + 13).map(r => r.id);
      break;
    }
    case 'wiki': {
      fm.source_repo = `https://git.example.com/acme/${toKebabCase(doc.title.replace(/\s*-\s*.*$/, ''))}`;
      fm.generator = 'deepwiki';
      fm.commit_sha = randomHexSha(seed + 10);
      fm.generated_at = randomDate(2025, 2026, seed + 11);
      fm.model = pick(['gpt-4', 'claude-3-sonnet', 'gpt-4o'], seed + 12);
      fm.importance = pick(['high', 'medium', 'low'], seed + 13);
      break;
    }
    case 'report': {
      fm.company = doc.domain.replace(/\s+/g, '');
      fm.report_month = randomMonth(2024, 2026, seed + 10);
      fm.report_type = pick(REPORT_TYPE_POOL, seed + 11);
      fm.overall_health = pick(HEALTH_POOL, seed + 12);
      fm.confidence = pick(CONFIDENCE_POOL, seed + 13);
      fm.active_initiatives_count = 1 + Math.floor(seededRandom(seed + 14) * 8);
      fm.critical_risks_count = Math.floor(seededRandom(seed + 15) * 4);
      break;
    }
    case 'postmortem': {
      fm.incident_number = `INC-${index + 5}`; // offset from hand-written INC-4
      fm.severity = pick(SEVERITY_POOL, seed + 10);
      fm.incident_date = randomDate(2024, 2026, seed + 11).split('T')[0];
      fm.detection_time = randomDate(2024, 2026, seed + 12);
      fm.resolution_time = randomDate(2024, 2026, seed + 13);
      fm.total_duration = pick(DURATION_POOL, seed + 14);
      const sops = docsOfType(lookup, d, 'sop');
      if (sops.length) fm.related_sop = pick(sops, seed + 15).id;
      break;
    }
    case 'adr': {
      const others = docsOfType(lookup, d, 'adr').filter(a => a.id !== doc.id);
      if (others.length && seededRandom(seed + 10) < 0.15) {
        fm.supersedes = pick(others, seed + 11).id;
      }
      break;
    }
    case 'tdd': {
      const adrs = docsOfType(lookup, d, 'adr');
      if (adrs.length) fm.related_adrs = pickN(adrs, 2, seed + 10).map(a => a.id);
      break;
    }
    case 'prd': {
      const tdds = docsOfType(lookup, d, 'tdd');
      const stds = docsOfType(lookup, d, 'standard');
      if (tdds.length) fm.related_tdds = pickN(tdds, 2, seed + 10).map(t => t.id);
      if (stds.length) fm.related_standards = pickN(stds, 1, seed + 11).map(s => s.id);
      break;
    }
    case 'flow': {
      fm.feature_area = doc.domain;
      const prds = docsOfType(lookup, d, 'prd');
      if (prds.length) fm.related_prds = pickN(prds, 1, seed + 10).map(p => p.id);
      break;
    }
    case 'capability': {
      const evidence = [
        ...docsOfType(lookup, d, 'policy'),
        ...docsOfType(lookup, d, 'standard'),
        ...docsOfType(lookup, d, 'process'),
      ];
      if (evidence.length) fm.evidence_links = pickN(evidence, 3, seed + 10).map(e => e.id);
      break;
    }
    case 'reference': {
      fm.upstream_url = `https://docs.example.com/${toKebabCase(doc.title)}`;
      fm.last_synced = randomDate(2025, 2026, seed + 10);
      fm.category = pick(REFERENCE_CATEGORY_POOL, seed + 11);
      fm.attribution = pick(ATTRIBUTION_POOL, seed + 12);
      break;
    }
  }
}

// ============================================================================
// Main Orchestrator
// ============================================================================

export async function orchestrateGeneration(options: GenerateOptions): Promise<void> {
  const { titles: titlesPath, dir: cwd, force } = options;

  // 1. Read and validate titles
  console.log(`Reading titles from ${titlesPath}...`);
  const titlesJson = await fs.readFile(path.resolve(titlesPath), 'utf-8');
  const titles: TitleEntry[] = JSON.parse(titlesJson);
  console.log(`  ${titles.length} titles loaded`);

  for (let i = 0; i < titles.length; i++) {
    const e = titles[i];
    if (!e.type || !e.title || !e.domain) {
      throw new Error(`Invalid entry at index ${i}: ${JSON.stringify(e)}`);
    }
    const registry = getTypeRegistry();
    if (!registry[e.type]) {
      throw new Error(`Unknown type "${e.type}" at index ${i}. Known: ${Object.keys(registry).sort().join(', ')}`);
    }
  }

  // 2. Scaffold all files (first pass)
  console.log('\nScaffolding documents...');
  const typeCounters = new Map<string, number>();
  const manifest: ManifestEntry[] = [];
  let created = 0;
  let skipped = 0;

  for (const entry of titles) {
    const count = (typeCounters.get(entry.type) || 0) + 1;
    typeCounters.set(entry.type, count);

    const id = generateId(entry.type, count);
    const filepath = await scaffoldOne(entry.type, entry.title, id, cwd, force);
    manifest.push({ ...entry, id, filepath });

    if (force) created++; else created++; // simplified — scaffoldOne handles skip logic
  }
  console.log(`  ${manifest.length} files scaffolded`);

  // 3. Patch frontmatter (second pass — cross-references need all IDs)
  console.log('Patching frontmatter with cross-references...');
  const lookup = buildDomainLookup(manifest);

  for (let i = 0; i < manifest.length; i++) {
    await patchDocument(manifest[i], i, lookup);
    if ((i + 1) % 100 === 0) {
      console.log(`  ${i + 1}/${manifest.length} patched`);
    }
  }
  console.log(`  ${manifest.length} files patched`);

  // 4. Write manifest
  const manifestDir = path.join(cwd, '.synapse-generate');
  await fs.ensureDir(manifestDir);
  const manifestPath = path.join(manifestDir, 'manifest.json');
  await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2));
  console.log(`\nManifest: ${path.relative(cwd, manifestPath)}`);

  // 5. Summary
  console.log('\nDistribution:');
  const counts: Record<string, number> = {};
  const domains: Record<string, number> = {};
  for (const doc of manifest) {
    counts[doc.type] = (counts[doc.type] || 0) + 1;
    domains[doc.domain] = (domains[doc.domain] || 0) + 1;
  }
  for (const [type, n] of Object.entries(counts).sort()) {
    console.log(`  ${type.padEnd(12)} ${n}`);
  }
  console.log(`\nDomains: ${Object.keys(domains).sort().join(', ')}`);
  console.log(`\nDone! ${manifest.length} documents generated.`);
  console.log('Bodies are placeholder copies of the hand-written examples.');
  console.log('Use Claude Code to fill realistic body content from the manifest.');
}
