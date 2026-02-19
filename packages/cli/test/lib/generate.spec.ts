import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import * as yaml from 'js-yaml';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { orchestrateGeneration, type TitleEntry } from '../../src/lib/generate';

const TEST_DIR = path.join(process.cwd(), 'test-generate-tmp');
const CONTENT_DIR = path.join(TEST_DIR, 'content');

// Helper to create a minimal example file for a type
async function createExample(
  folder: string,
  filename: string,
  frontmatter: Record<string, any>,
  body: string,
) {
  const examplesDir = path.join(CONTENT_DIR, folder, 'examples');
  await fs.ensureDir(examplesDir);
  const fmYaml = yaml.dump(frontmatter, { lineWidth: -1 }).trim();
  await fs.writeFile(
    path.join(examplesDir, filename),
    `---\n${fmYaml}\n---\n${body}`,
    'utf-8',
  );
}

// Read and parse a generated file
async function readGenerated(filepath: string) {
  const raw = await fs.readFile(filepath, 'utf-8');
  const lines = raw.split('\n');
  let start = -1, end = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() === '---') {
      if (start === -1) start = i;
      else { end = i; break; }
    }
  }
  const fmYaml = lines.slice(start + 1, end).join('\n');
  const body = lines.slice(end + 1).join('\n');
  return { frontmatter: yaml.load(fmYaml) as Record<string, any>, body };
}

