/**
 * Generate synthetic example documents from a titles manifest.
 *
 * Usage:
 *   synapse generate <titles.json> [--force] [--dir <path>]
 *
 * The titles.json is an array of { type, title, domain } objects.
 * Generate it however you like (Claude Code, script, by hand).
 *
 * This command:
 *   1. Scaffolds each doc using the existing example as template
 *   2. Assigns sequential IDs per type
 *   3. Patches frontmatter with cross-references, dates, owners
 *   4. Writes a manifest.json listing everything it created
 *
 * Body content is copied from the hand-written example (placeholder).
 * Use Claude Code to fill realistic body content afterward.
 */

import { orchestrateGeneration } from '../lib/generate.js';

export async function generateCommand(args: Record<string, any>): Promise<void> {
  const titlesPath = args._?.[0] || args.titles;

  if (!titlesPath) {
    console.error(
      'Missing required argument: path to titles.json\n\n' +
      'Usage: synapse generate <titles.json> [--force] [--dir <path>]\n\n' +
      'The titles.json should be a JSON array of objects:\n' +
      '  [{ "type": "policy", "title": "Data Retention Policy", "domain": "Data Pipeline" }, ...]\n\n' +
      'Available types: policy, standard, process, sop, runbook, guide, meeting,\n' +
      '  system, wiki, report, postmortem, adr, tdd, prd, flow, capability, reference'
    );
    process.exit(1);
  }

  await orchestrateGeneration({
    titles: titlesPath,
    dir: args.dir || process.cwd(),
    force: !!args.force,
  });
}
