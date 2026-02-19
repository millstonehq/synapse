---
id: PROCESS-054
type: process
title: Customer Support Escalation Process
status: draft
owner: Platform Lead
created: '2025-11-29T06:29:01.652Z'
updated: '2025-11-20T17:15:55.995Z'
tags:
  - process
  - customer-portal
summary: Customer Support Escalation Process
related_standards:
  - STANDARD-054
  - STANDARD-051
related_sops:
  - SOP-082
  - SOP-087
related_systems:
  - SYSTEM-042
example: true
---

## Purpose

This process defines the path for escalating Customer Portal support issues that cannot be resolved at tier-1 support to engineering teams. Without a defined escalation path, issues that require engineering investigation sit unresolved in support queues, customers are not kept informed, and duplicate investigations waste engineering time. This process ensures timely routing, clear ownership, and customer communication at each escalation level.

## Scope

- Support tickets raised by customers through the portal that require engineering investigation
- Bugs reproducible in the portal environment that cannot be resolved with standard troubleshooting steps
- Performance issues reported by customers that are not captured by existing monitoring
- Data discrepancies or account issues requiring backend investigation

## Roles and Responsibilities

- **Tier-1 Support Agent**: Performs initial triage, attempts resolution using knowledge base, escalates if unresolved after 30 minutes
- **Tier-2 Support Engineer**: Investigates escalated tickets with deeper access; reproduces issues and escalates to engineering if needed
- **Platform Lead**: Receives engineering escalations, assigns to appropriate engineer, tracks resolution SLA
- **On-Call Engineer**: Handles urgent escalations for portal availability or data integrity issues during on-call hours

## Triggers

- Tier-1 agent cannot resolve a ticket within 30 minutes using standard troubleshooting
- Customer reports a data integrity issue or potential data loss
- Multiple customers report the same issue in the same time window (pattern detection)
- An escalated ticket remains unresolved for more than 2 business days at tier-2

## Inputs

- Original support ticket with customer account details and issue description
- Steps to reproduce (or confirmation that the issue is not reproducible)
- Tier-1 and tier-2 investigation notes
- Portal error logs or session recording if available

## Outputs

- Root cause identified and documented in the ticket
- Fix deployed or workaround provided to the customer
- Customer status update sent at each escalation level transition
- Post-resolution review ticket created for recurring issues

## Steps

1. Tier-1 agent triages ticket, attempts standard resolution, and documents troubleshooting steps taken
2. If unresolved after 30 minutes, agent escalates to tier-2 support and notifies customer of escalation with expected response time
3. Tier-2 support engineer investigates with portal admin access, attempts reproduction, and checks recent deploy history
4. If root cause is a portal bug or infrastructure issue, tier-2 escalates to Platform Lead with reproduction steps and severity assessment
5. Platform Lead assigns the ticket to an engineer and sets investigation SLA based on customer impact severity
6. Engineer investigates, documents root cause, and either deploys a fix or provides a workaround with timeline for permanent fix
7. Platform Lead sends customer status update with root cause summary and resolution timeline
8. On ticket closure, tier-2 updates knowledge base if the issue pattern is likely to recur

## Controls

- P1 escalations (portal unavailable, data loss risk) must reach the on-call engineer within 15 minutes
- Customer must receive a status update within 4 business hours at every escalation level
- All engineering escalations must be linked to a tracked ticket; no out-of-band investigation without a ticket
