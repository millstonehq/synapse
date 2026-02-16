#!/usr/bin/env tsx
/**
 * Generate Decap CMS config.yml from JSON schemas and body grammars
 *
 * This ensures the CMS config stays in sync with schema definitions.
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import * as yaml from 'js-yaml';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PROJECT_ROOT = path.resolve(__dirname, '../../..');
const SCHEMAS_DIR = path.join(PROJECT_ROOT, 'schemas/frontmatter');
const GRAMMARS_DIR = path.join(PROJECT_ROOT, 'schemas/body-grammars');
const OUTPUT_PATH = path.join(__dirname, '../static/edit/config.yml');

// Collection configuration - maps doc types to their CMS settings
const COLLECTIONS: Record<string, {
  name: string;
  label: string;
  labelSingular: string;
  folder: string;
  slug?: string;
  statusOptions?: string[];
}> = {
  policy: {
    name: 'policies',
    label: '📜 Policies',
    labelSingular: 'Policy',
    folder: 'content/10_Policies',
  },
  standard: {
    name: 'standards',
    label: '📐 Standards',
    labelSingular: 'Standard',
    folder: 'content/20_Standards',
  },
  process: {
    name: 'processes',
    label: '🔄 Processes',
    labelSingular: 'Process',
    folder: 'content/30_Processes',
  },
  sop: {
    name: 'sops',
    label: '📋 SOPs',
    labelSingular: 'SOP',
    folder: 'content/40_SOPs',
  },
  runbook: {
    name: 'runbooks',
    label: '🔧 Runbooks',
    labelSingular: 'Runbook',
    folder: 'content/50_Runbooks',
  },
  guide: {
    name: 'guides',
    label: 'Guides',
    labelSingular: 'Guide',
    folder: 'content/55_Guides',
  },
  meeting: {
    name: 'meetings',
    label: '📅 Meetings',
    labelSingular: 'Meeting',
    folder: 'content/60_Meetings',
    slug: '{{year}}-{{month}}-{{day}}-{{slug}}',
  },
  postmortem: {
    name: 'postmortems',
    label: 'Postmortems',
    labelSingular: 'Postmortem',
    folder: 'content/70_Postmortems',
  },
  report: {
    name: 'reports',
    label: 'Reports',
    labelSingular: 'Report',
    folder: 'content/70_Reports',
  },
  system: {
    name: 'systems',
    label: '🖥️ Systems',
    labelSingular: 'System',
    folder: 'content/75_Systems',
  },
  wiki: {
    name: 'wikis',
    label: 'Wikis',
    labelSingular: 'Wiki',
    folder: 'content/75_Wikis',
  },
  adr: {
    name: 'adrs',
    label: '🏗️ ADRs',
    labelSingular: 'ADR',
    folder: 'content/90_Architecture/ADRs',
    slug: 'ADR-{{fields.adr_number}}-{{slug}}',
    statusOptions: ['proposed', 'accepted', 'deprecated', 'superseded'],
  },
  tdd: {
    name: 'tdds',
    label: '📐 TDDs',
    labelSingular: 'TDD',
    folder: 'content/90_Architecture/TDDs',
  },
  prd: {
    name: 'prds',
    label: '📦 PRDs',
    labelSingular: 'PRD',
    folder: 'content/100_Products/PRDs',
  },
  capability: {
    name: 'capabilities',
    label: '🎯 Capabilities',
    labelSingular: 'Capability',
    folder: 'content/110_Capabilities',
  },
  reference: {
    name: 'references',
    label: '📚 References',
    labelSingular: 'Reference',
    folder: 'content/200_References',
  },
};

interface SchemaProperty {
  type?: string;
  enum?: string[];
  const?: string;
  format?: string;
  items?: { type: string };
  minLength?: number;
}

interface Schema {
  properties: Record<string, SchemaProperty>;
  required?: string[];
  allOf?: Array<{ $ref: string }>;
}

interface BodyGrammarSection {
  id: string;
  title: string;
  required: boolean;
  order: number;
  shape: {
    type: string;
    ordered?: boolean;
    minItems?: number;
    allowedNodes?: string[];
  };
}

interface BodyGrammar {
  type: string;
  displayName: string;
  sections: BodyGrammarSection[];
}

interface DecapField {
  label: string;
  name: string;
  widget: string;
  required?: boolean;
  default?: string | boolean;
  hint?: string;
  options?: string[];
}

// Map JSON schema types to Decap widget types
function schemaTypeToWidget(prop: SchemaProperty, name: string): string {
  if (prop.enum) return 'select';
  if (prop.const) return 'hidden';
  if (prop.format === 'date-time') return 'datetime';
  if (prop.type === 'array') return 'list';
  if (prop.type === 'boolean') return 'boolean';
  if (name === 'summary') return 'text';
  return 'string';
}

// Generate placeholder content based on section shape
function generateSectionPlaceholder(section: BodyGrammarSection): string {
  const shape = section.shape;

  if (shape.type === 'list') {
    if (shape.ordered) {
      return '1. First item\n2. Second item';
    }
    return '- Item one\n- Item two';
  }

  if (shape.type === 'table') {
    return '| Column 1 | Column 2 |\n|----------|----------|\n| Data | Data |';
  }

  return '[Describe here...]';
}

// Generate default body template from body grammar
function generateDefaultBody(grammar: BodyGrammar): string {
  if (!grammar || !grammar.sections) return '';

  const sections = grammar.sections
    .filter(s => s.required)
    .sort((a, b) => a.order - b.order);

  return sections.map(section => {
    const placeholder = generateSectionPlaceholder(section);
    return `## ${section.title}\n\n${placeholder}`;
  }).join('\n\n');
}

// Generate hint showing required sections
function generateBodyHint(grammar: BodyGrammar): string {
  if (!grammar || !grammar.sections) return '';

  const required = grammar.sections
    .filter(s => s.required)
    .sort((a, b) => a.order - b.order)
    .map(s => {
      let hint = s.title;
      if (s.shape.type === 'list') {
        hint += s.shape.ordered ? ' (numbered list)' : ' (bullet list)';
      }
      return hint;
    });

  if (required.length === 0) return '';

  return `Required sections: ${required.join(', ')}`;
}

// Load and merge schema with base
function loadSchema(type: string): Schema {
  const schemaPath = path.join(SCHEMAS_DIR, `${type}.schema.json`);
  const basePath = path.join(SCHEMAS_DIR, 'base.schema.json');

  const baseSchema: Schema = JSON.parse(fs.readFileSync(basePath, 'utf-8'));

  if (!fs.existsSync(schemaPath)) {
    return baseSchema;
  }

  const typeSchema: Schema = JSON.parse(fs.readFileSync(schemaPath, 'utf-8'));

  // Merge properties
  return {
    properties: {
      ...baseSchema.properties,
      ...typeSchema.properties,
    },
    required: [
      ...(baseSchema.required || []),
      ...(typeSchema.required || []),
    ],
  };
}

// Load body grammar
function loadBodyGrammar(type: string): BodyGrammar | null {
  const grammarPath = path.join(GRAMMARS_DIR, `${type}.body-grammar.json`);

  if (!fs.existsSync(grammarPath)) {
    return null;
  }

  return JSON.parse(fs.readFileSync(grammarPath, 'utf-8'));
}

// Generate Decap fields from schema
function generateFields(
  type: string,
  schema: Schema,
  grammar: BodyGrammar | null,
  collectionConfig: typeof COLLECTIONS[string]
): DecapField[] {
  const fields: DecapField[] = [];
  const required = new Set(schema.required || []);

  // Define field order (important fields first)
  const fieldOrder = [
    'adr_number', // ADR-specific
    'id',
    'title',
    'type',
    'status',
    'owner',
    'created',
    'updated',
    'tags',
    'summary',
  ];

  // Get all property names and sort by order
  const propNames = Object.keys(schema.properties);
  const sortedProps = [
    ...fieldOrder.filter(f => propNames.includes(f)),
    ...propNames.filter(f => !fieldOrder.includes(f) && f !== 'example'),
  ];

  for (const name of sortedProps) {
    const prop = schema.properties[name];
    if (!prop) continue;

    // Skip 'example' field - internal use only
    if (name === 'example') continue;

    const widget = schemaTypeToWidget(prop, name);
    const field: DecapField = {
      label: formatLabel(name),
      name,
      widget,
      required: required.has(name),
    };

    // Handle special cases
    if (widget === 'hidden') {
      field.default = prop.const || type;
    }

    if (widget === 'select' && prop.enum) {
      // Use collection-specific status options if defined
      if (name === 'status' && collectionConfig.statusOptions) {
        field.options = collectionConfig.statusOptions;
        field.default = collectionConfig.statusOptions[0];
      } else {
        field.options = prop.enum;
        field.default = prop.enum[0];
      }
    }

    fields.push(field);
  }

  // Add body field with hint and default
  // Raw mode only - the preview pane provides visual feedback
  // and raw mode is more predictable for structured docs with required sections
  const bodyField: Record<string, any> = {
    label: 'Body',
    name: 'body',
    widget: 'markdown',
    required: true,
    modes: ['raw'],
  };

  if (grammar) {
    const hint = generateBodyHint(grammar);
    if (hint) {
      bodyField.hint = hint;
    }

    const defaultBody = generateDefaultBody(grammar);
    if (defaultBody) {
      bodyField.default = defaultBody;
    }
  }

  fields.push(bodyField);

  return fields;
}

// Format field name as label
function formatLabel(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Generate full config
function generateConfig(): object {
  const collections = [];

  for (const [type, config] of Object.entries(COLLECTIONS)) {
    const schema = loadSchema(type);
    const grammar = loadBodyGrammar(type);
    const fields = generateFields(type, schema, grammar, config);

    const collection: Record<string, any> = {
      name: config.name,
      label: config.label,
      label_singular: config.labelSingular,
      folder: config.folder,
      create: true,
      nested: { depth: 10 },
      slug: config.slug || '{{slug}}',
      extension: 'md',
      format: 'yaml-frontmatter',
      fields,
    };

    collections.push(collection);
  }

  return {
    backend: {
      name: process.env.DECAP_BACKEND || 'github',
      repo: process.env.DECAP_REPO || 'OWNER/REPO',
      branch: process.env.DECAP_BRANCH || 'main',
      auth_type: 'pkce',
      app_id: process.env.DECAP_APP_ID || '',
      api_root: process.env.DECAP_API_ROOT || 'https://api.github.com',
      base_url: process.env.DECAP_BASE_URL || 'https://github.com',
    },
    media_folder: 'content/_assets',
    public_folder: '/_assets',
    local_backend: true,
    site_url: '/',
    display_url: '/',
    logo_url: '/static/logo.png',
    collections,
  };
}

// Main
function main() {
  console.log('Generating Decap CMS config from schemas...');

  const config = generateConfig();

  // Convert to YAML
  const yamlContent = yaml.dump(config, {
    indent: 2,
    lineWidth: 120,
    noRefs: true,
    quotingType: '"',
    forceQuotes: false,
  });

  // Add header comment
  const output = `# Decap CMS Configuration - AUTO-GENERATED
# DO NOT EDIT MANUALLY - Run 'npm run build:decap-config' to regenerate
# Source: schemas/frontmatter/*.schema.json, schemas/body-grammars/*.body-grammar.json

${yamlContent}`;

  // Ensure output directory exists
  const outputDir = path.dirname(OUTPUT_PATH);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_PATH, output);
  console.log(`✓ Generated config.yml with ${Object.keys(COLLECTIONS).length} collections`);
}

main();
