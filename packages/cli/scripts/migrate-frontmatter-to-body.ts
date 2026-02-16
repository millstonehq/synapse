#!/usr/bin/env tsx
/**
 * Universal script to migrate frontmatter content fields to body sections
 * Handles all doc types: process, sop, policy, standard, capability, prd, etc.
 */

import fsExtra from 'fs-extra';
import * as path from 'path';
import * as yaml from 'js-yaml';
import glob from 'fast-glob';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fs = fsExtra;

// Define which fields should be moved to body for each doc type
const BODY_FIELDS_BY_TYPE: Record<string, string[]> = {
  process: ['purpose', 'scope', 'roles', 'triggers', 'inputs', 'outputs', 'steps', 'controls'],
  sop: ['purpose', 'scope', 'preconditions', 'materials', 'procedure', 'references', 'step_list', 'stepList', 'validation', 'rollback'],
  policy: ['purpose', 'scope', 'rationale', 'policy_statements', 'policyStatements', 'statements'],
  standard: ['area', 'purpose', 'scope', 'controls', 'compliance', 'mappings'],
  capability: ['domain', 'maturity', 'purpose', 'scope', 'metrics', 'evidence', 'notes'],
  prd: ['background', 'goals', 'in_scope', 'inScope', 'out_of_scope', 'outOfScope', 'milestones', 'success_metrics', 'successMetrics'],
  tdd: ['background', 'goals', 'constraints', 'components', 'data_flow', 'dataFlow', 'security', 'performance'],
  adr: ['context', 'decision', 'consequences', 'alternatives'],
  meeting: ['attendees', 'agenda', 'discussion', 'decisions', 'action_items', 'actionItems', 'context', 'followups'],
  scorecard: ['scores', 'findings', 'recommendations', 'dimensions', 'weighted_total', 'weightedTotal', 'overall_summary', 'overallSummary', 'strengths', 'top_risks', 'topRisks', 'recommendation', 'metrics', 'risks', 'action_plan', 'actionPlan'],
  runbook: ['purpose', 'scope', 'preconditions', 'steps', 'rollback', 'verification', 'service', 'alerts', 'diagnosis_steps', 'diagnosisSteps', 'remediation_steps', 'remediationSteps', 'escalation', 'dashboards', 'spec'],
  system: ['purpose', 'scope', 'architecture', 'dependencies', 'data_flows', 'dataFlows'],
  agreement: ['parties', 'scope', 'terms', 'obligations', 'termination'],
  sow: ['objective', 'scope_of_work', 'scopeOfWork', 'deliverables', 'out_of_scope', 'outOfScope', 'timeline_milestones', 'timelineMilestones', 'acceptance_criteria', 'acceptanceCriteria', 'assumptions', 'dependencies', 'risks_and_mitigations', 'risksAndMitigations', 'change_control', 'changeControl', 'pricing_payment_terms', 'pricingPaymentTerms', 'ip_and_confidentiality', 'ipAndConfidentiality', 'communication_cadence', 'communicationCadence', 'approval'],
};

interface DocFrontmatter {
  id: string;
  type: string;
  title: string;
  [key: string]: any;
}