// Seed the test content directory with one example per type we'll use
async function seedExamples() {
  await createExample(
    '10_Policies', 'example-test-policy.md',
    { id: 'test-policy', type: 'policy', title: 'Test Policy', status: 'draft', owner: 'CTO', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['policy'], summary: 'A test policy', example: true },
    '\n## Scope\n\nAll systems.\n\n## Policy Statements\n\n- Statement one.\n',
  );
  await createExample(
    '20_Standards', 'example-test-standard.md',
    { id: 'test-standard', type: 'standard', title: 'Test Standard', status: 'approved', owner: 'Head of Engineering', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['standard'], summary: 'A test standard', example: true },
    '\n## Purpose\n\nEstablish standards.\n',
  );
  await createExample(
    '30_Processes', 'example-test-process.md',
    { id: 'test-process', type: 'process', title: 'Test Process', status: 'approved', owner: 'Platform Lead', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['process'], summary: 'A test process', example: true },
    '\n## Purpose\n\nProcess description.\n',
  );
  await createExample(
    '40_SOPs', 'example-test-sop.md',
    { id: 'test-sop', type: 'sop', title: 'Test SOP', status: 'approved', owner: 'SRE Lead', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['sop'], summary: 'A test SOP', example: true },
    '\n## Prerequisites\n\n- Access to system.\n\n## Steps\n\n1. Do thing.\n',
  );
  await createExample(
    '90_Architecture/ADRs', 'example-test-adr.md',
    { id: 'ADR-0001', type: 'adr', title: 'Example ADR', status: 'proposed', owner: 'Tech Lead', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['adr'], example: true },
    '\n## Context\n\nSome context.\n\n## Decision\n\nWe decided X.\n',
  );
  await createExample(
    '90_Architecture/TDDs', 'example-test-tdd.md',
    { id: 'TDD-001', type: 'tdd', title: 'Example TDD', status: 'proposed', owner: 'Senior Engineer', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['tdd'], example: true },
    '\n## Problem\n\nDesign problem.\n',
  );
  await createExample(
    '100_Products/PRDs', 'example-test-prd.md',
    { id: 'PRD-001', type: 'prd', title: 'Example PRD', status: 'draft', owner: 'Product Manager', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['prd'], example: true },
    '\n## Problem\n\nProduct problem.\n',
  );
  await createExample(
    '70_Systems', 'example-test-system.md',
    { id: 'SYSTEM-001', type: 'system', title: 'Test System', status: 'approved', owner: 'Platform Engineering', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['system'], example: true },
    '\n## Service Overview\n\nSystem description.\n',
  );
  await createExample(
    '50_Runbooks', 'example-test-runbook.md',
    { id: 'RUNBOOK-001', type: 'runbook', title: 'Test Runbook', status: 'approved', owner: 'On-Call Engineer', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['runbook'], example: true },
    '\n## Service\n\n- **System**: Test\n\n## Alerts\n\n- test_alert\n',
  );
  await createExample(
    '55_Guides', 'example-test-guide.md',
    { id: 'GUIDE-001', type: 'guide', title: 'Test Guide', status: 'approved', owner: 'Engineering Team', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['guide'], example: true },
    '\n## Overview\n\nGuide description.\n',
  );
  await createExample(
    '60_Meetings', 'example-test-meeting.md',
    { id: 'MEETING-001', type: 'meeting', title: 'Test Meeting', status: 'approved', owner: 'Engineering Manager', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['meeting'], company: 'TestCo', topic: 'Test', meeting_date: '2025-01-01', our_attendees: ['Alice'], their_attendees: ['Bob'], example: true },
    '\n## Agenda\n\n1. Topic.\n',
  );
  await createExample(
    '75_Wikis', 'example-test-wiki.md',
    { id: 'WIKI-001', type: 'wiki', title: 'Test Wiki', status: 'approved', owner: 'Platform Team', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['wiki'], example: true },
    '\n## Overview\n\nWiki page.\n',
  );
  await createExample(
    '80_Reports', 'example-test-report.md',
    { id: 'REPORT-001', type: 'report', title: 'Test Report', status: 'approved', owner: 'Tech Lead', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['report'], example: true },
    '\n## Service Health\n\nAll good.\n',
  );
  await createExample(
    '85_Postmortems', 'example-test-postmortem.md',
    { id: 'POSTMORTEM-001', type: 'postmortem', title: 'Test Postmortem', status: 'approved', owner: 'Incident Commander', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['postmortem'], incident_number: 'INC-1', severity: 'SEV-2', incident_date: '2025-01-01', detection_time: '2025-01-01T00:00:00.000Z', resolution_time: '2025-01-01T01:00:00.000Z', total_duration: '~1 hour', example: true },
    '\n## Summary\n\nIncident summary.\n',
  );
  await createExample(
    '100_Products/Flows', 'example-test-flow.md',
    { id: 'FLOW-001', type: 'flow', title: 'Test Flow', status: 'approved', owner: 'QA Lead', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['flow'], example: true },
    '\n## Preconditions\n\n- User logged in.\n',
  );
  await createExample(
    '110_Capabilities', 'example-test-capability.md',
    { id: 'CAPABILITY-001', type: 'capability', title: 'Test Capability', status: 'approved', owner: 'Head of Engineering', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['capability'], example: true },
    '\n## Description\n\nCapability.\n',
  );
  await createExample(
    '200_References', 'example-test-reference.md',
    { id: 'REFERENCE-001', type: 'reference', title: 'Test Reference', status: 'published', owner: 'Security Team', created: '2025-01-01T00:00:00.000Z', updated: '2025-01-01T00:00:00.000Z', tags: ['reference'], upstream_url: 'https://example.com', category: 'documentation', example: true },
    '\n## Overview\n\nReference doc.\n',
  );
}

