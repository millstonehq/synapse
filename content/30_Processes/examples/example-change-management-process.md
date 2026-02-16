---
id: change-management-process
type: process
title: Change Management Process
status: draft
owner: Engineering Manager
created: '2025-10-18T19:48:03.151Z'
updated: '2025-10-18T19:48:03.151Z'
tags:
  - process
summary: Defines how production changes are proposed, reviewed, approved, executed, and verified.
related_standards:
  - Change Control Standard
example: true
---
## Purpose

Ensure safe, auditable changes to production systems.

## Scope

All production services and infrastructure.

## Roles and Responsibilities

- Change Owner
- Reviewer
- Approver

## Triggers

New change request requiring production deployment

## Inputs

- Change request ticket
- Deployment plan

## Outputs

- Approved change
- Deployment record

## Steps

1. Submit change request with impact assessment and rollback plan
1. Peer review and approval
1. Schedule maintenance window
1. Execute deployment per runbook
1. Post-deploy verification and close ticket

## Controls

- Require peer review for high-risk changes