function buildBodySections(frontmatter: DocFrontmatter, type: string): string[] {
  const sections: string[] = [];
  const fieldsToMigrate = BODY_FIELDS_BY_TYPE[type] || [];

  // Process-specific sections
  if (type === 'process') {
    if (frontmatter.purpose) {
      sections.push('## Purpose\n', `${frontmatter.purpose}\n`);
    }
    if (frontmatter.scope) {
      sections.push('## Scope\n', `${frontmatter.scope}\n`);
    }
    if (frontmatter.roles && Array.isArray(frontmatter.roles) && frontmatter.roles.length > 0) {
      sections.push('## Roles and Responsibilities\n');
      frontmatter.roles.forEach((role: string) => sections.push(`- **${role}**\n`));
      sections.push('');
    }
    if (frontmatter.triggers) {
      sections.push('## Triggers\n', `${frontmatter.triggers}\n`);
    }
    if (frontmatter.inputs && Array.isArray(frontmatter.inputs) && frontmatter.inputs.length > 0) {
      sections.push('## Inputs\n');
      frontmatter.inputs.forEach((input: string) => sections.push(`- ${input}\n`));
      sections.push('');
    }
    if (frontmatter.outputs && Array.isArray(frontmatter.outputs) && frontmatter.outputs.length > 0) {
      sections.push('## Outputs\n');
      frontmatter.outputs.forEach((output: string) => sections.push(`- ${output}\n`));
      sections.push('');
    }
    if (frontmatter.steps && Array.isArray(frontmatter.steps) && frontmatter.steps.length > 0) {
      sections.push('## Steps\n');
      frontmatter.steps.forEach((step: string) => sections.push(`1. ${step}\n`));
      sections.push('');
    }
    if (frontmatter.controls && Array.isArray(frontmatter.controls) && frontmatter.controls.length > 0) {
      sections.push('## Controls\n');
      frontmatter.controls.forEach((control: string) => sections.push(`- ${control}\n`));
      sections.push('');
    }
  }

  // SOP-specific sections
  if (type === 'sop') {
    if (frontmatter.purpose) {
      sections.push('## Purpose\n', `${frontmatter.purpose}\n`);
    }
    if (frontmatter.scope) {
      sections.push('## Scope\n', `${frontmatter.scope}\n`);
    }
    if (frontmatter.preconditions && Array.isArray(frontmatter.preconditions) && frontmatter.preconditions.length > 0) {
      sections.push('## Preconditions\n');
      frontmatter.preconditions.forEach((item: string) => sections.push(`- ${item}\n`));
      sections.push('');
    }
    if (frontmatter.materials && Array.isArray(frontmatter.materials) && frontmatter.materials.length > 0) {
      sections.push('## Materials/Access\n');
      frontmatter.materials.forEach((item: string) => sections.push(`- ${item}\n`));
      sections.push('');
    }
    if (frontmatter.procedure && Array.isArray(frontmatter.procedure) && frontmatter.procedure.length > 0) {
      sections.push('## Procedure\n');
      frontmatter.procedure.forEach((step: string) => sections.push(`1. ${step}\n`));
      sections.push('');
    }
    if (frontmatter.references && Array.isArray(frontmatter.references) && frontmatter.references.length > 0) {
      sections.push('## References\n');
      frontmatter.references.forEach((ref: string) => sections.push(`- ${ref}\n`));
      sections.push('');
    }
  }

  // Policy-specific sections
  if (type === 'policy') {
    if (frontmatter.purpose) {
      sections.push('## Purpose\n', `${frontmatter.purpose}\n`);
    }
    if (frontmatter.scope) {
      sections.push('## Scope\n', `${frontmatter.scope}\n`);
    }
    if (frontmatter.rationale) {
      sections.push('## Rationale\n', `${frontmatter.rationale}\n`);
    }
    const policyStatements = frontmatter.policy_statements || frontmatter.policyStatements;
    if (policyStatements && Array.isArray(policyStatements) && policyStatements.length > 0) {
      sections.push('## Policy Statements\n');
      policyStatements.forEach((stmt: string) => sections.push(`- ${stmt}\n`));
      sections.push('');
    }
    const relatedStandards = frontmatter.related_standards || frontmatter.relatedStandards;
    if (relatedStandards && Array.isArray(relatedStandards) && relatedStandards.length > 0) {
      sections.push('## Related Standards\n');
      relatedStandards.forEach((std: string) => sections.push(`- ${std}\n`));
      sections.push('');
    }
  }

  // Standard-specific sections
  if (type === 'standard') {
    if (frontmatter.area) {
      sections.push('## Area\n', `${frontmatter.area}\n`);
    }
    if (frontmatter.purpose) {
      sections.push('## Purpose\n', `${frontmatter.purpose}\n`);
    }
    if (frontmatter.scope) {
      sections.push('## Scope\n', `${frontmatter.scope}\n`);
    }
    if (frontmatter.controls && Array.isArray(frontmatter.controls) && frontmatter.controls.length > 0) {
      sections.push('## Controls\n');
      frontmatter.controls.forEach((control: string) => sections.push(`- ${control}\n`));
      sections.push('');
    }
    if (frontmatter.compliance && typeof frontmatter.compliance === 'object') {
      sections.push('## Compliance Mappings\n');
      Object.entries(frontmatter.compliance).forEach(([framework, controls]) => {
        sections.push(`- **${framework}**: ${Array.isArray(controls) ? controls.join(', ') : controls}\n`);
      });
      sections.push('');
    }
    const relatedPolicies = frontmatter.related_policies || frontmatter.relatedPolicies;
    if (relatedPolicies && Array.isArray(relatedPolicies) && relatedPolicies.length > 0) {
      sections.push('## Related Policies\n');
      relatedPolicies.forEach((policy: string) => sections.push(`- ${policy}\n`));
      sections.push('');
    }
  }

  // Capability-specific sections
  if (type === 'capability') {
    if (frontmatter.domain) {
      sections.push('## Domain\n', `${frontmatter.domain}\n`);
    }
    if (frontmatter.maturity) {
      sections.push('## Maturity Level\n', `${frontmatter.maturity}\n`);
    }
    if (frontmatter.purpose) {
      sections.push('## Purpose\n', `${frontmatter.purpose}\n`);
    }
    if (frontmatter.scope) {
      sections.push('## Scope\n', `${frontmatter.scope}\n`);
    }
    if (frontmatter.metrics && Array.isArray(frontmatter.metrics) && frontmatter.metrics.length > 0) {
      sections.push('## Metrics\n');
      frontmatter.metrics.forEach((metric: string) => sections.push(`- ${metric}\n`));
      sections.push('');
    }
    if (frontmatter.evidence && Array.isArray(frontmatter.evidence) && frontmatter.evidence.length > 0) {
      sections.push('## Evidence\n');
      frontmatter.evidence.forEach((item: string) => sections.push(`- ${item}\n`));
      sections.push('');
    }
    if (frontmatter.notes) {
      sections.push('## Notes\n', `${frontmatter.notes}\n`);
    }
  }

  // PRD-specific sections
  if (type === 'prd') {
    if (frontmatter.background) {
      sections.push('## Background\n', `${frontmatter.background}\n`);
    }
    if (frontmatter.goals && Array.isArray(frontmatter.goals) && frontmatter.goals.length > 0) {
      sections.push('## Goals\n');
      frontmatter.goals.forEach((goal: string) => sections.push(`- ${goal}\n`));
      sections.push('');
    }
    const inScope = frontmatter.in_scope || frontmatter.inScope;
    if (inScope && Array.isArray(inScope) && inScope.length > 0) {
      sections.push('## In Scope\n');
      inScope.forEach((item: string) => sections.push(`- ${item}\n`));
      sections.push('');
    }
    const outOfScope = frontmatter.out_of_scope || frontmatter.outOfScope;
    if (outOfScope && Array.isArray(outOfScope) && outOfScope.length > 0) {
      sections.push('## Out of Scope\n');
      outOfScope.forEach((item: string) => sections.push(`- ${item}\n`));
      sections.push('');
    }
    if (frontmatter.milestones && Array.isArray(frontmatter.milestones) && frontmatter.milestones.length > 0) {
      sections.push('## Milestones\n');
      frontmatter.milestones.forEach((milestone: any) => {
        if (typeof milestone === 'string') {
          sections.push(`### ${milestone}\n`);
        } else if (typeof milestone === 'object' && milestone.name) {
          sections.push(`### ${milestone.name}\n`);
          if (milestone.description) sections.push(`${milestone.description}\n`);
          if (milestone.deliverables && Array.isArray(milestone.deliverables)) {
            milestone.deliverables.forEach((d: string) => sections.push(`- ${d}\n`));
          }
          sections.push('');
        }
      });
      sections.push('');
    }
    const successMetrics = frontmatter.success_metrics || frontmatter.successMetrics;
    if (successMetrics && Array.isArray(successMetrics) && successMetrics.length > 0) {
      sections.push('## Success Metrics\n');
      successMetrics.forEach((metric: string) => sections.push(`- ${metric}\n`));
      sections.push('');
    }
  }

  // Meeting-specific sections
  if (type === 'meeting') {
    if (frontmatter.context) {
      sections.push('## Meeting Details\n', `${frontmatter.context}\n`);
    }
    if (frontmatter.followups && Array.isArray(frontmatter.followups) && frontmatter.followups.length > 0) {
      sections.push('## Decisions & Next Steps\n', '**Follow-ups:**\n\n');
      frontmatter.followups.forEach((item: string) => sections.push(`- ${item}\n`));
      sections.push('');
    }
  }

  // Runbook-specific sections
  if (type === 'runbook') {
    if (frontmatter.service) {
      sections.push('## Service\n', `${frontmatter.service}\n`, '');
    }
    if (frontmatter.alerts && Array.isArray(frontmatter.alerts) && frontmatter.alerts.length > 0) {
      sections.push('## Alerts\n');
      frontmatter.alerts.forEach((alert: string) => sections.push(`- ${alert}\n`));
      sections.push('');
    }
    const diagnosisSteps = frontmatter.diagnosis_steps || frontmatter.diagnosisSteps;
    if (diagnosisSteps && Array.isArray(diagnosisSteps) && diagnosisSteps.length > 0) {
      sections.push('## Diagnosis Steps\n');
      diagnosisSteps.forEach((step: string, idx: number) => sections.push(`${idx + 1}. ${step}\n`));
      sections.push('');
    }
    const remediationSteps = frontmatter.remediation_steps || frontmatter.remediationSteps;
    if (remediationSteps && Array.isArray(remediationSteps) && remediationSteps.length > 0) {
      sections.push('## Remediation Steps\n');
      remediationSteps.forEach((step: string, idx: number) => sections.push(`${idx + 1}. ${step}\n`));
      sections.push('');
    }
    if (frontmatter.escalation) {
      sections.push('## Escalation\n', `${frontmatter.escalation}\n`, '');
    }
    if (frontmatter.dashboards && Array.isArray(frontmatter.dashboards) && frontmatter.dashboards.length > 0) {
      sections.push('## Dashboards\n');
      frontmatter.dashboards.forEach((dashboard: string) => sections.push(`- ${dashboard}\n`));
      sections.push('');
    }
  }

  // Policy-specific sections
  if (type === 'policy') {
    if (frontmatter.statements && Array.isArray(frontmatter.statements) && frontmatter.statements.length > 0) {
      sections.push('## Policy Statements\n');
      frontmatter.statements.forEach((statement: string) => sections.push(`- ${statement}\n`));
      sections.push('');
    }
  }

  // Standard-specific sections
  if (type === 'standard') {
    if (frontmatter.mappings) {
      sections.push('## Compliance Mappings\n', `${frontmatter.mappings}\n`, '');
    }
  }

  return sections;
}

