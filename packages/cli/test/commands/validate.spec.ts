import fsExtra from 'fs-extra';
const fs = fsExtra;
import * as path from 'path';
import { validate } from '../../src/commands/validate';
import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';

describe('Validate Command - Duplicate Detection', () => {
  const testDir = path.join(process.cwd(), 'test-vault-duplicates');
  const contentDir = path.join(testDir, 'content');
  const schemaDir = path.join(contentDir, 'schemas');
  
  beforeEach(async () => {
    // Create test directory structure
    await fs.ensureDir(path.join(contentDir, '10_Policies'));
    await fs.ensureDir(schemaDir);
    
    // Copy schemas
    const realSchemaDir = path.resolve(process.cwd(), '../../schemas/frontmatter');
    const schemas = await fs.readdir(realSchemaDir);
    for (const schema of schemas) {
      if (schema.endsWith('.json')) {
        await fs.copy(
          path.join(realSchemaDir, schema),
          path.join(schemaDir, schema)
        );
      }
    }
  });
  
  afterEach(async () => {
    await fs.remove(testDir);
  });
  
  it('should detect duplicate titles within the same document type', async () => {
    // Create two policies with similar titles
    await fs.writeFile(
      path.join(contentDir, '10_Policies/POL001-data-protection.md'),
      `---
type: policy
id: data-protection-1
title: Data Protection
owner: Security Team
summary: First data protection policy
scope: All systems
rationale: Protect data
---

# Data Protection Policy 1`
    );
    
    await fs.writeFile(
      path.join(contentDir, '10_Policies/POL002-data-protection.md'),
      `---
type: policy
id: data-protection-2
title: Data Protection
owner: Security Team
summary: Second data protection policy
scope: Cloud systems
rationale: Protect cloud data
---

# Data Protection Policy 2`
    );
    
    const result = await validate({
      contentDir,
      schemaDir,
      strict: true
    });
    
    // Should have a warning about duplicate titles
    const duplicateWarnings = result.issues.filter(i =>
      i.type === 'warning' &&
      i.message.includes('Multiple policy documents with similar title')
    );
    
    expect(duplicateWarnings.length).toBeGreaterThan(0);
    expect(duplicateWarnings[0].message).toContain('data-protection');
  });
  
  it('should not warn about duplicates in examples directory', async () => {
    // Create example and regular doc with same title
    await fs.ensureDir(path.join(contentDir, '00_Guides/Examples'));
    
    await fs.writeFile(
      path.join(contentDir, '10_Policies/POL001-change-management.md'),
      `---
type: policy
id: change-mgmt-1
title: Change Management
owner: CTO
summary: Production change management
scope: Production
rationale: Safety
example: false
---

# Change Management`
    );
    
    await fs.writeFile(
      path.join(contentDir, '00_Guides/Examples/Example - Change Management.md'),
      `---
type: policy
id: change-mgmt-example
title: Change Management
owner: CTO
summary: Example policy
scope: Example
rationale: Example
example: true
---

# Example Change Management`
    );
    
    const result = await validate({
      contentDir,
      schemaDir,
      strict: true
    });
    
    // Should not have warnings about the example duplicate
    const duplicateWarnings = result.issues.filter(i =>
      i.type === 'warning' &&
      i.message.includes('Multiple policy documents with similar title')
    );
    
    expect(duplicateWarnings.length).toBe(0);
  });
});

