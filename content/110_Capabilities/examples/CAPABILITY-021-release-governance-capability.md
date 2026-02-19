---
id: CAPABILITY-021
type: capability
title: Release Governance Capability
status: approved
owner: Head of Engineering
created: '2025-10-14T02:54:47.193Z'
updated: '2026-09-12T19:52:01.154Z'
tags:
  - capability
  - ci-cd-platform
summary: Release Governance Capability
evidence_links:
  - POLICY-031
  - STANDARD-039
  - STANDARD-041
example: true
---

## Domain

- Deployment approval gates enforcing human sign-off for production deployments to high-risk services
- Canary deployment strategy providing progressive traffic shifting and automated analysis before full rollout
- Deployment window policy restricting production deployments to business hours for regulated services
- Change failure tracking measuring the rate of deployments requiring rollback or hotfix
- Artifact promotion enforcing that images pass vulnerability scanning and signing verification before reaching production

## Maturity (0-5)

- Approval gate coverage: 4/5 - Approval workflow is enforced for all SEV-1/SEV-2 risk-tier services; low-risk services use auto-approval; no exceptions without explicit waiver
- Canary deployment adoption: 3/5 - Canary rollouts are available for all services via ArgoCD Rollouts but only 60% of services have adopted them; remainder use rolling updates
- Change failure rate tracking: 3/5 - CFR is tracked in the DORA metrics dashboard for the fleet; per-team CFR visibility is available but not consistently reviewed
- Deployment window enforcement: 4/5 - Window restrictions for tier-1 services are enforced programmatically; tier-2 and below rely on team discipline
- Post-deploy monitoring: 4/5 - Automated post-deployment monitoring is live for 88% of services; automated rollback trigger enrolled for 75%

## Metrics

- Change failure rate (CFR): 3.8% this quarter (target: < 5%)
- Deployment frequency: 42 deployments/week fleet-wide (target: > 40)
- Mean time to rollback: 4.2 minutes average (target: < 5 minutes)
- Services with canary deployment enabled: 60% (target: 80% by end of quarter)
- Services enrolled in automated rollback: 75% (target: 100%)

## Evidence Links

- [[POLICY-031|POLICY-031]] - Release governance policy mandating approval gates and deployment window controls
- [[STANDARD-039|STANDARD-039]] - CI/CD standards specifying required pipeline gates for production deployments
- [[STANDARD-041|STANDARD-041]] - Artifact integrity standard requiring Cosign signing and Trivy scanning

## Notes

Release governance maturity improved significantly in Q4 after the deployment approval workflow launched and automated rollback was made available to all services. The primary gap is canary deployment adoption — teams using rolling updates have a higher incidence of post-deployment incidents because they lack the canary analysis safety net.

Expanding canary adoption to 80% of services by end of quarter is the top release governance priority. The platform team is creating a migration guide and running office hours for teams that have not yet adopted ArgoCD Rollouts.
