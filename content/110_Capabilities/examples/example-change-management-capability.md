---
id: change-management-capability
type: capability
title: Change Management Capability
status: approved
owner: Head of Engineering
created: '2025-10-18T00:00:00.000Z'
updated: '2025-10-18T00:00:00.000Z'
tags:
  - capability
  - governance
  - maturity
summary: >-
  Assesses the organization's maturity in safely executing production
  changes. USE A CAPABILITY when you need to assess and track an
  organization's MATURITY in a specific area. Capabilities answer
  "how good are we at X?" They link to evidence (policies, standards,
  processes, metrics) and score maturity on a 0-5 scale. Use them for
  maturity assessments, due diligence, and tracking improvement over
  time. Compare: a Policy says what must happen; a Standard defines the
  controls; a Capability measures how well the organization actually
  does it in practice, with evidence links back to those documents.
evidence_links:
  - change-management-process
  - change-management-policy
  - change-control-standard
example: true
---

## Domain

- SDLC
- Operations
- Governance

## Maturity (0-5)

**Current score: 3 / 5 (Defined)**

- **Level 0 - Initial**: No change management. Engineers deploy directly to production without review.
- **Level 1 - Ad hoc**: Some changes are reviewed, but there's no formal process. Depends on individual discipline.
- **Level 2 - Repeatable**: Change tickets exist but aren't consistently used. Reviews happen but aren't enforced.
- **Level 3 - Defined** (current): Formal policy, standard, and process are documented. Change tickets are mandatory. Peer review is enforced by CI pipeline. Rollback plans are required.
- **Level 4 - Managed**: Metrics are actively tracked (change failure rate, lead time). Automated compliance checks in the deployment pipeline. Regular process audits.
- **Level 5 - Optimizing**: Continuous improvement based on metrics. Automated canary deployments. Zero-downtime deployments standard. Change failure rate < 5%.

**Gap to Level 4**: Need to implement automated DORA metrics collection, add compliance checks to the deployment pipeline, and establish quarterly process audits.

## Metrics

- Change failure rate (CFR): Currently 8%, target < 5%
- Lead time for changes: Currently 2 days, target < 1 day
- Deployment frequency: Currently daily, target multiple per day
- Mean time to recovery (MTTR): Currently 2 hours, target < 30 minutes
- Percentage of changes with peer review: Currently 95%, target 100%
- Percentage of changes with rollback plan: Currently 85%, target 100%

## Evidence Links

- [[example-change-management-policy|Change Management Policy]] - Organizational mandate for change control
- [[example-change-control-standard|Change Control Standard]] - Specific controls and compliance mappings
- [[example-change-management-process|Change Management Process]] - Operational workflow for executing changes
- [[example-production-deployment-sop|Production Deployment SOP]] - Detailed deployment procedure
- [[example-service-outage-runbook|Service Outage Runbook]] - Incident response when changes cause outages

## Notes

The organization moved from Level 2 to Level 3 in Q3 2025 after formalizing the change management policy and deploying CI-enforced review gates.

Key improvements needed for Level 4:
- Implement automated DORA metrics dashboard (tracked in quarterly OKRs)
- Add pre-deploy compliance checks that verify change ticket approval status before allowing deployment
- Establish quarterly change management process audits with findings tracked in Jira
- Reduce change failure rate from 8% to < 5% by improving test coverage requirements