describe('Validate Command - Cross-link Rules', () => {
  const testDir = path.join(process.cwd(), 'test-vault');
  const contentDir = path.join(testDir, 'content');
  const schemaDir = path.join(contentDir, 'schemas');
  
  beforeEach(async () => {
    // Create test directory structure
    await fs.ensureDir(path.join(contentDir, '20_Standards'));
    await fs.ensureDir(path.join(contentDir, '30_Processes'));
    await fs.ensureDir(path.join(contentDir, '40_SOPs'));
    await fs.ensureDir(path.join(contentDir, '50_Runbooks'));
    await fs.ensureDir(path.join(contentDir, '70_Systems'));
    await fs.ensureDir(schemaDir);
    
    // Copy schemas
    const realSchemaDir = path.resolve(process.cwd(), '../../schemas/frontmatter');
    const schemas = await fs.readdir(realSchemaDir);
    for (const schema of schemas) {
      if (schema.endsWith('.json')) {
        await fs.copy(
          path.join(realSchemaDir, schema),
          path.join(schemaDir, schema)
        );
      }
    }
    
    // Create some reference documents
    await fs.writeFile(
      path.join(contentDir, '20_Standards/STD001-change-control-standard.md'),
      `---
type: standard
id: change-control-standard
title: Change Control Standard
status: approved
owner: Security Team
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Standards for change control processes
---

# Change Control Standard

This document defines the standards for change control.`
    );
    
    await fs.writeFile(
      path.join(contentDir, '70_Systems/SYS001-payments-api.md'),
      `---
type: system
id: payments-api
title: Payments API
status: approved
owner: Payments Team
owner_team: Payments Team
runtime: Node.js
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Core payments processing service
---

# Payments API

## Overview

The core payments processing service.

## Architecture

Node.js microservice`
    );
  });
  
  afterEach(async () => {
    // Clean up test directory
    await fs.remove(testDir);
  });
  
  describe('Process document validation', () => {
    it('should error when process has no related_standards', async () => {
      await fs.writeFile(
        path.join(contentDir, '30_Processes/PRC001-change-management.md'),
        `---
type: process
id: change-management
title: Change Management
status: approved
owner: Engineering Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Change management process
---

# Change Management Process

## Purpose
Manage changes

## Roles
- Change Owner

## Steps
- Submit change
- Review change`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: 'Process documents must reference at least one standard'
        })
      );
    });
    
    it('should error when process has empty related_standards array', async () => {
      await fs.writeFile(
        path.join(contentDir, '30_Processes/PRC001-change-management.md'),
        `---
type: process
id: change-management
title: Change Management
status: approved
owner: Engineering Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Change management process
related_standards: []
---

# Change Management Process

## Purpose
Manage changes

## Roles
- Change Owner

## Steps
- Submit change
- Review change`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: 'Process documents must reference at least one standard'
        })
      );
    });
    
    it('should pass when process has valid related_standards', async () => {
      await fs.writeFile(
        path.join(contentDir, '30_Processes/PRC001-change-management.md'),
        `---
type: process
id: change-management
title: Change Management
status: approved
owner: Engineering Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Change management process
related_standards:
  - "[[change-control-standard]]"
---

# Change Management Process

## Purpose
Manage changes

## Roles
- Change Owner

## Steps
- Submit change
- Review change`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => 
        i.type === 'error' && 
        i.message.includes('Process documents must reference')
      );
      expect(errors).toHaveLength(0);
    });
    
    it('should error when process references non-existent standard', async () => {
      await fs.writeFile(
        path.join(contentDir, '30_Processes/PRC001-change-management.md'),
        `---
type: process
id: change-management
title: Change Management
status: approved
owner: Engineering Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Change management process
related_standards:
  - "[[non-existent-standard]]"
---

# Change Management Process

## Purpose
Manage changes

## Roles
- Change Owner

## Steps
- Submit change
- Review change`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: expect.stringContaining('Referenced standard does not exist')
        })
      );
    });
  });
  
  describe('SOP document validation', () => {
    it('should error when SOP has no related_process', async () => {
      await fs.writeFile(
        path.join(contentDir, '40_SOPs/SOP001-deployment.md'),
        `---
type: sop
id: deployment-sop
title: Deployment Procedure
status: approved
owner: Release Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Deployment procedure
---

# Deployment SOP

## Steps
- Check prerequisites
- Deploy application`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: 'SOP must reference a parent process'
        })
      );
    });
    
    it('should error when SOP has empty related_process', async () => {
      await fs.writeFile(
        path.join(contentDir, '40_SOPs/SOP001-deployment.md'),
        `---
type: sop
id: deployment-sop
title: Deployment Procedure
status: approved
owner: Release Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Deployment procedure
related_process: ""
---

# Deployment SOP

## Steps
- Check prerequisites
- Deploy application`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: 'SOP must reference a parent process'
        })
      );
    });
    
    it('should pass when SOP has valid related_process', async () => {
      // First create a process to reference
      await fs.writeFile(
        path.join(contentDir, '30_Processes/PRC001-change-management.md'),
        `---
type: process
id: change-management
title: Change Management
status: approved
owner: Engineering Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Change management process
related_standards:
  - "[[change-control-standard]]"
---

# Change Management

## Purpose
Manage changes

## Roles
- Change Owner

## Steps
- Submit change`
      );

      await fs.writeFile(
        path.join(contentDir, '40_SOPs/SOP001-deployment.md'),
        `---
type: sop
id: deployment-sop
title: Deployment Procedure
status: approved
owner: Release Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Deployment procedure
related_process: "[[change-management]]"
---

# Deployment SOP

## Steps
- Check prerequisites
- Deploy application`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => 
        i.type === 'error' && 
        i.message.includes('SOP must reference')
      );
      expect(errors).toHaveLength(0);
    });
  });
  
  describe('Runbook document validation', () => {
    it('should error when runbook has no service', async () => {
      await fs.writeFile(
        path.join(contentDir, '50_Runbooks/RBK001-outage.md'),
        `---
type: runbook
id: outage-runbook
title: Service Outage
status: approved
owner: On-call Engineer
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Handle service outage
---

# Outage Runbook

## Diagnosis Steps
- Check logs
- Check metrics

## Remediation Steps
- Restart service
- Scale up`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: 'Runbook must reference a system/service'
        })
      );
    });
    
    it('should error when runbook has empty service', async () => {
      await fs.writeFile(
        path.join(contentDir, '50_Runbooks/RBK001-outage.md'),
        `---
type: runbook
id: outage-runbook
title: Service Outage
status: approved
owner: On-call Engineer
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Handle service outage
---

# Outage Runbook

## Service


## Diagnosis Steps
- Check logs
- Check metrics

## Remediation Steps
- Restart service
- Scale up`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: 'Runbook must reference a system/service'
        })
      );
    });
    
    it('should pass when runbook has valid service', async () => {
      await fs.writeFile(
        path.join(contentDir, '50_Runbooks/RBK001-outage.md'),
        `---
type: runbook
id: outage-runbook
title: Service Outage
status: approved
owner: On-call Engineer
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Handle service outage
---

# Outage Runbook

## Service
[[payments-api]]

## Diagnosis Steps
- Check logs
- Check metrics

## Remediation Steps
- Restart service
- Scale up`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => 
        i.type === 'error' && 
        i.message.includes('Runbook must reference')
      );
      expect(errors).toHaveLength(0);
    });
    
    it('should error when runbook references non-existent service', async () => {
      await fs.writeFile(
        path.join(contentDir, '50_Runbooks/RBK001-outage.md'),
        `---
type: runbook
id: outage-runbook
title: Service Outage
status: approved
owner: On-call Engineer
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Handle service outage
---

# Outage Runbook

## Service
[[non-existent-service]]

## Diagnosis Steps
- Check logs
- Check metrics

## Remediation Steps
- Restart service
- Scale up`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: expect.stringContaining('Referenced service does not exist')
        })
      );
    });
  });
  
  describe('Wikilink validation in body', () => {
    it('should error when body contains non-existent wikilinks', async () => {
      await fs.writeFile(
        path.join(contentDir, '30_Processes/PRC001-change-management.md'),
        `---
type: process
id: change-management
title: Change Management
status: approved
owner: Engineering Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Change management process
related_standards:
  - "[[change-control-standard]]"
---

# Change Management

## Purpose
Manage changes

## Roles
- Change Owner

## Steps
- Submit change

See also [[non-existent-document]] for more details.`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => i.type === 'error');
      expect(errors).toContainEqual(
        expect.objectContaining({
          type: 'error',
          message: 'Referenced document does not exist: [[non-existent-document]]'
        })
      );
    });
    
    it('should pass when body contains valid wikilinks', async () => {
      await fs.writeFile(
        path.join(contentDir, '30_Processes/PRC001-change-management.md'),
        `---
type: process
id: change-management
title: Change Management
status: approved
owner: Engineering Manager
created: "2024-01-01T00:00:00.000Z"
updated: "2024-01-01T00:00:00.000Z"
tags: []
summary: Change management process
related_standards:
  - "[[change-control-standard]]"
---

# Change Management

## Purpose
Manage changes

## Roles
- Change Owner

## Steps
- Submit change

See also [[payments-api]] for system details.`
      );
      
      const result = await validate({ contentDir, schemaDir });
      
      const errors = result.issues.filter(i => 
        i.type === 'error' && 
        i.message.includes('Referenced document does not exist')
      );
      expect(errors).toHaveLength(0);
    });
  });
});