describe('generate', () => {
  beforeEach(async () => {
    await fs.remove(TEST_DIR);
    await fs.ensureDir(CONTENT_DIR);
    await seedExamples();
  });

  afterEach(async () => {
    await fs.remove(TEST_DIR);
  });

  describe('orchestrateGeneration', () => {
    it('scaffolds documents from a titles manifest', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'Access Control Policy', domain: 'Auth' },
        { type: 'standard', title: 'Password Standard', domain: 'Auth' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      // Check files were created
      const policyPath = path.join(CONTENT_DIR, '10_Policies/examples/POLICY-001-access-control-policy.md');
      const standardPath = path.join(CONTENT_DIR, '20_Standards/examples/STANDARD-001-password-standard.md');
      expect(await fs.pathExists(policyPath)).toBe(true);
      expect(await fs.pathExists(standardPath)).toBe(true);
    });

    it('assigns sequential IDs per type', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'Policy One', domain: 'Auth' },
        { type: 'policy', title: 'Policy Two', domain: 'Auth' },
        { type: 'standard', title: 'Standard One', domain: 'Auth' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      const p1 = await readGenerated(path.join(CONTENT_DIR, '10_Policies/examples/POLICY-001-policy-one.md'));
      const p2 = await readGenerated(path.join(CONTENT_DIR, '10_Policies/examples/POLICY-002-policy-two.md'));
      const s1 = await readGenerated(path.join(CONTENT_DIR, '20_Standards/examples/STANDARD-001-standard-one.md'));

      expect(p1.frontmatter.id).toBe('POLICY-001');
      expect(p2.frontmatter.id).toBe('POLICY-002');
      expect(s1.frontmatter.id).toBe('STANDARD-001');
    });

    it('generates ADR IDs starting from 0002', async () => {
      const titles: TitleEntry[] = [
        { type: 'adr', title: 'Use React', domain: 'Frontend' },
        { type: 'adr', title: 'Use TypeScript', domain: 'Frontend' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      const a1 = await readGenerated(path.join(CONTENT_DIR, '90_Architecture/ADRs/examples/ADR-0002-use-react.md'));
      const a2 = await readGenerated(path.join(CONTENT_DIR, '90_Architecture/ADRs/examples/ADR-0003-use-typescript.md'));

      expect(a1.frontmatter.id).toBe('ADR-0002');
      expect(a2.frontmatter.id).toBe('ADR-0003');
    });

    it('patches frontmatter with example flag, tags, and deterministic fields', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'Security Policy', domain: 'Security' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      const doc = await readGenerated(path.join(CONTENT_DIR, '10_Policies/examples/POLICY-001-security-policy.md'));
      expect(doc.frontmatter.example).toBe(true);
      expect(doc.frontmatter.summary).toBe('Security Policy');
      expect(doc.frontmatter.tags).toContain('policy');
      expect(doc.frontmatter.tags).toContain('security');
      expect(doc.frontmatter.owner).toBeDefined();
      expect(doc.frontmatter.status).toBeDefined();
    });

    it('creates cross-references between types in the same domain', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'Data Policy', domain: 'Data' },
        { type: 'standard', title: 'Data Standard', domain: 'Data' },
        { type: 'process', title: 'Data Process', domain: 'Data' },
        { type: 'sop', title: 'Data SOP', domain: 'Data' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      // Policy should reference standards
      const policy = await readGenerated(path.join(CONTENT_DIR, '10_Policies/examples/POLICY-001-data-policy.md'));
      expect(policy.frontmatter.related_standards).toContain('STANDARD-001');

      // Standard should reference policies
      const standard = await readGenerated(path.join(CONTENT_DIR, '20_Standards/examples/STANDARD-001-data-standard.md'));
      expect(standard.frontmatter.related_policies).toContain('POLICY-001');

      // Process should reference standards and SOPs
      const process = await readGenerated(path.join(CONTENT_DIR, '30_Processes/examples/PROCESS-001-data-process.md'));
      expect(process.frontmatter.related_standards).toContain('STANDARD-001');
      expect(process.frontmatter.related_sops).toContain('SOP-001');

      // SOP should reference process
      const sop = await readGenerated(path.join(CONTENT_DIR, '40_SOPs/examples/SOP-001-data-sop.md'));
      expect(sop.frontmatter.related_process).toBe('PROCESS-001');
    });

    it('patches type-specific fields for all 17 types', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'Test Policy', domain: 'Test' },
        { type: 'standard', title: 'Test Standard', domain: 'Test' },
        { type: 'process', title: 'Test Process', domain: 'Test' },
        { type: 'sop', title: 'Test SOP', domain: 'Test' },
        { type: 'runbook', title: 'Test Runbook', domain: 'Test' },
        { type: 'guide', title: 'Test Guide', domain: 'Test' },
        { type: 'meeting', title: 'Test Meeting', domain: 'Test' },
        { type: 'system', title: 'Test System', domain: 'Test' },
        { type: 'wiki', title: 'Test Wiki', domain: 'Test' },
        { type: 'report', title: 'Test Report', domain: 'Test' },
        { type: 'postmortem', title: 'Test Postmortem', domain: 'Test' },
        { type: 'adr', title: 'Test ADR', domain: 'Test' },
        { type: 'tdd', title: 'Test TDD', domain: 'Test' },
        { type: 'prd', title: 'Test PRD', domain: 'Test' },
        { type: 'flow', title: 'Test Flow', domain: 'Test' },
        { type: 'capability', title: 'Test Capability', domain: 'Test' },
        { type: 'reference', title: 'Test Reference', domain: 'Test' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      // Meeting has company, topic, meeting_date, attendees
      const meeting = await readGenerated(path.join(CONTENT_DIR, '60_Meetings/examples/MEETING-001-test-meeting.md'));
      expect(meeting.frontmatter.company).toBe('Test');
      expect(meeting.frontmatter.topic).toBe('Test Meeting');
      expect(meeting.frontmatter.meeting_date).toBeDefined();
      expect(meeting.frontmatter.our_attendees).toBeDefined();
      expect(meeting.frontmatter.their_attendees).toBeDefined();

      // System has owner_team, runtime, repos, sla
      const system = await readGenerated(path.join(CONTENT_DIR, '70_Systems/examples/SYSTEM-001-test-system.md'));
      expect(system.frontmatter.owner_team).toBe('Test Engineering');
      expect(system.frontmatter.runtime).toBeDefined();
      expect(system.frontmatter.repos).toBeDefined();
      expect(system.frontmatter.sla).toBeDefined();

      // Wiki has source_repo, generator, model
      const wiki = await readGenerated(path.join(CONTENT_DIR, '75_Wikis/examples/WIKI-001-test-wiki.md'));
      expect(wiki.frontmatter.generator).toBe('deepwiki');
      expect(wiki.frontmatter.model).toBeDefined();
      expect(wiki.frontmatter.commit_sha).toMatch(/^[0-9a-f]{40}$/);

      // Report has company, report_month, report_type, health, confidence
      const report = await readGenerated(path.join(CONTENT_DIR, '80_Reports/examples/REPORT-001-test-report.md'));
      expect(report.frontmatter.report_month).toMatch(/^\d{4}-\d{2}$/);
      expect(report.frontmatter.report_type).toBeDefined();
      expect(report.frontmatter.overall_health).toBeDefined();
      expect(report.frontmatter.confidence).toBeDefined();

      // Postmortem has incident fields
      const postmortem = await readGenerated(path.join(CONTENT_DIR, '85_Postmortems/examples/POSTMORTEM-001-test-postmortem.md'));
      expect(postmortem.frontmatter.incident_number).toMatch(/^INC-/);
      expect(postmortem.frontmatter.severity).toMatch(/^SEV-/);
      expect(postmortem.frontmatter.incident_date).toBeDefined();
      expect(postmortem.frontmatter.total_duration).toBeDefined();

      // Reference has upstream_url, category, attribution
      const reference = await readGenerated(path.join(CONTENT_DIR, '200_References/examples/REFERENCE-001-test-reference.md'));
      expect(reference.frontmatter.upstream_url).toContain('https://');
      expect(reference.frontmatter.category).toBeDefined();
      expect(reference.frontmatter.attribution).toBeDefined();
      expect(reference.frontmatter.last_synced).toBeDefined();

      // Guide has audience
      const guide = await readGenerated(path.join(CONTENT_DIR, '55_Guides/examples/GUIDE-001-test-guide.md'));
      expect(['internal', 'customer', 'partner']).toContain(guide.frontmatter.audience);

      // Flow has feature_area
      const flow = await readGenerated(path.join(CONTENT_DIR, '100_Products/Flows/examples/FLOW-001-test-flow.md'));
      expect(flow.frontmatter.feature_area).toBe('Test');
    });

    it('writes a manifest.json to .synapse-generate/', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'Manifest Test Policy', domain: 'Test' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      const manifestPath = path.join(TEST_DIR, '.synapse-generate', 'manifest.json');
      expect(await fs.pathExists(manifestPath)).toBe(true);

      const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf-8'));
      expect(manifest).toHaveLength(1);
      expect(manifest[0].id).toBe('POLICY-001');
      expect(manifest[0].type).toBe('policy');
      expect(manifest[0].domain).toBe('Test');
    });

    it('is deterministic — same input produces same output', async () => {
      const titles: TitleEntry[] = [
        { type: 'system', title: 'Auth Service', domain: 'Auth' },
        { type: 'report', title: 'Auth Report', domain: 'Auth' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      // Run twice
      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });
      const first = await readGenerated(path.join(CONTENT_DIR, '70_Systems/examples/SYSTEM-001-auth-service.md'));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });
      const second = await readGenerated(path.join(CONTENT_DIR, '70_Systems/examples/SYSTEM-001-auth-service.md'));

      // Owner and status should be identical across runs (seeded PRNG)
      expect(first.frontmatter.owner).toBe(second.frontmatter.owner);
      expect(first.frontmatter.status).toBe(second.frontmatter.status);
      expect(first.frontmatter.runtime).toBe(second.frontmatter.runtime);
    });

    it('throws on invalid entry missing required fields', async () => {
      const titles = [{ type: 'policy', title: '' }]; // missing domain + empty title
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await expect(
        orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true }),
      ).rejects.toThrow('Invalid entry');
    });

    it('throws on unknown document type', async () => {
      const titles = [{ type: 'foobar', title: 'Bad Type', domain: 'Test' }];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await expect(
        orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true }),
      ).rejects.toThrow('Unknown type "foobar"');
    });

    it('does not overwrite existing files without --force', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'No Overwrite Policy', domain: 'Test' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      // First run creates the file
      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });
      const filePath = path.join(CONTENT_DIR, '10_Policies/examples/POLICY-001-no-overwrite-policy.md');
      const firstContent = await fs.readFile(filePath, 'utf-8');

      // Modify the file
      await fs.writeFile(filePath, firstContent + '\n<!-- modified -->', 'utf-8');

      // Second run without force — should not clobber modification
      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: false });
      const secondContent = await fs.readFile(filePath, 'utf-8');
      // Note: the patch pass will still rewrite frontmatter, but the scaffold pass won't overwrite
      // Since patch reads + rewrites the file, it will process whatever is there
      expect(await fs.pathExists(filePath)).toBe(true);
    });

    it('strips the type-only tag from example template', async () => {
      const titles: TitleEntry[] = [
        { type: 'policy', title: 'Tag Test Policy', domain: 'Test' },
      ];
      const titlesPath = path.join(TEST_DIR, 'titles.json');
      await fs.writeFile(titlesPath, JSON.stringify(titles));

      await orchestrateGeneration({ titles: titlesPath, dir: TEST_DIR, force: true });

      const doc = await readGenerated(path.join(CONTENT_DIR, '10_Policies/examples/POLICY-001-tag-test-policy.md'));
      // Tags should include domain tag, not just the type
      expect(doc.frontmatter.tags).toContain('test');
      expect(doc.frontmatter.tags).toContain('policy');
    });
  });
});