function cleanFrontmatter(frontmatter: DocFrontmatter, type: string): DocFrontmatter {
  const fieldsToRemove = BODY_FIELDS_BY_TYPE[type] || [];
  const cleaned = { ...frontmatter };

  // Remove all body content fields
  fieldsToRemove.forEach(field => {
    delete cleaned[field];
  });

  return cleaned;
}

function parseExistingSections(body: string): Map<string, { content: string; hasPlaceholder: boolean }> {
  const sections = new Map<string, { content: string; hasPlaceholder: boolean }>();
  const lines = body.split('\n');
  let currentSection: string | null = null;
  let currentContent: string[] = [];

  for (const line of lines) {
    const heading = line.match(/^##\s+(.+)$/);
    if (heading) {
      // Save previous section
      if (currentSection) {
        const content = currentContent.join('\n').trim();
        const hasPlaceholder = content.includes('_[TODO: Complete this section]_') ||
                              content.includes('\\_\\[TODO: Complete this section]\\_') ||
                              content === '';
        sections.set(currentSection.toLowerCase(), { content, hasPlaceholder });
      }
      // Start new section
      currentSection = heading[1].trim();
      currentContent = [];
    } else if (currentSection) {
      currentContent.push(line);
    }
  }

  // Save last section
  if (currentSection) {
    const content = currentContent.join('\n').trim();
    const hasPlaceholder = content.includes('_[TODO: Complete this section]_') ||
                          content.includes('\\_\\[TODO: Complete this section]\\_') ||
                          content === '';
    sections.set(currentSection.toLowerCase(), { content, hasPlaceholder });
  }

  return sections;
}

function mergeSections(
  frontmatter: DocFrontmatter,
  type: string,
  existingBody: string
): string {
  const existingSections = parseExistingSections(existingBody);
  const lines: string[] = [];
  const processedSections = new Set<string>();

  // Helper to add a section if needed
  const addSection = (title: string, content: string) => {
    const normalizedTitle = title.toLowerCase();
    const existing = existingSections.get(normalizedTitle);

    // Skip if section exists with real content
    if (existing && !existing.hasPlaceholder) {
      return false;
    }

    // Add section (either new or replacing placeholder)
    lines.push(`## ${title}\n`);
    lines.push(content);
    lines.push('');
    processedSections.add(normalizedTitle);
    return true;
  };

  // Process type-specific sections from frontmatter
  if (type === 'process') {
    if (frontmatter.purpose) addSection('Purpose', frontmatter.purpose);
    if (frontmatter.scope) addSection('Scope', frontmatter.scope);
    if (frontmatter.roles && Array.isArray(frontmatter.roles) && frontmatter.roles.length > 0) {
      const content = frontmatter.roles.map((r: string) => `- **${r}**`).join('\n');
      addSection('Roles and Responsibilities', content);
    }
    if (frontmatter.triggers) addSection('Triggers', frontmatter.triggers);
    if (frontmatter.inputs && Array.isArray(frontmatter.inputs) && frontmatter.inputs.length > 0) {
      const content = frontmatter.inputs.map((i: string) => `- ${i}`).join('\n');
      addSection('Inputs', content);
    }
    if (frontmatter.outputs && Array.isArray(frontmatter.outputs) && frontmatter.outputs.length > 0) {
      const content = frontmatter.outputs.map((o: string) => `- ${o}`).join('\n');
      addSection('Outputs', content);
    }
    if (frontmatter.steps && Array.isArray(frontmatter.steps) && frontmatter.steps.length > 0) {
      const content = frontmatter.steps.map((s: string) => `1. ${s}`).join('\n');
      addSection('Steps', content);
    }
    if (frontmatter.controls && Array.isArray(frontmatter.controls) && frontmatter.controls.length > 0) {
      const content = frontmatter.controls.map((c: string) => `- ${c}`).join('\n');
      addSection('Controls', content);
    }
  }

  if (type === 'sop') {
    if (frontmatter.purpose) addSection('Purpose', frontmatter.purpose);
    if (frontmatter.scope) addSection('Scope', frontmatter.scope);
    const relatedProcess = frontmatter.related_process || frontmatter.relatedProcess;
    if (relatedProcess) addSection('Related Process', typeof relatedProcess === 'string' ? relatedProcess : relatedProcess.join(', '));
    if (frontmatter.preconditions && Array.isArray(frontmatter.preconditions) && frontmatter.preconditions.length > 0) {
      const content = frontmatter.preconditions.map((p: string) => `- ${p}`).join('\n');
      addSection('Preconditions', content);
    }
    if (frontmatter.materials && Array.isArray(frontmatter.materials) && frontmatter.materials.length > 0) {
      const content = frontmatter.materials.map((m: string) => `- ${m}`).join('\n');
      addSection('Materials/Access', content);
    }
    const stepList = frontmatter.step_list || frontmatter.stepList || frontmatter.procedure;
    if (stepList && Array.isArray(stepList) && stepList.length > 0) {
      const content = stepList.map((p: string) => `1. ${p}`).join('\n');
      addSection('Procedure', content);
    }
    if (frontmatter.validation) {
      addSection('Validation', typeof frontmatter.validation === 'string' ? frontmatter.validation : frontmatter.validation.join('\n'));
    }
    if (frontmatter.rollback) {
      addSection('Rollback', typeof frontmatter.rollback === 'string' ? frontmatter.rollback : frontmatter.rollback.join('\n'));
    }
    if (frontmatter.references && Array.isArray(frontmatter.references) && frontmatter.references.length > 0) {
      const content = frontmatter.references.map((r: string) => `- ${r}`).join('\n');
      addSection('References', content);
    }
  }

  if (type === 'policy') {
    if (frontmatter.purpose) addSection('Purpose', frontmatter.purpose);
    if (frontmatter.scope) addSection('Scope', frontmatter.scope);
    if (frontmatter.rationale) addSection('Rationale', frontmatter.rationale);
    const policyStatements = frontmatter.policy_statements || frontmatter.policyStatements;
    if (policyStatements && Array.isArray(policyStatements) && policyStatements.length > 0) {
      const content = policyStatements.map((s: string) => `- ${s}`).join('\n');
      addSection('Policy Statements', content);
    }
    const relatedStandards = frontmatter.related_standards || frontmatter.relatedStandards;
    if (relatedStandards && Array.isArray(relatedStandards) && relatedStandards.length > 0) {
      const content = relatedStandards.map((s: string) => `- ${s}`).join('\n');
      addSection('Related Standards', content);
    }
  }

  if (type === 'standard') {
    if (frontmatter.area) addSection('Area', frontmatter.area);
    if (frontmatter.purpose) addSection('Purpose', frontmatter.purpose);
    if (frontmatter.scope) addSection('Scope', frontmatter.scope);
    if (frontmatter.controls && Array.isArray(frontmatter.controls) && frontmatter.controls.length > 0) {
      const content = frontmatter.controls.map((c: string) => `- ${c}`).join('\n');
      addSection('Controls', content);
    }
    if (frontmatter.compliance && typeof frontmatter.compliance === 'object') {
      const content = Object.entries(frontmatter.compliance)
        .map(([framework, controls]) => `- **${framework}**: ${Array.isArray(controls) ? controls.join(', ') : controls}`)
        .join('\n');
      addSection('Compliance Mappings', content);
    }
    const relatedPolicies = frontmatter.related_policies || frontmatter.relatedPolicies;
    if (relatedPolicies && Array.isArray(relatedPolicies) && relatedPolicies.length > 0) {
      const content = relatedPolicies.map((p: string) => `- ${p}`).join('\n');
      addSection('Related Policies', content);
    }
  }

  if (type === 'capability') {
    if (frontmatter.domain) addSection('Domain', frontmatter.domain);
    if (frontmatter.maturity) addSection('Maturity Level', frontmatter.maturity);
    if (frontmatter.purpose) addSection('Purpose', frontmatter.purpose);
    if (frontmatter.scope) addSection('Scope', frontmatter.scope);
    if (frontmatter.metrics && Array.isArray(frontmatter.metrics) && frontmatter.metrics.length > 0) {
      const content = frontmatter.metrics.map((m: string) => `- ${m}`).join('\n');
      addSection('Metrics', content);
    }
    if (frontmatter.evidence && Array.isArray(frontmatter.evidence) && frontmatter.evidence.length > 0) {
      const content = frontmatter.evidence.map((e: string) => `- ${e}`).join('\n');
      addSection('Evidence', content);
    }
    if (frontmatter.notes) addSection('Notes', frontmatter.notes);
  }

  if (type === 'prd') {
    if (frontmatter.background) addSection('Background', frontmatter.background);
    if (frontmatter.goals && Array.isArray(frontmatter.goals) && frontmatter.goals.length > 0) {
      const content = frontmatter.goals.map((g: string) => `- ${g}`).join('\n');
      addSection('Goals', content);
    }
    const inScope = frontmatter.in_scope || frontmatter.inScope;
    if (inScope && Array.isArray(inScope) && inScope.length > 0) {
      const content = inScope.map((i: string) => `- ${i}`).join('\n');
      addSection('In Scope', content);
    }
    const outOfScope = frontmatter.out_of_scope || frontmatter.outOfScope;
    if (outOfScope && Array.isArray(outOfScope) && outOfScope.length > 0) {
      const content = outOfScope.map((o: string) => `- ${o}`).join('\n');
      addSection('Out of Scope', content);
    }
    if (frontmatter.milestones && Array.isArray(frontmatter.milestones) && frontmatter.milestones.length > 0) {
      const milestoneLines: string[] = [];
      frontmatter.milestones.forEach((milestone: any) => {
        if (typeof milestone === 'string') {
          milestoneLines.push(`### ${milestone}`);
        } else if (typeof milestone === 'object' && milestone.name) {
          milestoneLines.push(`### ${milestone.name}`);
          if (milestone.description) milestoneLines.push(milestone.description);
          if (milestone.deliverables && Array.isArray(milestone.deliverables)) {
            milestone.deliverables.forEach((d: string) => milestoneLines.push(`- ${d}`));
          }
          milestoneLines.push('');
        }
      });
      addSection('Milestones', milestoneLines.join('\n'));
    }
    const successMetrics = frontmatter.success_metrics || frontmatter.successMetrics;
    if (successMetrics && Array.isArray(successMetrics) && successMetrics.length > 0) {
      const content = successMetrics.map((m: string) => `- ${m}`).join('\n');
      addSection('Success Metrics', content);
    }
  }

  if (type === 'meeting') {
    // Add context to Meeting Details section if present
    if (frontmatter.context) {
      const existing = existingSections.get('meeting details');
      if (existing && existing.hasPlaceholder) {
        addSection('Meeting Details', frontmatter.context);
      }
    }
    
    // Add followups to Decisions & Next Steps if present
    if (frontmatter.followups && Array.isArray(frontmatter.followups) && frontmatter.followups.length > 0) {
      const existing = existingSections.get('decisions & next steps') || existingSections.get('decisions and next steps');
      if (existing && existing.hasPlaceholder) {
        const content = '**Follow-ups:**\n\n' + frontmatter.followups.map((f: string) => `- ${f}`).join('\n');
        addSection('Decisions & Next Steps', content);
      }
    }
  }

  if (type === 'sow') {
    if (frontmatter.objective) addSection('Objective', frontmatter.objective);
    const scopeOfWork = frontmatter.scope_of_work || frontmatter.scopeOfWork;
    if (scopeOfWork && typeof scopeOfWork === 'object') {
      const lines: string[] = [];
      Object.entries(scopeOfWork).forEach(([key, value]) => {
        lines.push(`**${key}**:`);
        if (Array.isArray(value)) {
          value.forEach((item: string) => lines.push(`- ${item}`));
        } else {
          lines.push(`${value}`);
        }
      });
      addSection('Scope of Work', lines.join('\n'));
    }
    if (frontmatter.deliverables && Array.isArray(frontmatter.deliverables)) {
      const content = frontmatter.deliverables.map((d: string) => `- ${d}`).join('\n');
      addSection('Deliverables', content);
    }
    const outOfScope = frontmatter.out_of_scope || frontmatter.outOfScope;
    if (outOfScope && Array.isArray(outOfScope)) {
      const content = outOfScope.map((o: string) => `- ${o}`).join('\n');
      addSection('Out of Scope', content);
    }
    const timelineMilestones = frontmatter.timeline_milestones || frontmatter.timelineMilestones;
    if (timelineMilestones && typeof timelineMilestones === 'object') {
      const lines: string[] = [];
      Object.entries(timelineMilestones).forEach(([key, value]) => {
        lines.push(`**${key}**: ${value}`);
      });
      addSection('Timeline and Milestones', lines.join('\n'));
    }
    const acceptanceCriteria = frontmatter.acceptance_criteria || frontmatter.acceptanceCriteria;
    if (acceptanceCriteria && Array.isArray(acceptanceCriteria)) {
      const content = acceptanceCriteria.map((c: string) => `- ${c}`).join('\n');
      addSection('Acceptance Criteria', content);
    }
    if (frontmatter.assumptions && Array.isArray(frontmatter.assumptions)) {
      const content = frontmatter.assumptions.map((a: string) => `- ${a}`).join('\n');
      addSection('Assumptions', content);
    }
    if (frontmatter.dependencies && Array.isArray(frontmatter.dependencies)) {
      const content = frontmatter.dependencies.map((d: string) => `- ${d}`).join('\n');
      addSection('Dependencies', content);
    }
    const risksAndMitigations = frontmatter.risks_and_mitigations || frontmatter.risksAndMitigations;
    if (risksAndMitigations && typeof risksAndMitigations === 'object') {
      const lines: string[] = [];
      Object.entries(risksAndMitigations).forEach(([risk, mitigation]) => {
        lines.push(`**${risk}**: ${mitigation}`);
      });
      addSection('Risks and Mitigations', lines.join('\n'));
    }
    const changeControl = frontmatter.change_control || frontmatter.changeControl;
    if (changeControl) {
      addSection('Change Control', typeof changeControl === 'string' ? changeControl : JSON.stringify(changeControl, null, 2));
    }
    const pricingPaymentTerms = frontmatter.pricing_payment_terms || frontmatter.pricingPaymentTerms;
    if (pricingPaymentTerms) {
      addSection('Pricing and Payment Terms', typeof pricingPaymentTerms === 'string' ? pricingPaymentTerms : JSON.stringify(pricingPaymentTerms, null, 2));
    }
    const ipAndConfidentiality = frontmatter.ip_and_confidentiality || frontmatter.ipAndConfidentiality;
    if (ipAndConfidentiality) {
      addSection('IP and Confidentiality', typeof ipAndConfidentiality === 'string' ? ipAndConfidentiality : JSON.stringify(ipAndConfidentiality, null, 2));
    }
    const communicationCadence = frontmatter.communication_cadence || frontmatter.communicationCadence;
    if (communicationCadence) {
      addSection('Communication Cadence', typeof communicationCadence === 'string' ? communicationCadence : JSON.stringify(communicationCadence, null, 2));
    }
    if (frontmatter.approval && typeof frontmatter.approval === 'object') {
      const lines: string[] = [];
      Object.entries(frontmatter.approval).forEach(([key, value]) => {
        lines.push(`**${key}**: ${value}`);
      });
      addSection('Approval', lines.join('\n'));
    }
  }

  // Add remaining existing body sections that weren't processed
  const bodyLines = existingBody.split('\n');
  let currentSection: string | null = null;
  let currentLines: string[] = [];
  let inUnprocessedSection = false;
  let hasAnyH2Headers = false;

  for (const line of bodyLines) {
    const heading = line.match(/^##\s+(.+)$/);
    if (heading) {
      hasAnyH2Headers = true;
      // Output previous unprocessed section
      if (inUnprocessedSection && currentLines.length > 0) {
        lines.push(...currentLines);
        lines.push('');
      }

      currentSection = heading[1].trim();
      const normalized = currentSection.toLowerCase();
      inUnprocessedSection = !processedSections.has(normalized);
      currentLines = [line];
    } else if (inUnprocessedSection) {
      currentLines.push(line);
    }
  }

  // Output final unprocessed section
  if (inUnprocessedSection && currentLines.length > 0) {
    lines.push(...currentLines);
  }

  // CRITICAL FIX: If the file had NO H2 headers but has body content,
  // preserve ALL of it under a "Legacy Content" section at the end
  if (!hasAnyH2Headers && existingBody.trim().length > 0) {
    lines.push('');
    lines.push('## Legacy Content (Please Review and Reorganize)');
    lines.push('');
    lines.push('<!-- This content was preserved from the original file. Please reorganize it into the appropriate sections above. -->');
    lines.push('');
    lines.push(existingBody.trim());
  }

  return lines.join('\n').trim();
}

async function migrateFile(filePath: string, dryRun: boolean = false): Promise<boolean> {
  const content = await fs.readFile(filePath, 'utf-8');

  // Extract frontmatter and body
  const match = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) {
    console.log(`⚠️  Skipping ${path.basename(filePath)}: No frontmatter found`);
    return false;
  }

  const [, frontmatterStr, existingBody] = match;
  const frontmatter = yaml.load(frontmatterStr) as DocFrontmatter;

  if (!frontmatter.type) {
    console.log(`⚠️  Skipping ${path.basename(filePath)}: No type specified`);
    return false;
  }

  const type = frontmatter.type;
  const fieldsToMigrate = BODY_FIELDS_BY_TYPE[type] || [];

  // Check if any fields need migration
  const hasFieldsToMigrate = fieldsToMigrate.some(field => frontmatter[field] !== undefined);

  if (!hasFieldsToMigrate) {
    return false;
  }

  // Clean frontmatter
  const cleanedFrontmatter = cleanFrontmatter(frontmatter, type);

  // Merge sections intelligently
  const newBody = mergeSections(frontmatter, type, existingBody);

  // Reconstruct file
  const newContent = `---\n${yaml.dump(cleanedFrontmatter, { lineWidth: -1 })}---\n${newBody}\n`;

  if (!dryRun) {
    await fs.writeFile(filePath, newContent, 'utf-8');
  }

  return true;
}

async function main() {
  const dryRun = process.argv.includes('--dry-run');
  const contentDir = path.resolve(__dirname, '../../../content');

  console.log(dryRun ? '🔍 DRY RUN MODE - No files will be modified\n' : '📝 MIGRATION MODE - Files will be updated\n');

  const allFiles = await glob('**/*.md', {
    cwd: contentDir,
    absolute: true,
    ignore: ['**/node_modules/**', '**/dist/**'],
  });

  console.log(`Found ${allFiles.length} markdown files\n`);

  let migrated = 0;
  let skipped = 0;
  let errors = 0;

  for (const file of allFiles) {
    try {
      const wasMigrated = await migrateFile(file, dryRun);
      if (wasMigrated) {
        console.log(`✅ ${dryRun ? 'Would migrate' : 'Migrated'} ${path.relative(contentDir, file)}`);
        migrated++;
      } else {
        skipped++;
      }
    } catch (error) {
      console.error(`❌ Error processing ${path.basename(file)}:`, error);
      errors++;
    }
  }

  console.log(`\n📊 Summary:`);
  console.log(`   ${dryRun ? 'Would migrate' : 'Migrated'}: ${migrated}`);
  console.log(`   Skipped: ${skipped}`);
  console.log(`   Errors: ${errors}`);

  if (dryRun) {
    console.log(`\n💡 Run without --dry-run to apply changes`);
  }
}

main().catch(console.error);
